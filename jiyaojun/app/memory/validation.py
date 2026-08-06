"""Journal tree validation — fail closed on corrupt session logs。"""

from __future__ import annotations

from app.memory.journal_entry import JournalEntry


class JournalValidationError(ValueError):
    pass


VALID_ENTRY_TYPES = frozenset(
    {
        "message",
        "tool_result",
        "state",
        "compaction",
        "branch",
        "observation",
        "session_meta",
    }
)


def validate_journal_entries(session_id: str, entries: list[JournalEntry]) -> None:
    if not session_id:
        raise JournalValidationError("session_id required")
    seen_order: list[str] = []
    seen: set[str] = set()
    by_id: dict[str, JournalEntry] = {}
    for e in entries:
        if not e.id:
            raise JournalValidationError("entry missing id")
        if e.id in seen:
            raise JournalValidationError(f"duplicate entry id: {e.id}")
        seen.add(e.id)
        if e.entry_type not in VALID_ENTRY_TYPES:
            raise JournalValidationError(f"invalid entry_type: {e.entry_type}")
        if e.session_id and e.session_id != session_id:
            raise JournalValidationError(
                f"cross-session entry {e.id}: {e.session_id} != {session_id}"
            )
        if e.parent_id is not None and e.parent_id not in seen:
            raise JournalValidationError(
                f"forward parent missing: {e.parent_id} must appear before {e.id}"
            )
        seen_order.append(e.id)
        by_id[e.id] = e

    for e in entries:
        if e.parent_id is not None and e.parent_id not in by_id:
            raise JournalValidationError(f"missing parent {e.parent_id} for {e.id}")

    for start in entries:
        visited: set[str] = set()
        cur: str | None = start.id
        while cur:
            if cur in visited:
                raise JournalValidationError(f"cycle detected at {cur}")
            visited.add(cur)
            node = by_id.get(cur)
            if not node:
                break
            cur = node.parent_id


def resolve_active_leaf(entries: list[JournalEntry]) -> str | None:
    """reload 取最后一条合法 entry（含 branch marker）。"""
    if not entries:
        return None
    return entries[-1].id


def active_path(entries: list[JournalEntry], leaf_id: str | None) -> list[JournalEntry]:
    """从 leaf 沿 parent 链到根；branch marker 自身不入 path 内容。"""
    if not leaf_id:
        return []
    by_id = {e.id: e for e in entries}
    path: list[JournalEntry] = []
    cur: str | None = leaf_id
    visited: set[str] = set()
    while cur:
        if cur in visited:
            raise JournalValidationError(f"cycle at {cur}")
        visited.add(cur)
        node = by_id.get(cur)
        if not node:
            break
        if node.entry_type != "branch":
            path.append(node)
        cur = node.parent_id
    path.reverse()
    return path


def get_session_meta(entries: list[JournalEntry]) -> dict | None:
    for e in entries:
        if e.entry_type == "session_meta":
            return dict(e.payload)
    return None
