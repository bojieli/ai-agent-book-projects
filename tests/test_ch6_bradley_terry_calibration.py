import pytest
pytest.importorskip("pandas")
"""
Test suite for compute_mle_elo calibration model and calibration rating handling.
"""

import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
ELO_DIR = HERE / "chapter6" / "elo-leaderboard"
if str(ELO_DIR) not in sys.path:
    sys.path.insert(0, str(ELO_DIR))

from bradley_terry import compute_mle_elo  # noqa: E402


def test_compute_mle_elo_calibration_model_default_none_rating():
    df = pd.DataFrame(
        [
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"},
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_b"},
        ]
    )
    res = compute_mle_elo(df, calibration_model="gpt-4")
    assert "gpt-4" in res.index
    assert res["gpt-4"] == 1000.0


def test_compute_mle_elo_explicit_calibration_rating():
    df = pd.DataFrame(
        [
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"},
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_b"},
        ]
    )
    res = compute_mle_elo(df, calibration_model="gpt-4", calibration_rating=1200.0)
    assert "gpt-4" in res.index
    assert abs(res["gpt-4"] - 1200.0) < 1e-6


def test_compute_mle_elo_custom_init_rating_and_calibration():
    df = pd.DataFrame(
        [
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"},
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_b"},
        ]
    )
    res = compute_mle_elo(df, INIT_RATING=1500, calibration_model="gpt-4")
    assert "gpt-4" in res.index
    assert res["gpt-4"] == 1500.0


def test_compute_mle_elo_calibration_model_not_in_df():
    df = pd.DataFrame(
        [
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"},
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_b"},
        ]
    )
    res = compute_mle_elo(df, calibration_model="non_existent_model")
    assert "gpt-4" in res.index
    assert "claude-3" in res.index


def test_compute_mle_elo_no_calibration():
    df = pd.DataFrame(
        [
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"},
            {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_b"},
        ]
    )
    res = compute_mle_elo(df, calibration_model=None)
    assert "gpt-4" in res.index
    assert "claude-3" in res.index
