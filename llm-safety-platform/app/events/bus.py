"""In-memory event bus for Phase 0."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DomainEvent:
    event_type: str
    tenant_id: str
    app_id: str
    request_id: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: float = field(default_factory=time.time)
    policy_binding_id: str | None = None
    policy_version: int | None = None


class EventBus:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def emit(self, event: DomainEvent) -> DomainEvent:
        self.events.append(event)
        return event

    def of_type(self, event_type: str) -> list[DomainEvent]:
        return [e for e in self.events if e.event_type == event_type]
