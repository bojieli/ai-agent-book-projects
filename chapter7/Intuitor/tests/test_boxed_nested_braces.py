"""Regression: nested braces inside \\boxed{} must not truncate."""

from evaluate_from_cache import extract_answer_from_boxed


def test_boxed_nested_frac():
    text = r"The answer is \boxed{\frac{1}{2}}"
    assert extract_answer_from_boxed(text) == r"\frac{1}{2}"


def test_boxed_simple_integer():
    text = r"Final answer: \boxed{42}"
    assert extract_answer_from_boxed(text) == "42"


def test_boxed_deeper_nesting():
    text = r"\boxed{\frac{a}{b+c}}"
    assert extract_answer_from_boxed(text) == r"\frac{a}{b+c}"
