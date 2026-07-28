"""detect_pii must treat JSON null pii_values like an empty list."""
import json
import sys
import types
from unittest.mock import patch

sys.modules.setdefault("ollama", types.ModuleType("ollama"))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

from agent import LogSanitizationAgent


def test_null_pii_values_returns_empty_list():
    agent = object.__new__(LogSanitizationAgent)
    agent.count_tokens = lambda text: len(text) // 4
    agent._chat_stream = lambda messages: iter(
        [json.dumps({"pii_values": None})]
    )

    with patch("builtins.print"):
        pii_values, metrics = agent.detect_pii("Alice phone 555-0100")

    assert pii_values == []
    assert metrics["pii_items_found"] == 0


def test_list_pii_values_still_cleaned():
    agent = object.__new__(LogSanitizationAgent)
    agent.count_tokens = lambda text: len(text) // 4
    agent._chat_stream = lambda messages: iter(
        [json.dumps({"pii_values": ["  Alice  ", "-", "Bob"]})]
    )

    with patch("builtins.print"):
        pii_values, metrics = agent.detect_pii("text")

    assert pii_values == ["Alice", "Bob"]
    assert metrics["pii_items_found"] == 2
