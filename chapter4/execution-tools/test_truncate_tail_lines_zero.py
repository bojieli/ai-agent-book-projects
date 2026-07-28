"""tail_lines=0 must keep no tail lines (Python lines[-0:] quirk)."""
from execution_tools import truncate_and_persist


def test_tail_lines_zero_keeps_only_head():
    text = "\n".join(f"line{i}" for i in range(100))
    out, path = truncate_and_persist(
        text, head_lines=3, tail_lines=0, max_lines=10, max_chars=50
    )
    assert path is not None
    assert "line0" in out and "line1" in out and "line2" in out
    assert "line99" not in out
    assert "line50" not in out
    assert out.count("line0") == 1


def test_tail_lines_positive_still_keeps_tail():
    text = "\n".join(f"line{i}" for i in range(100))
    out, path = truncate_and_persist(
        text, head_lines=2, tail_lines=2, max_lines=10, max_chars=50
    )
    assert path is not None
    assert "line0" in out and "line1" in out
    assert "line98" in out and "line99" in out
    assert "line50" not in out


def test_short_file_char_overflow_does_not_duplicate_lines():
    text = ("x" * 4000 + "\n") * 3
    out, path = truncate_and_persist(
        text, head_lines=50, tail_lines=50, max_lines=200, max_chars=100
    )
    assert path is not None
    # Three content lines plus the guide line — no head/tail duplication.
    content_lines = [ln for ln in out.split("\n") if ln.startswith("x")]
    assert len(content_lines) == 3
