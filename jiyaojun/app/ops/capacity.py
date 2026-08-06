"""Capacity / night window policy (04) — mock enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time


@dataclass
class CapacityPolicy:
    """8000 users + 30% buffer design numbers — enforce night rules in mock."""

    day_start: time = time(9, 0)
    day_end: time = time(23, 0)
    night_agentic_ratio: float = 0.3
    allow_enqueue_at_night: bool = True
    allow_big_reindex_at_night: bool = False


def is_night(now: datetime, policy: CapacityPolicy | None = None) -> bool:
    policy = policy or CapacityPolicy()
    t = now.time()
    return not (policy.day_start <= t < policy.day_end)


def allow_agentic_retrieve(now: datetime, current_ratio: float, policy: CapacityPolicy | None = None) -> bool:
    policy = policy or CapacityPolicy()
    if not is_night(now, policy):
        return True
    return current_ratio <= policy.night_agentic_ratio


def allow_reindex(now: datetime, policy: CapacityPolicy | None = None) -> bool:
    policy = policy or CapacityPolicy()
    if is_night(now, policy):
        return policy.allow_big_reindex_at_night
    return True
