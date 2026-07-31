import pandas as pd
from bradley_terry import compute_mle_elo, get_bootstrap_result


def test_bootstrap_is_reproducible():
    battles = pd.DataFrame(
        [
            {"model_a": "a", "model_b": "b", "winner": "model_a"},
            {"model_a": "a", "model_b": "b", "winner": "model_b"},
            {"model_a": "a", "model_b": "b", "winner": "tie"},
            {"model_a": "b", "model_b": "a", "winner": "model_a"},
        ]
    )
    first = get_bootstrap_result(battles, compute_mle_elo, num_round=3)
    second = get_bootstrap_result(battles, compute_mle_elo, num_round=3)
    pd.testing.assert_frame_equal(first, second)
