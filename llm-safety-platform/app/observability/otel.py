"""Minimal OTel-style span recorder (export-ready; full SDK optional)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.config import settings


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    start_ms: float
    end_ms: float | None = None
    attrs: dict[str, Any] = field(default_factory=dict)


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []

    def start(self, name: str, **attrs: Any) -> Span:
        span = Span(
            name=name,
            trace_id=uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            start_ms=time.time() * 1000,
            attrs=attrs,
        )
        return span

    def end(self, span: Span) -> None:
        span.end_ms = time.time() * 1000
        if settings.otel_enabled or True:
            self.spans.append(span)


tracer = Tracer()
