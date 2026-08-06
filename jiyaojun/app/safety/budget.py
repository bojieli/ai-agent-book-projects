"""模型调用预算：输入 8K / 输出 2K / 日 100 次 / 月 200 元（ADR-0003）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelBudgetTracker:
    """进程内预算；超限时不得放宽安全边界（fail-closed）。"""

    max_input_tokens: int = 8192
    max_output_tokens: int = 2048
    daily_call_limit: int = 100
    monthly_budget_cny: float = 200.0
    cost_per_1k_tokens_cny: float = 0.02
    daily_calls: int = 0
    monthly_spend_cny: float = 0.0
    events: list[str] = field(default_factory=list)

    def estimate_tokens(self, text: str) -> int:
        """粗估 token（约 4 字符 ≈ 1 token）。"""
        return max(1, len(text) // 4)

    def check_request(self, *, input_text: str, planned_output_tokens: int | None = None) -> str | None:
        """
        请求前检查；返回拒绝原因，通过则返回 None。
        普通调用不能放宽这些上限。
        """
        inp = self.estimate_tokens(input_text)
        if inp > self.max_input_tokens:
            self.events.append("budget.input_exceeded")
            return "input_token_limit"
        out_cap = planned_output_tokens if planned_output_tokens is not None else self.max_output_tokens
        if out_cap > self.max_output_tokens:
            self.events.append("budget.output_exceeded")
            return "output_token_limit"
        if self.daily_calls >= self.daily_call_limit:
            self.events.append("budget.daily_calls_exhausted")
            return "daily_call_limit"
        if self.monthly_spend_cny >= self.monthly_budget_cny:
            self.events.append("budget.monthly_exhausted")
            return "monthly_budget"
        return None

    def charge(self, *, input_text: str, output_text: str) -> None:
        """成功调用后记账。"""
        tokens = self.estimate_tokens(input_text) + self.estimate_tokens(output_text)
        self.daily_calls += 1
        self.monthly_spend_cny += (tokens / 1000.0) * self.cost_per_1k_tokens_cny
        self.events.append(f"budget.charged:{tokens}")
