"""Celery 调度器 — 与 InProcessScheduler 相近的 submit/status/cancel API。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from celery.result import AsyncResult

from app.config import InfrastructureSettings
from app.runtime.factory import build_task_state_store
from app.scheduler.celery_tasks import run_pipeline_job
from app.scheduler.task_state import CeleryTaskStateStore
from app.scheduler.tasks import (
    TERMINAL_STATUSES,
    ScheduledTask,
    TaskFn,
    TaskJournalHook,
    TaskStatus,
)


@dataclass
class CeleryScheduler:
    """将长流水线提交到 Celery Worker；状态写入 Redis / 任务投影。"""

    settings: InfrastructureSettings
    journal_hook: TaskJournalHook | None = None
    tasks: dict[str, ScheduledTask] = field(default_factory=dict)
    _state_store: CeleryTaskStateStore | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._state_store = build_task_state_store(self.settings)

    def _store(self) -> CeleryTaskStateStore:
        assert self._state_store is not None
        return self._state_store

    def _emit_journal(self, task: ScheduledTask, payload: dict[str, Any]) -> None:
        if self.journal_hook:
            self.journal_hook.on_task_state(task.session_id, payload)

    def _cache_task(self, task: ScheduledTask, **extra: Any) -> None:
        self.tasks[task.task_id] = task
        self._store().save_task(task, **extra)

    def _set_status(
        self,
        task: ScheduledTask,
        status: TaskStatus,
        *,
        terminal: str = "",
        idempotency_key: str = "",
    ) -> None:
        if task.status in TERMINAL_STATUSES:
            return
        task.status = status
        if terminal:
            task.terminal = terminal
        self._cache_task(task, idempotency_key=idempotency_key)
        self._emit_journal(
            task,
            {
                "task_id": task.task_id,
                "status": task.status.value,
                "terminal": task.terminal,
                "owner_user_id": task.owner_user_id,
                "kind": task.kind,
                **({"idempotency_key": idempotency_key} if idempotency_key else {}),
            },
        )

    def register_projection(
        self,
        *,
        task_id: str,
        session_id: str,
        owner_user_id: str,
        kind: str,
        status: str,
        terminal: str = "",
    ) -> ScheduledTask:
        """从 journal / 投影恢复任务（Worker 或 API 进程重启后）。"""
        if task_id in self.tasks:
            return self.tasks[task_id]
        cached = self._store().load_task(task_id)
        if cached:
            task = self._store().to_scheduled_task(cached)
            self.tasks[task_id] = task
            return task
        try:
            st = TaskStatus(status)
        except ValueError:
            st = TaskStatus.ORPHANED
        task = ScheduledTask(
            task_id=task_id,
            session_id=session_id,
            kind=kind,
            owner_user_id=owner_user_id,
            status=st,
            terminal=terminal,
        )
        self._cache_task(task)
        return task

    def submit(
        self,
        *,
        session_id: str,
        kind: str,
        fn: TaskFn | None = None,
        owner_user_id: str = "",
        meeting_id: str = "",
        idempotency_key: str = "",
    ) -> ScheduledTask:
        """提交 Celery 长任务；fn 在 Worker 模式不序列化，仅用于测试钩子占位。"""
        if fn is not None:
            raise TypeError(
                "CeleryScheduler 不支持进程内 fn；请使用 meeting_id/session_id/idempotency_key"
            )

        store = self._store()
        idem = idempotency_key or f"idem_{session_id}_{kind}"
        existing_id = store.task_id_for_idempotency(idem)
        if existing_id:
            cached = store.load_task(existing_id)
            if cached:
                task = store.to_scheduled_task(cached)
                self.tasks[task.task_id] = task
                return task

        tid = f"task_{uuid.uuid4().hex[:10]}"
        task = ScheduledTask(
            task_id=tid,
            session_id=session_id,
            kind=kind,
            owner_user_id=owner_user_id,
            status=TaskStatus.PENDING,
        )
        store.map_idempotency(idem, tid)
        self._set_status(task, TaskStatus.PENDING, idempotency_key=idem)

        async_result = run_pipeline_job.apply_async(
            kwargs={
                "task_id": tid,
                "meeting_id": meeting_id or session_id,
                "session_id": session_id,
                "idempotency_key": idem,
                "owner_user_id": owner_user_id,
                "kind": kind,
            },
        )
        self._cache_task(task, celery_id=async_result.id, idempotency_key=idem)
        return task

    def _refresh_from_celery(self, task: ScheduledTask) -> ScheduledTask:
        """从 Celery AsyncResult 同步终态（result backend）。"""
        if task.status in TERMINAL_STATUSES:
            return task
        cached = self._store().load_task(task.task_id) or {}
        celery_id = str(cached.get("celery_id") or task.task_id)
        ar = AsyncResult(celery_id, app=run_pipeline_job.app)
        if ar.successful():
            task.status = TaskStatus.SUCCEEDED
            task.terminal = "succeeded"
            task.result = ar.result if isinstance(ar.result, dict) else {"value": ar.result}
            self._cache_task(task)
        elif ar.failed():
            task.status = TaskStatus.FAILED
            task.terminal = "failed"
            task.error = str(ar.result)
            self._cache_task(task)
        elif ar.state == "REVOKED":
            task.status = TaskStatus.CANCELLED
            task.terminal = "cancelled"
            self._cache_task(task)
        return task

    def status(self, task_id: str) -> ScheduledTask:
        cached = self._store().load_task(task_id)
        if cached:
            task = self._store().to_scheduled_task(cached)
            self.tasks[task_id] = task
            return self._refresh_from_celery(task)
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError(task_id)
        return self._refresh_from_celery(
            ScheduledTask(
                task_id=task.task_id,
                session_id=task.session_id,
                kind=task.kind,
                owner_user_id=task.owner_user_id,
                status=task.status,
                terminal=task.terminal,
                result=dict(task.result),
                error=task.error,
            )
        )

    def cancel(self, task_id: str) -> ScheduledTask:
        """软撤销 Celery 任务（revoke soft，不强杀 Worker 进程）。"""
        task = self.status(task_id)
        if task.status in TERMINAL_STATUSES:
            return task
        run_pipeline_job.app.control.revoke(task_id, terminate=False)
        task.status = TaskStatus.CANCEL_REQUESTED
        self._cache_task(task)
        self._emit_journal(
            task,
            {
                "task_id": task_id,
                "status": TaskStatus.CANCEL_REQUESTED.value,
                "owner_user_id": task.owner_user_id,
                "kind": task.kind,
            },
        )
        return task

    def mark_orphaned_on_restart(self) -> int:
        """进程/Worker 重启后，将未终态任务标为 orphaned/needs_resume。"""
        count = 0
        seen: set[str] = set(self.tasks)
        for row in self._store().list_all_tasks():
            seen.add(str(row.get("task_id")))
        for tid in seen:
            try:
                task = self.status(tid)
            except KeyError:
                continue
            if task.status in {
                TaskStatus.PENDING,
                TaskStatus.RUNNING,
                TaskStatus.CANCEL_REQUESTED,
            }:
                task.status = TaskStatus.ORPHANED
                task.terminal = "needs_resume"
                self._cache_task(task)
                self._emit_journal(
                    task,
                    {
                        "task_id": tid,
                        "status": TaskStatus.ORPHANED.value,
                        "terminal": "needs_resume",
                        "owner_user_id": task.owner_user_id,
                        "kind": task.kind,
                    },
                )
                count += 1
        return count

    def get_token(self, task_id: str) -> None:
        """Celery 模式无合作式 token；取消请用 cancel()。"""
        return None
