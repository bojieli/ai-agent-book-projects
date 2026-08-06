"""Celery Worker 集成测试 — Redis 不可用时 skip。"""

from __future__ import annotations

import os
import time
import uuid
from unittest.mock import patch

import pytest
import redis

from app.config import InfrastructureSettings
from app.runtime.factory import build_scheduler
from app.scheduler.celery_scheduler import CeleryScheduler
from app.scheduler.tasks import TaskStatus


def _redis_url() -> str | None:
    return os.getenv("JIYAOJUN_REDIS_URL", "").strip() or None


def _broker_url() -> str | None:
    return (
        os.getenv("JIYAOJUN_CELERY_BROKER_URL", "").strip()
        or _redis_url()
    )


def _can_ping_redis(url: str) -> bool:
    try:
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture
def celery_settings():
    broker = _broker_url()
    cache = _redis_url()
    if not broker or not _can_ping_redis(broker):
        pytest.skip("Redis/Celery broker 不可用")
    return InfrastructureSettings(
        scheduler_backend="celery",
        redis_backend="redis" if cache else "memory",
        redis_url=cache or "",
        celery_broker_url=broker,
    )


@pytest.fixture
def eager_celery(celery_settings):
    """同进程 eager 执行，免独立 worker 进程。"""
    from app.scheduler.celery_app import celery_app, configure_celery_app

    configure_celery_app(celery_settings, task_always_eager=True)
    yield celery_app
    configure_celery_app(celery_settings, task_always_eager=False)


@pytest.mark.integration
def test_celery_submit_and_complete(eager_celery, celery_settings):
    sched = build_scheduler(celery_settings)
    assert isinstance(sched, CeleryScheduler)
    idem = f"idem_{uuid.uuid4().hex[:8]}"
    task = sched.submit(
        session_id="cel_sess_1",
        kind="pipeline",
        meeting_id="meet_1",
        idempotency_key=idem,
        owner_user_id="u1",
    )
    deadline = time.time() + 5
    while time.time() < deadline:
        st = sched.status(task.task_id)
        if st.status == TaskStatus.SUCCEEDED:
            break
        time.sleep(0.05)
    st = sched.status(task.task_id)
    assert st.status == TaskStatus.SUCCEEDED
    assert st.result.get("session_id") == "cel_sess_1"


@pytest.mark.integration
def test_celery_idempotency_no_duplicate_side_effect(eager_celery, celery_settings):
    sched = build_scheduler(celery_settings)
    idem = f"idem_dup_{uuid.uuid4().hex[:8]}"
    calls = {"n": 0}

    def counting_body(**kwargs):
        calls["n"] += 1
        return {"terminal": "succeeded", "count": calls["n"]}

    with patch("app.scheduler.celery_tasks._run_pipeline_body", side_effect=counting_body):
        t1 = sched.submit(
            session_id="cel_sess_2",
            kind="pipeline",
            meeting_id="meet_2",
            idempotency_key=idem,
        )
        deadline = time.time() + 5
        while time.time() < deadline:
            if sched.status(t1.task_id).status == TaskStatus.SUCCEEDED:
                break
            time.sleep(0.05)
        t2 = sched.submit(
            session_id="cel_sess_2",
            kind="pipeline",
            meeting_id="meet_2",
            idempotency_key=idem,
        )
    assert t1.task_id == t2.task_id
    assert calls["n"] == 1


@pytest.mark.integration
def test_celery_orphan_recovery_on_restart(eager_celery, celery_settings):
    sched = build_scheduler(celery_settings)
    idem = f"idem_orphan_{uuid.uuid4().hex[:8]}"
    task = sched.submit(
        session_id="cel_sess_3",
        kind="pipeline",
        meeting_id="meet_3",
        idempotency_key=idem,
    )
    # 模拟 Worker 崩溃：任务仍在 running
    running = sched.status(task.task_id)
    running.status = TaskStatus.RUNNING
    sched._cache_task(running, idempotency_key=idem)

    sched2 = build_scheduler(celery_settings)
    restored = sched2.register_projection(
        task_id=task.task_id,
        session_id="cel_sess_3",
        owner_user_id="u1",
        kind="pipeline",
        status=TaskStatus.RUNNING.value,
    )
    assert restored.status == TaskStatus.RUNNING
    n = sched2.mark_orphaned_on_restart()
    assert n >= 1
    st = sched2.status(task.task_id)
    assert st.status == TaskStatus.ORPHANED
    assert st.terminal == "needs_resume"
