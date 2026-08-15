"""Ties must contribute to Bradley-Terry weights (not be zeroed by pivot+T)."""
import pandas as pd

from bradley_terry import compute_mle_elo


def test_all_ties_rates_models_instead_of_sample_weight_error():
    df = pd.DataFrame(
        [
            {"model_a": "A", "model_b": "B", "winner": "tie"},
            {"model_a": "A", "model_b": "C", "winner": "tie (bothbad)"},
            {"model_a": "B", "model_b": "C", "winner": "tie"},
        ]
    )
    ratings = compute_mle_elo(df)
    assert set(ratings.index) == {"A", "B", "C"}
    # Pure ties -> equal latent skills under BT.
    assert abs(float(ratings["A"]) - float(ratings["B"])) < 1e-6
    assert abs(float(ratings["A"]) - float(ratings["C"])) < 1e-6


def test_ties_change_ratings_versus_wins_only():
    wins_only = pd.DataFrame(
        [
            {"model_a": "A", "model_b": "B", "winner": "model_a"},
            {"model_a": "B", "model_b": "C", "winner": "model_a"},
        ]
    )
    with_ties = pd.concat(
        [
            wins_only,
            pd.DataFrame(
                [{"model_a": "A", "model_b": "C", "winner": "tie"}] * 8
            ),
        ],
        ignore_index=True,
    )
    r1 = compute_mle_elo(wins_only)
    r2 = compute_mle_elo(with_ties)
    # Extra A–C ties pull A and C together relative to the wins-only fit.
    assert abs(float(r2["A"]) - float(r2["C"])) < abs(float(r1["A"]) - float(r1["C"]))
