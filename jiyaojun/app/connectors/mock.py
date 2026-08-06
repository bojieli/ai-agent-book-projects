"""Mock connectors — draft-only for Phase 0; MCP descriptors required."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


def _desc(tool_id: str, description: str, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool_id,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": [k for k in properties if k != "idempotency_key"],
        },
    }


@dataclass
class MockTaskConnector:
    id: str = "connector.task.create"
    production_effect: str = "draft_only"
    store: dict[str, Any] = field(default_factory=dict)

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return _desc(self.id, "Create task draft", {"title": {"type": "string"}, "idempotency_key": {"type": "string"}})

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        key = args.get("idempotency_key") or str(uuid.uuid4())
        if key in self.store:
            return self.store[key]
        obj = {
            "external_id": f"TASK-{len(self.store) + 1}",
            "status": "draft",
            "title": args.get("title", "untitled"),
            "idempotency_key": key,
            "production_effect": self.production_effect,
        }
        self.store[key] = obj
        return obj


@dataclass
class MockDefectConnector:
    id: str = "connector.defect.create"
    production_effect: str = "draft_only"
    store: dict[str, Any] = field(default_factory=dict)

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return _desc(self.id, "Create defect draft", {"title": {"type": "string"}, "idempotency_key": {"type": "string"}})

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        key = args.get("idempotency_key") or str(uuid.uuid4())
        if key in self.store:
            return self.store[key]
        obj = {
            "external_id": f"BUG-{len(self.store) + 1}",
            "status": "draft",
            "title": args.get("title", "untitled"),
            "idempotency_key": key,
            "production_effect": self.production_effect,
        }
        self.store[key] = obj
        return obj


@dataclass
class ForbiddenProductionConnector:
    id: str = "connector.policy.production_enable"
    production_effect: str = "production"

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return _desc(self.id, "FORBIDDEN production enable", {})

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("production enable must never run in V1 demos")
