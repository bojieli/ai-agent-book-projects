"""Regression: head_limit=-1 must mean unlimited, not stop after first hit."""
from pathlib import Path


def test_source_treats_negative_head_limit_as_unlimited():
    src = Path(__file__).resolve().parents[1] / "tools" / "grep_tool.py"
    text = src.read_text()
    assert "if head_limit is not None and head_limit < 0:" in text
    assert "head_limit = None" in text.split("head_limit < 0:")[1][:80]
