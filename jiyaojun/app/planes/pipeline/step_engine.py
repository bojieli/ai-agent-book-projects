"""步骤执行引擎 — Phase0 / SOP / Playbook 共享运行时。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agents import Evaluator
from app.agents.llm_evaluator import IndependentLLMEvaluator
from app.connectors import MockDefectConnector, MockTaskConnector
from app.domain_layer import WorkObjectRef, validate_envelope
from app.events import DomainEvent, DomainEventType, EventLog, PRODUCTION_EFFECT_RANK
from app.harness import ToolRuntime, idem_key
from app.knowledge import KnowledgePlane
from app.observability import BudgetTracker, CostQuota, Observability, UsageLedger
from app.policy import AmbiguityService, max_strict_embed_gate, policy_hooks_ok
from app.render import RenderService
from app.safety.dual_authz import authorize_tool_dual
from app.safety.factory import build_safety_gateway
from app.safety.model_client import SafetyRoutedLLMClient
from app.observability.telemetry import SPAN_WRITEBACK, default_telemetry
from app.skills_runtime.checklist import load_checklist, validate_checklist
from app.skills_runtime.skill_pack import SkillPack

# 已知别名 → 已注册 connector id（禁止静默回退未知工具）
CONNECTOR_ALIASES: dict[str, str] = {
    "connector.change_draft.create": "connector.task.create",
}

KNOWN_VALIDATE_HOOKS = frozenset(
    {"schema_validate", "policy_hooks", "release_gate_checklist", "evidence_required"}
)


@dataclass
class StepRunState:
    """单次流水线运行上下文。"""

    meeting_id: str
    org_domains: list[str]
    scenario_type: str
    skill_pack_id: str
    purpose: str
    classification: str = "internal"
    continuum_write_class: str = "wide"
    default_embed_gate: str = "confirm_only"
    production_effect_cap: str = "draft_only"
    maturity: str = "L2"
    series_id: str | None = "series_r1_demo"
    participants: list[str] = field(default_factory=lambda: ["u_dev_a", "u_pm"])
    orchestration_mode: str = "playbook"
    pipeline_path: str = "playbook"
    tool_allowlist: list[str] = field(
        default_factory=lambda: ["connector.defect.create", "connector.task.create"]
    )
    force_validate_fail: set[str] = field(default_factory=set)


@dataclass
class StepEngineResult:
    terminal: str
    artifacts: list[dict[str, Any]]
    work_objects: list[dict[str, Any]]
    render: dict[str, Any] | None
    events: list[str]
    traces: int
    usage: dict[str, Any]
    sop_steps: list[dict[str, str]] = field(default_factory=list)
    pipeline_path: str = ""


class StepEngine:
    def __init__(self, repo_root: Path, knowledge: KnowledgePlane | None = None) -> None:
        self.repo_root = repo_root
        self.events = EventLog()
        self.obs = Observability()
        self.runtime = ToolRuntime()
        self.runtime.register(MockTaskConnector())
        self.runtime.register(MockDefectConnector())
        self.render = RenderService(repo_root / "app" / "render" / "default")
        self.knowledge = knowledge or KnowledgePlane()
        if not self.knowledge.docs:
            self.knowledge.seed_demo()
        # 与 KnowledgePlane 共用同一 bridge/store，briefing 才能召回 pipeline 写入的 open items
        self.series_bridge = self.knowledge.series_bridge
        self.evaluator = Evaluator()
        # 模型调用统一经安全网关（默认离线确定性，无旁路直连）
        self.safety_gateway = build_safety_gateway()
        self.llm_evaluator = IndependentLLMEvaluator(
            SafetyRoutedLLMClient(self.safety_gateway, classification="internal")
        )
        self.ambiguity = AmbiguityService()
        self.budget = BudgetTracker(CostQuota())
        self.work_links: list[dict[str, Any]] = []
        self._run_id = ""
        self._trace_id = ""

    def begin_run(self) -> None:
        self.events = EventLog()
        self.obs = Observability()
        self.budget = BudgetTracker(CostQuota())
        self.work_links = []

    def run_from_spec(
        self,
        meeting: StepRunState,
        *,
        skill_pack: SkillPack,
        steps: list[dict[str, Any]],
        hitl_passed: bool = True,
        transcript_ok: bool = True,
        embed_tools: list[str] | None = None,
    ) -> StepEngineResult:
        """按 steps.yaml / playbook.yaml 逐步执行（阶段式状态机，非 ReAct）。"""
        self._run_id = str(uuid.uuid4())
        self._trace_id = str(uuid.uuid4())
        t0 = self.obs.start_span("pipeline", meeting.meeting_id, self._trace_id)
        sop_steps: list[dict[str, str]] = []
        artifacts: list[dict[str, Any]] = []
        work_objects: list[dict[str, Any]] = []
        render_out: dict[str, Any] | None = None
        embed_gate = max_strict_embed_gate(meeting.default_embed_gate)
        hits: list[Any] = []

        if meeting.series_id and meeting.continuum_write_class != "none":
            self.series_bridge.sync_open_items_to_continuum(
                meeting.series_id,
                org_domain=meeting.org_domains[0],
                classification=meeting.classification,
                write_class=meeting.continuum_write_class,
                acl_principals=meeting.participants,
            )

        for step in steps:
            sid = step["id"]
            stype = step.get("type", "")
            wall = bool(step.get("wall"))
            detail = stype

            if stype == "understand":
                quality = "ok" if transcript_ok else "low"
                self._emit(
                    DomainEventType.UNDERSTANDING_COMPLETED,
                    meeting,
                    {
                        "quality": quality,
                        "unknown_terms": [],
                        "blocks_decision": not transcript_ok,
                    },
                    producer="understanding",
                )
                if not transcript_ok:
                    sop_steps.append({"step_id": sid, "status": "failed", "detail": "low_quality"})
                    return self._finish(
                        meeting, t0, "degraded_minutes_only", artifacts, None, sop_steps, meeting.pipeline_path
                    )
                sop_steps.append({"step_id": sid, "status": "ok", "detail": detail})
                continue

            if stype == "retrieve":
                query = "超时 阻塞 灰度 网关"
                if "continuum" in str(step.get("tools", [])):
                    query = "阻塞 open 网关"
                span = self.obs.start_span("retrieve", meeting.meeting_id, self._trace_id)
                hits, hops = self.knowledge.retrieve(
                    user_id=meeting.participants[0],
                    org_domains=meeting.org_domains,
                    query=query,
                    max_hops=self.budget.quota.max_retrieve_hops,
                )
                self.budget.charge(retrieve_hops=hops)
                if self.budget.exhausted:
                    self._emit(DomainEventType.BUDGET_EXHAUSTED, meeting, {"which": self.budget.exhausted[0]})
                    sop_steps.append({"step_id": sid, "status": "failed", "detail": "budget"})
                    return self._finish(meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path)
                span.end(hits=len(hits), hops=hops)
                sop_steps.append({"step_id": sid, "status": "ok", "detail": f"hits={len(hits)}"})
                continue

            if stype in {"extract", "decide"}:
                sop_steps.append({"step_id": sid, "status": "ok", "detail": stype})
                continue

            if stype == "artifact":
                refs = [{"corpus": h.corpus, "id": h.id, "span": h.span} for h in hits[:3]]
                artifact = skill_pack.build_artifact(
                    meeting_id=meeting.meeting_id,
                    scenario_type=meeting.scenario_type,
                    skill_pack_id=meeting.skill_pack_id,
                    org_domains=meeting.org_domains,
                    classification=meeting.classification,
                    continuum_write_class=meeting.continuum_write_class,
                    references=refs,
                )
                artifacts = [artifact]
                self._emit(
                    DomainEventType.ARTIFACT_PERSISTED,
                    meeting,
                    {"artifact_ids": [artifact["artifact_id"]]},
                )
                sop_steps.append({"step_id": sid, "status": "ok", "detail": artifact.get("schema_id", "")})
                continue

            if stype == "validate":
                hook = step.get("hook", "")
                ok = True
                fail_detail = hook
                artifact = artifacts[0] if artifacts else {}
                prod_effect = (
                    "none"
                    if meeting.production_effect_cap == "none"
                    else "draft_only"
                )

                if sid in meeting.force_validate_fail or hook in meeting.force_validate_fail:
                    ok = False
                    fail_detail = f"forced_fail:{hook or sid}"
                elif hook == "schema_validate" or "schema" in hook:
                    env_errs = validate_envelope(artifact)
                    payload_errs = skill_pack.validate_payload(artifact.get("payload") or {})
                    ok = not env_errs and not payload_errs
                    fail_detail = ";".join(env_errs[:2] + payload_errs[:2]) or hook
                elif "checklist" in hook or step.get("checklist"):
                    cl_rel = step.get("checklist") or "sop/checklists/release_gate.yaml"
                    checklist = load_checklist(skill_pack.skill_dir, cl_rel)
                    ok, fails = validate_checklist(checklist, artifact=artifact)
                    fail_detail = ",".join(fails[:3]) or hook
                elif hook == "policy_hooks" or "no_production" in hook or "no_hot" in hook:
                    fails = policy_hooks_ok(
                        classification=meeting.classification,
                        continuum_write_class=meeting.continuum_write_class,
                        production_effect=prod_effect,
                        production_effect_cap=meeting.production_effect_cap,
                        embed_gate=embed_gate,
                        maturity=meeting.maturity,
                    )
                    ok = not fails
                    fail_detail = ",".join(fails) or hook
                else:
                    ok = False
                    fail_detail = f"unknown_hook:{hook or sid}"

                status = "ok" if ok else "failed"
                sop_steps.append({"step_id": sid, "status": status, "detail": fail_detail})
                if wall and not ok:
                    return self._finish(meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path)
                if not ok:
                    return self._finish(meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path)
                continue

            if stype == "evaluate":
                artifact = artifacts[0] if artifacts else {}
                prod_effect = (
                    "none"
                    if meeting.production_effect_cap == "none"
                    else "draft_only"
                )
                ambiguity_open = any(
                    r.meeting_id == meeting.meeting_id and r.status == "open"
                    for r in self.ambiguity.records.values()
                )
                prose_agree = "各方同意" in str(artifact.get("payload", {}))
                policy_failures = policy_hooks_ok(
                    classification=meeting.classification,
                    continuum_write_class=meeting.continuum_write_class,
                    production_effect=prod_effect,
                    production_effect_cap=meeting.production_effect_cap,
                    embed_gate=embed_gate,
                    maturity=meeting.maturity,
                )
                criteria = skill_pack.success_criteria or ["schema", "policy"]
                eval_res = (
                    self.llm_evaluator.evaluate(
                        artifact=artifact,
                        success_criteria=criteria,
                        policy_failures=policy_failures,
                        require_llm=True,
                    )
                    if meeting.maturity == "L3"
                    else self.evaluator.evaluate(
                        artifact=artifact,
                        success_predicates=criteria,
                        policy_failures=policy_failures,
                        ambiguity_open=ambiguity_open,
                        prose_claims_all_agree=prose_agree,
                    )
                )
                if not eval_res.passed:
                    self._emit(
                        DomainEventType.EVALUATION_FAILED,
                        meeting,
                        {"eval_run_id": str(uuid.uuid4()), "failures": eval_res.failures},
                    )
                    sop_steps.append({"step_id": sid, "status": "failed", "detail": "evaluate"})
                    return self._finish(
                        meeting, t0, "awaiting_hitl", artifacts, None, sop_steps, meeting.pipeline_path
                    )
                self._emit(
                    DomainEventType.EVALUATION_PASSED,
                    meeting,
                    {"eval_run_id": str(uuid.uuid4()), "checks": eval_res.checks},
                )
                sop_steps.append({"step_id": sid, "status": "ok", "detail": "evaluate"})
                continue

            if stype == "hitl":
                if embed_gate in {"block", "confirm_only"}:
                    self._emit(
                        DomainEventType.HITL_REQUESTED,
                        meeting,
                        {"task_id": "hitl_1", "kind": "embed_confirm"},
                    )
                    if not hitl_passed:
                        sop_steps.append({"step_id": sid, "status": "failed", "detail": "hitl"})
                        return self._finish(
                            meeting, t0, "awaiting_hitl", artifacts, None, sop_steps, meeting.pipeline_path
                        )
                    self._emit(
                        DomainEventType.HITL_RESOLVED,
                        meeting,
                        {"task_id": "hitl_1", "decision": "approve"},
                    )
                sop_steps.append({"step_id": sid, "status": "ok", "detail": "hitl"})
                continue

            if stype == "embed":
                if any(
                    r.meeting_id == meeting.meeting_id and r.status == "open"
                    for r in self.ambiguity.records.values()
                ):
                    sop_steps.append({"step_id": sid, "status": "failed", "detail": "ambiguity_open"})
                    return self._finish(meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path)
                skip = (
                    meeting.maturity == "L0"
                    or embed_gate == "block"
                    or meeting.production_effect_cap == "none"
                )
                if skip:
                    sop_steps.append({"step_id": sid, "status": "skipped", "detail": "skip_if"})
                    continue
                artifact = artifacts[0] if artifacts else {}
                payload = artifact.get("payload") or {}
                declared = embed_tools or step.get("tools") or meeting.tool_allowlist
                try:
                    connector, allowlist = self._resolve_embed_tools(declared)
                except (KeyError, ValueError) as exc:
                    sop_steps.append({"step_id": sid, "status": "failed", "detail": str(exc)})
                    return self._finish(meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path)
                title = self._embed_title(payload, artifact)
                key = idem_key(meeting.meeting_id, connector.split(".")[-1], title)
                span = self.obs.start_span("embed", meeting.meeting_id, self._trace_id)
                wb_span = default_telemetry.start_span(
                    SPAN_WRITEBACK,
                    meeting_id=meeting.meeting_id,
                    trace_id=self._trace_id or self._run_id,
                )
                self.budget.charge(embed_attempts=1)
                # ADR-0004：业务 allowlist 之后独立安全授权；取更严格结果
                dual = authorize_tool_dual(
                    self.safety_gateway,
                    tool_id=connector,
                    arguments={"title": title},
                    granted_ids=list(allowlist) if allowlist is not None else None,
                    trace_id=self._trace_id or self._run_id,
                    org_domain=meeting.org_domains[0] if meeting.org_domains else "",
                    policy_binding="jiyaojun/pipeline",
                )
                if not dual.allowed:
                    default_telemetry.end_span(wb_span, status="denied", reason=dual.reason)
                    sop_steps.append(
                        {
                            "step_id": sid,
                            "status": "failed",
                            "detail": f"safety_denied:{dual.reason}:{dual.final_decision}",
                        }
                    )
                    return self._finish(
                        meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path
                    )
                result = self.runtime.call(
                    connector,
                    meeting.meeting_id,
                    {"title": title},
                    allowlist=allowlist,
                    max_effect=meeting.production_effect_cap,
                    effect_rank=PRODUCTION_EFFECT_RANK,
                    idempotency_key=key,
                )
                default_telemetry.end_span(wb_span, status="ok", connector=connector)
                self.budget.charge(tool_calls=1)
                wo = WorkObjectRef(
                    work_object_id=f"wo_{result['external_id']}",
                    connector_id=connector,
                    org_domain=meeting.org_domains[0],
                    object_type=connector.split(".")[-2],
                    production_effect=result["production_effect"],
                    idempotency_key=key,
                    meeting_id=meeting.meeting_id,
                    status=result["status"],
                    external_id=result["external_id"],
                    artifact_id=artifact.get("artifact_id", ""),
                    source_spans=list(artifact.get("source_spans") or []),
                    series_id=meeting.series_id,
                    owner_user_id=meeting.participants[0],
                    acl_snapshot={"principals": meeting.participants},
                )
                work_objects = [wo.to_dict()]
                self.work_links.append(wo.to_dict())
                self._emit(
                    DomainEventType.WORK_LINK_SUBMITTED,
                    meeting,
                    {"work_object_id": wo.work_object_id, "idempotency_key": key},
                )
                wo.status = "open"
                wo.last_synced_at = "2026-08-03T15:00:00+08:00"
                work_objects = [wo.to_dict()]
                self._emit(
                    DomainEventType.WORK_LINK_SYNCED,
                    meeting,
                    {
                        "work_object_id": wo.work_object_id,
                        "status": "open",
                        "external_id": wo.external_id,
                    },
                )
                span.end(external_id=wo.external_id)
                sop_steps.append({"step_id": sid, "status": "ok", "detail": connector})
                continue

            if stype == "index":
                write_dec = self.knowledge.decide_continuum_write(
                    classification=meeting.classification,
                    requested_write_class=meeting.continuum_write_class,
                )
                self._emit(
                    DomainEventType.CONTINUUM_WRITE_DECIDED,
                    meeting,
                    {
                        "write_class": write_dec.write_class,
                        "receipt_id": f"cwr_{meeting.meeting_id}",
                        "rejected_reason": write_dec.rejected_reason,
                        "index_alias": write_dec.index_alias,
                    },
                )
                if write_dec.accepted and meeting.series_id and artifacts:
                    payload = artifacts[0].get("payload") or {}
                    title = self._embed_title(payload, artifacts[0])
                    self.series_bridge.write_open_item(
                        series_id=meeting.series_id,
                        item_id=f"{meeting.meeting_id}_open",
                        title=title,
                        source_meeting_id=meeting.meeting_id,
                        org_domain=meeting.org_domains[0],
                        classification=meeting.classification,
                        write_class=write_dec.write_class,
                        acl_principals=meeting.participants,
                    )
                sop_steps.append({"step_id": sid, "status": "ok", "detail": "continuum"})
                continue

            if stype == "render":
                artifact = artifacts[0] if artifacts else {}
                allowlist_render = [] if meeting.classification == "critical" else None
                view = self.render.materialize_acl_view(
                    view_id=f"acl_{meeting.meeting_id}",
                    meeting_id=meeting.meeting_id,
                    artifacts=artifacts,
                    viewer_ids=meeting.participants,
                    classification=meeting.classification,
                    allowlist=allowlist_render,
                )
                rr = self.render.render_email(
                    job_id=f"rj_{meeting.meeting_id}",
                    acl_view=view,
                    classification=meeting.classification,
                    allowlist=allowlist_render,
                    context={
                        "artifacts": artifacts,
                        "meeting": {"id": meeting.meeting_id, "purpose": meeting.purpose},
                    },
                )
                if rr.status == "completed":
                    self.budget.charge(render_variants=1)
                if rr.status == "skipped":
                    self._emit(
                        DomainEventType.RENDER_SKIPPED,
                        meeting,
                        {
                            "reason": rr.skip_reason,
                            "classification": meeting.classification,
                            "render_job_id": rr.render_job_id,
                        },
                    )
                    render_out = {"status": "skipped", "reason": rr.skip_reason}
                else:
                    self._emit(
                        DomainEventType.RENDER_COMPLETED,
                        meeting,
                        {
                            "render_job_id": rr.render_job_id,
                            "acl_view_id": rr.acl_view_id,
                            "artifact_ids": [a["artifact_id"] for a in artifacts],
                        },
                    )
                    self._emit(
                        DomainEventType.DELIVERY_SENT,
                        meeting,
                        {
                            "channel": "email",
                            "recipient_set_hash": "demo",
                            "render_job_id": rr.render_job_id,
                        },
                    )
                    render_out = {
                        "status": "completed",
                        "html_len": len(rr.html or ""),
                        "html_preview": (rr.html or "")[:240],
                    }
                sop_steps.append({"step_id": sid, "status": "ok", "detail": rr.status})
                continue

            if stype == "notify":
                sop_steps.append({"step_id": sid, "status": "ok", "detail": "notify"})
                continue

            sop_steps.append({"step_id": sid, "status": "failed", "detail": f"unknown_step_type:{stype or 'missing'}"})
            return self._finish(meeting, t0, "failed", artifacts, None, sop_steps, meeting.pipeline_path)

        usage = UsageLedger(
            org_domain=meeting.org_domains[0],
            scenario=meeting.scenario_type,
            llm_tokens=0,
            tool_calls=self.budget.tool_calls,
            retrieve_hops=self.budget.retrieve_hops,
            embed_attempts=self.budget.embed_attempts,
            render_variants=self.budget.render_variants,
            wall_clock_sec=0.0,
        )
        self.obs.record_usage(usage)
        simulated_usage = {
            "measurement_mode": "simulated",
            "tool_calls": usage.tool_calls,
            "embed_attempts": usage.embed_attempts,
            "render_variants": usage.render_variants,
            "retrieve_hops": usage.retrieve_hops,
            "llm_tokens_simulated": 1200,
            "wall_clock_sec_simulated": 0.05,
        }
        return self._finish(
            meeting,
            t0,
            "succeeded",
            artifacts,
            render_out,
            sop_steps,
            meeting.pipeline_path,
            work_objects=work_objects,
            usage=simulated_usage,
        )

    def _registered_connectors(self) -> set[str]:
        return set(self.runtime._tools.keys())

    def _resolve_embed_tools(self, declared: list[str]) -> tuple[str, list[str]]:
        """解析 step/policy 声明的工具；未知或未注册则 fail closed。"""
        if not declared:
            raise ValueError("embed: no tools declared")
        registered = self._registered_connectors()
        resolved: list[str] = []
        for raw in declared:
            cid = CONNECTOR_ALIASES.get(raw, raw)
            if cid not in registered:
                raise KeyError(f"unknown or unregistered tool: {raw}")
            resolved.append(cid)
        allowlist = list(dict.fromkeys(resolved))
        return allowlist[0], allowlist

    def _embed_title(self, payload: dict[str, Any], artifact: dict[str, Any]) -> str:
        if payload.get("items"):
            return str(payload["items"][0].get("title", "follow-up"))
        if payload.get("summary"):
            return str(payload["summary"])[:80]
        return str(artifact.get("artifact_kind", "artifact"))

    def _emit(
        self,
        etype: DomainEventType,
        meeting: StepRunState,
        payload: dict[str, Any],
        *,
        producer: str = "pipeline",
    ) -> None:
        self.events.emit(
            DomainEvent(
                etype,
                meeting.meeting_id,
                payload,
                pipeline_run_id=self._run_id,
                trace_id=self._trace_id,
                producer=producer,
            )
        )

    def _finish(
        self,
        meeting: StepRunState,
        t0: Any,
        terminal: str,
        artifacts: list[dict[str, Any]],
        render: dict[str, Any] | None,
        sop_steps: list[dict[str, str]],
        pipeline_path: str,
        *,
        work_objects: list[dict[str, Any]] | None = None,
        usage: dict[str, Any] | None = None,
    ) -> StepEngineResult:
        self._emit(
            DomainEventType.PIPELINE_TERMINAL,
            meeting,
            {
                "terminal": terminal,
                "pipeline_path": pipeline_path,
                "budget_used": {
                    "retrieve_hops": self.budget.retrieve_hops,
                    "embed_attempts": self.budget.embed_attempts,
                    "tool_calls": self.budget.tool_calls,
                },
            },
        )
        t0.end(terminal=terminal)
        return StepEngineResult(
            terminal=terminal,
            artifacts=artifacts,
            work_objects=work_objects or [],
            render=render,
            events=self.events.types(),
            traces=len(self.obs.spans),
            usage=usage or {},
            sop_steps=sop_steps,
            pipeline_path=pipeline_path,
        )
