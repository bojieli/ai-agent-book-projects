"""Jira 确定性模拟器单测。"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.connectors.jira_simulator import JiraSimulator
from app.connectors.mock_saas import MockJiraConnector
from app.connectors.persistent_defect import PersistentDefectConnector


def test_jira_idempotency_same_issue(tmp_path: Path):
    backend = PersistentDefectConnector(tmp_path / "d.json")
    sim = JiraSimulator(backend=backend)
    r1 = sim.execute({"title": "超时", "idempotency_key": "k1"})
    r2 = sim.execute({"title": "超时", "idempotency_key": "k1"})
    assert r1["external_id"] == r2["external_id"]
    assert r1["jira_key"] == r2["jira_key"]
    assert len(sim.issues) == 1


def test_jira_fail_mode_no_create(tmp_path: Path):
    backend = PersistentDefectConnector(tmp_path / "d.json")
    sim = JiraSimulator(backend=backend, mode="fail")
    out = sim.execute({"title": "应失败", "idempotency_key": "fail1"})
    assert out["ok"] is False
    assert out["error"] == "jira_create_failed"
    assert backend.get("fail1") is None
    assert sim.issues == {}


def test_jira_timeout_mode(tmp_path: Path):
    sim = JiraSimulator(mode="timeout")
    out = sim.execute({"title": "应超时", "idempotency_key": "to1"})
    assert out == {"ok": False, "error": "timeout"}
    assert "to1" not in sim.issues


def test_jira_transition_and_callback(tmp_path: Path):
    backend = PersistentDefectConnector(tmp_path / "d.json")
    jira = MockJiraConnector(backend=backend)
    issue = jira.execute({"title": "流转测试", "idempotency_key": "tr1"})
    key = issue["jira_key"]
    moved = jira.transition(key, "in_progress")
    assert moved["status"] == "in_progress"

    received: list[dict] = []

    def handler(payload: dict) -> None:
        received.append(payload)

    jira.schedule_webhook_callback(handler, {"jira_key": key, "status": "closed"})
    assert jira.simulator.flush_callbacks() == 1
    assert received[0]["status"] == "closed"

    emitted = jira.emit_callback(handler, {"jira_key": key, "status": "done"})
    assert emitted["emitted"] is True
    assert len(received) == 2


def test_jira_transition_unknown_raises():
    sim = JiraSimulator()
    with pytest.raises(KeyError):
        sim.transition("ENG-9999", "closed")
