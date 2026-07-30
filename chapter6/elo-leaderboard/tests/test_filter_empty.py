"""
Regression test for filter_data on empty input (实验 6-6 排行榜).

An empty arena data file (e.g. a failed/truncated download saved as `[]`) used to
crash with ZeroDivisionError at the "After filtering" percentage print.
"""
import pandas as pd
import pytest

from data_loader import filter_data


def test_filter_data_tolerates_empty_dataframe():
    """Empty input no longer raises ZeroDivisionError; returns an empty DataFrame."""
    empty = pd.DataFrame({"model_a": [], "model_b": [], "winner": []})
    result = filter_data(empty)
    assert len(result) == 0


def test_filter_data_normal_case_unchanged():
    """Non-empty input still filters and reports normally."""
    df = pd.DataFrame({
        "model_a": ["a", "b", "a"],
        "model_b": ["b", "a", "c"],
        "winner": ["model_a", "model_b", "tie"],
        "anony": [True, True, False],
    })
    result = filter_data(df, anony_only=True, use_dedup=False)
    assert len(result) == 2   # 非匿名的一条被过滤


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
