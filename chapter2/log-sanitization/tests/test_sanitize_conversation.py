#!/usr/bin/env python3
"""Regression tests for sanitize_conversation() in agent.py.

Bug: detect_pii() catches any backend exception and returns ([], {}), but
sanitize_conversation then subscripted the empty metrics dict
(perf_metrics['input_tokens']) -> KeyError that killed the whole batch.
Fixed with .get(..., 0) defaults so a dead backend degrades gracefully.
"""

import pytest

from agent import LogSanitizationAgent
from metrics import MetricsCollector


def _make_agent(client, tmp_path):
    """Build an agent without __init__ (which requires a live Ollama)."""
    ag = LogSanitizationAgent.__new__(LogSanitizationAgent)
    ag.model = "qwen3:0.6b"
    ag.backend = "ollama"
    ag.metrics_collector = MetricsCollector(tmp_path)
    ag.client = client
    return ag


CONV = {
    "conversation_id": "demo_001",
    "messages": [{"role": "user", "content": "My SSN is 123-45-6789."}],
}


class _DeadClient:
    def chat(self, **kwargs):
        raise ConnectionError("[test] Ollama server is not running")


class _FakeClient:
    """Mimics ollama.Client.chat(stream=True) chunk shape."""

    def __init__(self, payload: str):
        self.payload = payload

    def chat(self, **kwargs):
        return [{"message": {"content": self.payload}}]


def test_dead_backend_returns_result_with_zero_metrics(tmp_path):
    ag = _make_agent(_DeadClient(), tmp_path)
    result = ag.sanitize_conversation(CONV, "t1")  # must not raise
    assert result["pii_found"] == []
    assert result["replacements_made"] == 0
    assert result["metrics"]["input_tokens"] == 0
    assert result["metrics"]["pii_items_found"] == 0


def test_working_backend_still_detects_pii(tmp_path):
    ag = _make_agent(_FakeClient('{"pii_values": ["123-45-6789"]}'), tmp_path)
    result = ag.sanitize_conversation(CONV, "t1")
    assert result["pii_found"] == ["123-45-6789"]
    assert result["replacements_made"] == 1
    assert "[REDACTED]" in result["sanitized_text"]
    assert result["metrics"]["pii_items_found"] == 1
