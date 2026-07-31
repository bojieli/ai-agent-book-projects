"""Regression test: ProcessVerifier must tolerate null/None values for process_facts, sensitive_values, claims, and promises."""
import pytest
from verifier import ProcessVerifier, PASS, UNCERTAIN


def test_process_verifier_tolerates_null_fields():
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
