"""Deterministic acceptance tests for book Experiment 6-3."""

import json

from evaluator import LLMEvaluator


def evaluator_without_network():
    evaluator = object.__new__(LLMEvaluator)
    return evaluator


def response(*, hallucination=False):
    return json.dumps(
        {
            "dimensions": {
                "precision": {"score": 4, "grade": "excellent", "reasoning": "exact", "evidence": ["4429853327"], "boundary_case": None},
                "recall": {"score": 3, "grade": "good", "reasoning": "core fact", "evidence": ["account"], "boundary_case": "optional routing number"},
                "reasoning": {"score": 3, "grade": "good", "reasoning": "correct link", "evidence": [], "boundary_case": None},
                "proactivity": {"score": 2, "grade": "pass", "reasoning": "limited", "evidence": [], "boundary_case": "next step useful"},
            },
            "hallucination": {
                "detected": hallucination,
                "claims": ["wrong routing"] if hallucination else [],
                "evidence": ["source differs"] if hallucination else ["all claims traceable"],
                "reasoning": "grounding check",
            },
            "overall_reasoning": "dimension audit",
            "required_info_found": {"checking account": True},
            "suggestions": "include routing number",
        }
    )


def test_four_dimensions_compute_reward_and_normalize_grade():
    result = evaluator_without_network()._parse_evaluation_response(response(), "case-1")
    assert result.reward == 0.666667
    assert result.passed is True
    assert set(result.dimensions) == {"precision", "recall", "reasoning", "proactivity"}
    assert result.dimensions["precision"].grade.value == "excellent"
    assert result.required_info_found == {"checking account": 1.0}
    assert result.veto_applied is False


def test_hallucination_is_an_unconditional_veto():
    result = evaluator_without_network()._parse_evaluation_response(response(hallucination=True), "case-2")
    assert result.reward == 0.0
    assert result.passed is False
    assert result.veto_applied is True
    assert result.hallucination.detected is True


def test_partial_credit_on_a_core_dimension_is_not_task_success():
    payload = json.loads(response())
    payload["dimensions"]["recall"]["score"] = 2
    result = evaluator_without_network()._parse_evaluation_response(json.dumps(payload), "case-core")
    assert result.reward > 0
    assert result.passed is False
    assert result.veto_applied is False


def test_missing_dimension_fails_closed():
    payload = json.loads(response())
    del payload["dimensions"]["recall"]
    result = evaluator_without_network()._parse_evaluation_response(json.dumps(payload), "case-3")
    assert result.reward == 0.0
    assert result.passed is False
    assert result.dimensions == {}
    assert "Missing rubric dimension" in result.reasoning


def test_prompt_contains_source_scale_examples_boundaries_and_veto(monkeypatch):
    # Importing the framework loads the real synthetic 60-case suite but makes no API call.
    from framework import UserMemoryEvaluationFramework

    framework = UserMemoryEvaluationFramework()
    case = framework.get_test_case("layer1_01_bank_account")
    prompt = evaluator_without_network()._build_evaluation_prompt(case, "4429853327", None)
    assert "AUTHORITATIVE CONVERSATION SOURCE" in prompt
    assert "4429853327" in prompt
    assert "4 / excellent" in prompt and "1 / fail" in prompt
    assert "Excellent example" in prompt
    assert "Boundary" in prompt
    assert "hallucination (VETO)" in prompt


def test_live_judge_semantic_parse_is_retried(monkeypatch):
    from framework import UserMemoryEvaluationFramework

    case = UserMemoryEvaluationFramework().get_test_case("layer1_01_bank_account")
    evaluator = evaluator_without_network()
    replies = iter(["{malformed", response()])
    calls = []

    def fake_call(messages):
        calls.append(messages)
        return next(replies)

    evaluator._call_llm = fake_call
    result = evaluator.evaluate(case, "4429853327")
    assert len(calls) == 2
    assert result.dimensions["precision"].score == 4
