"""Celery 长流水线任务 — 幂等防重复写回 + 任务投影。"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from app.config import InfrastructureSettings, settings as default_settings
from app.runtime.factory import (
    build_idempotency_cache,
    build_task_projection_store,
    build_task_state_store,
)
from app.scheduler.celery_app import celery_app
from app.scheduler.task_state import CeleryTaskStateStore
from app.scheduler.tasks import ScheduledTask, TaskStatus

logger = logging.getLogger(__name__)


def _run_pipeline_stub(
    *,
    meeting_id: str,
    session_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """占位流水线 — 无项目 root 的快速路径或测试 monkeypatch。"""
    time.sleep(0.05)
    return {
        "meeting_id": meeting_id,
        "session_id": session_id,
        "idempotency_key": idempotency_key,
        "terminal": "succeeded",
    }


def _run_pipeline_orchestrator(
    *,
    meeting_id: str,
    session_id: str,
    idempotency_key: str,
    scenario_code: str = "tech_review",
) -> dict[str, Any]:
    """调用真实 Orchestrator.bind_and_run；失败则抛异常供 Celery 标 failed。"""
    root = Path(__file__).resolve().parents[2]
    orch_dir = root / "app" / "orchestrator"
    if not orch_dir.is_dir():
        logger.warning("未找到 Orchestrator 目录，回退 stub: %s", orch_dir)
        return _run_pipeline_stub(
            meeting_id=meeting_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
        )
    from app.orchestrator import Orchestrator

    orch = Orchestrator(root, allow_draft_skills=True)
    out = orch.bind_and_run(
        scenario_code=scenario_code,
        meeting_id=meeting_id,
        hitl_passed=True,
        series_id=os.getenv("JIYAOJUN_CELERY_SERIES_ID") or None,
    )
    terminal = (out.get("pipeline") or {}).get("terminal")
    if terminal != "succeeded":
        raise RuntimeError(f"orchestrator terminal={terminal}")
    out["session_id"] = session_id
    out["idempotency_key"] = idempotency_key
    out["terminal"] = terminal
    return out


def _run_pipeline_body(
    *,
    meeting_id: str,
    session_id: str,
    idempotency_key: str,
    scenario_code: str = "tech_review",
) -> dict[str, Any]:
    """默认走真实 Orchestrator；JIYAOJUN_CELERY_PIPELINE=stub 可切换占位逻辑。"""
    mode = (
        os.getenv("JIYAOJUN_CELERY_PIPELINE", default_settings.celery_pipeline)
        .strip()
        .lower()
    )
    if mode == "stub":
        return _run_pipeline_stub(
            meeting_id=meeting_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
        )
    if mode != "orchestrator":
        raise ValueError(f"unknown JIYAOJUN_CELERY_PIPELINE: {mode}")
    return _run_pipeline_orchestrator(
        meeting_id=meeting_id,
        session_id=session_id,
        idempotency_key=idempotency_key,
        scenario_code=scenario_code,
    )


def _load_task(
    store: CeleryTaskStateStore,
    task_id: str,
    *,
    session_id: str,
    kind: str,
    owner_user_id: str,
) -> ScheduledTask:
    data = store.load_task(task_id)
    if data:
        return store.to_scheduled_task(data)
    return ScheduledTask(
        task_id=task_id,
        session_id=session_id,
        kind=kind,
        owner_user_id=owner_user_id,
    )


def _persist_projection(
    cfg: InfrastructureSettings,
    task: ScheduledTask,
    *,
    idempotency_key: str = "",
) -> None:
    """写入 Redis 任务状态；postgres 可用时同步 app_task_projection。"""
    store = build_task_state_store(cfg)
    store.save_task(task, idempotency_key=idempotency_key)
    pg = build_task_projection_store(cfg)
    if pg is None:
        return
    pg.upsert(
        task_id=task.task_id,
        session_id=task.session_id,
        owner_user_id=task.owner_user_id,
        status=task.status.value,
        kind=task.kind,
        payload={
            "terminal": task.terminal,
            "result": task.result,
            "error": task.error,
            "idempotency_key": idempotency_key,
        },
    )


def _emit_journal(
    hook: Any,
    task: ScheduledTask,
    *,
    idempotency_key: str = "",
) -> None:
    if hook is None:
        return
    payload: dict[str, Any] = {
        "task_id": task.task_id,
        "status": task.status.value,
        "terminal": task.terminal,
        "owner_user_id": task.owner_user_id,
        "kind": task.kind,
    }
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    hook.on_task_state(task.session_id, payload)


@celery_app.task(name="jiyaojun.run_pipeline_job", bind=True)
def run_pipeline_job(
    self,
    *,
    task_id: str,
    meeting_id: str,
    session_id: str,
    idempotency_key: str,
    owner_user_id: str = "",
    kind: str = "pipeline",
    scenario_code: str = "tech_review",
) -> dict[str, Any]:
    """执行长流水线；执行前用 Redis 幂等键防重复副作用。"""
    cfg = default_settings
    idem = build_idempotency_cache(cfg)
    state_store = build_task_state_store(cfg)
    journal_hook = getattr(self, "_journal_hook", None)

    task = _load_task(
        state_store,
        task_id,
        session_id=session_id,
        kind=kind,
        owner_user_id=owner_user_id,
    )

    # 幂等：同一 key 已成功执行则直接返回缓存结果，不再跑副作用。
    if not idem.try_acquire(idempotency_key, task_id):
        cached = state_store.load_task(task_id)
        if cached and cached.get("status") == TaskStatus.SUCCEEDED.value:
            return dict(cached.get("result") or {})
        existing_tid = state_store.task_id_for_idempotency(idempotency_key)
        if existing_tid:
            cached = state_store.load_task(existing_tid)
            if cached and cached.get("status") == TaskStatus.SUCCEEDED.value:
                return dict(cached.get("result") or {})
        logger.info("幂等键已占用，跳过重复执行: %s", idempotency_key)
        return {"skipped": True, "reason": "idempotent_in_flight", "task_id": task_id}

    task.status = TaskStatus.RUNNING
    _persist_projection(cfg, task, idempotency_key=idempotency_key)
    _emit_journal(journal_hook, task, idempotency_key=idempotency_key)

    try:
        result = _run_pipeline_body(
            meeting_id=meeting_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
            scenario_code=scenario_code,
        )
        task.status = TaskStatus.SUCCEEDED
        task.terminal = "succeeded"
        task.result = result
        _persist_projection(cfg, task, idempotency_key=idempotency_key)
        _emit_journal(journal_hook, task, idempotency_key=idempotency_key)
        return result
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.terminal = "failed"
        task.error = str(exc)
        idem.release(idempotency_key)
        _persist_projection(cfg, task, idempotency_key=idempotency_key)
        _emit_journal(journal_hook, task, idempotency_key=idempotency_key)
        raise
