"""Regression: negative currency formats and negative fractions must preserve negative sign."""

from evaluate_from_cache import extract_answer_from_gsm8k_format
from evaluate_from_cache import extract_and_normalize_answer, normalize_number


def test_negative_dollar_amount():
    assert normalize_number("-$42") == "-42"


def test_negative_latex_dollar_amount():
    assert normalize_number(r"-\$42") == "-42"


def test_boxed_negative_dollar_amount():
    assert extract_and_normalize_answer(r"\boxed{-\$42}") == "-42"


def test_negative_latex_frac():
    assert normalize_number(r"-\frac{6}{2}") == "-3"
    assert normalize_number(r"-\dfrac{6}{2}") == "-3"


def test_extract_gsm8k_multiple_hash_markers():
    assert extract_answer_from_gsm8k_format("#### step 1 #### 42") == "42"
    assert extract_and_normalize_answer("#### step 1 #### 42") == "42"


def test_negative_fraction_with_space():
    assert normalize_number("- 1/2") == "-0.5"
    assert extract_and_normalize_answer(r"\boxed{- 1/2}") == "-0.5"
