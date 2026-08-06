"""经安全控制面路由的 LLM 客户端；禁止旁路直连外部模型。"""

from __future__ import annotations

from typing import Any

from app.agents.llm_evaluator import MockLLMClient, MockLLMResponse
from app.safety.protocol import SafetyGateway


class SafetyRoutedLLMClient:
    """
    所有 complete() 经 SafetyGateway.chat_completions。
    可包装既有 MockLLMClient 作为离线兜底内容源（仍不直连外网）。
    """

    def __init__(
        self,
        gateway: SafetyGateway,
        *,
        model: str = "mock-llm",
        classification: str = "internal",
        fallback: MockLLMClient | None = None,
        org_domain: str = "eng",
        policy_binding: str = "jiyaojun/default",
    ) -> None:
        self.gateway = gateway
        self.model = model
        self.classification = classification
        self.fallback = fallback or MockLLMClient(model=model)
        self.org_domain = org_domain
        self.policy_binding = policy_binding
        self.calls: list[dict[str, Any]] = []

    def complete(self, system: str, user: str) -> MockLLMResponse:
        """评估器兼容接口：返回 MockLLMResponse 形状。"""
        result = self.gateway.chat_completions(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=self.model,
            classification=self.classification,
            org_domain=self.org_domain,
            policy_binding=self.policy_binding,
        )
        self.calls.append(
            {
                "decision": result.decision,
                "upstream": result.upstream,
                "external_provider_calls": result.external_provider_calls,
                "blocked_reason": result.blocked_reason,
            }
        )
        if result.decision == "block":
            return MockLLMResponse(
                self.model,
                prompt_hash="blocked",
                verdict="fail",
                rationale=result.blocked_reason or result.content,
                scores={"faithfulness": 0.0, "schema": 0.0},
            )
        # 离线代理已给出确定性文本；用 fallback 规则做 pass/fail 启发式时复用原逻辑
        if result.upstream == "offline":
            return self.fallback.complete(system, user)
        # HTTP 代理返回的内容：默认视为 pass（具体评测由上层规则决定）
        return MockLLMResponse(
            self.model,
            prompt_hash=result.request_id[:16] or "http",
            verdict="pass",
            rationale=result.content[:200],
            scores={"faithfulness": 0.8, "schema": 0.9},
        )
