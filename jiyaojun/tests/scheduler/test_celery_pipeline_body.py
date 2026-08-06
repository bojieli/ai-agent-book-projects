"""Celery pipeline body 模式切换单测（无需 Redis）。"""

from __future__ import annotations

import os

from app.scheduler import celery_tasks


def test_run_pipeline_body_stub_mode(monkeypatch):
    monkeypatch.setenv("JIYAOJUN_CELERY_PIPELINE", "stub")
    out = celery_tasks._run_pipeline_body(
        meeting_id="m1",
        session_id="s1",
        idempotency_key="idem1",
    )
    assert out["terminal"] == "succeeded"
    assert out["meeting_id"] == "m1"


def test_run_pipeline_body_orchestrator_mode():
    prev = os.environ.get("JIYAOJUN_CELERY_PIPELINE")
    os.environ["JIYAOJUN_CELERY_PIPELINE"] = "orchestrator"
    try:
        out = celery_tasks._run_pipeline_body(
            meeting_id="mtg_celery_orch_unit",
            session_id="sess_orch",
            idempotency_key="idem_orch_unit",
            scenario_code="tech_review",
        )
        assert out["pipeline"]["terminal"] == "succeeded"
        assert out["session_id"] == "sess_orch"
    finally:
        if prev is None:
            os.environ.pop("JIYAOJUN_CELERY_PIPELINE", None)
        else:
            os.environ["JIYAOJUN_CELERY_PIPELINE"] = prev


def test_run_pipeline_body_unknown_mode_raises(monkeypatch):
    monkeypatch.setenv("JIYAOJUN_CELERY_PIPELINE", "invalid_mode")
    try:
        celery_tasks._run_pipeline_body(
            meeting_id="m2",
            session_id="s2",
            idempotency_key="idem2",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "invalid_mode" in str(exc)
