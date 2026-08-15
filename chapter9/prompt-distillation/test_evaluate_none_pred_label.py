"""Regression: unparseable model output (pred_label None) must not crash progress prints."""
import sys
import types

import pytest


def _stub_evaluate_deps() -> None:
    for name in ["torch", "numpy", "transformers", "peft", "tqdm"]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["transformers"].AutoTokenizer = object
    sys.modules["transformers"].AutoModelForCausalLM = object
    sys.modules["peft"].PeftModel = object
    sys.modules["tqdm"].tqdm = lambda x, **k: x


_stub_evaluate_deps()

from evaluate import format_pred_label, parse_language_label  # noqa: E402


def test_parse_language_label_returns_none_for_prose():
    assert parse_language_label("I believe this is English.") is None


def test_format_pred_label_none_is_displayable():
    pred_label = parse_language_label("I believe this is English.")
    assert pred_label is None
    token = format_pred_label(pred_label)
    assert token == "??"
    assert f"Pred: {token:>2s}" == "Pred: ??"
    with pytest.raises(TypeError):
        f"{pred_label:>2s}"


def test_format_pred_label_keeps_real_codes():
    assert format_pred_label("en") == "en"
    assert f"{format_pred_label('fr'):>2s}" == "fr"
