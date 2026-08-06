"""Glossary governance — draft → approve (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.governance.state import GovernanceStatus
from app.knowledge.glossary import GlossaryEntry, GlossaryStore


@dataclass
class GlossaryAdmin:
    store: GlossaryStore = field(default_factory=GlossaryStore)
    pending: list[GlossaryEntry] = field(default_factory=list)

    def submit(self, entry: GlossaryEntry) -> GlossaryEntry:
        e = GlossaryEntry(entry.org_domain, entry.term, entry.gloss, "draft")
        self.pending.append(e)
        return e

    def approve(self, org_domain: str, term: str, approver: str) -> GlossaryEntry:
        for i, e in enumerate(self.pending):
            if e.org_domain == org_domain and e.term == term:
                approved = GlossaryEntry(org_domain, term, e.gloss, "approved")
                self.pending.pop(i)
                self.store._entries.append(approved)
                return approved
        raise KeyError(f"{org_domain}/{term}")
