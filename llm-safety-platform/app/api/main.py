"""FastAPI production gateway + admin APIs."""

from __future__ import annotations

from contextlib import asynccontextmanager
import json
import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path

from app.auth import Principal, get_db, require_admin, require_roles, require_vk, vk_service
from app.bootstrap import get_state
from app.db.models import (
    ApprovalRow,
    AuditDecisionRow,
    EventRow,
    PolicyBindingRow,
    PublishGateRow,
    RedTeamRunRow,
    VaultEntryRow,
)
from app.events import enums as E
from app.observability.chain_verify import verify_audit_rows, verify_chain_list
from app.policy import ScannerSpec
from sqlalchemy.orm import Session


@asynccontextmanager
async def _lifespan(_: FastAPI):
    """启动时校验并初始化共享状态，替代已废弃的 on_event。"""
    get_state()
    yield


app = FastAPI(title="LLM Safety Platform", version="2.0.0", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", response_model=None)
def readyz() -> dict[str, Any] | JSONResponse:
    st = get_state()
    if not st.chain_ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "audit_chain_integrity_failed", "chain": st.chain_error},
        )
    return {"status": "ready"}


@app.get("/metrics")
def prometheus_metrics() -> Response:
    return PlainTextResponse(get_state().metrics.render_prometheus(), media_type="text/plain")


class SafetyChatRequest(BaseModel):
    messages: list[dict[str, str]]
    invoke_model: bool = True
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    model: str = "mock-llm"
    deanonymize_output: bool = True
    system_prompt: str = ""
    rag_chunks: list[dict[str, Any]] = Field(default_factory=list)
    model_digest: str = ""
    session_id: str = ""


