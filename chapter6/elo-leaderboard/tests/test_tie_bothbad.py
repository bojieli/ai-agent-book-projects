"""
Regression test for 'tie (bothbad)' handling in optimized_elo (实验 6-6 排行榜).

Chatbot Arena battle data has four outcomes; 'tie (bothbad)' was missing from
the outcome map, so Series.map produced NaN. NaN then propagated through the
rating updates and spread to every model that later faced an affected one,
leaving the whole leaderboard NaN.
"""
import numpy as np
import pandas as pd

from optimized_elo import NumpyEloRatingSystem


def test_tie_bothbad_does_not_produce_nan_outcomes():
    """'tie (bothbad)' maps to a tie instead of NaN."""
    df = pd.DataFrame({
        "model_a": ["a", "a"],
        "model_b": ["b", "b"],
        "winner": ["model_a", "tie (bothbad)"],
    })
    _, _, outcomes = NumpyEloRatingSystem()._prepare_data(df)
    assert not np.isnan(outcomes).any()
    assert outcomes[1] == 0.5


def test_tie_bothbad_does_not_poison_the_leaderboard():
    """One 'tie (bothbad)' battle used to NaN every rating, including model c."""
    df = pd.DataFrame({
        "model_a": ["a", "a", "b"],
        "model_b": ["b", "b", "c"],
        "winner": ["model_a", "tie (bothbad)", "model_a"],
    })
    system = NumpyEloRatingSystem()
    system.process_matches_vectorized(df, show_progress=False)
    ratings = [rating for _, rating, _, _ in system.get_leaderboard()]
    assert len(ratings) == 3
    assert not any(np.isnan(r) for r in ratings)


def test_unknown_outcome_falls_back_to_tie():
    """An unrecognized label degrades to a tie rather than NaN."""
    df = pd.DataFrame({
        "model_a": ["a"],
        "model_b": ["b"],
        "winner": ["something_new"],
    })
    _, _, outcomes = NumpyEloRatingSystem()._prepare_data(df)
    assert outcomes[0] == 0.5
