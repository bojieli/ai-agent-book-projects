"""Append-only session journal — session tree + branch marker + 原子 append。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from app.memory.journal_entry import JournalEntry
from app.memory.summarizer import DeterministicExtractiveSummarizer, Summarizer
from app.memory.validation import (
    active_path,
    get_session_meta,
    resolve_active_leaf,
    validate_journal_entries,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionAccessError(PermissionError):
    pass


class JournalRepository(Protocol):
    def load(self, session_id: str) -> list[JournalEntry]: ...
    def append_entry(self, session_id: str, entry: JournalEntry) -> None: ...
    def list_sessions(self) -> list[str]: ...


@dataclass
class SessionJournal:
    """单会话 append-only 日志；branch marker 自身为 active leaf。"""

    session_id: str
    repository: JournalRepository
    entries: list[JournalEntry] = field(default_factory=list)
    active_leaf_id: str | None = None
    summarizer: Summarizer = field(default_factory=DeterministicExtractiveSummarizer)

    @classmethod
    def resume(cls, session_id: str, repository: JournalRepository) -> SessionJournal:
        entries = repository.load(session_id)
        validate_journal_entries(session_id, entries)
        leaf = resolve_active_leaf(entries)
        return cls(session_id=session_id, repository=repository, entries=entries, active_leaf_id=leaf)

    @classmethod
    def open_or_resume(
        cls,
        session_id: str,
        repository: JournalRepository,
        *,
        owner_user_id: str,
        org_domains: list[str],
    ) -> SessionJournal:
        entries = repository.load(session_id)
        if not entries:
            j = cls(session_id=session_id, repository=repository, entries=[], active_leaf_id=None)
            j._append_locked(
                JournalEntry(
                    id=f"je_meta_{uuid.uuid4().hex[:8]}",
                    parent_id=None,
                    entry_type="session_meta",
                    timestamp=_now_iso(),
                    payload={
                        "owner_user_id": owner_user_id,
                        "org_domains": list(org_domains),
                    },
                    session_id=session_id,
                )
            )
            return j
        validate_journal_entries(session_id, entries)
        leaf = resolve_active_leaf(entries)
        journal = cls(session_id=session_id, repository=repository, entries=entries, active_leaf_id=leaf)
        journal.assert_access(user_id=owner_user_id, org_domains=org_domains)
        return journal

    def session_meta(self) -> dict[str, Any]:
        meta = get_session_meta(self.entries)
        return meta or {}

    def assert_access(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        is_admin: bool = False,
    ) -> None:
        if is_admin:
            return
        meta = self.session_meta()
        if not meta:
            raise SessionAccessError("session_meta missing")
        owner = meta.get("owner_user_id")
        if owner and owner != user_id:
            raise SessionAccessError(f"session owner mismatch: {owner} != {user_id}")
        allowed_orgs = set(meta.get("org_domains") or [])
        if allowed_orgs and not (set(org_domains) & allowed_orgs):
            raise SessionAccessError("org_domain not in session scope")

    def path_entries(self) -> list[JournalEntry]:
        return active_path(self.entries, self.active_leaf_id)

    def _append_locked(self, entry: JournalEntry) -> JournalEntry:
        self.repository.append_entry(self.session_id, entry)
        self.entries.append(entry)
        self.active_leaf_id = entry.id
        return entry

    def append(
        self,
        entry_type: str,
        payload: dict[str, Any],
        *,
        entry_id: str | None = None,
    ) -> JournalEntry:
        eid = entry_id or f"je_{uuid.uuid4().hex[:12]}"
        entry = JournalEntry(
            id=eid,
            parent_id=self.active_leaf_id,
            entry_type=entry_type,
            timestamp=_now_iso(),
            payload=payload,
            session_id=self.session_id,
        )
        return self._append_locked(entry)

    def append_compaction_if_needed(
        self,
        *,
        max_uncompacted: int = 12,
    ) -> JournalEntry | None:
        path = self.path_entries()
        last_compaction_idx = -1
        prior_summary: str | None = None
        for i, e in enumerate(path):
            if e.entry_type == "compaction":
                last_compaction_idx = i
                prior_summary = str(e.payload.get("summary", ""))

        uncompacted = [
            e
            for e in path[last_compaction_idx + 1 :]
            if e.entry_type not in {"compaction", "branch", "session_meta"}
        ]
        if len(uncompacted) <= max_uncompacted:
            return None

        to_cover = uncompacted[:-4]
        if not to_cover:
            return None
        covered_until_id = to_cover[-1].id
        summary = self.summarizer.summarize(to_cover, prior_summary=prior_summary)
        return self.append(
            "compaction",
            {
                "summary": summary,
                "covered_until_id": covered_until_id,
                "covered_count": len(to_cover),
            },
        )

    def append_compaction(self, summary: str, *, covered_until_id: str) -> JournalEntry:
        return self.append(
            "compaction",
            {"summary": summary, "covered_until_id": covered_until_id},
        )

    def fork_from(self, entry_id: str) -> JournalEntry:
        """分支：branch marker 自身成为 active leaf（parent=目标 entry）。"""
        if not any(e.id == entry_id for e in self.entries):
            raise KeyError(f"entry not found: {entry_id}")
        branch = JournalEntry(
            id=f"je_branch_{uuid.uuid4().hex[:8]}",
            parent_id=entry_id,
            entry_type="branch",
            timestamp=_now_iso(),
            payload={"fork_target": entry_id},
            session_id=self.session_id,
        )
        return self._append_locked(branch)

    def pending_suspend(self) -> dict[str, Any] | None:
        for e in reversed(self.path_entries()):
            if e.entry_type == "state":
                if e.payload.get("suspend"):
                    return e.payload
                if e.payload.get("hitl_resolved") or e.payload.get("hitl_rejected"):
                    return None
        return None

    def mark_suspend(
        self,
        reason: str,
        *,
        discovery_grant_ids: list[str],
        policy_allowlist: list[str] | None,
    ) -> JournalEntry:
        return self.append(
            "state",
            {
                "suspend": True,
                "reason": reason,
                "discovery_grant_ids": list(discovery_grant_ids),
                "policy_allowlist": None if policy_allowlist is None else list(policy_allowlist),
            },
        )

    def mark_hitl_resolved(self, approved: bool, user_id: str) -> JournalEntry:
        if approved:
            return self.append(
                "state",
                {"hitl_resolved": True, "user_id": user_id},
            )
        return self.append(
            "state",
            {"hitl_rejected": True, "user_id": user_id},
        )
