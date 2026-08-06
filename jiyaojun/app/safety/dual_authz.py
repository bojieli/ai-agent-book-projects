"""业务权限 ∩ 安全风险上限 → 更严格结果生效（ADR-0001）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.safety.decisions import is_executable, max_strict
from app.safety.protocol import SafetyGateway, ToolAuthorizeResult


@dataclass
class DualAuthzResult:
    """双重授权最终结果。"""

    allowed: bool
    final_decision: str
    business_decision: str
    safety_decision: str
    reason: str = ""
    safety: ToolAuthorizeResult | None = None
    audit: dict[str, Any] = field(default_factory=dict)


def business_tool_decision(
    *,
    tool_id: str,
    granted_ids: list[str] | None,
) -> str:
    """本地业务权限：不在 discovery grant 内则 block。"""
    if granted_ids is not None and tool_id not in granted_ids:
        return "block"
    return "allow"


def combine_business_and_safety(
    *,
    business_decision: str,
    safety: ToolAuthorizeResult,
) -> DualAuthzResult:
    """
    最终取更严格值。
    安全平台不能授予业务侧已拒绝的工具；接口失败（fail_closed）亦不得放行。
    """
    final = max_strict([business_decision, safety.decision])
    # 安全侧 executed 必须为 False（授权干跑）；若异常为 True 仍不允许扩大为“已执行”
    if safety.executed:
        final = max_strict([final, "block"])
    allowed = is_executable(final) and business_decision == "allow"
    reason = ""
    if not allowed:
        if business_decision == "block":
            reason = "business_denied"
        elif safety.fail_closed:
            reason = "safety_fail_closed"
        else:
            reason = f"safety_{safety.decision}"
    return DualAuthzResult(
        allowed=allowed,
        final_decision=final,
        business_decision=business_decision,
        safety_decision=safety.decision,
        reason=reason,
        safety=safety,
        audit={
            "trace_id": safety.trace_id,
            "org_domain": safety.org_domain,
            "policy_binding": safety.policy_binding,
            "request_id": safety.request_id,
            "risk": safety.risk,
        },
    )


def authorize_tool_dual(
    gateway: SafetyGateway,
    *,
    tool_id: str,
    arguments: dict[str, Any],
    granted_ids: list[str] | None,
    trace_id: str = "",
    org_domain: str = "",
    policy_binding: str = "",
) -> DualAuthzResult:
    """先算业务权限，再调安全授权接口，最后取更严。"""
    biz = business_tool_decision(tool_id=tool_id, granted_ids=granted_ids)
    if biz == "block":
        # 业务已拒绝：仍可调安全做审计，但最终必为 block；为省调用可短路。
        return DualAuthzResult(
            allowed=False,
            final_decision="block",
            business_decision="block",
            safety_decision="allow",  # 未咨询；最终仍 block
            reason="business_denied",
            audit={"short_circuit": True, "trace_id": trace_id, "org_domain": org_domain},
        )
    safety = gateway.authorize_tool(
        tool_id=tool_id,
        arguments=arguments,
        trace_id=trace_id,
        org_domain=org_domain,
        policy_binding=policy_binding,
    )
    return combine_business_and_safety(business_decision=biz, safety=safety)
