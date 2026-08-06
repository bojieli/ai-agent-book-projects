import pytest
import json
import os
import sys
import types

sys.path.insert(0, os.path.abspath("chapter8/trajectory-verifier"))

from llm_judge import OpenAIQualityJudge


class _FakeClient:
    model = "fake-model"

    def __init__(self, payload):
        self._payload = payload

    def complete(self, **kwargs):
        message = types.SimpleNamespace(content=json.dumps(self._payload))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def test_quality_judge_tolerates_non_dict_payload_and_items():
    # When the LLM outputs a top-level JSON list of dimension dicts (or non-dict payload),
    # OpenAIQualityJudge.evaluate must not crash with AttributeError: 'list' object has no attribute 'get'.
    payload_list = [
        {
            "dimension": "expression_quality",
            "verdict": "pass",
            "score": 0.9,
            "confidence": 0.8,
            "evidence": ["turn 1"],
        },
        "invalid_non_dict_item",
    ]
    judge = OpenAIQualityJudge(evidence_client=_FakeClient(payload_list))
    results = list(judge.evaluate({"messages": [], "process_facts": {}}))

    assert len(results) == 2
    eq = next(r for r in results if r.dimension == "expression_quality")
    assert eq.verdict == "pass"
    assert eq.score == 0.9
