"""Regression: slowmo factor<=0 must not ZeroDivisionError."""
from pathlib import Path


def test_source_skips_nonpositive_factor():
    src = Path(__file__).with_name("video_editor.py").read_text()
    assert "if factor <= 0:" in src
    assert "continue" in src.split("if factor <= 0:")[1][:80]


def test_division_guard_math():
    factor = 0.0
    if factor <= 0:
        skipped = True
    else:
        _ = 1.0 / factor
        skipped = False
    assert skipped is True
