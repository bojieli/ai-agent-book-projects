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
    """Contract: ResultVerifier safely handles None or non-dict expected_outcome and final_state.

    Locks out AttributeError ('NoneType' object has no attribute 'items' or 'get') when
    expected_outcome or final_state is None.
    """
    verifier = ResultVerifier()
    # expected_outcome and final_state set to None or non-dict
    results1 = verifier.evaluate({"expected_outcome": None, "final_state": None})
    assert len(results1) == 1
    assert results1[0].verdict == UNCERTAIN
    assert results1[0].dimension == "task_resolution"

    results2 = verifier.evaluate({"expected_outcome": {"key": "val"}, "final_state": None})
    assert len(results2) == 1
    assert results2[0].verdict == FAIL

    # TrajectoryVerifier with null messages and null expected_outcome
    tv = TrajectoryVerifier()
    report = tv.evaluate({
        "id": "traj-1",
        "messages": None,
        "expected_outcome": None,
        "final_state": None,
    })
    assert report["trajectory_id"] == "traj-1"
    assert isinstance(report["overall_score"], float)

    # diagnostic_utility with null dimensions
    assert diagnostic_utility({"dimensions": None}) == 1.0
