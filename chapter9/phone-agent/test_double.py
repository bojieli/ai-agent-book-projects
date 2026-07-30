"""Explicit, deterministic test double for Pine Voice; never used by default."""

from __future__ import annotations

import hashlib
from typing import Any


def make_phone_call(phone_number: str, goal: str, context: str = "", **_: Any) -> dict[str, Any]:
    confirmation = "TEST-" + hashlib.sha1(goal.encode()).hexdigest()[:8].upper()
    return {
        "provider": "test-double",
        "call_id": "test-call",
        "phone_number": phone_number,
        "goal": goal,
        "status": "completed",
        "duration_seconds": 0,
        "credits_charged": 0,
        "summary": "Deterministic test call completed; no telephone network was contacted.",
        "goal_achieved": True,
        "key_fields": {"confirmation_number": confirmation, "context": context},
        "transcript": [],
        "follow_up_needed": False,
        "follow_up_reason": "",
        "raw_provider_result": {},
    }
