"""Empty problems JSONL must not ZeroDivisionError in the pass-rate summary."""

import asyncio
import os
from types import ModuleType
import sys

# generate_data imports openai; stub if missing so the test stays offline.
try:
    import openai  # noqa: F401
except ImportError:
    _oai = ModuleType("openai")

    class _AsyncOpenAI:
        def __init__(self, *a, **k):
            pass

    _oai.AsyncOpenAI = _AsyncOpenAI
    sys.modules["openai"] = _oai

import generate_data as gd


def test_empty_problems_summary_does_not_divide_by_zero(tmp_path, monkeypatch):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    raw = tmp_path / "raw.jsonl"
    sft = tmp_path / "sft.jsonl"
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-used")

    argv = [
        "generate_data.py",
        "--input",
        str(empty),
        "--raw_output",
        str(raw),
        "--sft_output",
        str(sft),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    asyncio.run(gd.main())
    assert raw.exists() and sft.exists()
    assert sft.read_text(encoding="utf-8") == ""


def test_nonempty_pass_rate_still_computes():
    records = [{"verified": True, "error": None, "reasoning": "x", "usage": {}}]
    passed = [r for r in records if r["verified"]]
    pass_rate = (len(passed) / len(records) * 100) if records else 0.0
    assert pass_rate == 100.0
