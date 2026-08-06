"""Context assembly — active path 上最新 compaction + 保留消息。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.memory.session_journal import SessionJournal


@dataclass
class ContextBundle:
    session_id: str
    compaction_summaries: list[str]
    recent_entries: list[dict[str, Any]]
    active_leaf_id: str | None
    total_entries: int
    path_length: int = 0
    memory_kind: str = "session_journal"

    def to_messages(self) -> list[dict[str, Any]]:
        msgs: list[dict[str, Any]] = []
        for s in self.compaction_summaries:
            msgs.append({"role": "system", "content": f"[compaction] {s}"})
        for e in self.recent_entries:
            et = e.get("entry_type")
            p = e.get("payload") or {}
            if et == "message":
                msgs.append({"role": p.get("role", "user"), "content": p.get("content", "")})
            elif et in {"tool_result", "observation"}:
                msgs.append({"role": "tool", "content": str(p.get("result", p))})
            elif et == "state":
                msgs.append({"role": "system", "content": f"[state] {p}"})
        return msgs


def build_context(
    journal: SessionJournal,
    *,
    max_recent: int = 12,
) -> ContextBundle:
    """仅沿 active leaf 的 parent 路径；只放路径上最新 compaction + first_kept 后消息。"""
    path = journal.path_entries()
    latest_compaction: str | None = None
    first_kept_idx = 0

    for i, e in enumerate(path):
        if e.entry_type == "compaction":
            latest_compaction = str(e.payload.get("summary", ""))
            covered = e.payload.get("covered_until_id")
            if covered:
                for j, pe in enumerate(path):
                    if pe.id == covered:
                        first_kept_idx = max(first_kept_idx, j + 1)

    if latest_compaction and first_kept_idx == 0:
        # compaction 存在但未找到 covered id — 从 compaction 之后
        for i, e in enumerate(path):
            if e.entry_type == "compaction":
                first_kept_idx = i + 1

    tail = [
        e
        for e in path[first_kept_idx:]
        if e.entry_type not in {"compaction", "branch"}
    ]
    recent_raw = tail[-max_recent:]

    summaries = [latest_compaction] if latest_compaction else []

    return ContextBundle(
        session_id=journal.session_id,
        compaction_summaries=summaries,
        recent_entries=[e.to_dict() for e in recent_raw],
        active_leaf_id=journal.active_leaf_id,
        total_entries=len(journal.entries),
        path_length=len(path),
    )
