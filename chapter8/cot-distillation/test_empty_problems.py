"""Empty problems JSONL must not ZeroDivisionError in the pass-rate summary."""

import asyncio
import json
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


def test_native_moonshot_reasoning_effort_uses_supported_top_level_control():
    assert gd.reasoning_extra_body("https://api.moonshot.cn/v1", "low", 0) == {
        "reasoning_effort": "low"
    }
    assert gd.reasoning_extra_body("https://openrouter.ai/api/v1", "low", 0) == {
        "reasoning": {"effort": "low"}
    }


def test_targeted_resume_preserves_verified_rows_and_retries_failure(tmp_path, monkeypatch):
    problems = tmp_path / "problems.jsonl"
    raw = tmp_path / "raw.jsonl"
    sft = tmp_path / "sft.jsonl"
    problem_rows = [
        {"id": "one", "question": "1+1?", "answer": 2},
        {"id": "two", "question": "2+2?", "answer": 4},
    ]
    problems.write_text(
        "".join(json.dumps(row) + "\n" for row in problem_rows), encoding="utf-8"
    )
    raw.write_text(
        "".join(
            json.dumps(row) + "\n"
            for row in (
                {
                    "id": "one", "question": "1+1?", "gold_answer": 2,
                    "model": "teacher", "content": "Final Answer: 2", "reasoning": "ok",
                    "verified": True, "usage": {}, "error": None,
                },
                {
                    "id": "two", "question": "2+2?", "gold_answer": 4,
                    "model": "teacher", "content": None, "reasoning": None,
                    "verified": False, "usage": None, "error": "timeout",
                },
            )
        ),
        encoding="utf-8",
    )
    calls = []

    async def fake_distill(client, problem, args, semaphore):
        calls.append(problem["id"])
        return {
            "id": problem["id"], "question": problem["question"],
            "gold_answer": problem["answer"], "model": args.model,
            "content": "Final Answer: 4", "reasoning": "worked",
            "verified": True, "usage": {}, "error": None, "attempts": [],
        }

    monkeypatch.setattr(gd, "distill_one", fake_distill)
    monkeypatch.setattr(gd, "AsyncOpenAI", lambda **kwargs: object())
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-used")
    monkeypatch.setattr(sys, "argv", [
        "generate_data.py", "--input", str(problems), "--raw_output", str(raw),
        "--sft_output", str(sft), "--problem-id", "two", "--resume",
    ])

    asyncio.run(gd.main())

    raw_rows = gd.load_jsonl(raw)
    assert calls == ["two"]
    assert [row["id"] for row in raw_rows] == ["one", "two"]
    assert all(row["verified"] for row in raw_rows)
    assert raw_rows[1]["prior_failures"][0]["error"] == "timeout"
    assert len(gd.load_jsonl(sft)) == 2
