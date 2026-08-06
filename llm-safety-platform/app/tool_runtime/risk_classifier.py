"""ToolRiskClassifier — parameter-level dangerous operation recognition (ADR-019)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class ToolRiskRule:
    id: str
    tool_id: str
    field: str
    type: str  # domain_not_in_allowlist | url_is_ip_or_non_https | regex | always
    op_risk_tier: str = "medium"
    decision: str = "confirm_only"
    pattern: str = ""


@dataclass
class RiskAssessment:
    op_risk_tier: str
    decision: str
    reason_codes: list[str] = field(default_factory=list)
    matched_rules: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "op_risk_tier": self.op_risk_tier,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "matched_rules": list(self.matched_rules),
        }


_TIER_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_DEC_RANK = {
    "allow": 0,
    "alert_only": 1,
    "confirm_only": 2,
    "block": 3,
}


def _get_field(args: dict[str, Any], dotted: str) -> Any:
    cur: Any = args
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _domain(email_or_host: str) -> str:
    s = (email_or_host or "").strip().lower()
    if "@" in s:
        return s.split("@", 1)[1]
    return s


class ToolRiskClassifier:
    """Rule-first classifier; SPI-ready for ML adapters later."""

    def assess(
        self,
        tool_id: str,
        args: dict[str, Any],
        *,
        rules: tuple[ToolRiskRule, ...] | list[ToolRiskRule] = (),
        email_domain_allowlist: tuple[str, ...] | list[str] = (),
    ) -> RiskAssessment:
        best_tier = "low"
        best_decision = "allow"
        reasons: list[str] = []
        matched: list[str] = []

        for rule in rules:
            if rule.tool_id != tool_id and rule.tool_id != "*":
                continue
            hit, reason = self._match(rule, args, email_domain_allowlist)
            if not hit:
                continue
            matched.append(rule.id)
            reasons.append(reason)
            if _TIER_RANK[rule.op_risk_tier] > _TIER_RANK[best_tier]:
                best_tier = rule.op_risk_tier
            if _DEC_RANK[rule.decision] > _DEC_RANK[best_decision]:
                best_decision = rule.decision

        return RiskAssessment(
            op_risk_tier=best_tier,
            decision=best_decision,
            reason_codes=reasons,
            matched_rules=matched,
        )

    def _match(
        self,
        rule: ToolRiskRule,
        args: dict[str, Any],
        email_domain_allowlist: tuple[str, ...] | list[str],
    ) -> tuple[bool, str]:
        if rule.type == "always":
            return True, f"rule:{rule.id}:always"

        value = _get_field(args, rule.field)
        if value is None:
            return False, ""

        if rule.type == "domain_not_in_allowlist":
            dom = _domain(str(value))
            allow = {d.lower() for d in email_domain_allowlist}
            if allow and dom not in allow:
                return True, f"rule:{rule.id}:domain_not_allowed:{dom}"
            return False, ""

        if rule.type == "url_is_ip_or_non_https":
            raw = str(value)
            try:
                u = urlparse(raw if "://" in raw else "http://" + raw)
            except Exception:  # noqa: BLE001
                return True, f"rule:{rule.id}:bad_url"
            host = (u.hostname or "").lower()
            if u.scheme and u.scheme != "https":
                return True, f"rule:{rule.id}:non_https"
            if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host or ""):
                return True, f"rule:{rule.id}:ip_host"
            return False, ""

        if rule.type == "regex":
            if rule.pattern and re.search(rule.pattern, str(value), re.I):
                return True, f"rule:{rule.id}:regex"
            return False, ""

        return False, ""
