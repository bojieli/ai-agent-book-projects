"""离线确定性安全网关：无 Key / 无 URL 时保持 run_all 全绿。"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from app.safety.budget import ModelBudgetTracker
from app.safety.egress import evaluate_egress
from app.safety.protocol import ChatCompletionResult, ToolAuthorizeResult

# 平台硬拒绝工具（与安全控制面对齐）
_OFFLINE_DENYLIST = frozenset(
    {"shell_exec", "transfer_money_unrestricted", "os_system", "kubectl_exec"}
)

# 纪要君默认业务工具：离线允许授权
_OFFLINE_MEETING_ALLOW = frozenset(
    {
        "connector.defect.create",
        "connector.task.create",
        "connector.wecom.notify",
        "search_kb",
        "fetch_url",
    }
)


class OfflineSafetyGateway:
    """
    本地确定性替身：不发外网、不读真实凭据。
    高敏内容 external_provider_calls 恒为 0。
    """

    def __init__(self, budget: ModelBudgetTracker | None = None) -> None:
        self.budget = budget or ModelBudgetTracker()
        self._external_calls = 0
        self.audit: list[dict[str, Any]] = []

    @property
    def external_provider_calls(self) -> int:
        return self._external_calls

    def chat_completions(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "mock-llm",
        classification: str = "internal",
        sealed: bool = False,
        trace_id: str = "",
        org_domain: str = "",
        policy_binding: str = "",
    ) -> ChatCompletionResult:
        user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user = m.get("content", "")
                break
        eg = evaluate_egress(classification=classification, text=user, sealed=sealed)
        req_id = "off_" + uuid.uuid4().hex[:10]
        if not eg.allowed:
            self.audit.append(
                {
                    "type": "chat",
                    "decision": "block",
                    "reason": eg.reason,
                    "trace_id": trace_id,
                    "org_domain": org_domain,
                    "policy_binding": policy_binding,
                    "external_provider_calls": 0,
                }
            )
            return ChatCompletionResult(
                content=f"[blocked] {eg.reason}",
                decision="block",
                request_id=req_id,
                blocked_reason=eg.reason,
                finish_reason="content_filter",
                upstream="blocked",
                external_provider_calls=0,
            )

        deny = self.budget.check_request(input_text=eg.redacted_text)
        if deny:
            self.audit.append({"type": "chat", "decision": "block", "reason": deny})
            return ChatCompletionResult(
                content=f"[blocked] budget:{deny}",
                decision="block",
                request_id=req_id,
                blocked_reason=deny,
                finish_reason="content_filter",
                upstream="blocked",
                external_provider_calls=0,
            )

        # 确定性本地回复（非外部 provider）
        digest = hashlib.sha256(eg.redacted_text.encode()).hexdigest()[:12]
        content = f"（offline safety mock）understood:{eg.redacted_text[:80]}#{digest}"
        self.budget.charge(input_text=eg.redacted_text, output_text=content)
        self.audit.append(
            {
                "type": "chat",
                "decision": eg.decision,
                "trace_id": trace_id,
                "org_domain": org_domain,
                "policy_binding": policy_binding,
                "model": model,
                "upstream": "offline",
            }
        )
        return ChatCompletionResult(
            content=content,
            decision=eg.decision,
            request_id=req_id,
            finish_reason="stop",
            upstream="offline",
            external_provider_calls=0,
            meta={"model": model},
        )

    def authorize_tool(
        self,
        *,
        tool_id: str,
        arguments: dict[str, Any],
        trace_id: str = "",
        org_domain: str = "",
        policy_binding: str = "",
    ) -> ToolAuthorizeResult:
        req_id = "off_authz_" + uuid.uuid4().hex[:8]
        if tool_id in _OFFLINE_DENYLIST:
            decision = "block"
            risk = {"op_risk_tier": "critical", "decision": "block", "matched_rules": ["denylist"]}
        elif tool_id in _OFFLINE_MEETING_ALLOW or tool_id.startswith("connector."):
            decision = "allow"
            risk = {"op_risk_tier": "low", "decision": "allow", "matched_rules": []}
        else:
            # 未知工具离线默认 confirm_only，避免扩大权限
            decision = "confirm_only"
            risk = {
                "op_risk_tier": "medium",
                "decision": "confirm_only",
                "matched_rules": ["unknown_tool_offline"],
            }
        self.audit.append(
            {
                "type": "authorize",
                "tool_id": tool_id,
                "decision": decision,
                "trace_id": trace_id,
                "org_domain": org_domain,
                "policy_binding": policy_binding,
                "arguments_keys": list(arguments.keys()),
            }
        )
        return ToolAuthorizeResult(
            decision=decision,
            request_id=req_id,
            risk=risk,
            executed=False,
            trace_id=trace_id,
            org_domain=org_domain,
            policy_binding=policy_binding,
        )
