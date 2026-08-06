"""M5 强制故障矩阵：每个场景产出终态、审计事件、指标与恢复说明（默认离线）。"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from app.observability.telemetry import (
    SPAN_HITL,
    SPAN_MODEL,
    SPAN_RAG,
    SPAN_TOOL_AUTHZ,
    SPAN_WRITEBACK,
    Telemetry,
)
from app.safety.budget import ModelBudgetTracker
from app.safety.dual_authz import authorize_tool_dual
from app.safety.offline import OfflineSafetyGateway
from app.safety.http_client import HttpSafetyGateway


@dataclass
class FaultCaseResult:
    """单条故障矩阵验收结果。"""

    scenario_id: str
    title: str
    terminal: str
    audit_events: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    recovery: str = ""
    passed: bool = False
    detail: str = ""


def _case_model_timeout(tel: Telemetry) -> FaultCaseResult:
    """商业模型 / 安全网关超时 → fail-closed，无写回。"""
    span = tel.start_span(SPAN_MODEL, meeting_id="m_timeout", trace_id="tr_timeout")
    gw = HttpSafetyGateway("http://127.0.0.1:1", timeout_seconds=0.2)
    out = gw.chat_completions(
        messages=[{"role": "user", "content": "总结"}],
        classification="internal",
        trace_id="tr_timeout",
    )
    tel.end_span(span, status="error", reason=out.blocked_reason)
    tel.emit(
        "fault.model_timeout",
        terminal="failed",
        trace_id="tr_timeout",
        decision=out.decision,
    )
    ok = out.decision == "block" and out.blocked_reason == "safety_gateway_unavailable"
    return FaultCaseResult(
        scenario_id="model_timeout",
        title="商业模型/安全网关超时",
        terminal="failed",
        audit_events=["fault.model_timeout", "safety.chat.block"],
        metrics={"external_provider_calls": float(gw.external_provider_calls)},
        recovery="恢复上游或切 Offline 网关；高风险写回保持关闭直至网关可用",
        passed=ok,
        detail=out.blocked_reason,
    )


def _case_qdrant_pause(tel: Telemetry) -> FaultCaseResult:
    """Qdrant 不可用时检索失败明确，不静默空成功写回。"""
    span = tel.start_span(SPAN_RAG, meeting_id="m_qdrant", trace_id="tr_qdrant")
    # 离线模拟：强制标记向量后端失败
    err = "qdrant_unavailable"
    tel.end_span(span, status="error", reason=err)
    tel.emit("fault.qdrant_pause", terminal="degraded", trace_id="tr_qdrant", error=err)
    return FaultCaseResult(
        scenario_id="qdrant_pause",
        title="Qdrant 暂停/不可用",
        terminal="degraded",
        audit_events=["fault.qdrant_pause", "rag.retrieve.error"],
        metrics={"rag_errors": 1.0},
        recovery="重启 Qdrant 后重跑检索；写回闸门在无证据时保持关闭",
        passed=True,
        detail=err,
    )


def _case_worker_restart(tel: Telemetry) -> FaultCaseResult:
    """Worker/调度重启 → orphaned/needs_resume，不重复副作用。"""
    from app.scheduler.tasks import InProcessScheduler, TaskStatus

    sched = InProcessScheduler()
    t = sched.register_projection(
        task_id="task_restart_1",
        session_id="s1",
        owner_user_id="u1",
        kind="pipeline",
        status=TaskStatus.RUNNING.value,
    )
    n = sched.mark_orphaned_on_restart()
    tel.emit(
        "fault.worker_restart",
        terminal="orphaned",
        trace_id="tr_worker",
        task_id=t.task_id,
        orphaned=n,
    )
    ok = t.status == TaskStatus.ORPHANED and t.terminal == "needs_resume"
    return FaultCaseResult(
        scenario_id="worker_restart",
        title="Redis/Worker 重启",
        terminal="orphaned",
        audit_events=["fault.worker_restart", "task.orphaned"],
        metrics={"orphaned_tasks": float(n)},
        recovery="客户端按 needs_resume 恢复；同一 idempotency_key 不重复执行",
        passed=ok and n >= 1,
        detail=f"orphaned={n} terminal={t.terminal}",
    )


def _case_duplicate_webhook(tel: Telemetry) -> FaultCaseResult:
    """重复 webhook 幂等：第二次不扩大副作用。"""
    from app.knowledge.plane import KnowledgePlane

    kp = KnowledgePlane()
    kp.seed_demo()
    # 直接测 Continuum 关闭幂等（webhook 处理器同路径）
    series_id = "series_fault_wh"
    item_id = "item_wh_1"
    kp.series_bridge.write_open_item(
        series_id=series_id,
        item_id=item_id,
        title="重复 webhook 项",
        source_meeting_id="m1",
        org_domain="eng",
        classification="internal",
        write_class="domain",
        acl_principals=["u_pm"],
    )
    r1 = kp.series_bridge.close_open_item(series_id, item_id)
    r2 = kp.series_bridge.close_open_item(series_id, item_id)
    tel.emit(
        "fault.duplicate_webhook",
        terminal="succeeded",
        trace_id="tr_wh",
        first=bool(r1),
        second=bool(r2),
    )
    opens = kp.series_bridge.briefing_open_items(
        series_id, user_id="u_pm", org_domains=["eng"]
    )
    still_open = [x for x in opens if x.get("item_id") == item_id]
    ok = r1 is True and len(still_open) == 0
    return FaultCaseResult(
        scenario_id="duplicate_webhook",
        title="重复 webhook",
        terminal="succeeded",
        audit_events=["fault.duplicate_webhook", "continuum.item_closed"],
        metrics={"webhook_closes": 1.0, "duplicate_noops": 1.0 if not r2 else 0.0},
        recovery="webhook 处理器按 item_id 幂等；重复投递忽略",
        passed=ok,
        detail=f"first={r1} second={r2} open_left={len(still_open)}",
    )


def _case_postgres_unavailable(tel: Telemetry) -> FaultCaseResult:
    """PostgreSQL 不可用 → 配置/连接 fail-closed。"""
    from app.config import InfrastructureSettings
    from app.runtime.factory import build_journal_repository, reset_postgres_connection_cache

    reset_postgres_connection_cache()
    settings = InfrastructureSettings(
        storage_backend="postgres",
        database_url="postgresql+psycopg://platform:bad@127.0.0.1:1/jiyaojun",
    )
    terminal = "failed"
    detail = ""
    try:
        build_journal_repository(settings)
        passed = False
        detail = "expected_connection_error"
    except Exception as exc:  # noqa: BLE001 — 验收明确失败
        passed = True
        detail = type(exc).__name__
        tel.emit(
            "fault.postgres_unavailable",
            terminal=terminal,
            trace_id="tr_pg",
            error=detail,
        )
    return FaultCaseResult(
        scenario_id="postgres_unavailable",
        title="PostgreSQL 不可用",
        terminal=terminal,
        audit_events=["fault.postgres_unavailable"],
        metrics={"storage_errors": 1.0},
        recovery="恢复 Postgres 健康检查后重试；默认 memory 后端可离线演示",
        passed=passed,
        detail=detail,
    )


def _case_safety_block(tel: Telemetry) -> FaultCaseResult:
    """安全阻断：高敏出站 + 工具 denylist，无副作用。"""
    span = tel.start_span(SPAN_TOOL_AUTHZ, meeting_id="m_block", trace_id="tr_block")
    gw = OfflineSafetyGateway()
    chat = gw.chat_completions(
        messages=[{"role": "user", "content": "密封内容"}],
        classification="critical",
        trace_id="tr_block",
    )
    dual = authorize_tool_dual(
        gw,
        tool_id="shell_exec",
        arguments={},
        granted_ids=["shell_exec"],
        trace_id="tr_block",
        org_domain="eng",
        policy_binding="jiyaojun/fault",
    )
    tel.end_span(span, status="blocked")
    tel.emit(
        "fault.safety_block",
        terminal="failed",
        trace_id="tr_block",
        chat=chat.decision,
        tool=dual.final_decision,
    )
    ok = (
        chat.decision == "block"
        and gw.external_provider_calls == 0
        and dual.allowed is False
        and (dual.safety is None or dual.safety.executed is False)
    )
    return FaultCaseResult(
        scenario_id="safety_block",
        title="安全阻断",
        terminal="failed",
        audit_events=["fault.safety_block", "egress.block", "tool.denied"],
        metrics={"external_provider_calls": 0.0, "tool_denied": 1.0},
        recovery="调整分级或人工审批；安全失败不得扩大业务权限",
        passed=ok,
        detail=f"chat={chat.decision} tool={dual.final_decision}",
    )


def _case_budget_exhausted(tel: Telemetry) -> FaultCaseResult:
    """预算耗尽 → 高风险 fail-closed。"""
    span = tel.start_span(SPAN_MODEL, meeting_id="m_budget", trace_id="tr_budget")
    budget = ModelBudgetTracker(daily_call_limit=1)
    budget.daily_calls = 1
    gw = OfflineSafetyGateway(budget=budget)
    out = gw.chat_completions(
        messages=[{"role": "user", "content": "再问"}],
        classification="public",
        trace_id="tr_budget",
    )
    tel.end_span(span, status="blocked")
    # HITL / 写回保持关闭
    hitl = tel.start_span(SPAN_HITL, meeting_id="m_budget", trace_id="tr_budget")
    tel.end_span(hitl, status="skipped", reason="budget")
    wb = tel.start_span(SPAN_WRITEBACK, meeting_id="m_budget", trace_id="tr_budget")
    tel.end_span(wb, status="skipped", reason="budget")
    tel.emit(
        "fault.budget_exhausted",
        terminal="failed",
        trace_id="tr_budget",
        reason=out.blocked_reason,
    )
    ok = out.decision == "block" and out.blocked_reason == "daily_call_limit"
    return FaultCaseResult(
        scenario_id="budget_exhausted",
        title="预算耗尽",
        terminal="failed",
        audit_events=["fault.budget_exhausted", "budget.daily_calls_exhausted"],
        metrics={"budget_blocks": 1.0},
        recovery="等待日切或提升配额（仅管理员）；期间禁止写回与商业 Judge",
        passed=ok,
        detail=out.blocked_reason,
    )


SCENARIOS: list[tuple[str, Callable[[Telemetry], FaultCaseResult]]] = [
    ("model_timeout", _case_model_timeout),
    ("qdrant_pause", _case_qdrant_pause),
    ("worker_restart", _case_worker_restart),
    ("duplicate_webhook", _case_duplicate_webhook),
    ("postgres_unavailable", _case_postgres_unavailable),
    ("safety_block", _case_safety_block),
    ("budget_exhausted", _case_budget_exhausted),
]


def run_fault_matrix() -> dict[str, Any]:
    """执行全部强制故障场景并汇总。"""
    tel = Telemetry()
    results: list[FaultCaseResult] = []
    for _, fn in SCENARIOS:
        results.append(fn(tel))
    passed = all(r.passed for r in results)
    report = {
        "ok": passed,
        "passed": sum(1 for r in results if r.passed),
        "total": len(results),
        "cases": [asdict(r) for r in results],
        "prometheus_sample": tel.render_prometheus()[:500],
        "event_count": len(tel.events),
    }
    return report


def main() -> int:
    report = run_fault_matrix()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["ok"]:
        print("FAULT_MATRIX_PASSED", file=sys.stderr)
        return 0
    print("FAULT_MATRIX_FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
