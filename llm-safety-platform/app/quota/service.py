"""Rate limit + token budget + concurrency (Redis or in-memory)."""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from threading import Lock
from typing import Iterator

from app.config import settings

try:
    import redis  # type: ignore
except Exception:  # noqa: BLE001
    redis = None


class QuotaService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._daily: dict[str, tuple[str, int]] = {}  # key -> (yyyymmdd, tokens)
        self._inflight: dict[str, int] = defaultdict(int)
        self._redis = None
        if settings.redis_url and redis is not None:
            try:
                self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:  # noqa: BLE001
                self._redis = None

    def check_rpm(self, key: str, limit: int) -> bool:
        now = time.time()
        window = 60.0
        if self._redis is not None:
            rk = f"rpm:{key}"
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(rk, 0, now - window)
            pipe.zadd(rk, {str(now): now})
            pipe.zcard(rk)
            pipe.expire(rk, 120)
            _, _, count, _ = pipe.execute()
            return int(count) <= limit
        with self._lock:
            arr = [t for t in self._hits[key] if now - t < window]
            arr.append(now)
            self._hits[key] = arr
            return len(arr) <= limit

    def check_daily_tokens(self, key: str, add_tokens: int, daily_budget: int) -> bool:
        """LLM10 — daily token budget. daily_budget<=0 means unlimited."""
        if daily_budget <= 0:
            return True
        day = time.strftime("%Y%m%d", time.gmtime())
        if self._redis is not None:
            rk = f"daily:{key}:{day}"
            nxt = int(self._redis.incrby(rk, add_tokens))
            self._redis.expire(rk, 86400 * 2)
            if nxt > daily_budget:
                self._redis.incrby(rk, -add_tokens)
                return False
            return True
        with self._lock:
            d, used = self._daily.get(key, (day, 0))
            if d != day:
                used = 0
            if used + add_tokens > daily_budget:
                return False
            self._daily[key] = (day, used + add_tokens)
            return True

    def add_spend(self, spent: int, budget: int, current: int) -> tuple[bool, int]:
        nxt = current + spent
        return nxt <= budget, nxt

    @contextmanager
    def concurrency_slot(self, key: str, max_concurrency: int) -> Iterator[bool]:
        """LLM10 — max in-flight requests per key. max_concurrency<=0 unlimited."""
        if max_concurrency <= 0:
            yield True
            return
        acquired = False
        with self._lock:
            if self._inflight[key] >= max_concurrency:
                yield False
                return
            self._inflight[key] += 1
            acquired = True
        try:
            yield True
        finally:
            if acquired:
                with self._lock:
                    self._inflight[key] = max(0, self._inflight[key] - 1)
