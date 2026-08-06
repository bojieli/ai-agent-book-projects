"""Department connectors — same SPI; register without touching Orchestrator (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


def _mcp(tool_id: str, desc: str) -> dict[str, Any]:
    return {
        "name": tool_id,
        "description": desc,
        "inputSchema": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "idempotency_key": {"type": "string"}},
            "required": ["title"],
        },
    }


@dataclass
class InMemoryDraftConnector:
    id: str
    production_effect: str = "draft_only"
    object_prefix: str = "OBJ"
    store: dict[str, Any] = field(default_factory=dict)

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return _mcp(self.id, f"Draft connector {self.id}")

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        key = args.get("idempotency_key") or str(uuid.uuid4())
        if key in self.store:
            return self.store[key]
        obj = {
            "external_id": f"{self.object_prefix}-{len(self.store)+1}",
            "status": "draft",
            "title": args.get("title", "untitled"),
            "idempotency_key": key,
            "production_effect": self.production_effect,
        }
        self.store[key] = obj
        return obj


def department_connectors() -> list[InMemoryDraftConnector]:
    return [
        InMemoryDraftConnector("connector.task.create", object_prefix="TASK"),
        InMemoryDraftConnector("connector.limit_draft.create", object_prefix="LIM"),
        InMemoryDraftConnector("connector.policy_draft.create", object_prefix="POL"),
        InMemoryDraftConnector("connector.observe_task.create", object_prefix="OBS"),
        InMemoryDraftConnector("connector.remediation_ledger.upsert", object_prefix="REM"),
        InMemoryDraftConnector(
            "connector.hr_ledger.draft",
            production_effect="none",
            object_prefix="HR",
        ),
    ]
