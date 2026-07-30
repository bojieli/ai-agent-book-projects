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


def test_working_backend_with_structured_pii_items(tmp_path):
    conv = {
        "conversation_id": "demo_002",
        "messages": [
            {
                "role": "user",
                "content": "My SSN is 000-00-0000 and my card is 0000-0000-0000-0000.",
            }
        ],
    }
    payload = (
        '{"pii_items": ['
        '{"type": "social_security_number", "value": "000-00-0000"}, '
        '{"type": "credit_card_number", "value": "0000-0000-0000-0000"}'
        ']}'
    )
    ag = _make_agent(_FakeClient(payload), tmp_path)
    result = ag.sanitize_conversation(conv, "t2")
    assert result["pii_found"] == ["000-00-0000", "0000-0000-0000-0000"]
    assert result["replacements_made"] == 2
    assert result["sanitized_text"].count("[REDACTED]") == 2
    assert result["metrics"]["pii_items_found"] == 2


def test_structured_pii_items_preserve_original_value(tmp_path):
    conv = {
        "conversation_id": "demo_003",
        "messages": [
            {
                "role": "user",
                "content": "The secret is -abc- and the password is   p4ss  .",
            }
        ],
    }
    payload = (
        '{"pii_items": ['
        '{"type": "secret", "value": "-abc-"}, '
        '{"type": "password", "value": "  p4ss  "}'
        ']}'
    )
    ag = _make_agent(_FakeClient(payload), tmp_path)
    result = ag.sanitize_conversation(conv, "t3")
    assert result["pii_found"] == ["-abc-", "  p4ss  "]
    assert result["replacements_made"] == 2
    assert result["sanitized_text"].count("[REDACTED]") == 2


def test_pii_items_metric_excludes_rejected_and_malformed_items(tmp_path):
    conv = {
        "conversation_id": "demo_004",
        "messages": [
            {
                "role": "user",
                "content": "My email is alice@example.com.",
            }
        ],
    }
    payload = (
        '{"pii_items": ['
        '{"type": "email", "value": "alice@example.com"}, '
        '{"type": "ssn", "value": "999-99-9999"}, '
        '{"type": "unknown", "value": ""}, '
        '{"type": "broken"}, '
        '"just a string"'
        ']}'
    )
    ag = _make_agent(_FakeClient(payload), tmp_path)
    result = ag.sanitize_conversation(conv, "t4")
    assert result["pii_found"] == ["alice@example.com"]
    assert result["replacements_made"] == 1
    assert result["metrics"]["pii_items_found"] == 1
    items = result["pii_items"]
    assert len(items) == 1
    assert items[0]["type"] == "email"
    assert items[0]["value"] == "alice@example.com"
