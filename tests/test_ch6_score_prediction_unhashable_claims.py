import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
EVAL_DIR = HERE / "chapter6" / "public-health-reporting-eval"
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from evaluator import score_prediction  # noqa: E402


def test_score_prediction_unhashable_dict_claims():
    pred = {"claims": [{"statement": "flu cases up 10%"}]}
    exp = {
        "task_id": "t1",
        "tool": None,
        "arguments": None,
        "result": {},
        "supported_claims": [{"statement": "flu cases up 10%"}],
    }
    res = score_prediction(pred, exp)
    assert res["details"]["grounding_and_safety"] == 1


def test_score_prediction_none_supported_claims():
    pred = {"claims": ["claim1"]}
    exp = {
        "task_id": "t2",
        "tool": None,
        "arguments": None,
        "result": {},
        "supported_claims": None,
    }
    res = score_prediction(pred, exp)
    assert res["details"]["grounding_and_safety"] == 0
