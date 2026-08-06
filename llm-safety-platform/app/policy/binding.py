"""Versioned policy_binding — never rewrite history (ADR-005 / ADR-019)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.tool_runtime.risk_classifier import ToolRiskRule

VALID_TIERS = ("low", "medium", "high", "critical")
VALID_FAIL = ("fail_closed", "fail_open")
VALID_EFFECT = ("none", "draft_only", "observe", "production")

EFFECT_RANK = {
    "none": 0,
    "draft_only": 1,
    "observe": 2,
    "production": 3,
}


@dataclass(frozen=True)
class ScannerSpec:
    id: str
    threshold: float = 0.5
    max_tokens: int | None = None
    topics: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()  # content_safety: sexual|violence|political|self_harm


@dataclass(frozen=True)
class PolicyBinding:
    policy_binding_id: str
    tenant_id: str
    app_id: str
    version: int
    reason: str
    risk_tier: str
    fail_mode: str
    effect_cap: str
    tool_allowlist: tuple[str, ...] = ()
    tool_denylist: tuple[str, ...] = ()
    model_allowlist: tuple[str, ...] = ()
    email_domain_allowlist: tuple[str, ...] = ()
    tool_risk_rules: tuple[ToolRiskRule, ...] = ()
    input_scanners: tuple[ScannerSpec, ...] = ()
    output_scanners: tuple[ScannerSpec, ...] = ()
    retention: str = "hash_only"
    require_dual_publish: bool = False
    # OWASP supply chain / grounding / system integrity
    scanner_bundle_id: str = "bundle_shim_v1"
    model_digests: tuple[str, ...] = ()
    system_prompt_hash: str = ""
    grounding_required: bool = False
    daily_token_budget: int = 0  # 0 = unlimited
    max_concurrency: int = 0  # 0 = unlimited

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


class PolicyStore:
    def __init__(self) -> None:
        self._by_app: dict[tuple[str, str], list[PolicyBinding]] = {}

    def create_initial(self, binding: PolicyBinding) -> PolicyBinding:
        if binding.version != 1 or binding.reason != "initial":
            raise ValueError("initial binding must be version=1 reason=initial")
        self._validate(binding)
        key = (binding.tenant_id, binding.app_id)
        if key in self._by_app and self._by_app[key]:
            raise ValueError("initial already exists")
        self._by_app.setdefault(key, []).append(binding)
        return binding

    def append_version(self, binding: PolicyBinding) -> PolicyBinding:
        self._validate(binding)
        key = (binding.tenant_id, binding.app_id)
        hist = self._by_app.setdefault(key, [])
        if not hist:
            raise ValueError("no initial binding")
        if binding.version != hist[-1].version + 1:
            raise ValueError("version must monotonically increase")
        prev = hist[-1]
        if VALID_TIERS.index(binding.risk_tier) < VALID_TIERS.index(prev.risk_tier):
            raise ValueError("cannot loosen risk_tier")
        if EFFECT_RANK[binding.effect_cap] > EFFECT_RANK[prev.effect_cap]:
            raise ValueError("cannot raise effect_cap")
        # allowlist only shrink; denylist only grow (ADR-019)
        if not set(binding.tool_allowlist).issubset(set(prev.tool_allowlist)):
            raise ValueError("cannot expand tool_allowlist")
        if not set(prev.tool_denylist).issubset(set(binding.tool_denylist)):
            raise ValueError("cannot shrink tool_denylist")
        hist.append(binding)
        return binding

    def current(self, tenant_id: str, app_id: str) -> PolicyBinding | None:
        hist = self._by_app.get((tenant_id, app_id)) or []
        return hist[-1] if hist else None

    def history(self, tenant_id: str, app_id: str) -> list[PolicyBinding]:
        return list(self._by_app.get((tenant_id, app_id)) or [])

    def _validate(self, b: PolicyBinding) -> None:
        if b.risk_tier not in VALID_TIERS:
            raise ValueError(f"bad risk_tier: {b.risk_tier}")
        if b.fail_mode not in VALID_FAIL:
            raise ValueError(f"bad fail_mode: {b.fail_mode}")
        if b.effect_cap not in VALID_EFFECT:
            raise ValueError(f"bad effect_cap: {b.effect_cap}")
        if b.risk_tier in ("high", "critical") and b.fail_mode != "fail_closed":
            raise ValueError("high/critical must fail_closed")
        overlap = set(b.tool_allowlist) & set(b.tool_denylist)
        if overlap:
            raise ValueError(f"tool in both allow and deny: {overlap}")
