"""In-memory event bus for Phase 0 (no broker required)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.events.enums import DomainEventType


@dataclass
class DomainEvent:
    event_type: DomainEventType
    meeting_id: str
    payload: dict[str, Any]
    pipeline_run_id: str | None = None
    trace_id: str | None = None
    producer: str = "phase0"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": str(self.event_type),
            "occurred_at": self.occurred_at,
            "trace_id": self.trace_id,
            "meeting_id": self.meeting_id,
            "pipeline_run_id": self.pipeline_run_id,
            "producer": self.producer,
            "payload": self.payload,
        }


class EventLog:
    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def emit(self, event: DomainEvent) -> DomainEvent:
        self._events.append(event)
        return event

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def types(self) -> list[str]:
        return [str(e.event_type) for e in self._events]
