"""Regression: prepare_animation_data must tolerate empty history."""
import pandas as pd
from animation import prepare_animation_data


def test_empty_history_returns_empty_frames():
    df = pd.DataFrame(columns=["date", "model", "rating", "rank", "matches", "wins"])
    data = prepare_animation_data(df)
    assert data["frames"] == []
    assert data["total_frames"] == 0
    assert data["start_date"] is None
