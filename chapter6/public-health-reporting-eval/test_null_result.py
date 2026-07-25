"""score_prediction must tolerate result:null like missing/empty result."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from agent import DeterministicReportingAgent
from evaluator import MAX_SCORE, expected_by_task, load_json, score_prediction
from reporting_tools import ReportingEnvironment


ROOT = Path(__file__).parent


def _sample_expected():
    expected = expected_by_task(ROOT / "expected_answers.json")
    tasks = load_json(ROOT / "tasks.json")
    environment = ReportingEnvironment(ROOT / "data" / "synthetic_reports.csv")
    agent = DeterministicReportingAgent(environment, expected)
    prediction = agent.run(tasks[0])
    return prediction, expected[prediction["task_id"]]


def test_null_result_scores_without_attribute_error():
    prediction, expected = _sample_expected()
    prediction = deepcopy(prediction)
    prediction["result"] = None
    result = score_prediction(prediction, expected)
    assert result["details"]["answer"] == 0
    assert result["details"]["evidence"] == 0
    assert result["score"] == (
        result["details"]["tool_selection"]
        + result["details"]["arguments"]
        + result["details"]["grounding_and_safety"]
    )


def test_missing_result_matches_null_result_score():
    prediction, expected = _sample_expected()
    null_pred = deepcopy(prediction)
    null_pred["result"] = None
    missing_pred = deepcopy(prediction)
    del missing_pred["result"]
    assert score_prediction(null_pred, expected) == score_prediction(missing_pred, expected)


def test_valid_result_still_full_score():
    prediction, expected = _sample_expected()
    result = score_prediction(prediction, expected)
    assert result["score"] == MAX_SCORE
