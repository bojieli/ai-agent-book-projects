"""Regression: LaTeX fractions and division with formatting/units must evaluate correctly."""

from evaluate_from_cache import extract_and_normalize_answer, normalize_number


def test_frac_thin_space_evaluates():
    assert normalize_number(r"\frac{1\,000}{2}") == "500"
    assert normalize_number(r"\dfrac{1\,500}{3}") == "500"
    assert normalize_number(r"-\frac{1\,000}{2}") == "-500"


def test_frac_text_units_evaluates():
    assert normalize_number(r"\frac{100\text{ kg}}{2}") == "50"
    assert normalize_number(r"\frac{100}{2\text{ kg}}") == "50"
    assert normalize_number(r"\frac{\text{100 kg}}{2}") == "50"


def test_frac_numeric_format_wrappers_evaluate():
    assert normalize_number(r"\frac{\mathrm{1,000}}{2}") == "500"
    assert normalize_number(r"\frac{\mathbf{6}}{2}") == "3"


def test_slash_division_with_units_and_formatting():
    assert normalize_number("6/2 kg") == "3"
    assert normalize_number("$6/2$") == "3"
    assert normalize_number("1,000 / 2") == "500"
