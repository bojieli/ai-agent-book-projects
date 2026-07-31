"""Empty battle DataFrame must not crash Bradley-Terry LogisticRegression."""
import pandas as pd

from bradley_terry import compute_bradley_terry_leaderboard, compute_mle_elo


def test_compute_mle_elo_empty_battles():
    df = pd.DataFrame(columns=["model_a", "model_b", "winner"])
    ratings = compute_mle_elo(df)
    assert isinstance(ratings, pd.Series)
    assert len(ratings) == 0


def test_compute_bradley_terry_leaderboard_empty():
    df = pd.DataFrame(columns=["model_a", "model_b", "winner"])
    board = compute_bradley_terry_leaderboard(df)
    assert isinstance(board, pd.DataFrame)
    assert len(board) == 0


def test_nonempty_still_rates():
    df = pd.DataFrame(
        [
            {"model_a": "A", "model_b": "B", "winner": "model_a"},
            {"model_a": "A", "model_b": "B", "winner": "model_a"},
            {"model_a": "B", "model_b": "C", "winner": "model_b"},
            {"model_a": "A", "model_b": "C", "winner": "model_a"},
        ]
    )
    ratings = compute_mle_elo(df)
    assert set(ratings.index) >= {"A", "B", "C"}
    assert ratings["A"] > ratings["C"]
