import argparse

from demo import (
    _checkpoint_identity,
    _execution_completion,
    _load_checkpoint,
    _write_checkpoint,
    paired_analysis,
)
from tasks import TASKS


def test_frozen_matrix_has_every_factorial_cell_once():
    cells = {
        (
            task.source["cabin"],
            task.source["hours_since_booking"],
            task.source["flight_status"],
        )
        for task in TASKS
    }
    assert len(TASKS) == 60
    assert len(cells) == 60
    assert sum(task.expect_refundable for task in TASKS) == 54


def test_paired_analysis_detects_codified_gain():
    control = [{"task_id": str(i), "success": i < 2} for i in range(20)]
    codified = [{"task_id": str(i), "success": i < 19} for i in range(20)]
    result = paired_analysis(control, codified)
    assert result["codified_success_rate"] == 0.95
    assert result["codified_significantly_higher"] is True


def test_checkpoint_round_trip_and_identity_guard(tmp_path):
    args = argparse.Namespace(
        provider="ollama", small_model="qwen3:4b", big_model=None, mode="both"
    )
    arms = [
        {"key": "small_control"},
        {"key": "small_codified"},
    ]
    identity = _checkpoint_identity(args, TASKS, arms, "abc123")
    path = tmp_path / "campaign.json.checkpoint.json"
    rows = {
        "small_control": {"TB001": {"task_id": "TB001", "success": True}},
        "small_codified": {},
    }
    _write_checkpoint(path, identity, rows)
    loaded = _load_checkpoint(path, identity)
    assert loaded == rows

    changed = {**identity, "small_model": "qwen3:1.7b"}
    try:
        _load_checkpoint(path, changed)
    except ValueError as exc:
        assert "identity mismatch" in str(exc)
    else:
        raise AssertionError("mismatched checkpoint identity was accepted")


def test_execution_completion_requires_full_exact_campaign():
    args = argparse.Namespace(
        provider="ollama", small_model="qwen3:4b", big_model=None, mode="both"
    )
    arms = [
        {"key": "small_control"},
        {"key": "small_codified"},
    ]

    def row(task_id):
        return {
            "task_id": task_id,
            "messages": [{"role": "user", "content": "x"}],
            "transcript": [],
            "provider_receipts": [{
                "response_id": "chatcmpl-1",
                "response_model": "qwen3:4b",
                "usage": {"total_tokens": 1},
            }],
        }

    complete_rows = [[row(task.task_id) for task in TASKS] for _ in arms]
    completion = _execution_completion(args, TASKS, arms, complete_rows)
    assert completion["campaign_complete"] is True
    assert completion["observed_trajectories"] == 120

    incomplete = _execution_completion(args, TASKS[:1], arms, [[row(TASKS[0].task_id)]] * 2)
    assert incomplete["campaign_complete"] is False
