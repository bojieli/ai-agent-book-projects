"""HTTP 安全网关客户端：只走 /v1/chat/completions 与 /v1/tools/authorize。"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from typing import Any

from app.safety.budget import ModelBudgetTracker
from app.safety.egress import evaluate_egress
from app.safety.protocol import ChatCompletionResult, ToolAuthorizeResult


class HttpSafetyGateway:
    """
    纪要君 → 安全控制面；不得旁路直连外部模型。
    接口失败 fail-closed，不得扩大业务权限。
    """

    def __init__(
        self,
        base_url: str,
        token: str = "",
        *,
        timeout_seconds: float = 5.0,
        budget: ModelBudgetTracker | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.budget = budget or ModelBudgetTracker()
        self._external_calls = 0
        self.audit: list[dict[str, Any]] = []

    @property
    def external_provider_calls(self) -> int:
        return self._external_calls

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = self.base_url + path
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers=self._headers(), method="POST"
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

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
        req_id = "http_" + uuid.uuid4().hex[:10]
        if not eg.allowed:
            self.audit.append({"type": "chat", "decision": "block", "reason": eg.reason})
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
            return ChatCompletionResult(
                content=f"[blocked] budget:{deny}",
                decision="block",
                request_id=req_id,
                blocked_reason=deny,
                finish_reason="content_filter",
                upstream="blocked",
                external_provider_calls=0,
            )

        # 出站前替换为脱敏文本
        safe_messages = []
        for m in messages:
            if m.get("role") == "user" and m.get("content") == user:
                safe_messages.append({"role": "user", "content": eg.redacted_text})
            else:
                safe_messages.append(dict(m))

        try:
            out = self._post(
                "/v1/chat/completions",
                {"model": model, "messages": safe_messages},
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
            self.audit.append({"type": "chat", "decision": "block", "reason": f"gateway_error:{exc}"})
            return ChatCompletionResult(
                content="[blocked] safety_gateway_unavailable",
                decision="block",
                request_id=req_id,
                blocked_reason="safety_gateway_unavailable",
                finish_reason="content_filter",
                upstream="blocked",
                external_provider_calls=0,
                meta={"error": str(exc)},
            )

        choice = (out.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = str(msg.get("content") or "")
        finish = str(choice.get("finish_reason") or "stop")
        decision = "block" if finish == "content_filter" else eg.decision
        # 经安全代理的真实上游调用计 1；本地 mock-llm 由平台决定，仍计入代理调用而非旁路
        self._external_calls += 1
        self.budget.charge(input_text=eg.redacted_text, output_text=content)
        self.audit.append(
            {
                "type": "chat",
                "decision": decision,
                "trace_id": trace_id,
                "org_domain": org_domain,
                "policy_binding": policy_binding,
            }
        )
        return ChatCompletionResult(
            content=content,
            decision=decision,
            request_id=str(out.get("id") or req_id),
            finish_reason=finish,
            upstream="http",
            external_provider_calls=1,
            meta={"trace_id": trace_id, "org_domain": org_domain},
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
        try:
            out = self._post(
                "/v1/tools/authorize",
                {
                    "tool_id": tool_id,
                    "arguments": arguments,
                    "trace_id": trace_id,
                    "org_domain": org_domain,
                    "policy_binding": policy_binding,
                },
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
            # 失败不得扩大权限
            self.audit.append({"type": "authorize", "decision": "block", "error": str(exc)})
            return ToolAuthorizeResult(
                decision="block",
                request_id="fail_" + uuid.uuid4().hex[:8],
                risk={"decision": "block", "reason_codes": ["gateway_unavailable"]},
                executed=False,
                trace_id=trace_id,
                org_domain=org_domain,
                policy_binding=policy_binding,
                fail_closed=True,
                message=f"safety_gateway_unavailable:{exc}",
            )

        decision = str(out.get("decision") or "block")
        self.audit.append(
            {
                "type": "authorize",
                "tool_id": tool_id,
                "decision": decision,
                "trace_id": trace_id,
                "org_domain": org_domain,
            }
        )
        return ToolAuthorizeResult(
            decision=decision,
            request_id=str(out.get("request_id") or ""),
            risk=dict(out.get("risk") or {}),
            executed=bool(out.get("executed", False)),
            trace_id=str(out.get("trace_id") or trace_id),
            org_domain=str(out.get("org_domain") or org_domain),
            policy_binding=str(out.get("policy_binding") or policy_binding),
            message=str(out.get("message") or ""),
        )
