"""Contract tests for the exact Experiment 4-7 runner (no model/API calls)."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "run_exact_experiment.py"
SPEC = importlib.util.spec_from_file_location("experiment_4_7_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def test_protocol_is_exact_book_contract():
    protocol = json.loads((HERE / "experiment_protocol.json").read_text(encoding="utf-8"))
    assert protocol["model"] == "qwen3:4b"
    assert protocol["minimum_mcp_tools"] >= 120
    assert protocol["minimum_control_schema_tokens"] >= 50000
    assert protocol["treatment"]["system_tools"] == [
        "web_search", "code_interpreter", "discover_tools"
    ]
    assert "cannot substitute" in protocol["treatment"]["base_tool_boundary"]
    assert "structured market quote" in runner.TREATMENT_GUIDANCE
    assert "call discover_tools separately" in runner.TREATMENT_GUIDANCE
    assert len(protocol["tasks"]) == 3


def test_plan_grading_requires_both_cross_domain_slots():
    task = runner.TASKS[0]
    incomplete = runner.grade_plan(task, [{"tool": "web_search"}])
    complete = runner.grade_plan(task, [
        {"tool": "yfinance_quote"}, {"tool": "web_search"}
    ])
    assert incomplete["accuracy"] == 0.5
    assert not incomplete["all_required_capabilities_selected"]
    assert complete["accuracy"] == 1.0
    assert complete["all_required_capabilities_selected"]


def test_visualization_code_writes_real_svg(tmp_path):
    output = tmp_path / "contributors.svg"
    code = runner.visualization_code([
        {"login": "alice", "contributions": 7},
        {"login": "bob", "contributions": 3},
    ], output)
    namespace = {}
    exec(compile(code, "<test>", "exec"), namespace)
    assert output.read_text(encoding="utf-8").startswith("<svg")
    assert output.stat().st_size > 100


def _real_receipt(tool: str, backend: str = "live.example") -> dict:
    return {
        "tool": tool,
        "success": True,
        "transport": "mcp-stdio",
        "mcp_result_is_error": False,
        "backend_provenance": {"backend": backend, "origin": "live-api"},
        "simulation_markers": [],
        "substantive_observation": True,
        "payload": {"success": True, "data": {"observed": True}},
    }


def test_real_execution_gate_rejects_missing_required_receipt():
    record = {"execution": {"receipts": [_real_receipt("yfinance_quote")]}}
    assert not runner._required_receipts_real(record, runner.TASKS[0])


def test_real_execution_gate_rejects_failed_receipt():
    receipts = [_real_receipt("yfinance_quote"), _real_receipt("web_search")]
    receipts[1]["success"] = False
    record = {"execution": {"receipts": receipts}}
    assert not runner._required_receipts_real(record, runner.TASKS[0])


def test_real_execution_gate_rejects_tampered_mock_provenance():
    receipts = [_real_receipt("yfinance_quote"), _real_receipt("web_search")]
    tampered = deepcopy(receipts)
    tampered[0]["backend_provenance"] = {"backend": "mock-server", "origin": "mock"}
    tampered[0]["simulation_markers"] = ["mock"]
    record = {"execution": {"receipts": tampered}}
    assert not runner._required_receipts_real(record, runner.TASKS[0])


def test_acceptance_status_fails_closed_without_campaign_receipts():
    protocol = json.loads((HERE / "experiment_protocol.json").read_text(encoding="utf-8"))
    result = runner.derive_acceptance([], [], {}, protocol, {}, {})
    assert result["status"] == "failed"
    assert not result["gates"]["real_mcp_execution_only"]
    assert not any(result["gates"].values())


def test_run_group_resume_reuses_only_compatible_receipt(tmp_path):
    task = runner.TASKS[0]
    task_dir = tmp_path / "control" / task["id"]
    task_dir.mkdir(parents=True)
    expected = {
        "strategy": "control",
        "task": task["id"],
        "model": runner.MODEL,
        "execution": {"task_complete": True},
    }
    (task_dir / "receipt.json").write_text(json.dumps(expected), encoding="utf-8")

    original_tasks = runner.TASKS
    runner.TASKS = [task]
    try:
        records = asyncio.run(
            runner.run_group(None, [], None, "control", tmp_path, resume=True)
        )
    finally:
        runner.TASKS = original_tasks

    assert records == [expected]


def test_run_group_resume_archives_and_retries_one_incomplete_attempt(tmp_path):
    task = runner.TASKS[0]
    task_dir = tmp_path / "treatment" / task["id"]
    task_dir.mkdir(parents=True)
    failed = {
        "strategy": "treatment",
        "task": task["id"],
        "model": runner.MODEL,
        "execution": {"task_complete": False},
    }
    (task_dir / "receipt.json").write_text(json.dumps(failed), encoding="utf-8")
    (task_dir / "partial.svg").write_text("<svg/>", encoding="utf-8")
    recovered = {
        "strategy": "treatment",
        "task": task["id"],
        "model": runner.MODEL,
        "execution": {"task_complete": True},
    }

    async def fake_run_agent_task(*_args, **_kwargs):
        assert not (task_dir / "receipt.json").exists()
        assert not (task_dir / "partial.svg").exists()
        return recovered

    original_tasks = runner.TASKS
    original_run_agent_task = runner.run_agent_task
    runner.TASKS = [task]
    runner.run_agent_task = fake_run_agent_task
    try:
        records = asyncio.run(
            runner.run_group(None, [], None, "treatment", tmp_path, resume=True)
        )
    finally:
        runner.TASKS = original_tasks
        runner.run_agent_task = original_run_agent_task

    archive = task_dir / "failed_attempts" / "attempt-1"
    assert records == [recovered]
    assert json.loads((archive / "receipt.json").read_text(encoding="utf-8")) == failed
    assert (archive / "partial.svg").read_text(encoding="utf-8") == "<svg/>"
    assert json.loads((task_dir / "receipt.json").read_text(encoding="utf-8")) == recovered


def test_run_group_resume_refuses_third_real_attempt(tmp_path):
    task = runner.TASKS[0]
    task_dir = tmp_path / "treatment" / task["id"]
    (task_dir / "failed_attempts" / "attempt-1").mkdir(parents=True)
    failed = {
        "strategy": "treatment",
        "task": task["id"],
        "model": runner.MODEL,
        "execution": {"task_complete": False},
    }
    (task_dir / "receipt.json").write_text(json.dumps(failed), encoding="utf-8")

    original_tasks = runner.TASKS
    runner.TASKS = [task]
    try:
        with pytest.raises(RuntimeError, match="maximum two real attempts exhausted"):
            asyncio.run(
                runner.run_group(None, [], None, "treatment", tmp_path, resume=True)
            )
    finally:
        runner.TASKS = original_tasks