@app.post("/v1/safety/chat")
def safety_chat(
    body: SafetyChatRequest,
    principal: Principal = Depends(require_vk),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    st = get_state()
    assert principal.vk is not None
    if not st.chain_ok:
        raise HTTPException(status_code=503, detail={"audit_chain_integrity_failed": st.chain_error})
    vk = principal.vk
    if not st.quota.check_rpm(vk.key_id, vk.rpm_limit):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    binding_pre = st.policy.resolve(vk.tenant_id, vk.app_id)
    user_content = ""
    for m in reversed(body.messages):
        if m.get("role") == "user":
            user_content = m.get("content", "")
            break
    if not user_content:
        raise HTTPException(status_code=400, detail="user message required")
    est_tokens = max(1, len(user_content) // 4)
    if not st.quota.check_daily_tokens(
        vk.key_id, est_tokens, binding_pre.daily_token_budget
    ):
        raise HTTPException(status_code=429, detail="daily token budget exceeded")

    # L4 confirm_only path for critical production tools
    for tc in body.tool_calls:
        if tc.get("name") == "send_email":
            binding = binding_pre
            if binding.risk_tier == "critical" or binding.effect_cap != "production":
                # If not allowlisted, gateway will deny; if needs confirm:
                if "send_email" not in binding.tool_allowlist:
                    apr = st.approvals.enqueue(
                        db,
                        tenant_id=vk.tenant_id,
                        app_id=vk.app_id,
                        request_id="pre_" + uuid.uuid4().hex[:8],
                        action=tc,
                    )
                    st.metrics.inc('llm_safety_requests_total{decision="confirm_only"}')
                    return {
                        "decision": "confirm_only",
                        "approval_id": apr.approval_id,
                        "message": "tool requires human approval",
                    }

    with st.quota.concurrency_slot(vk.key_id, binding_pre.max_concurrency) as ok:
        if not ok:
            raise HTTPException(status_code=429, detail="concurrency limit exceeded")
        r = st.gateway.chat(
            tenant_id=vk.tenant_id,
            app_id=vk.app_id,
            user_content=user_content,
            invoke_model=body.invoke_model,
            tool_calls=body.tool_calls or None,
            deanonymize_output=body.deanonymize_output,
            system_prompt=body.system_prompt,
            rag_chunks=body.rag_chunks or None,
            model_id=body.model,
            model_digest=body.model_digest,
            session_id=body.session_id or "",
        )

    # persist audit + vault ciphertext + events
    sd = r.safety_decision
    db.add(
        AuditDecisionRow(
            request_id=r.request_id,
            tenant_id=vk.tenant_id,
            app_id=vk.app_id,
            decision=r.decision,
            body_json=json.dumps(sd, ensure_ascii=False),
            content_hash=sd.get("content_hash", ""),
            chain_hash=sd.get("chain_hash", ""),
            prev_chain_hash=sd.get("prev_chain_hash", ""),
        )
    )
    for tok in st.vault.encrypted_entries_for_request(r.request_id):
        db.add(
            VaultEntryRow(
                token=tok.token,
                tenant_id=tok.tenant_id,
                request_id=tok.request_id,
                pii_type=tok.pii_type,
                ciphertext=tok.ciphertext,
                nonce=tok.nonce,
            )
        )
    for et in r.events:
        db.add(
            EventRow(
                event_id=str(uuid.uuid4()),
                event_type=et,
                tenant_id=vk.tenant_id,
                app_id=vk.app_id,
                request_id=r.request_id,
                body_json="{}",
            )
        )
        st.siem.emit(
            {
                "event_type": et,
                "request_id": r.request_id,
                "tenant_id": vk.tenant_id,
                "app_id": vk.app_id,
                "decision": r.decision,
                "chain_hash": sd.get("chain_hash", ""),
                "prev_chain_hash": sd.get("prev_chain_hash", ""),
            }
        )
    st.siem.emit(
        {
            "event_type": "safety.decision",
            "request_id": r.request_id,
            "tenant_id": vk.tenant_id,
            "app_id": vk.app_id,
            "decision": r.decision,
            "chain_hash": sd.get("chain_hash", ""),
            "prev_chain_hash": sd.get("prev_chain_hash", ""),
        }
    )
    # budget
    tokens = max(1, len(user_content) // 4)
    ok, nxt = st.quota.add_spend(tokens, vk.budget_tokens, vk.spent_tokens)
    if not ok:
        db.rollback()
        raise HTTPException(status_code=429, detail="token budget exceeded")
    vk.spent_tokens = nxt
    db.commit()
    st.metrics.inc(f'llm_safety_requests_total{{decision="{r.decision}"}}')
    return {
        "request_id": r.request_id,
        "decision": r.decision,
        "policy_binding_id": r.policy_binding_id,
        "policy_version": r.policy_version,
        "messages": r.messages,
        "model_output": r.model_output,
        "refusal_message": r.refusal_message,
        "tool_results": r.tool_results,
        "safety_decision": r.safety_decision,
        "blocked_reason": r.blocked_reason,
        "events": r.events,
    }


class OpenAIChatRequest(BaseModel):
    model: str = "mock-llm"
    messages: list[dict[str, str]]


@app.post("/v1/chat/completions")
def openai_compatible(
    body: OpenAIChatRequest,
    principal: Principal = Depends(require_vk),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    out = safety_chat(
        SafetyChatRequest(messages=body.messages, model=body.model),
        principal,
        db,
    )
    if out.get("decision") == "block":
        return {
            "id": out.get("request_id"),
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": out.get("refusal_message")
                        or out.get("model_output")
                        or f"[blocked] {out.get('blocked_reason')}",
                    },
                    "finish_reason": "content_filter",
                }
            ],
        }
    return {
        "id": out.get("request_id"),
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": out.get("model_output") or ""},
                "finish_reason": "stop",
            }
        ],
    }


class CreateVKRequest(BaseModel):
    tenant_id: str
    app_id: str
    name: str = ""
    model_allowlist: list[str] = Field(default_factory=lambda: ["mock-llm"])
    rpm_limit: int = 120
    budget_tokens: int = 1_000_000


