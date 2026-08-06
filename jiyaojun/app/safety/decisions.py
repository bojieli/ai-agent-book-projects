"""五态安全判决与更严格归约（与安全控制面 ADR-004 对齐）。"""

from __future__ import annotations

from typing import Iterable

# 五态：allow / alert_only / redact / confirm_only / block
DECISIONS = ("allow", "alert_only", "redact", "confirm_only", "block")

# 数值越大越严格
_RANK = {
    "allow": 0,
    "alert_only": 1,
    "redact": 2,
    "confirm_only": 3,
    "block": 4,
}


def max_strict(decisions: Iterable[str]) -> str:
    """取更严格结果；未知决策视为 block（fail-closed）。"""
    best = "allow"
    for d in decisions:
        if d not in _RANK:
            return "block"
        if _RANK[d] > _RANK[best]:
            best = d
    return best


def is_executable(decision: str) -> bool:
    """仅 allow / alert_only / redact 可继续本地副作用；confirm/block 不可。"""
    return decision in ("allow", "alert_only", "redact")
