"""Celery 调度器任务状态 — Redis JSON 投影。"""

from __future__ import annotations

import json
from typing import Any

from app.cache.redis_client import InMemoryJsonCache, RedisCache
from app.scheduler.tasks import ScheduledTask, TaskStatus


class CeleryTaskStateStore:
    """任务状态缓存 — ctask:{task_id}、idem_task:{idempotency_key}。"""

    def __init__(self, backend: RedisCache | InMemoryJsonCache) -> None:
        self._backend = backend

    def _task_key(self, task_id: str) -> str:
        return f"ctask:{task_id}"

    def _idem_key(self, idempotency_key: str) -> str:
        return f"idem_task:{idempotency_key}"

    def save_task(self, task: ScheduledTask, **extra: Any) -> None:
        """写入或更新任务快照。"""
        payload: dict[str, Any] = {
            "task_id": task.task_id,
            "session_id": task.session_id,
            "kind": task.kind,
            "owner_user_id": task.owner_user_id,
            "status": task.status.value,
            "terminal": task.terminal,
            "result": dict(task.result),
            "error": task.error,
        }
        payload.update(extra)
        self._backend.set_json(self._task_key(task.task_id), payload)

    def load_task(self, task_id: str) -> dict[str, Any] | None:
        return self._backend.get_json(self._task_key(task_id))

    def map_idempotency(self, idempotency_key: str, task_id: str) -> None:
        """记录幂等键到 task_id 的映射。"""
        self._backend.set_json(
            self._idem_key(idempotency_key),
            {"task_id": task_id, "idempotency_key": idempotency_key},
        )

    def task_id_for_idempotency(self, idempotency_key: str) -> str | None:
        raw = self._backend.get_json(self._idem_key(idempotency_key))
        if not raw:
            return None
        return str(raw.get("task_id") or "")

    def to_scheduled_task(self, data: dict[str, Any]) -> ScheduledTask:
        try:
            status = TaskStatus(str(data.get("status") or TaskStatus.PENDING.value))
        except ValueError:
            status = TaskStatus.ORPHANED
        result = data.get("result") or {}
        if isinstance(result, str):
            result = json.loads(result)
        return ScheduledTask(
            task_id=str(data["task_id"]),
            session_id=str(data.get("session_id") or ""),
            kind=str(data.get("kind") or "pipeline"),
            owner_user_id=str(data.get("owner_user_id") or ""),
            status=status,
            terminal=str(data.get("terminal") or ""),
            result=dict(result),
            error=str(data.get("error") or ""),
        )

    def list_all_tasks(self) -> list[dict[str, Any]]:
        """列出内存后端全部任务；Redis 后端仅用于测试 eager 模式。"""
        store = getattr(self._backend, "_store", None)
        if not isinstance(store, dict):
            return []
        out: list[dict[str, Any]] = []
        for key, raw in store.items():
            if not key.startswith("ctask:"):
                continue
            out.append(json.loads(raw))
        return out
