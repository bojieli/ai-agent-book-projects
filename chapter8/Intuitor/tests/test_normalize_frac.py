"""Regression: \\frac{a}{b} and a/b must evaluate, not concatenate digit runs."""

from evaluate_from_cache import extract_and_normalize_answer, normalize_number


def test_frac_six_over_two():
    assert extract_and_normalize_answer(r"\boxed{\frac{6}{2}}") == "3"


def test_plain_slash_six_over_two():
    assert extract_and_normalize_answer(r"\boxed{6/2}") == "3"


def test_frac_one_half():
    assert extract_and_normalize_answer(r"\boxed{\frac{1}{2}}") == "0.5"


def test_plain_integer_unchanged():
    assert extract_and_normalize_answer(r"\boxed{42}") == "42"
    assert normalize_number("1,234") == "1234"
