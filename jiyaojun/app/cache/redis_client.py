"""Redis 缓存与会话投影 / 幂等键 — 连接失败明确报错。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import redis


class RedisConnectionError(ConnectionError):
    """Redis 连接或命令失败。"""


class RedisCache:
    """基础 JSON 缓存封装。"""

    def __init__(self, redis_url: str, **kwargs: Any) -> None:
        try:
            self._client = redis.Redis.from_url(redis_url, decode_responses=True, **kwargs)
            self._client.ping()
        except Exception as exc:
            raise RedisConnectionError(f"无法连接 Redis ({redis_url}): {exc}") from exc

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: dict[str, Any], ex: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        self._client.set(key, payload, ex=ex)

    def set_nx(self, key: str, value: str, ex: int | None = None) -> bool:
        """SET NX — 成功返回 True，键已存在返回 False。"""
        return bool(self._client.set(key, value, nx=True, ex=ex))

    def delete(self, key: str) -> None:
        self._client.delete(key)


class InMemoryJsonCache:
    """内存 JSON 缓存 — redis_backend=memory 时使用。"""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self._store.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: dict[str, Any], ex: int | None = None) -> None:
        self._store[key] = json.dumps(value, ensure_ascii=False)

    def set_nx(self, key: str, value: str, ex: int | None = None) -> bool:
        if key in self._store:
            return False
        self._store[key] = value
        return True

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class SessionProjectionCache:
    """会话投影缓存 — key: sess:{session_id}，存 active_leaf / owner / updated_at。"""

    def __init__(self, backend: RedisCache | InMemoryJsonCache) -> None:
        self._backend = backend

    def _key(self, session_id: str) -> str:
        return f"sess:{session_id}"

    def get(self, session_id: str) -> dict[str, Any] | None:
        return self._backend.get_json(self._key(session_id))

    def set(
        self,
        session_id: str,
        *,
        active_leaf: str | None,
        owner: str,
        updated_at: str | None = None,
    ) -> None:
        self._backend.set_json(
            self._key(session_id),
            {
                "active_leaf": active_leaf,
                "owner": owner,
                "updated_at": updated_at or datetime.now(timezone.utc).isoformat(),
            },
        )

    def delete(self, session_id: str) -> None:
        self._backend.delete(self._key(session_id))


class IdempotencyCache:
    """幂等键缓存 — key: idem:{key}，使用 set_nx 防重复。"""

    def __init__(self, backend: RedisCache | InMemoryJsonCache) -> None:
        self._backend = backend

    def _key(self, key: str) -> str:
        return f"idem:{key}"

    def try_acquire(self, key: str, value: str = "1", ex: int | None = 3600) -> bool:
        return self._backend.set_nx(self._key(key), value, ex=ex)

    def release(self, key: str) -> None:
        self._backend.delete(self._key(key))
