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
