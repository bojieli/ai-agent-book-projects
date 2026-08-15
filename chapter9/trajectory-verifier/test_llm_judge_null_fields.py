"""Regression: OpenAIQualityJudge must tolerate an explicit JSON null for
score / confidence / evidence in the model's response — dict.get(key, default)
only applies the default when the key is ABSENT, so a null value returns None and
float(None) / iterating None crash the whole trajectory evaluation."""
import json
import types

from llm_judge import OpenAIQualityJudge


class _FakeClient:
    model = "fake-model"

    def __init__(self, payload):
        self._payload = payload

    def complete(self, **kwargs):
        message = types.SimpleNamespace(content=json.dumps(self._payload))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def test_quality_judge_tolerates_null_score_confidence_evidence():
    """Contract: OpenAIQualityJudge coerces explicit JSON null score, confidence, and evidence fields to safe defaults.

    Locks out TypeError/ValueError when an LLM judge emits JSON null values for score, confidence, or evidence.
    """
    payload = {
        "dimensions": [
            {
                "dimension": "expression_quality",
                "verdict": "uncertain",
                "score": None,
                "confidence": None,
                "evidence": None,
            },
            {
                "dimension": "compliant_flexibility",
                "verdict": "pass",
                "score": 0.8,
                "confidence": 0.9,
                "evidence": ["turn 2"],
            },
        ]
    }
    judge = OpenAIQualityJudge(evidence_client=_FakeClient(payload))
    results = list(judge.evaluate({"messages": [], "process_facts": {}}))

    assert len(results) == 2
    eq = next(r for r in results if r.dimension == "expression_quality")
    assert eq.score == 0.5
    assert eq.confidence == 0.5
    assert eq.evidence == ["LLM returned no evidence"]


def test_quality_judge_tolerates_null_dimensions_array_and_non_dict_payload():
    """Contract: OpenAIQualityJudge handles explicit JSON null dimensions array, non-dict payloads, null items, and invalid trajectories.

    Locks out TypeError ('NoneType' object is not iterable) and AttributeError when LLM response
    payload or trajectory input has null, non-dict, or malformed structure.
    """
    # Test explicit JSON null dimensions array
    judge_null_dims = OpenAIQualityJudge(evidence_client=_FakeClient({"dimensions": None}))
    results1 = list(judge_null_dims.evaluate({"messages": [], "process_facts": None}))
    assert len(results1) == 2
    for res in results1:
        assert res.verdict == "uncertain"
        assert res.score == 0.5

    # Test non-dict JSON response payload (e.g. JSON list)
    judge_list_payload = OpenAIQualityJudge(evidence_client=_FakeClient([{"dimension": "expression_quality"}]))
    results2 = list(judge_list_payload.evaluate({"messages": []}))
    assert len(results2) == 2

    # Test dimensions array with null item or non-dict items
    judge_null_item = OpenAIQualityJudge(evidence_client=_FakeClient({"dimensions": [None, "invalid", 123]}))
    results3 = list(judge_null_item.evaluate({"messages": []}))
    assert len(results3) == 2

    # Test evidence containing null items
    payload_null_ev = {
        "dimensions": [
            {
                "dimension": "expression_quality",
                "verdict": "pass",
                "score": 1.0,
                "confidence": 0.9,
                "evidence": [None, "turn 1"],
            }
        ]
    }
    judge_null_ev = OpenAIQualityJudge(evidence_client=_FakeClient(payload_null_ev))
    results4 = list(judge_null_ev.evaluate({"messages": []}))
    eq = next(r for r in results4 if r.dimension == "expression_quality")
    assert eq.evidence == ["turn 1"]

    # Test null or non-dict trajectory input
    results_null_traj = list(judge_null_dims.evaluate(None))
    assert len(results_null_traj) == 2
    results_str_traj = list(judge_null_dims.evaluate("invalid_trajectory"))
    assert len(results_str_traj) == 2