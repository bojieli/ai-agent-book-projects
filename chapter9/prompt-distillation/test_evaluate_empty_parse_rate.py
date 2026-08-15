"""Regression: empty test set must not ZeroDivisionError on parse-rate summary."""
import sys
import types


def _stub_evaluate_deps() -> None:
    for name in ["torch", "numpy", "transformers", "peft", "tqdm"]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["transformers"].AutoTokenizer = object
    sys.modules["transformers"].AutoModelForCausalLM = object
    sys.modules["peft"].PeftModel = object
    sys.modules["tqdm"].tqdm = lambda x, **k: x


_stub_evaluate_deps()

from evaluate import compute_parse_rate  # noqa: E402


def test_compute_parse_rate_empty_total_is_zero():
    assert compute_parse_rate(0, 0) == 0.0


def test_compute_parse_rate_nonzero_total():
    assert compute_parse_rate(8, 10) == 0.8
