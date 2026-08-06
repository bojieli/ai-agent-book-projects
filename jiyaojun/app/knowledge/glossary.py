"""Domain glossary — isolation required (eng must not use HR gloss)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlossaryEntry:
    org_domain: str
    term: str
    gloss: str
    governance_status: str = "approved"


DEFAULT_GLOSSARY: list[GlossaryEntry] = [
    GlossaryEntry("eng", "灰度", "发布 canary / 流量灰度"),
    GlossaryEntry("business", "灰度", "客群名单试点 / 客群灰度"),
    GlossaryEntry("hr", "校准", "绩效等级校准会议"),
    GlossaryEntry("risk", "Shadow", "策略旁路观察，不改变生产决策"),
    GlossaryEntry("compliance", "整改项", "检查发现问题的闭环台账条目"),
]


class GlossaryStore:
    def __init__(self, entries: list[GlossaryEntry] | None = None) -> None:
        self._entries = entries or list(DEFAULT_GLOSSARY)

    def lookup(self, term: str, scopes: list[str]) -> list[GlossaryEntry]:
        return [e for e in self._entries if e.term == term and e.org_domain in scopes]

    def isolation_violation(self, term: str, allowed_scopes: list[str], used_domain: str) -> bool:
        """True if used_domain gloss injected outside allowed scopes."""
        if used_domain not in allowed_scopes:
            return True
        return False
