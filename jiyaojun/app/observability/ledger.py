"""Observability stubs: trace spans + usage ledger (in-memory)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceSpan:
    span_id: str
    trace_id: str
    name: str
    meeting_id: str
    attrs: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None

    def end(self, **attrs: Any) -> None:
        self.attrs.update(attrs)
        self.ended_at = time.time()


@dataclass
class UsageLedger:
    org_domain: str
    scenario: str
    llm_tokens: int = 0
    tool_calls: int = 0
    retrieve_hops: int = 0
    embed_attempts: int = 0
    render_variants: int = 0
    wall_clock_sec: float = 0.0
    meeting_count: int = 1


class Observability:
    def __init__(self) -> None:
        self.spans: list[TraceSpan] = []
        self.usage: list[UsageLedger] = []

    def start_span(self, name: str, meeting_id: str, trace_id: str, **attrs: Any) -> TraceSpan:
        span = TraceSpan(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            name=name,
            meeting_id=meeting_id,
            attrs=dict(attrs),
        )
        self.spans.append(span)
        return span

    def record_usage(self, ledger: UsageLedger) -> None:
        self.usage.append(ledger)
