"""Regression test for compare_win_rates when comparisons list is empty."""
import numpy as np
import pandas as pd
from elo_rating import EloRatingSystem
from leaderboard import compare_win_rates


def test_compare_win_rates_empty_has_required_columns():
    """compare_win_rates must return a DataFrame with required columns when no valid comparisons exist."""
    elo = EloRatingSystem()
    empirical_df = pd.DataFrame(np.nan, index=["model_a", "model_b"], columns=["model_a", "model_b"])
    df_comp = compare_win_rates(elo, empirical_df)
    assert list(df_comp.columns) == ["model_a", "model_b", "empirical", "predicted", "error"]
    assert len(df_comp) == 0
    # Accessing columns on empty result must not raise KeyError
    assert "error" in df_comp
    assert df_comp["error"].empty
