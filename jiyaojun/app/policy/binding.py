"""Policy binding versioning (never rewrite old versions)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PolicyBinding:
    policy_binding_id: str
    meeting_id: str
    version: int
    reason: str
    embed_gate: str
    classification: str
    continuum_write_class: str
    production_effect_cap: str
    delivery_scope: str = "participants_min"
    tool_allowlist: list[str] = field(default_factory=list)
    glossary_scopes: list[str] = field(default_factory=list)


class PolicyStore:
    def __init__(self) -> None:
        self._by_meeting: dict[str, list[PolicyBinding]] = {}

    def create_initial(self, binding: PolicyBinding) -> PolicyBinding:
        assert binding.version == 1 and binding.reason == "initial"
        self._by_meeting.setdefault(binding.meeting_id, []).append(binding)
        return binding

    def append_version(self, binding: PolicyBinding) -> PolicyBinding:
        hist = self._by_meeting.setdefault(binding.meeting_id, [])
        if hist and binding.version != hist[-1].version + 1:
            raise ValueError("version must monotonically increase")
        # immutability: never mutate previous
        hist.append(binding)
        return binding

    def current(self, meeting_id: str) -> PolicyBinding | None:
        hist = self._by_meeting.get(meeting_id) or []
        return hist[-1] if hist else None

    def history(self, meeting_id: str) -> list[PolicyBinding]:
        return list(self._by_meeting.get(meeting_id) or [])
