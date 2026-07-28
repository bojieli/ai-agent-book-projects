"""Offline regression tests; no model, API key or network access required."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from agent import DeterministicReportingAgent
from evaluator import MAX_SCORE, evaluate, expected_by_task, load_json, score_prediction
from reporting_tools import ReportingEnvironment


ROOT = Path(__file__).parent


def reference_predictions():
    expected = expected_by_task(ROOT / "expected_answers.json")
    tasks = load_json(ROOT / "tasks.json")
    environment = ReportingEnvironment(ROOT / "data" / "synthetic_reports.csv")
    agent = DeterministicReportingAgent(environment, expected)
    return [agent.run(task) for task in tasks], expected


def test_reference_agent_receives_full_score():
    predictions, expected = reference_predictions()
    report = evaluate(predictions, expected)
    assert report["score"] == report["max_score"] == len(predictions) * MAX_SCORE


def test_wrong_numeric_answer_loses_answer_points():
    predictions, expected = reference_predictions()
    prediction = deepcopy(predictions[0])
    prediction["result"]["test_positivity_pct"] = 99.0
    result = score_prediction(prediction, expected[prediction["task_id"]])
    assert result["details"]["answer"] == 0
    assert result["score"] == MAX_SCORE - 2


def test_missing_evidence_loses_evidence_point():
    predictions, expected = reference_predictions()
    prediction = deepcopy(predictions[1])
    prediction["result"]["evidence"] = []
    result = score_prediction(prediction, expected[prediction["task_id"]])
    assert result["details"]["evidence"] == 0


def test_null_evidence_loses_evidence_point():
    predictions, expected = reference_predictions()
    prediction = deepcopy(predictions[1])
    prediction["result"]["evidence"] = None
    result = score_prediction(prediction, expected[prediction["task_id"]])
    assert result["details"]["evidence"] == 0
    assert result["score"] == MAX_SCORE - 1


def test_unsupported_claim_loses_grounding_point():
    predictions, expected = reference_predictions()
    prediction = deepcopy(predictions[2])
    prediction["claims"].append("This trend proves an outbreak will occur.")
    result = score_prediction(prediction, expected[prediction["task_id"]])
    assert result["details"]["grounding_and_safety"] == 0


def test_data_quality_tool_detects_deliberate_synthetic_errors():
    environment = ReportingEnvironment(ROOT / "data" / "synthetic_reports.csv")
    result = environment.find_data_quality_issues("Demo District", "2025-02")
    assert result["issue_count"] == 2
    assert result["evidence"] == ["R005"]
