"""Persistent defect connector — simulates real external tracker (Phase 3)."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PersistentDefectConnector:
    """File-backed defect system — same SPI; Orchestrator does not change."""

    path: Path
    id: str = "connector.defect.create"
    production_effect: str = "draft_only"
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"defects": {}}, ensure_ascii=False), encoding="utf-8")

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return {
            "name": self.id,
            "description": "Create/update defect in persistent tracker",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "idempotency_key": {"type": "string"},
                    "status": {"type": "string"},
                },
                "required": ["title"],
            },
        }

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            key = args.get("idempotency_key") or str(uuid.uuid4())
            if key in data["defects"]:
                return data["defects"][key]
            external_id = f"BUG-{len(data['defects']) + 1:04d}"
            obj = {
                "external_id": external_id,
                "status": args.get("status", "draft"),
                "title": args["title"],
                "idempotency_key": key,
                "production_effect": self.production_effect,
            }
            data["defects"][key] = obj
            self._save(data)
            return obj

    def sync_status(self, idempotency_key: str, status: str) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            if idempotency_key not in data["defects"]:
                raise KeyError(idempotency_key)
            data["defects"][idempotency_key]["status"] = status
            self._save(data)
            return data["defects"][idempotency_key]

    def get(self, idempotency_key: str) -> dict[str, Any] | None:
        return self._load()["defects"].get(idempotency_key)
