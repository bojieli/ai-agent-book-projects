"""CostQuota — Observability companion (03 §2.15)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CostQuota:
    max_llm_tokens: int = 200_000
    max_tool_calls: int = 50
    max_retrieve_hops: int = 6
    max_embed_attempts: int = 3
    max_render_variants: int = 5
    max_wall_clock_sec: float = 600.0


@dataclass
class BudgetTracker:
    quota: CostQuota
    llm_tokens: int = 0
    tool_calls: int = 0
    retrieve_hops: int = 0
    embed_attempts: int = 0
    render_variants: int = 0
    wall_clock_sec: float = 0.0
    exhausted: list[str] = field(default_factory=list)

    def charge(self, **kwargs: float | int) -> list[str]:
        for k, v in kwargs.items():
            setattr(self, k, getattr(self, k) + v)
        return self.check()

    def check(self) -> list[str]:
        self.exhausted = []
        if self.llm_tokens > self.quota.max_llm_tokens:
            self.exhausted.append("llm")
        if self.tool_calls > self.quota.max_tool_calls:
            self.exhausted.append("tool")
        if self.retrieve_hops > self.quota.max_retrieve_hops:
            self.exhausted.append("retrieve")
        if self.embed_attempts > self.quota.max_embed_attempts:
            self.exhausted.append("embed")
        if self.render_variants > self.quota.max_render_variants:
            self.exhausted.append("render")
        if self.wall_clock_sec > self.quota.max_wall_clock_sec:
            self.exhausted.append("wall_clock")
        return list(self.exhausted)
