"""Unified safety decision enum + max_strict reduction (ADR-004)."""

from __future__ import annotations

from typing import Iterable

DECISIONS = ("allow", "redact", "block", "confirm_only", "alert_only")

# Higher rank = stricter
_RANK = {
    "allow": 0,
    "alert_only": 1,
    "redact": 2,
    "confirm_only": 3,
    "block": 4,
}


def max_strict(decisions: Iterable[str]) -> str:
    best = "allow"
    for d in decisions:
        if d not in _RANK:
            raise ValueError(f"unknown decision: {d}")
        if _RANK[d] > _RANK[best]:
            best = d
    return best


def assert_decision(d: str) -> str:
    if d not in _RANK:
        raise ValueError(f"unknown decision: {d}")
    return d
