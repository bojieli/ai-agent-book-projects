"""安全控制面客户端协议（模型代理 + 工具授权两条接口）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ChatCompletionResult:
    """OpenAI-compatible 聊天结果（经安全代理）。"""

    content: str
    decision: str
    request_id: str = ""
    blocked_reason: str = ""
    finish_reason: str = "stop"
    upstream: str = "offline"  # offline | http | blocked
    external_provider_calls: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolAuthorizeResult:
    """工具授权干跑结果；executed 恒为 False。"""

    decision: str
    request_id: str = ""
    risk: dict[str, Any] = field(default_factory=dict)
    executed: bool = False
    trace_id: str = ""
    org_domain: str = ""
    policy_binding: str = ""
    fail_closed: bool = False  # True 表示接口失败后的保守拒绝
    message: str = ""


class SafetyGateway(Protocol):
    """纪要君唯一允许的模型/工具安全出口。"""

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
    ) -> ChatCompletionResult: ...

    def authorize_tool(
        self,
        *,
        tool_id: str,
        arguments: dict[str, Any],
        trace_id: str = "",
        org_domain: str = "",
        policy_binding: str = "",
    ) -> ToolAuthorizeResult: ...

    @property
    def external_provider_calls(self) -> int:
        """累计真实外部模型调用次数（高敏验收用）。"""
        ...
