"""Regression: negative Read.limit must not silently drop a file suffix."""
from pathlib import Path

from tools.read_tool import ReadTool
from system_state import SystemState


def test_negative_limit_reads_to_eof(tmp_path: Path):
    path = tmp_path / "f.txt"
    path.write_text("\n".join(f"L{i}" for i in range(1, 11)) + "\n")
    tool = ReadTool(SystemState(current_directory=str(tmp_path)))
    out = tool._read_text(path, offset=0, limit=-1)
    assert "L10" in out["content"]
