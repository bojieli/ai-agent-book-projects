#!/usr/bin/env python3
"""Regression tests for the local LLM serving benchmark."""

from types import SimpleNamespace
from unittest.mock import patch

from benchmark import stream_once


class FakeCompletions:
    def __init__(self, chunks):
        self.chunks = chunks

    def create(self, **kwargs):
        return iter(self.chunks)


def make_client(chunks):
    completions = FakeCompletions(chunks)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def run_reasoning_stream(field):
    delta = SimpleNamespace(**{field: "Thinking about the answer."})
    chunks = [
        SimpleNamespace(
            usage=None,
            choices=[SimpleNamespace(delta=delta)],
        ),
        SimpleNamespace(
            usage=SimpleNamespace(completion_tokens=8),
            choices=[],
        ),
    ]

    with patch("benchmark.time.perf_counter", side_effect=[0.0, 0.25, 1.0]):
        return stream_once(
            make_client(chunks),
            model="qwen3:0.6b",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=8,
            temperature=0.0,
        )


def test_stream_once_uses_reasoning_chunks_for_ttft():
    for field in ("reasoning_content", "reasoning"):
        result = run_reasoning_stream(field)

        assert result["ttft"] == 0.25, field
        assert result["total"] == 1.0, field
        assert result["output_tokens"] == 8.0, field
        assert result["decode_tps"] == 8.0 / 0.75, field
