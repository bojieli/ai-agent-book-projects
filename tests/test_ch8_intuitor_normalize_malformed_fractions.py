import sys
import os
import pytest

pytest.importorskip("pandas")

sys.path.insert(0, os.path.abspath("chapter8/Intuitor"))

from evaluate_from_cache import _normalize_number, normalize_number


def test_normalize_number_malformed_fractions():
    """Contract: _normalize_number handles malformed fraction strings without crashing or raising exceptions."""
    malformed_inputs = [
        r"\frac{}{}",
        r"\frac{abc}{def}",
        r"\frac{1}{}",
        r"\frac{}{2}",
        r"1/0",
        r"1/",
        r"/2",
        r"a/b",
    ]

    for inp in malformed_inputs:
        # Must execute cleanly without raising AttributeError, ValueError, ZeroDivisionError, etc.
        res1 = _normalize_number(inp)
        res2 = normalize_number(inp)
        assert res1 == res2


def test_normalize_number_valid_fractions():
    """Contract: _normalize_number correctly normalizes valid fractions."""
    assert _normalize_number(r"\frac{6}{2}") == "3"
    assert _normalize_number(r"-\frac{10}{2}") == "-5"
    assert _normalize_number(r"\frac{1}{2}") == "0.5"
    assert _normalize_number("3/4") == "0.75"
