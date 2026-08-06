"""In-process scheduler tests."""

from __future__ import annotations

import time

from app.scheduler.tasks import InProcessScheduler, TaskCancelledError, TaskStatus


def test_scheduler_async_and_status():
    sched = InProcessScheduler()

    def work(task, token):
        time.sleep(0.05)
        return {"terminal": "succeeded", "value": 42}

    t = sched.submit(session_id="s1", kind="pipeline", fn=work)
    time.sleep(0.12)
    st = sched.status(t.task_id)
    assert st.status == TaskStatus.SUCCEEDED
    assert st.result.get("value") == 42


def test_scheduler_cooperative_cancel():
    sched = InProcessScheduler()
    side_effect = {"ran": False}

    def slow(task, token):
        time.sleep(0.05)
        token.check()
        side_effect["ran"] = True
        time.sleep(0.2)
        return {"terminal": "succeeded"}

    t = sched.submit(session_id="s2", kind="pipeline", fn=slow)
    time.sleep(0.02)
    sched.cancel(t.task_id)
    time.sleep(0.15)
    st = sched.status(t.task_id)
    assert st.status == TaskStatus.CANCELLED
    assert not side_effect["ran"]


def test_terminal_not_overwritten():
    sched = InProcessScheduler()

    def work(task, token):
        return {"ok": True}

    t = sched.submit(session_id="s3", kind="pipeline", fn=work)
    time.sleep(0.05)
    st = sched.status(t.task_id)
    assert st.status == TaskStatus.SUCCEEDED
    sched._set_status(st, TaskStatus.FAILED)
    st2 = sched.status(t.task_id)
    assert st2.status == TaskStatus.SUCCEEDED
