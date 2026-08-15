"""Empty rating history must not crash analyze_rating_changes / get_rating_history."""
import pandas as pd

from animation import prepare_animation_data
from leaderboard import (
    analyze_rating_changes,
    build_historical_leaderboards,
    get_rating_history,
)


def test_get_rating_history_empty_keeps_columns():
    hist = build_historical_leaderboards(
        pd.DataFrame(columns=["model_a", "model_b", "winner"]),
        [(pd.Timestamp("2020-01-01"), pd.DataFrame(columns=["model_a", "model_b", "winner"]))],
    )
    rh = get_rating_history(hist)
    assert list(rh.columns) == ["date", "model", "rating", "rank", "matches", "wins"]
    assert len(rh) == 0


def test_analyze_empty_history_returns_empty_frame():
    empty = pd.DataFrame(columns=["date", "model", "rating", "rank", "matches", "wins"])
    stats = analyze_rating_changes(empty)
    assert len(stats) == 0
    assert "model" in stats.columns


def test_analyze_after_empty_historical_leaderboards():
    hist = build_historical_leaderboards(
        pd.DataFrame(columns=["model_a", "model_b", "winner"]),
        [(pd.Timestamp("2020-01-01"), pd.DataFrame(columns=["model_a", "model_b", "winner"]))],
    )
    rh = get_rating_history(hist)
    stats = analyze_rating_changes(rh)
    assert len(stats) == 0
    anim = prepare_animation_data(rh)
    assert anim["frames"] == []
    assert anim["total_frames"] == 0
