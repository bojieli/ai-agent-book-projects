"""Journal entry datamodel — 独立模块避免循环 import。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class JournalEntry:
    id: str
    parent_id: str | None
    entry_type: str  # message | tool_result | state | compaction | branch | observation
    timestamp: str
    payload: dict[str, Any]
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "entry_type": self.entry_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JournalEntry:
        return cls(
            id=str(data["id"]),
            parent_id=data.get("parent_id"),
            entry_type=str(data["entry_type"]),
            timestamp=str(data["timestamp"]),
            payload=data.get("payload") or {},
            session_id=str(data.get("session_id", "")),
        )
