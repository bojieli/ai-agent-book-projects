"""Connector catalog + lazy discovery（chapter4 active-tool-discovery）。"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from app.events.enums import PRODUCTION_EFFECT_RANK

_FORBIDDEN_DESC_PATTERNS = (
    r"ignore\s+previous",
    r"system\s*:",
    r"<\s*script",
    r"```",
    r"override\s+policy",
)


def sanitize_tool_description(text: str, *, max_len: int = 240) -> str:
    cleaned = (text or "").strip()[:max_len]
    for pat in _FORBIDDEN_DESC_PATTERNS:
        if re.search(pat, cleaned, re.I):
            raise ValueError(f"tool description failed sanitizer: pattern={pat}")
    return cleaned


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_tool_description(value, max_len=500)
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(v) for v in value]
    return value


def sanitize_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    """递归净化 MCP descriptor / schema 中所有字符串。"""
    return _sanitize_value(copy.deepcopy(descriptor))


@dataclass
class ConnectorCatalogEntry:
    connector_id: str
    summary: str
    org_domains: list[str]
    scenarios: list[str]
    production_effect: str
    schema_ref: str
    full_descriptor: dict[str, Any] | None = None

    def summary_dict(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "summary": self.summary,
            "org_domains": self.org_domains,
            "scenarios": self.scenarios,
            "production_effect": self.production_effect,
            "schema_ref": self.schema_ref,
        }


@dataclass
class RankedCandidate:
    entry: ConnectorCatalogEntry
    score: float
    reason: str


@dataclass
class DiscoveryGrant:
    granted_ids: list[str]
    ranked_summaries: list[dict[str, Any]]
    denied_reasons: dict[str, str] = field(default_factory=dict)
    grant_scores: dict[str, float] = field(default_factory=dict)
    grant_reasons: dict[str, str] = field(default_factory=dict)


class ConnectorCatalog:
    def __init__(self) -> None:
        self.entries: dict[str, ConnectorCatalogEntry] = {}

    def register(self, entry: ConnectorCatalogEntry) -> None:
        if entry.connector_id in self.entries:
            raise ValueError(f"duplicate connector: {entry.connector_id}")
        if entry.production_effect not in PRODUCTION_EFFECT_RANK:
            raise ValueError(f"unknown production_effect: {entry.production_effect}")
        entry.summary = sanitize_tool_description(entry.summary)
        if entry.full_descriptor:
            entry.full_descriptor = sanitize_descriptor(entry.full_descriptor)
        self.entries[entry.connector_id] = entry

    def register_from_connector(
        self, connector: Any, *, org_domains: list[str], scenarios: list[str]
    ) -> None:
        desc = sanitize_descriptor(connector.mcp_tool_descriptor())
        summary = sanitize_tool_description(desc.get("description", connector.id))
        self.register(
            ConnectorCatalogEntry(
                connector_id=connector.id,
                summary=summary,
                org_domains=org_domains,
                scenarios=scenarios,
                production_effect=connector.production_effect,
                schema_ref=f"schema://{connector.id}",
                full_descriptor=desc,
            )
        )

    def lazy_load_schema(self, connector_id: str) -> dict[str, Any]:
        entry = self.entries.get(connector_id)
        if not entry or not entry.full_descriptor:
            raise KeyError(f"schema not loaded for {connector_id}")
        return sanitize_descriptor(copy.deepcopy(entry.full_descriptor.get("inputSchema") or {}))


@dataclass
class ToolDiscoveryService:
    catalog: ConnectorCatalog
    ranker: Callable[[str, list[ConnectorCatalogEntry]], list[RankedCandidate]] | None = None
    min_score: float = 1.0

    def discover(
        self,
        *,
        need: str,
        org_domains: list[str],
        scenario: str,
        max_effect: str,
        tool_allowlist: list[str] | None = None,
        top_k: int = 3,
        scenario_default: bool = False,
    ) -> DiscoveryGrant:
        denied: dict[str, str] = {}
        candidates: list[ConnectorCatalogEntry] = []

        if tool_allowlist is not None and len(tool_allowlist) == 0:
            return DiscoveryGrant(granted_ids=[], ranked_summaries=[], denied_reasons={"*": "empty_allowlist"})

        for eid, ent in self.catalog.entries.items():
            if tool_allowlist is not None and eid not in tool_allowlist:
                denied[eid] = "not_in_policy_allowlist"
                continue
            if ent.production_effect not in PRODUCTION_EFFECT_RANK:
                denied[eid] = "unknown_effect_rank"
                continue
            if PRODUCTION_EFFECT_RANK[ent.production_effect] > PRODUCTION_EFFECT_RANK[max_effect]:
                denied[eid] = "effect_exceeds_cap"
                continue
            if not any(o in org_domains for o in ent.org_domains) and ent.org_domains != ["*"]:
                denied[eid] = "org_domain_mismatch"
                continue
            if scenario and ent.scenarios and scenario not in ent.scenarios and "*" not in ent.scenarios:
                denied[eid] = "scenario_mismatch"
                continue
            candidates.append(ent)

        ranked = self.ranker(need, candidates) if self.ranker else _lexical_rank(need, candidates)
        effective_min = 0.0 if scenario_default else self.min_score
        filtered = [r for r in ranked if r.score >= effective_min][:top_k]

        grant_scores = {r.entry.connector_id: r.score for r in filtered}
        grant_reasons = {r.entry.connector_id: r.reason for r in filtered}

        return DiscoveryGrant(
            granted_ids=[r.entry.connector_id for r in filtered],
            ranked_summaries=[
                {**r.entry.summary_dict(), "score": r.score, "reason": r.reason} for r in filtered
            ],
            denied_reasons=denied,
            grant_scores=grant_scores,
            grant_reasons=grant_reasons,
        )


def _lexical_rank(need: str, entries: list[ConnectorCatalogEntry]) -> list[RankedCandidate]:
    terms = set(re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", need.lower()))
    # 中文工具意图 → 英文 connector 别名
    zh_aliases = {
        "建缺陷": ["defect"],
        "建任务": ["task"],
        "缺陷": ["defect"],
        "任务": ["task"],
    }
    for zh, aliases in zh_aliases.items():
        if zh in need:
            terms.update(aliases)
    out: list[RankedCandidate] = []
    for ent in entries:
        id_parts = re.findall(r"[a-zA-Z0-9_]+", ent.connector_id.lower())
        blob = f"{ent.connector_id} {' '.join(id_parts)} {ent.summary}".lower()
        matched = [t for t in terms if t in blob]
        score = float(len(matched))
        reason = f"matched_terms={matched}" if matched else "no_term_match"
        out.append(RankedCandidate(entry=ent, score=score, reason=reason))
    return sorted(out, key=lambda r: r.score, reverse=True)
