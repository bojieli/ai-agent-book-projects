"""Regression: negative -B/-A/-C must not wipe matches via empty ranges."""
from pathlib import Path


def test_source_clamps_context():
    src = Path(__file__).resolve().parents[1] / "tools" / "grep_tool.py"
    text = src.read_text()
    assert "context_before = max(0, int(context_before))" in text
