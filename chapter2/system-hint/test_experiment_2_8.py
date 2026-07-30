import json
from pathlib import Path

import run_experiment_2_8 as campaign


def test_condition_order_alternates_and_timestamp_has_three_arms():
    assert campaign.condition_order("timestamps", 0) == [
        "timestamps_guided", "timestamps_raw", "disabled"
    ]
    assert campaign.condition_order("timestamps", 1) == [
        "disabled", "timestamps_raw", "timestamps_guided"
    ]
    assert campaign.condition_order("tool_counter", 0) == ["tool_counter", "disabled"]
    assert campaign.condition_order("tool_counter", 1) == ["disabled", "tool_counter"]


def test_timestamp_objective_is_derived_from_actions(tmp_path: Path):
    case = {"records": {"old": "2025-01-01", "new": "2025-01-02"}, "expected": "new"}
    events = [
        {"name": "read_record", "arguments": {"name": "old"}, "ok": True},
        {"name": "read_record", "arguments": {"name": "new"}, "ok": True},
        {"name": "submit_result", "arguments": {"selected_record": "new"}, "ok": True},
    ]
    assert campaign.component_scores("timestamps", case, events, tmp_path) == {"timestamps": True}


def test_detailed_error_gate_requires_failed_old_name_and_actual_read(tmp_path: Path):
    case = {"requested": "old.txt", "actual": "new.txt", "token": "T-1"}
    events = [
        {"name": "read_document", "arguments": {"file": "old.txt"}, "ok": False},
        {"name": "read_document", "arguments": {"file": "new.txt"}, "ok": True},
        {"name": "submit_result", "arguments": {"document": "new.txt", "token": "T-1"}, "ok": True},
    ]
    assert campaign.component_scores("detailed_errors", case, events, tmp_path)["detailed_errors"]


def test_tool_protocol_rejects_non_tool_between_call_and_result():
    good = [
        {"role": "assistant", "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "tool_call_id": "c1"},
    ]
    bad = [good[0], {"role": "user", "content": "interleaved"}, good[1]]
    assert campaign.validate_tool_protocol(good)
    assert not campaign.validate_tool_protocol(bad)


def test_initialize_sandbox_isolated_and_hashed(tmp_path: Path):
    root = tmp_path / "case"
    case = {"id": "todo-x", "token": "ABC", "artifacts": ["one.txt"]}
    campaign.initialize_sandbox(root, "todo_list", case)
    assert json.loads((root / "initial_state.json").read_text())["token"] == "ABC"
    before = campaign.sandbox_hash(root)
    (root / "artifacts" / "one.txt").write_text("ABC")
    assert campaign.sandbox_hash(root) != before


def test_completed_real_campaign_accepts_detailed_error_in_tool_event():
    run_dir = Path(__file__).parent / "runs" / "exp2-8-kimi-k3-20260730-v1"
    comparison_path = run_dir / "comparison.json"
    if not comparison_path.exists():
        return
    protocol_bytes = campaign.PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    rows = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((run_dir / "cases").glob("*.json"))
    ]
    comparison = campaign.summarize(
        protocol, campaign.sha256_bytes(protocol_bytes), run_dir, rows
    )
    assert comparison["acceptance"]["interventions_visible_and_controls_clean"]
    assert comparison["acceptance"]["detailed_error_feature_exercised"]
