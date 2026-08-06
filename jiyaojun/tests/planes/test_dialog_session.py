"""Dialog session service integration tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from app.knowledge import KnowledgePlane
from app.memory.session_journal import SessionAccessError
from app.planes.dialog.session_service import DialogSessionService
from app.scheduler.tasks import TaskCancelledError, TaskStatus


def test_session_resume_same_session_id():
    kp = KnowledgePlane()
    kp.seed_demo()
    svc = DialogSessionService(knowledge=kp)
    r1 = svc.chat(
        session_id="sess_resume",
        user_id="u_pm",
        org_domains=["eng"],
        message="超时重试规范是什么",
    )
    assert r1["mode"] == "rag_grounding"
    r2 = svc.chat(
        session_id="sess_resume",
        user_id="u_pm",
        org_domains=["eng"],
        message="上次决议呢",
    )
    ctx = svc.get_context("sess_resume", user_id="u_pm", org_domains=["eng"])
    assert ctx["total_entries"] >= 4


def test_jsonl_session_persist(tmp_path: Path):
    kp = KnowledgePlane()
    svc = DialogSessionService.with_jsonl(kp, tmp_path / "j")
    svc.chat(session_id="persist1", user_id="u_pm", org_domains=["eng"], message="hello")
    svc2 = DialogSessionService.with_jsonl(kp, tmp_path / "j")
    ctx = svc2.get_context("persist1", user_id="u_pm", org_domains=["eng"])
    assert ctx["total_entries"] >= 2


def test_hitl_approve_and_reject():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    r1 = svc.chat(
        session_id="hitl1",
        user_id="u_pm",
        org_domains=["eng"],
        message="需要人工 HITL 确认后再建任务",
    )
    assert r1["terminal"] == "suspended"
    r2 = svc.resume_hitl(
        session_id="hitl1",
        user_id="u_pm",
        org_domains=["eng"],
        message="已批准，建任务",
        approved=True,
        tool_allowlist=["connector.task.create"],
    )
    assert r2["terminal"] == "succeeded"

    r3 = svc.chat(
        session_id="hitl2",
        user_id="u_pm",
        org_domains=["eng"],
        message="人工确认建缺陷",
    )
    assert r3["terminal"] == "suspended"
    r4 = svc.resume_hitl(
        session_id="hitl2",
        user_id="u_pm",
        org_domains=["eng"],
        message="",
        approved=False,
    )
    assert r4["terminal"] == "rejected"


def test_empty_allowlist_denies_tools():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    r = svc.chat(
        session_id="empty_allow",
        user_id="u_pm",
        org_domains=["eng"],
        message="建缺陷：空 allowlist 测试",
        tool_allowlist=[],
    )
    assert r["mode"] == "agent_loop"
    assert "无可用工具" in r.get("answer", "") or r["terminal"] in {"succeeded", "failed"}


def test_agent_loop_observation_at_least_two_steps():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    r = svc.chat(
        session_id="loop2",
        user_id="u_pm",
        org_domains=["eng"],
        message="请建缺陷：观测两轮",
        tool_allowlist=["connector.defect.create"],
    )
    assert r["terminal"] == "succeeded"
    assert r.get("tool_calls", 0) >= 1
    assert r.get("steps", 0) >= 2


def test_chinese_intent_picks_task_vs_defect():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    r_task = svc.chat(
        session_id="intent_task",
        user_id="u_pm",
        org_domains=["eng"],
        message="请建任务：跟进发布",
        tool_allowlist=["connector.task.create", "connector.defect.create"],
    )
    assert r_task["terminal"] == "succeeded"
    assert "connector.task.create" in r_task.get("answer", "")

    r_defect = svc.chat(
        session_id="intent_defect",
        user_id="u_pm",
        org_domains=["eng"],
        message="请建缺陷：网关超时",
        tool_allowlist=["connector.task.create", "connector.defect.create"],
    )
    assert r_defect["terminal"] == "succeeded"
    assert "connector.defect.create" in r_defect.get("answer", "")


def test_cross_user_session_denied():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    svc.chat(session_id="owned", user_id="u_pm", org_domains=["eng"], message="hello")
    with pytest.raises(SessionAccessError):
        svc.get_context("owned", user_id="u_hrbp", org_domains=["hr"])


def test_admin_can_access_other_session():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    svc.chat(session_id="admin_sess", user_id="u_pm", org_domains=["eng"], message="hello")
    ctx = svc.get_context("admin_sess", user_id="u_admin", org_domains=["eng"], is_admin=True)
    assert ctx["owner_user_id"] == "u_pm"


def test_branch_fork_and_resume(tmp_path: Path):
    kp = KnowledgePlane()
    svc = DialogSessionService.with_jsonl(kp, tmp_path / "j")
    svc.chat(session_id="br1", user_id="u_pm", org_domains=["eng"], message="hello branch")
    ctx = svc.get_context("br1", user_id="u_pm", org_domains=["eng"])
    entries = svc._journal("br1", user_id="u_pm", org_domains=["eng"]).entries
    fork_at = entries[0].id
    svc.fork_branch("br1", fork_at, user_id="u_pm", org_domains=["eng"])
    svc.chat(session_id="br1", user_id="u_pm", org_domains=["eng"], message="after fork")
    ctx2 = svc.get_context("br1", user_id="u_pm", org_domains=["eng"])
    assert ctx2["path_length"] <= ctx["total_entries"]


def test_background_pipeline_not_blocking():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)

    def pipeline_job(token):
        time.sleep(0.05)
        return {"terminal": "succeeded"}

    tid = svc.submit_pipeline_background(
        session_id="bg1",
        user_id="u_pm",
        org_domains=["eng"],
        fn=pipeline_job,
    )
    r = svc.chat(session_id="bg1", user_id="u_pm", org_domains=["eng"], message="规范")
    assert r["terminal"] == "succeeded"
    time.sleep(0.08)
    st = svc.task_status(tid, user_id="u_pm")
    assert st["terminal"] == "succeeded"


def test_background_cancel_before_side_effect():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)
    started = {"v": False}

    def slow_job(token):
        time.sleep(0.02)
        token.check()
        started["v"] = True
        time.sleep(0.2)
        return {"terminal": "succeeded"}

    tid = svc.submit_pipeline_background(
        session_id="bg_cancel",
        user_id="u_pm",
        org_domains=["eng"],
        fn=slow_job,
    )
    time.sleep(0.01)
    svc.cancel_task(tid, user_id="u_pm")
    time.sleep(0.15)
    st = svc.task_status(tid, user_id="u_pm")
    assert st["status"] in {TaskStatus.CANCELLED.value, TaskStatus.CANCEL_REQUESTED.value}
    assert not started["v"]


def test_orphan_on_restart():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)

    def never_finishes(token):
        time.sleep(5)
        return {}

    tid = svc.submit_pipeline_background(
        session_id="orphan1",
        user_id="u_pm",
        org_domains=["eng"],
        fn=never_finishes,
    )
    t = svc.scheduler.tasks[tid]
    t.status = TaskStatus.RUNNING
    n = svc.mark_orphaned_tasks_on_restart()
    assert n >= 1
    st = svc.task_status(tid, user_id="u_pm")
    assert st["status"] == TaskStatus.ORPHANED.value


def test_task_status_cross_user_denied():
    kp = KnowledgePlane()
    svc = DialogSessionService(knowledge=kp)

    def quick(token):
        return {"ok": True}

    tid = svc.submit_pipeline_background(
        session_id="task_acl",
        user_id="u_pm",
        org_domains=["eng"],
        fn=quick,
    )
    time.sleep(0.05)
    with pytest.raises(SessionAccessError):
        svc.task_status(tid, user_id="u_hrbp")
