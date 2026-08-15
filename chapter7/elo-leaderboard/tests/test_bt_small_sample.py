"""Regression: compute_mle_elo must work on small Arena-shaped battle sets."""
import pandas as pd
from battle_simulator import simulate_battles
from bradley_terry import compute_mle_elo


def test_small_two_model_sample():
    df = pd.DataFrame(simulate_battles({"gpt-4": 1200.0, "llama-3": 1000.0}, 10, seed=1))
    ratings = compute_mle_elo(df)
    assert len(ratings) == 2
    assert set(ratings.index) == {"gpt-4", "llama-3"}
