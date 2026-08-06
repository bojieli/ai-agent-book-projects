"""Rate limit + PII/sensitive redaction (Phase 4)."""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Simple token bucket per user — Dialog peak guard."""

    max_per_window: int = 20
    window_sec: float = 10.0
    _hits: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def allow(self, user_id: str) -> bool:
        now = time.time()
        q = self._hits[user_id]
        self._hits[user_id] = [t for t in q if now - t < self.window_sec]
        if len(self._hits[user_id]) >= self.max_per_window:
            return False
        self._hits[user_id].append(now)
        return True


_PHONE = re.compile(r"1\d{10}")
_ID = re.compile(r"\b\d{17}[\dXx]\b")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def redact_text(text: str) -> str:
    text = _PHONE.sub("[PHONE]", text)
    text = _ID.sub("[ID]", text)
    text = _EMAIL.sub("[EMAIL]", text)
    return text


def redact_artifact(artifact: dict) -> dict:
    import copy

    a = copy.deepcopy(artifact)
    payload = a.get("payload")
    if isinstance(payload, dict):
        for k, v in list(payload.items()):
            if isinstance(v, str):
                payload[k] = redact_text(v)
            elif isinstance(v, list):
                payload[k] = [
                    {**it, **({kk: redact_text(vv) for kk, vv in it.items() if isinstance(vv, str)})}
                    if isinstance(it, dict)
                    else it
                    for it in v
                ]
    for span in a.get("source_spans") or []:
        if "quote" in span and isinstance(span["quote"], str):
            span["quote"] = redact_text(span["quote"])
    return a
