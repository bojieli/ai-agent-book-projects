import sys
import os

sys.path.insert(0, os.path.abspath("chapter9/trajectory-verifier"))

from verifier import HeuristicQualityJudge, FAIL


def test_heuristic_quality_judge_string_expression_issues():
    """Contract: HeuristicQualityJudge supports string items in quality_facts.expression_issues without throwing AttributeError."""
    judge = HeuristicQualityJudge()

    trajectory = {
        "quality_facts": {
            "expression_issues": [
                "Redundant response",
                "Overly verbose explanation",
                {"turn": 2, "issue": "Repetitive phrasing"},
            ]
        }
    }

    results = judge.evaluate(trajectory)
    assert len(results) == 2

    expression_res = next(r for r in results if r.dimension == "expression_quality")
    assert expression_res.verdict == FAIL
    assert expression_res.score == 0.0
    assert expression_res.evidence == [
        "Redundant response",
        "Overly verbose explanation",
        "turn 2: Repetitive phrasing",
    ]
