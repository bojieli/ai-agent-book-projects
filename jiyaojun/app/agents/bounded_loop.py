"""Bounded agent tool loop — observation → 下一轮 planner。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol

from app.connectors.discovery import DiscoveryGrant, ToolDiscoveryService
from app.events.enums import PRODUCTION_EFFECT_RANK
from app.harness import ToolRuntime
from app.memory.context import ContextBundle, build_context
from app.memory.session_journal import SessionJournal
from app.observability import BudgetTracker, CostQuota
from app.safety.dual_authz import authorize_tool_dual
from app.safety.factory import build_safety_gateway
from app.safety.protocol import SafetyGateway
from app.observability.telemetry import SPAN_TOOL_AUTHZ, SPAN_HITL, default_telemetry

_DEFAULT_POLICY_ALLOWLIST = ["connector.defect.create", "connector.task.create"]


class PlannerAction(str, Enum):
    ANSWER = "answer"
    TOOL_CALL = "tool_call"
    SUSPEND = "suspend"


@dataclass
class PlannerDecision:
    action: PlannerAction
    content: str = ""
    tool_id: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    suspend_reason: str = ""


class Planner(Protocol):
    def decide(
        self,
        *,
        context: ContextBundle,
        grant: DiscoveryGrant,
        step: int,
        tools_called: list[str],
        pending_hitl: bool = False,
    ) -> PlannerDecision: ...


def _pick_tool_for_intent(last_user: str, grant: DiscoveryGrant) -> str | None:
    """按明确中文/英文意图选择 task vs defect。"""
    lu = last_user.lower()
    if "建任务" in last_user or "create task" in lu:
        preferred = "connector.task.create"
    elif "建缺陷" in last_user or "create defect" in lu:
        preferred = "connector.defect.create"
    else:
        return None
    if preferred in grant.granted_ids:
        return preferred
    return None


@dataclass
class MockPlanner:
    def decide(
        self,
        *,
        context: ContextBundle,
        grant: DiscoveryGrant,
        step: int,
        tools_called: list[str],
        pending_hitl: bool = False,
    ) -> PlannerDecision:
        if pending_hitl:
            return PlannerDecision(PlannerAction.SUSPEND, suspend_reason="hitl_required")

        has_tool_result = any(
            e.get("entry_type") in {"tool_result", "observation"} for e in context.recent_entries
        )
        if has_tool_result and tools_called:
            last_ext = ""
            for e in reversed(context.recent_entries):
                if e.get("entry_type") == "tool_result":
                    last_ext = str((e.get("payload") or {}).get("result", {}).get("external_id", ""))
                    break
            return PlannerDecision(
                PlannerAction.ANSWER,
                content=f"已完成工具调用 {tools_called[-1]}，external_id={last_ext}",
            )

        last_user = ""
        for e in reversed(context.recent_entries):
            if e.get("entry_type") == "message":
                p = e.get("payload") or {}
                if p.get("role") == "user":
                    last_user = str(p.get("content", ""))
                    break

        if ("人工" in last_user or "HITL" in last_user.upper()) and not has_tool_result:
            return PlannerDecision(PlannerAction.SUSPEND, suspend_reason="hitl_required")

        tool_triggers = ("建缺陷", "建任务", "create defect", "create task")
        wants_tool = any(t in last_user for t in tool_triggers)

        if wants_tool and not has_tool_result:
            tid = _pick_tool_for_intent(last_user, grant)
            if not tid:
                return PlannerDecision(
                    PlannerAction.ANSWER,
                    content="无可用工具 grant，无法执行写回。",
                )
            if tid in tools_called:
                return PlannerDecision(
                    PlannerAction.ANSWER,
                    content=f"工具 {tid} 已调用，不再重复。",
                )
            return PlannerDecision(
                PlannerAction.TOOL_CALL,
                tool_id=tid,
                tool_args={"title": last_user[:80]},
            )

        return PlannerDecision(
            PlannerAction.ANSWER,
            content=f"（mock planner）已理解：{last_user[:120] or '…'}",
        )


PreToolHook = Callable[[str, dict[str, Any], DiscoveryGrant], tuple[bool, str]]


def deny_first_pre_tool_hook(
    tool_id: str,
    args: dict[str, Any],
    grant: DiscoveryGrant,
) -> tuple[bool, str]:
    if tool_id not in grant.granted_ids:
        return False, "tool_not_in_discovery_grant"
    return True, ""


def resolve_resume_allowlist(
    *,
    suspend_payload: dict[str, Any],
    policy_allowlist: list[str] | None,
    default_policy: list[str] | None = None,
) -> list[str]:
    """resume 权限 = policy_allowlist ∩ discovery_grant_ids；不得扩大。"""
    suspended_grant = set(suspend_payload.get("discovery_grant_ids") or [])
    if policy_allowlist is not None:
        policy_cap = list(policy_allowlist)
    elif suspend_payload.get("policy_allowlist") is not None:
        policy_cap = list(suspend_payload["policy_allowlist"])
    elif default_policy is not None:
        policy_cap = list(default_policy)
    else:
        policy_cap = []
    return [t for t in policy_cap if t in suspended_grant]


@dataclass
class AgentLoopResult:
    terminal: str
    answer: str = ""
    steps: int = 0
    tool_calls: int = 0
    events: list[str] = field(default_factory=list)
    suspend_reason: str = ""


@dataclass
class BoundedAgentLoop:
    runtime: ToolRuntime
    discovery: ToolDiscoveryService
    planner: Planner
    max_steps: int = 5
    pre_tool_hook: PreToolHook = deny_first_pre_tool_hook
    max_effect: str = "draft_only"
    default_policy_allowlist: list[str] = field(
        default_factory=lambda: list(_DEFAULT_POLICY_ALLOWLIST)
    )
    # 安全控制面：默认离线网关；业务授权后再调 /v1/tools/authorize
    safety_gateway: SafetyGateway | None = None
    policy_binding: str = "jiyaojun/dialog"
    dual_authz_enabled: bool = True

    def _gateway(self) -> SafetyGateway:
        if self.safety_gateway is None:
            self.safety_gateway = build_safety_gateway()
        return self.safety_gateway

    def run(
        self,
        *,
        journal: SessionJournal,
        need: str,
        org_domains: list[str],
        scenario: str,
        tool_allowlist: list[str] | None = None,
        meeting_id: str = "dialog",
        pending_hitl: bool = False,
        trace_id: str = "",
    ) -> AgentLoopResult:
        budget = BudgetTracker(CostQuota(max_tool_calls=self.max_steps))
        events: list[str] = []
        answer = ""
        tool_calls = 0
        tools_called: list[str] = []

        for step in range(1, self.max_steps + 1):
            if budget.exhausted:
                events.append("budget.exhausted")
                return AgentLoopResult("failed", answer=answer, steps=step - 1, tool_calls=tool_calls, events=events)

            ctx = build_context(journal)
            grant = self.discovery.discover(
                need=need,
                org_domains=org_domains,
                scenario=scenario,
                max_effect=self.max_effect,
                tool_allowlist=tool_allowlist,
            )
            journal.append("state", {"discovery_grant": grant.granted_ids, "step": step})
            events.append("discovery.granted")

            decision = self.planner.decide(
                context=ctx,
                grant=grant,
                step=step,
                tools_called=tools_called,
                pending_hitl=pending_hitl,
            )
            pending_hitl = False

            if decision.action == PlannerAction.SUSPEND:
                journal.mark_suspend(
                    decision.suspend_reason,
                    discovery_grant_ids=list(grant.granted_ids),
                    policy_allowlist=tool_allowlist,
                )
                hitl_span = default_telemetry.start_span(
                    SPAN_HITL, meeting_id=meeting_id, trace_id=trace_id or journal.session_id
                )
                default_telemetry.end_span(hitl_span, status="suspended", reason=decision.suspend_reason)
                default_telemetry.emit(
                    "hitl.suspend",
                    terminal="suspended",
                    trace_id=trace_id or journal.session_id,
                    reason=decision.suspend_reason,
                )
                events.append("hitl.suspend")
                return AgentLoopResult(
                    "suspended",
                    steps=step,
                    tool_calls=tool_calls,
                    events=events,
                    suspend_reason=decision.suspend_reason,
                )

            if decision.action == PlannerAction.ANSWER:
                answer = decision.content
                journal.append("message", {"role": "assistant", "content": answer})
                events.append("planner.answer")
                return AgentLoopResult(
                    "succeeded", answer=answer, steps=step, tool_calls=tool_calls, events=events
                )

            if decision.action == PlannerAction.TOOL_CALL:
                ok, reason = self.pre_tool_hook(decision.tool_id, decision.tool_args, grant)
                if not ok:
                    events.append(f"pretool.denied:{reason}")
                    return AgentLoopResult("failed", steps=step, tool_calls=tool_calls, events=events)

                # ADR-0004：本地业务授权之后调用独立安全授权；取更严格结果
                if self.dual_authz_enabled:
                    tid = trace_id or f"{journal.session_id}:{step}"
                    authz_span = default_telemetry.start_span(
                        SPAN_TOOL_AUTHZ, meeting_id=meeting_id, trace_id=tid
                    )
                    dual = authorize_tool_dual(
                        self._gateway(),
                        tool_id=decision.tool_id,
                        arguments=decision.tool_args,
                        granted_ids=list(grant.granted_ids),
                        trace_id=tid,
                        org_domain=(org_domains[0] if org_domains else ""),
                        policy_binding=self.policy_binding,
                    )
                    default_telemetry.end_span(
                        authz_span,
                        status="ok" if dual.allowed else "denied",
                        decision=dual.final_decision,
                    )
                    journal.append(
                        "state",
                        {
                            "dual_authz": {
                                "tool_id": decision.tool_id,
                                "final": dual.final_decision,
                                "business": dual.business_decision,
                                "safety": dual.safety_decision,
                                "audit": dual.audit,
                            }
                        },
                    )
                    if not dual.allowed:
                        events.append(f"safety.denied:{dual.reason}:{dual.final_decision}")
                        return AgentLoopResult(
                            "failed", steps=step, tool_calls=tool_calls, events=events
                        )
                    events.append(f"safety.authorized:{dual.final_decision}")

                key = f"agent_{journal.session_id}_{step}_{decision.tool_id}"
                try:
                    result = self.runtime.call(
                        decision.tool_id,
                        meeting_id,
                        decision.tool_args,
                        allowlist=grant.granted_ids,
                        max_effect=self.max_effect,
                        effect_rank=PRODUCTION_EFFECT_RANK,
                        idempotency_key=key,
                    )
                except (KeyError, PermissionError) as exc:
                    events.append(f"tool.failed:{exc}")
                    return AgentLoopResult("failed", steps=step, tool_calls=tool_calls, events=events)

                budget.charge(tool_calls=1)
                tool_calls += 1
                tools_called.append(decision.tool_id)
                journal.append("tool_result", {"tool_id": decision.tool_id, "result": result})
                journal.append(
                    "observation",
                    {"tool_id": decision.tool_id, "result": result, "observation": "tool_executed"},
                )
                events.append("tool.executed")
                continue

        events.append("max_steps.exceeded")
        return AgentLoopResult("failed", steps=self.max_steps, tool_calls=tool_calls, events=events)

    def resume(
        self,
        *,
        journal: SessionJournal,
        need: str,
        org_domains: list[str],
        scenario: str,
        tool_allowlist: list[str] | None = None,
        meeting_id: str = "dialog",
        hitl_approved: bool = True,
        user_id: str = "",
    ) -> AgentLoopResult:
        suspend = journal.pending_suspend()
        if not suspend:
            return AgentLoopResult("failed", suspend_reason="no_pending_suspend", events=["hitl.no_pending"])

        if not hitl_approved:
            journal.mark_hitl_resolved(False, user_id)
            return AgentLoopResult("rejected", events=["hitl.rejected"])

        effective_allowlist = resolve_resume_allowlist(
            suspend_payload=suspend,
            policy_allowlist=tool_allowlist,
            default_policy=self.default_policy_allowlist,
        )

        journal.mark_hitl_resolved(True, user_id)
        if need:
            journal.append("message", {"role": "user", "content": need, "user_id": user_id})

        return self.run(
            journal=journal,
            need=need or "continue",
            org_domains=org_domains,
            scenario=scenario,
            tool_allowlist=effective_allowlist,
            meeting_id=meeting_id,
            pending_hitl=False,
        )
