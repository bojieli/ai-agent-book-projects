"""prepare_animation_data must keep fractional wins from Elo ties."""
import pandas as pd
from animation import prepare_animation_data


def test_tie_half_wins_are_not_truncated():
    history = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-07", "2024-01-07"]),
            "model": ["A", "B"],
            "rating": [1000.0, 1000.0],
            "rank": [1, 2],
            "matches": [1, 1],
            "wins": [0.5, 0.5],
        }
    )
    data = prepare_animation_data(history, top_n=2)
    wins = {m["name"]: m["wins"] for m in data["frames"][0]["models"]}
    assert wins["A"] == 0.5
    assert wins["B"] == 0.5


def test_whole_wins_still_serialize():
    history = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-07"]),
            "model": ["A"],
            "rating": [1010.0],
            "rank": [1],
            "matches": [2],
            "wins": [2.0],
        }
    )
    data = prepare_animation_data(history, top_n=1)
    assert data["frames"][0]["models"][0]["wins"] == 2.0
