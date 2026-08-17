import pytest
pytest.importorskip("pandas")

import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
ELO_DIR = HERE / "chapter7" / "elo-leaderboard"
if str(ELO_DIR) not in sys.path:
    sys.path.insert(0, str(ELO_DIR))

from bradley_terry import compute_mle_elo  # noqa: E402


def test_compute_mle_elo_single_model():
    df = pd.DataFrame([
        {"model_a": "gpt-4", "model_b": "gpt-4", "winner": "model_a"}
    ])
    res = compute_mle_elo(df)
    assert isinstance(res, pd.Series)
    assert len(res) == 1
    assert "gpt-4" in res.index
    assert res["gpt-4"] == 1000.0


def test_compute_mle_elo_single_model_custom_init_rating():
    df = pd.DataFrame([
        {"model_a": "claude-3", "model_b": "claude-3", "winner": "model_b"}
    ])
    res = compute_mle_elo(df, INIT_RATING=1500)
    assert isinstance(res, pd.Series)
    assert len(res) == 1
    assert "claude-3" in res.index
    assert res["claude-3"] == 1500.0


def test_compute_mle_elo_zero_unique_models():
    df = pd.DataFrame([], columns=["model_a", "model_b", "winner"])
    res = compute_mle_elo(df)
    assert isinstance(res, pd.Series)
    assert len(res) == 0


def test_compute_mle_elo_nan_model_names_multimodel():
    df = pd.DataFrame([
        {"model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"},
        {"model_a": None, "model_b": "claude-3", "winner": "model_b"},
        {"model_a": "gpt-4", "model_b": float("nan"), "winner": "model_a"},
    ])
    res = compute_mle_elo(df)
    assert isinstance(res, pd.Series)
    assert len(res) == 2
    assert "gpt-4" in res.index
    assert "claude-3" in res.index
