"""Regression: negative size must read to EOF, not drop a suffix."""
import sys
import types
from pathlib import Path


def _stub():
    sys.modules.setdefault("openai", types.ModuleType("openai"))
    sys.modules["openai"].OpenAI = object
    # other optional deps
    for name in ["openrouter_fallback"]:
        sys.modules.setdefault(name, types.ModuleType(name))


_stub()

from agent import LocalFileTools  # noqa: E402


def test_negative_size_reads_all(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a\nb\nc\n", encoding="utf-8")
    tools = LocalFileTools(str(tmp_path))
    out = tools.read_file("a.txt", offset=0, size=-1)
    assert out["success"] is True
    assert out["content"] == "a\nb\nc\n"
    assert out["lines_read"] == 3
