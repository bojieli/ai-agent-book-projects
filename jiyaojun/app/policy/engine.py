"""Policy helpers: embed_gate max_strict, effect cap checks."""

from __future__ import annotations

from app.events.enums import EMBED_GATE_RANK, PRODUCTION_EFFECT_RANK


def max_strict_embed_gate(*gates: str) -> str:
    return max(gates, key=lambda g: EMBED_GATE_RANK[g])


def effect_allowed(actual: str, cap: str) -> bool:
    return PRODUCTION_EFFECT_RANK[actual] <= PRODUCTION_EFFECT_RANK[cap]


def policy_hooks_ok(
    *,
    classification: str,
    continuum_write_class: str,
    production_effect: str,
    production_effect_cap: str,
    embed_gate: str,
    maturity: str,
) -> list[str]:
    """Return list of failure codes (empty = pass)."""
    failures: list[str] = []
    if not effect_allowed(production_effect, production_effect_cap):
        failures.append("effect_exceeds_cap")
    if classification == "critical" and continuum_write_class not in {"sealed", "none"}:
        failures.append("critical_requires_sealed_or_none")
    if maturity == "L0" and embed_gate != "block":
        failures.append("l0_must_block")
    if maturity == "L0" and production_effect_cap != "none":
        failures.append("l0_cap_must_none")
    return failures
