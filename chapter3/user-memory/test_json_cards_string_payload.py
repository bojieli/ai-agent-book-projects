"""Regression test for JSON cards tool payload parsing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import UserMemoryAgent
from config import MemoryMode


def test_json_cards_add_memory_parses_stringified_json():
    captured = {}

    class FakeMemoryManager:
        def add_memory(self, content, session_id, **kwargs):
            captured["content"] = content
            captured["session_id"] = session_id
            return "banking.first_national.checking_account_number"

    agent = UserMemoryAgent.__new__(UserMemoryAgent)
    agent.config = type("Cfg", (), {"memory_mode": MemoryMode.JSON_CARDS})()
    agent.memory_manager = FakeMemoryManager()
    agent.session_id = "session-test"

    result = agent._tool_add_memory(
        content='{"category": "banking", "subcategory": "first_national", "key": "checking_account_number", "value": "4429853327"}'
    )

    assert captured["session_id"] == "session-test"
    assert captured["content"] == {
        "category": "banking",
        "subcategory": "first_national",
        "key": "checking_account_number",
        "value": "4429853327",
    }
    assert result["success"] is True
    assert result["memory_id"] == "banking.first_national.checking_account_number"
