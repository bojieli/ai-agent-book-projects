import pytest
import os
import sys

sys.path.insert(0, os.path.abspath("chapter8/trajectory-verifier"))

from verifier import DimensionResult, FAIL, PASS, diagnostic_utility


def test_diagnostic_utility_with_dimension_result_objects():
    dim1 = DimensionResult(
        dimension="task_resolution",
        layer="environment_result",
        verdict=FAIL,
        score=0.0,
        evidence=["mismatch in field x"],
        confidence=1.0,
    )
    dim2 = DimensionResult(
        dimension="rule_compliance",
        layer="process_rules",
        verdict=FAIL,
        score=0.0,
        evidence=[],
        confidence=1.0,
    )
    report = {"trajectory_id": "traj-1", "dimensions": [dim1, dim2]}
    # dim1 has evidence (actionable), dim2 does not -> 1/2 = 0.5
    utility = diagnostic_utility(report)
    assert utility == 0.5


def test_diagnostic_utility_with_dict_objects():
    report = {
        "trajectory_id": "traj-2",
        "dimensions": [
            {"verdict": FAIL, "evidence": ["error log"]},
            {"verdict": FAIL, "evidence": []},
            {"verdict": PASS, "evidence": []},
        ],
    }
    # 2 failures, 1 has evidence -> 0.5
    assert diagnostic_utility(report) == 0.5


def test_diagnostic_utility_with_mixed_objects():
    dim_obj = DimensionResult(
        dimension="task_resolution",
        layer="environment_result",
        verdict=FAIL,
        score=0.0,
        evidence=["obj failure detail"],
        confidence=1.0,
    )
    dict_obj = {"verdict": FAIL, "evidence": []}
    report = {"trajectory_id": "traj-3", "dimensions": [dim_obj, dict_obj]}
    # 2 failures, 1 with evidence -> 0.5
    assert diagnostic_utility(report) == 0.5


def test_diagnostic_utility_no_failures():
    dim_pass = DimensionResult(
        dimension="task_resolution",
        layer="environment_result",
        verdict=PASS,
        score=1.0,
        evidence=["success"],
        confidence=1.0,
    )
    report = {"trajectory_id": "traj-4", "dimensions": [dim_pass]}
    # 0 failures -> returns 1.0
    assert diagnostic_utility(report) == 1.0


def test_diagnostic_utility_empty_dimensions():
    assert diagnostic_utility({}) == 1.0
    assert diagnostic_utility({"dimensions": []}) == 1.0
