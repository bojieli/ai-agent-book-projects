"""In-process scheduler — 合作式 cancel + journal 状态持久化。"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ORPHANED = "orphaned"


TERMINAL_STATUSES = frozenset(
    {
        TaskStatus.SUCCEEDED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.ORPHANED,
    }
)


class CancellationToken:
    """合作式取消令牌 — 不可强杀线程。"""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self.is_cancelled:
            raise TaskCancelledError()


class TaskCancelledError(Exception):
    pass


@dataclass
class ScheduledTask:
    task_id: str
    session_id: str
    kind: str
    owner_user_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    terminal: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""


TaskFn = Callable[[ScheduledTask, CancellationToken], dict[str, Any]]


class TaskJournalHook(Protocol):
    def on_task_state(self, session_id: str, payload: dict[str, Any]) -> None: ...


@dataclass
class InProcessScheduler:
    tasks: dict[str, ScheduledTask] = field(default_factory=dict)
    _tokens: dict[str, CancellationToken] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    journal_hook: TaskJournalHook | None = None

    def _emit_journal(self, task: ScheduledTask, payload: dict[str, Any]) -> None:
        if self.journal_hook:
            self.journal_hook.on_task_state(task.session_id, payload)

    def _set_status(self, task: ScheduledTask, status: TaskStatus, *, terminal: str = "") -> None:
        with self._lock:
            if task.status in TERMINAL_STATUSES:
                return
            task.status = status
            if terminal:
                task.terminal = terminal
            snap = {
                "task_id": task.task_id,
                "status": task.status.value,
                "terminal": task.terminal,
                "owner_user_id": task.owner_user_id,
            }
        self._emit_journal(task, snap)

    def _set_result(self, task: ScheduledTask, *, result: dict[str, Any] | None = None, error: str = "") -> None:
        with self._lock:
            if task.status in TERMINAL_STATUSES and result is not None:
                return
            if result is not None:
                task.result = result
            if error:
                task.error = error

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
        """从 journal 重建任务投影（新 scheduler 实例）。"""
        with self._lock:
            if task_id in self.tasks:
                return self.tasks[task_id]
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
            self.tasks[task_id] = task
            return task

    def submit(
        self,
        *,
        session_id: str,
        kind: str,
        fn: TaskFn,
        owner_user_id: str = "",
    ) -> ScheduledTask:
        tid = f"task_{uuid.uuid4().hex[:10]}"
        task = ScheduledTask(task_id=tid, session_id=session_id, kind=kind, owner_user_id=owner_user_id)
        token = CancellationToken()
        with self._lock:
            self.tasks[tid] = task
            self._tokens[tid] = token

        def _run() -> None:
            self._set_status(task, TaskStatus.RUNNING)
            try:
                if token.is_cancelled:
                    self._set_status(task, TaskStatus.CANCELLED, terminal="cancelled")
                    return
                out = fn(task, token)
                if token.is_cancelled:
                    self._set_status(task, TaskStatus.CANCELLED, terminal="cancelled")
                else:
                    self._set_result(task, result=out)
                    self._set_status(task, TaskStatus.SUCCEEDED, terminal="succeeded")
            except TaskCancelledError:
                self._set_status(task, TaskStatus.CANCELLED, terminal="cancelled")
            except Exception as exc:
                self._set_result(task, error=str(exc))
                self._set_status(task, TaskStatus.FAILED, terminal="failed")

        threading.Thread(target=_run, daemon=True).start()
        self._set_status(task, TaskStatus.PENDING)
        return task

    def status(self, task_id: str) -> ScheduledTask:
        with self._lock:
            t = self.tasks.get(task_id)
            if not t:
                raise KeyError(task_id)
            return ScheduledTask(
                task_id=t.task_id,
                session_id=t.session_id,
                kind=t.kind,
                owner_user_id=t.owner_user_id,
                status=t.status,
                terminal=t.terminal,
                result=dict(t.result),
                error=t.error,
            )

    def cancel(self, task_id: str) -> ScheduledTask:
        with self._lock:
            token = self._tokens.get(task_id)
            task = self.tasks.get(task_id)
            if not task:
                raise KeyError(task_id)
            if task.status in TERMINAL_STATUSES:
                return task
            if token:
                token.cancel()
            task.status = TaskStatus.CANCEL_REQUESTED
            snap = {"task_id": task_id, "status": "cancel_requested", "owner_user_id": task.owner_user_id}
        self._emit_journal(task, snap)
        return task

    def mark_orphaned_on_restart(self) -> int:
        count = 0
        to_orphan: list[ScheduledTask] = []
        with self._lock:
            for t in self.tasks.values():
                if t.status in {TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.CANCEL_REQUESTED}:
                    t.status = TaskStatus.ORPHANED
                    t.terminal = "needs_resume"
                    to_orphan.append(t)
                    count += 1
        for t in to_orphan:
            self._emit_journal(
                t,
                {
                    "task_id": t.task_id,
                    "status": TaskStatus.ORPHANED.value,
                    "terminal": "needs_resume",
                    "owner_user_id": t.owner_user_id,
                },
            )
        return count

    def get_token(self, task_id: str) -> CancellationToken | None:
        with self._lock:
            return self._tokens.get(task_id)
