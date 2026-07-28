"""Regression: optimize_dataframe must tolerate empty object columns."""
import pandas as pd
from parallel_processing import optimize_dataframe


def test_optimize_empty_object_columns():
    df = pd.DataFrame({
        "model_a": pd.Series([], dtype=object),
        "model_b": pd.Series([], dtype=object),
        "winner": pd.Series([], dtype=object),
    })
    out = optimize_dataframe(df)
    assert len(out) == 0
