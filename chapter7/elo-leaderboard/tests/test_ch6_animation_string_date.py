"""Regression test for prepare_animation_data with string or date objects in history_df."""
import pandas as pd
from animation import prepare_animation_data


def test_prepare_animation_data_string_date():
    """prepare_animation_data must handle string dates without raising AttributeError."""
    history = pd.DataFrame([
        {
            "date": "2024-08-01",
            "model": "model_a",
            "rating": 1050.0,
            "rank": 1,
            "matches": 10,
            "wins": 7.0,
        },
        {
            "date": "2024-08-01",
            "model": "model_b",
            "rating": 950.0,
            "rank": 2,
            "matches": 10,
            "wins": 3.0,
        },
    ])
    data = prepare_animation_data(history, top_n=2)
    assert data["total_frames"] == 1
    assert data["start_date"] == "2024-08-01"
    assert data["end_date"] == "2024-08-01"
    assert len(data["frames"]) == 1
    assert data["frames"][0]["date"] == "2024-08-01"
    assert data["frames"][0]["timestamp"] == 1722470400
