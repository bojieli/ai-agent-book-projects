"""Regression tests: verifier module must tolerate null/None or non-dict values for trajectory fields."""
import pytest
from verifier import (
    ProcessVerifier,
    ResultVerifier,
    TrajectoryVerifier,
    diagnostic_utility,
    FAIL,
    PASS,
    UNCERTAIN,
)


def test_process_verifier_tolerates_null_fields():
    """Contract: ProcessVerifier returns valid DimensionResults when optional container fields are None.

    Locks out AttributeError/TypeError when process_facts, sensitive_values, claims, promises,
    or tool_calls are explicitly set to None in trajectory log payloads.
    """
    verifier = ProcessVerifier()
    trajectory = {
        "messages": [{"role": "assistant", "content": "Hello"}],
        "process_facts": None,
        "sensitive_values": None,
        "claims": None,
        "promises": None,
        "tool_calls": None,
    }
    results = verifier.evaluate(trajectory)
    assert len(results) == 4
    for res in results:
        assert res.verdict in (PASS, UNCERTAIN)


def test_process_verifier_tolerates_invalid_container_types():
    """Contract: ProcessVerifier returns valid DimensionResults when container fields are non-iterable non-dict types.

    Locks out TypeError when process_facts, sensitive_values, claims, or promises are integers or booleans.
    """
    verifier = ProcessVerifier()
    trajectory = {
        "messages": [{"role": "assistant", "content": "Hello"}],
        "process_facts": 123,
        "sensitive_values": "invalid",
        "claims": 456,
        "promises": True,
        "tool_calls": 789,
    }
    results = verifier.evaluate(trajectory)
    assert len(results) == 4
    for res in results:
        assert res.verdict in (PASS, UNCERTAIN)


def test_result_verifier_tolerates_null_and_invalid_fields():
    """Contract: ResultVerifier safely handles None, non-dict, empty dict, or nested null expected_outcome and final_state.

    Locks out AttributeError ('NoneType' object has no attribute 'items' or 'get') when
    expected_outcome or final_state is None, non-dict, or contains null values.
    """
    verifier = ResultVerifier()
    # expected_outcome and final_state set to None or non-dict
    results1 = verifier.evaluate({"expected_outcome": None, "final_state": None})
    assert len(results1) == 1
    assert results1[0].verdict == UNCERTAIN
    assert results1[0].dimension == "task_resolution"

    # Empty dicts
    results_empty = verifier.evaluate({"expected_outcome": {}, "final_state": {}})
    assert len(results_empty) == 1
    assert results_empty[0].verdict == UNCERTAIN

    # Non-dict expected_outcome or final_state
    results_non_dict1 = verifier.evaluate({"expected_outcome": "invalid_type", "final_state": 12345})
    assert len(results_non_dict1) == 1
    assert results_non_dict1[0].verdict == UNCERTAIN

    results_non_dict2 = verifier.evaluate({"expected_outcome": {"key": "val"}, "final_state": None})
    assert len(results_non_dict2) == 1
    assert results_non_dict2[0].verdict == FAIL

    # Nested nulls - matching
    results_nested_null_match = verifier.evaluate({
        "expected_outcome": {"status": None, "code": 200},
        "final_state": {"status": None, "code": 200},
    })
    assert len(results_nested_null_match) == 1
    assert results_nested_null_match[0].verdict == PASS

    # Nested nulls - mismatch
    results_nested_null_mismatch = verifier.evaluate({
        "expected_outcome": {"status": None},
        "final_state": {"status": "ok"},
    })
    assert len(results_nested_null_mismatch) == 1
    assert results_nested_null_mismatch[0].verdict == FAIL

    # Non-dict trajectory payload itself
    results_null_traj = verifier.evaluate(None)
    assert len(results_null_traj) == 1
    assert results_null_traj[0].verdict == UNCERTAIN

    results_str_traj = verifier.evaluate("invalid_trajectory")
    assert len(results_str_traj) == 1
    assert results_str_traj[0].verdict == UNCERTAIN

    # TrajectoryVerifier with null messages, null expected_outcome, and non-dict payload
    tv = TrajectoryVerifier()
    report = tv.evaluate({
        "id": "traj-1",
        "messages": None,
        "expected_outcome": None,
        "final_state": None,
    })
    assert report["trajectory_id"] == "traj-1"
    assert isinstance(report["overall_score"], float)

    report_null = tv.evaluate(None)
    assert report_null["trajectory_id"] is None
    assert isinstance(report_null["overall_score"], float)

    # diagnostic_utility with null dimensions
    assert diagnostic_utility({"dimensions": None}) == 1.0
    assert diagnostic_utility(None) == 1.0
