"""Ambiguity adjudication (03 §2.10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AmbiguityRecord:
    ambiguity_record_id: str
    meeting_id: str
    term: str
    candidate_senses: list[dict[str, str]]
    status: str = "open"  # open|resolved|escalated|expired
    resolved_sense: str | None = None
    resolver_user_id: str | None = None
    effect_on_embed_gate: str = "confirm_only"

    @property
    def blocks_fake_agree(self) -> bool:
        return self.status == "open"


class AmbiguityService:
    def __init__(self) -> None:
        self.records: dict[str, AmbiguityRecord] = {}

    def open(
        self,
        meeting_id: str,
        term: str,
        senses: list[dict[str, str]],
    ) -> AmbiguityRecord:
        rid = f"amb_{meeting_id}_{term}"
        rec = AmbiguityRecord(
            ambiguity_record_id=rid,
            meeting_id=meeting_id,
            term=term,
            candidate_senses=senses,
            status="open",
            effect_on_embed_gate="block",
        )
        self.records[rid] = rec
        return rec

    def resolve(self, rid: str, sense: str, user_id: str) -> AmbiguityRecord:
        rec = self.records[rid]
        rec.status = "resolved"
        rec.resolved_sense = sense
        rec.resolver_user_id = user_id
        return rec
