"""Empty battles JSON array [] must load as an empty battle frame."""
import json
from pathlib import Path

import cli


def test_load_battles_empty_json_array(tmp_path):
    path = tmp_path / "battles.json"
    path.write_text("[]", encoding="utf-8")
    df = cli._load_battles(str(path))
    assert list(df.columns) == ["model_a", "model_b", "winner"]
    assert len(df) == 0


def test_load_battles_nonempty_still_requires_columns(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"x": 1}]), encoding="utf-8")
    try:
        cli._load_battles(str(path))
        assert False, "expected ValueError"
    except ValueError as e:
        assert "model_a" in str(e)


def test_load_battles_normal(tmp_path):
    path = tmp_path / "ok.json"
    path.write_text(
        json.dumps([{"model_a": "A", "model_b": "B", "winner": "model_a"}]),
        encoding="utf-8",
    )
    df = cli._load_battles(str(path))
    assert len(df) == 1
    assert df.iloc[0]["winner"] == "model_a"