@app.post("/v1/admin/virtual-keys")
def create_vk(
    body: CreateVKRequest,
    _: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    raw, row = vk_service.create(
        db,
        tenant_id=body.tenant_id,
        app_id=body.app_id,
        name=body.name,
        model_allowlist=body.model_allowlist,
        rpm_limit=body.rpm_limit,
        budget_tokens=body.budget_tokens,
    )
    return {"virtual_key": raw, "key_id": row.key_id, "warning": "store once; not shown again"}


@app.get("/v1/admin/virtual-keys")
def list_vk(
    _: Principal = Depends(require_roles("Admin", "Security", "AppOwner", "Auditor")),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = vk_service.list_keys(db)
    return [
        {
            "key_id": r.key_id,
            "tenant_id": r.tenant_id,
            "app_id": r.app_id,
            "name": r.name,
            "revoked": r.revoked,
            "spent_tokens": r.spent_tokens,
            "budget_tokens": r.budget_tokens,
            "rpm_limit": r.rpm_limit,
        }
        for r in rows
    ]


@app.post("/v1/admin/virtual-keys/{key_id}/revoke")
def revoke_vk(
    key_id: str,
    _: Principal = Depends(require_roles("Admin", "Security")),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    vk_service.revoke(db, key_id)
    return {"status": "revoked"}


@app.get("/v1/admin/policies/{tenant_id}/{app_id}")
def get_policy(
    tenant_id: str,
    app_id: str,
    _: Principal = Depends(require_admin),
) -> dict[str, Any]:
    b = get_state().policy.resolve(tenant_id, app_id)
    return b.to_dict()


class PublishRequest(BaseModel):
    reason: str
    risk_tier: str | None = None
    tool_allowlist: list[str] | None = None
    security_approver: str = ""
    owner_approver: str = ""


class PublishGateApproveRequest(BaseModel):
    """Critical 双人发布：Security / AppOwner 各签一次。

    actor 默认为当前 principal.subject；本地 Admin 可填不同 actor 名完成双人门禁演示。
    """

    role: str = Field(description="security|owner")
    actor: str = ""


def _attach_corpus_gates(report: dict[str, Any]) -> dict[str, Any]:
    """挂上 ADR-029 publish profile gates，供 ReleaseEvaluator 统一判门禁。"""
    from app.eval.publish_profile import run_publish_gates

    gates = run_publish_gates()
    by_stem = {Path(r["source"]).stem: r for r in gates.get("results") or []}
    out = dict(report)
    out["corpus_gates"] = by_stem
    out["corpus_gates_passed"] = bool(gates.get("passed"))
    out["corpus_gates_failed"] = list(gates.get("failed") or [])
    out["publish_profile"] = gates.get("publish_profile")
    out["publish_gates_audit"] = gates.get("gates_audit")
    return out


def _finalize_policy_publish(
    *,
    st: Any,
    db: Session,
    tenant_id: str,
    app_id: str,
    body: PublishRequest,
    principal: Principal,
    ev_metrics: dict[str, Any] | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    nxt = st.policy.publish(
        tenant_id=tenant_id,
        app_id=app_id,
        reason=body.reason,
        risk_tier=body.risk_tier,
        tool_allowlist=body.tool_allowlist,
    )
    db.add(
        PolicyBindingRow(
            policy_binding_id=nxt.policy_binding_id,
            tenant_id=nxt.tenant_id,
            app_id=nxt.app_id,
            version=nxt.version,
            reason=nxt.reason,
            risk_tier=nxt.risk_tier,
            fail_mode=nxt.fail_mode,
            effect_cap=nxt.effect_cap,
            body_json=json.dumps(nxt.to_dict(), ensure_ascii=False),
            require_dual_publish=nxt.risk_tier == "critical",
        )
    )
    db.add(
        EventRow(
            event_id=str(uuid.uuid4()),
            event_type=E.POLICY_PUBLISHED,
            tenant_id=tenant_id,
            app_id=app_id,
            request_id="publish",
            body_json=json.dumps({"version": nxt.version, "by": principal.subject}),
        )
    )
    if commit:
        db.commit()
    return {"status": "published", "version": nxt.version, "eval": ev_metrics or {}}


@app.post("/v1/admin/policies/{tenant_id}/{app_id}/publish")
def publish_policy(
    tenant_id: str,
    app_id: str,
    body: PublishRequest,
    principal: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    st = get_state()
    cur = st.policy.resolve(tenant_id, app_id)
    # shim 探针 + corpus shim gates（与 run_all / ADR-029 对齐）
    report = _attach_corpus_gates(st.redteam.run_shim_suite(db))
    ev = st.evaluator.evaluate(redteam=report, risk_tier=body.risk_tier or cur.risk_tier)
    if not ev.passed:
        db.add(
            EventRow(
                event_id=str(uuid.uuid4()),
                event_type=E.EVAL_FAILED,
                tenant_id=tenant_id,
                app_id=app_id,
                request_id="publish",
                body_json=json.dumps({"defects": ev.defects}),
            )
        )
        db.commit()
        raise HTTPException(status_code=400, detail={"eval_failed": ev.defects})

    tier = body.risk_tier or cur.risk_tier
    if tier == "critical":
        if not body.security_approver or not body.owner_approver:
            gate = PublishGateRow(
                gate_id="pg_" + uuid.uuid4().hex[:12],
                tenant_id=tenant_id,
                app_id=app_id,
                status="pending",
                eval_passed=True,
                body_json=json.dumps(body.model_dump()),
            )
            db.add(gate)
            db.commit()
            return {"status": "awaiting_dual_approval", "gate_id": gate.gate_id}
        if body.security_approver == body.owner_approver:
            raise HTTPException(status_code=400, detail="dual publish requires two distinct actors")

    return _finalize_policy_publish(
        st=st,
        db=db,
        tenant_id=tenant_id,
        app_id=app_id,
        body=body,
        principal=principal,
        ev_metrics=ev.metrics,
    )


@app.get("/v1/admin/publish-gates")
def list_publish_gates(
    _: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
    db: Session = Depends(get_db),
    status: str = "pending",
    limit: int = 50,
) -> dict[str, Any]:
    """列出 critical 双人发布待办（默认 pending）。"""
    q = db.query(PublishGateRow).order_by(PublishGateRow.id.desc())
    if status:
        q = q.filter(PublishGateRow.status == status)
    rows = q.limit(max(1, min(limit, 200))).all()
    return {
        "gates": [
            {
                "gate_id": g.gate_id,
                "tenant_id": g.tenant_id,
                "app_id": g.app_id,
                "status": g.status,
                "security_approved_by": g.security_approved_by,
                "owner_approved_by": g.owner_approved_by,
                "eval_passed": g.eval_passed,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in rows
        ]
    }


@app.post("/v1/admin/publish-gates/{gate_id}/approve")
def approve_publish_gate(
    gate_id: str,
    body: PublishGateApproveRequest,
    principal: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Critical 双人签字：Security 与 AppOwner（或 Admin 代签一侧）各批一次后真正 publish。"""
    gate = db.query(PublishGateRow).filter(PublishGateRow.gate_id == gate_id).first()
    if not gate:
        raise HTTPException(status_code=404, detail="publish_gate_not_found")
    if gate.status != "pending":
        raise HTTPException(status_code=400, detail=f"gate_not_pending:{gate.status}")

    role = (body.role or "").strip().lower()
    actor = (body.actor or principal.subject or "").strip()
    if not actor:
        raise HTTPException(status_code=400, detail="actor_required")
    if role == "security":
        if "Security" not in principal.roles and "Admin" not in principal.roles:
            raise HTTPException(status_code=403, detail="security_role_required")
        if gate.security_approved_by:
            raise HTTPException(status_code=400, detail="security_already_approved")
        # 另一侧已签时禁止同一 actor
        if gate.owner_approved_by and gate.owner_approved_by == actor:
            raise HTTPException(status_code=400, detail="dual publish requires two distinct actors")
        gate.security_approved_by = actor
    elif role == "owner":
        if "AppOwner" not in principal.roles and "Admin" not in principal.roles:
            raise HTTPException(status_code=403, detail="owner_role_required")
        if gate.owner_approved_by:
            raise HTTPException(status_code=400, detail="owner_already_approved")
        if gate.security_approved_by and gate.security_approved_by == actor:
            raise HTTPException(status_code=400, detail="dual publish requires two distinct actors")
        gate.owner_approved_by = actor
    else:
        raise HTTPException(status_code=400, detail="role_must_be_security_or_owner")

    if gate.security_approved_by and gate.owner_approved_by:
        payload = json.loads(gate.body_json or "{}")
        req = PublishRequest(**payload)
        st = get_state()
        # 最终批准前必须重新跑当前 publish gates（防第二人延迟批准导致规则漂移）
        report = _attach_corpus_gates(st.redteam.run_shim_suite(db))
        ev = st.evaluator.evaluate(redteam=report, risk_tier="critical")
        if not ev.passed:
            gate.status = "failed"
            gate.eval_passed = False
            db.add(gate)
            db.add(
                EventRow(
                    event_id=str(uuid.uuid4()),
                    event_type=E.EVAL_FAILED,
                    tenant_id=gate.tenant_id,
                    app_id=gate.app_id,
                    request_id="publish_gate_final",
                    body_json=json.dumps({"gate_id": gate_id, "defects": ev.defects}),
                )
            )
            db.commit()
            raise HTTPException(
                status_code=400,
                detail={"eval_failed": ev.defects, "gate_id": gate_id, "gate_status": "failed"},
            )
        gate.status = "published"
        db.add(gate)
        result = _finalize_policy_publish(
            st=st,
            db=db,
            tenant_id=gate.tenant_id,
            app_id=gate.app_id,
            body=req,
            principal=principal,
            ev_metrics={"dual_approved": True, "final_eval": ev.metrics},
            commit=True,
        )
        return {**result, "gate_id": gate.gate_id, "status": "published"}

    db.add(gate)
    db.commit()
    return {
        "status": "awaiting_dual_approval",
        "gate_id": gate.gate_id,
        "security_approved_by": gate.security_approved_by,
        "owner_approved_by": gate.owner_approved_by,
    }


@app.get("/v1/admin/audit")
def list_audit(
    _: Principal = Depends(require_roles("Admin", "Security", "Auditor")),
    db: Session = Depends(get_db),
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = db.query(AuditDecisionRow).order_by(AuditDecisionRow.id.desc()).limit(limit).all()
    return [
        {
            "request_id": r.request_id,
            "tenant_id": r.tenant_id,
            "app_id": r.app_id,
            "decision": r.decision,
            "content_hash": r.content_hash,
            "chain_hash": r.chain_hash,
        }
        for r in rows
    ]


@app.get("/v1/approvals")
def list_approvals(
    _: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = get_state().approvals.list_pending(db)
    return [
        {
            "approval_id": r.approval_id,
            "tenant_id": r.tenant_id,
            "app_id": r.app_id,
            "request_id": r.request_id,
            "action": json.loads(r.action_json),
            "status": r.status,
        }
        for r in rows
    ]


class DecideBody(BaseModel):
    approve: bool


@app.post("/v1/approvals/{approval_id}/decide")
def decide_approval(
    approval_id: str,
    body: DecideBody,
    principal: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    st = get_state()
    row = st.approvals.decide(db, approval_id, approve=body.approve, actor=principal.subject)
    resumed = None
    if body.approve:
        action = json.loads(row.action_json)
        binding = st.policy.resolve(row.tenant_id, row.app_id)
        # Temporarily allow the tool for resume under confirm_only workflow
        allow = list(binding.tool_allowlist) + [action.get("name", "")]
        try:
            resumed = st.tools.call(
                action.get("name", ""),
                row.request_id,
                action.get("arguments") or {},
                allowlist=allow,
                effect_cap="production",
                denylist=binding.tool_denylist,
                risk_rules=binding.tool_risk_rules,
                email_domain_allowlist=binding.email_domain_allowlist,
                skip_risk_execute_gate=True,
            )
        except Exception as e:  # noqa: BLE001
            resumed = {"error": str(e)}
    return {
        "approval_id": row.approval_id,
        "status": row.status,
        "decided_by": row.decided_by,
        "resumed": resumed,
    }


@app.post("/v1/redteam/run")
def run_redteam(
    suite: str = "shim",
    _: Principal = Depends(require_roles("Admin", "Security")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    st = get_state()
    if suite == "garak":
        return st.redteam.run_garak_stub(db)
    if suite == "pyrit":
        return st.redteam.run_pyrit_stub(db)
    if suite == "agentic_security":
        return st.redteam.run_agentic_security_stub(db)
    if suite == "promptfoo":
        return st.redteam.run_promptfoo_stub(db)
    return st.redteam.run_shim_suite(db)


@app.get("/v1/redteam/runs")
def list_redteam(
    _: Principal = Depends(require_roles("Admin", "Security", "Auditor")),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.query(RedTeamRunRow).order_by(RedTeamRunRow.id.desc()).limit(50).all()
    return [
        {
            "run_id": r.run_id,
            "suite": r.suite,
            "passed": r.passed,
            "leak_rate": r.leak_rate,
        }
        for r in rows
    ]


class CorpusSubmitRequest(BaseModel):
    name: str
    sample_text: str
    note: str = ""


@app.post("/v1/admin/corpus/admissions")
def corpus_submit(
    body: CorpusSubmitRequest,
    principal: Principal = Depends(require_roles("Admin", "Security", "AppOwner")),
) -> dict[str, Any]:
    """LLM04 — submit fine-tune/RAG corpus sample for admission."""
    st = get_state()
    tenant = "t_demo"
    item = st.corpus.submit(
        tenant_id=tenant,
        name=body.name,
        sample_text=body.sample_text,
        note=body.note,
    )
    return item.as_dict()


@app.post("/v1/admin/corpus/admissions/{admission_id}/approve")
def corpus_approve(
    admission_id: str,
    principal: Principal = Depends(require_roles("Admin", "Security")),
) -> dict[str, Any]:
    st = get_state()
    try:
        item = st.corpus.approve(admission_id, reviewer=principal.subject)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return item.as_dict()


@app.get("/v1/admin/corpus/admissions")
def corpus_list(
    _: Principal = Depends(require_roles("Admin", "Security", "Auditor")),
) -> list[dict[str, Any]]:
    return [x.as_dict() for x in get_state().corpus.list()]


class ScanOnlyRequest(BaseModel):
    text: str
    layer: str = "input"  # input|output


@app.post("/v1/safety/scan")
def safety_scan(
    body: ScanOnlyRequest,
    principal: Principal = Depends(require_vk),
) -> dict[str, Any]:
    st = get_state()
    assert principal.vk is not None
    binding = st.policy.resolve(principal.vk.tenant_id, principal.vk.app_id)
    req_id = "scan_" + uuid.uuid4().hex[:10]
    if body.layer == "output":
        d, text, results = st.gateway.scanners.run_output(
            body.text, binding, principal.vk.tenant_id, req_id, st.vault
        )
    else:
        d, text, results = st.gateway.scanners.run_input(
            body.text, binding, principal.vk.tenant_id, req_id, st.vault
        )
    return {
        "request_id": req_id,
        "decision": d,
        "text": text,
        "scanner_results": [r.as_dict() for r in results],
    }


class ToolExecuteRequest(BaseModel):
    tool_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    # 业务侧关联审计字段（可选，ADR-0004）
    trace_id: str = ""
    org_domain: str = ""
    policy_binding: str = ""


@app.post("/v1/tools/authorize")
def tools_authorize(
    body: ToolExecuteRequest,
    principal: Principal = Depends(require_vk),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    工具授权干跑：只返回五态决策，不在安全侧执行副作用。
    供纪要君等业务在本地业务授权之后、本地执行之前调用。
    """
    st = get_state()
    assert principal.vk is not None
    binding = st.policy.resolve(principal.vk.tenant_id, principal.vk.app_id)
    req_id = "authz_" + uuid.uuid4().hex[:10]
    out = st.tools.authorize(
        body.tool_id,
        req_id,
        body.arguments,
        allowlist=binding.tool_allowlist,
        effect_cap=binding.effect_cap,
        denylist=binding.tool_denylist,
        risk_rules=binding.tool_risk_rules,
        email_domain_allowlist=binding.email_domain_allowlist,
    )
    st.siem.emit(
        {
            "event_type": E.TOOL_DENIED if out["decision"] == "block" else E.TOOL_EXECUTED,
            "request_id": req_id,
            "tool_id": body.tool_id,
            "tenant_id": principal.vk.tenant_id,
            "decision": out["decision"],
            "authorize_only": True,
            "trace_id": body.trace_id,
            "org_domain": body.org_domain,
            "policy_binding": body.policy_binding or f"{principal.vk.tenant_id}/{principal.vk.app_id}",
        }
    )
    db.add(
        EventRow(
            event_id=str(uuid.uuid4()),
            event_type="tool.authorized" if out["decision"] != "block" else E.TOOL_DENIED,
            tenant_id=principal.vk.tenant_id,
            app_id=principal.vk.app_id,
            request_id=req_id,
            body_json=json.dumps(
                {
                    "tool_id": body.tool_id,
                    "decision": out["decision"],
                    "risk": out.get("risk"),
                    "trace_id": body.trace_id,
                    "org_domain": body.org_domain,
                    "policy_binding": body.policy_binding,
                    "authorize_only": True,
                },
                ensure_ascii=False,
            ),
        )
    )
    db.commit()
    return {
        **out,
        "trace_id": body.trace_id,
        "org_domain": body.org_domain,
        "policy_binding": body.policy_binding
        or f"{principal.vk.tenant_id}/{principal.vk.app_id}",
    }


@app.post("/v1/tools/execute")
def tools_execute(
    body: ToolExecuteRequest,
    principal: Principal = Depends(require_vk),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    st = get_state()
    assert principal.vk is not None
    binding = st.policy.resolve(principal.vk.tenant_id, principal.vk.app_id)
    req_id = "tool_" + uuid.uuid4().hex[:10]
    from app.tool_runtime import ConfirmRequiredError

    try:
        result = st.tools.call(
            body.tool_id,
            req_id,
            body.arguments,
            allowlist=binding.tool_allowlist,
            effect_cap=binding.effect_cap,
            denylist=binding.tool_denylist,
            risk_rules=binding.tool_risk_rules,
            email_domain_allowlist=binding.email_domain_allowlist,
            idempotency_key=body.idempotency_key,
        )
        risk = result.pop("_risk", {}) if isinstance(result, dict) else {}
        if risk.get("matched_rules"):
            st.siem.emit(
                {
                    "event_type": E.TOOL_RISK_FLAGGED,
                    "request_id": req_id,
                    "tool_id": body.tool_id,
                    "risk": risk,
                    "tenant_id": principal.vk.tenant_id,
                }
            )
        st.siem.emit(
            {
                "event_type": E.TOOL_EXECUTED,
                "request_id": req_id,
                "tool_id": body.tool_id,
                "tenant_id": principal.vk.tenant_id,
                "risk": risk,
            }
        )
        return {"request_id": req_id, "decision": risk.get("decision", "allow"), "result": result, "risk": risk}
    except ConfirmRequiredError as e:
        apr = st.approvals.enqueue(
            db,
            tenant_id=principal.vk.tenant_id,
            app_id=principal.vk.app_id,
            request_id=req_id,
            action={"name": body.tool_id, "arguments": body.arguments},
        )
        return {
            "request_id": req_id,
            "decision": "confirm_only",
            "approval_id": apr.approval_id,
            "risk": e.risk.as_dict(),
            "message": str(e),
        }
    except PermissionError as e:
        st.siem.emit(
            {
                "event_type": E.TOOL_DENIED,
                "request_id": req_id,
                "tool_id": body.tool_id,
                "reason": str(e),
                "tenant_id": principal.vk.tenant_id,
            }
        )
        db.add(
            EventRow(
                event_id=str(uuid.uuid4()),
                event_type=E.TOOL_DENIED,
                tenant_id=principal.vk.tenant_id,
                app_id=principal.vk.app_id,
                request_id=req_id,
                body_json=json.dumps({"tool_id": body.tool_id, "reason": str(e)}),
            )
        )
        db.commit()
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.get("/v1/admin/audit/chain/verify")
def verify_chain(
    _: Principal = Depends(require_roles("Admin", "Security", "Auditor")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = (
        db.query(AuditDecisionRow)
        .filter(AuditDecisionRow.chain_hash != "")
        .all()
    )
    if rows:
        return verify_audit_rows(rows)
    return verify_chain_list(get_state().ledger.chain)


@app.get("/v1/admin/dashboard")
def dashboard(
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from app.db.models import VirtualKeyRow

    return {
        "audit_count": db.query(AuditDecisionRow).count(),
        "vk_count": db.query(VirtualKeyRow).count(),
        "pending_approvals": db.query(ApprovalRow).filter_by(status="pending").count(),
        "redteam_runs": db.query(RedTeamRunRow).count(),
        "metrics": get_state().metrics.counters,
    }


_console_dist = Path(__file__).resolve().parents[2] / "console" / "dist"
_console_static = Path(__file__).resolve().parents[2] / "console" / "public"
_console_dir = _console_dist if _console_dist.exists() else _console_static
if _console_dir.exists():
    app.mount("/console", StaticFiles(directory=str(_console_dir), html=True), name="console")
