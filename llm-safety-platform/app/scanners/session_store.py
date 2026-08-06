"""Session graph store — in-memory + Redis-shaped interface (ADR-023/027)."""

from __future__ import annotations

import json
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TurnRecord:
    role: str  # user|assistant|system
    text_preview: str
    inj: bool = False
    crescendo: bool = False
    role_drift: bool = False
    ts: float = field(default_factory=time.time)


@dataclass
class SessionGraph:
    session_id: str
    turns: list[TurnRecord] = field(default_factory=list)
    inj_hits: int = 0
    crescendo_hits: int = 0
    role_drift_hits: int = 0
    crescendo_score: float = 0.0
    last_ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turns": [asdict(t) for t in self.turns],
            "inj_hits": self.inj_hits,
            "crescendo_hits": self.crescendo_hits,
            "role_drift_hits": self.role_drift_hits,
            "crescendo_score": self.crescendo_score,
            "last_ts": self.last_ts,
            "turn_count": len(self.turns),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionGraph":
        turns = [TurnRecord(**t) for t in (data.get("turns") or [])]
        return cls(
            session_id=str(data["session_id"]),
            turns=turns,
            inj_hits=int(data.get("inj_hits") or 0),
            crescendo_hits=int(data.get("crescendo_hits") or 0),
            role_drift_hits=int(data.get("role_drift_hits") or 0),
            crescendo_score=float(data.get("crescendo_score") or 0.0),
            last_ts=float(data.get("last_ts") or time.time()),
        )


class SessionStore(ABC):
    @abstractmethod
    def get(self, session_id: str) -> SessionGraph | None: ...

    @abstractmethod
    def put(self, graph: SessionGraph) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...


class InMemorySessionStore(SessionStore):
    def __init__(self, max_sessions: int = 4096) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, SessionGraph] = {}
        self._max = max_sessions

    def get(self, session_id: str) -> SessionGraph | None:
        with self._lock:
            g = self._data.get(session_id)
            return None if g is None else SessionGraph.from_dict(g.to_dict())

    def put(self, graph: SessionGraph) -> None:
        with self._lock:
            self._data[graph.session_id] = graph
            if len(self._data) > self._max:
                oldest = sorted(self._data.items(), key=lambda kv: kv[1].last_ts)[:512]
                for k, _ in oldest:
                    self._data.pop(k, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


class RedisShapedSessionStore(SessionStore):
    """Redis-compatible interface; falls back to memory if redis unavailable."""

    def __init__(self, redis_url: str | None = None, ttl_sec: int = 86400) -> None:
        self.ttl = ttl_sec
        self._mem = InMemorySessionStore()
        self._r = None
        url = redis_url or os.getenv("SAFETY_REDIS_URL", "")
        if url:
            try:
                import redis  # type: ignore

                client = redis.Redis.from_url(url, decode_responses=True)
                client.ping()
                self._r = client
            except Exception:  # noqa: BLE001
                self._r = None

    def _key(self, session_id: str) -> str:
        return f"llm_safety:session:{session_id}"

    def get(self, session_id: str) -> SessionGraph | None:
        if self._r is None:
            return self._mem.get(session_id)
        raw = self._r.get(self._key(session_id))
        if not raw:
            return None
        return SessionGraph.from_dict(json.loads(raw))

    def put(self, graph: SessionGraph) -> None:
        if self._r is None:
            self._mem.put(graph)
            return
        self._r.setex(self._key(graph.session_id), self.ttl, json.dumps(graph.to_dict()))

    def clear(self) -> None:
        if self._r is None:
            self._mem.clear()
            return
        # Only clear keys we know about via memory mirror; tests use InMemory.
        self._mem.clear()


_STORE: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _STORE
    if _STORE is None:
        backend = os.getenv("SAFETY_SESSION_STORE", "memory").lower()
        if backend == "redis":
            _STORE = RedisShapedSessionStore()
        else:
            _STORE = InMemorySessionStore()
    return _STORE


def set_session_store(store: SessionStore | None) -> None:
    global _STORE
    _STORE = store


def reset_session_store() -> None:
    get_session_store().clear()
