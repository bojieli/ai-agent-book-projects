"""Regression tests for issue #493's cross-session history leak."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conversational_agent import ConversationConfig, ConversationalAgent
from conversation_history import ConversationHistory, ConversationTurn


class StubMemoryManager:
    def __init__(self, context: str):
        self.context = context
        self.load_count = 0

    def load_memory(self):
        self.load_count += 1

    def get_context_string(self) -> str:
        return self.context


def make_agent(history: ConversationHistory, session_id: str):
    """Build the prompt-only portion of an agent without an API client."""
    agent = ConversationalAgent.__new__(ConversationalAgent)
    agent.config = ConversationConfig()
    agent.memory_manager = StubMemoryManager("Preferred editor: VS Code")
    agent.conversation_history = history
    agent.session_id = session_id
    return agent


def test_memory_context_excludes_raw_turns_from_previous_sessions():
    history = ConversationHistory.__new__(ConversationHistory)
    history.conversations = [
        ConversationTurn(
            "session-old",
            "My private detail from the old session",
            "I will remember that detail",
            "2026-07-28T10:00:00",
            1,
        ),
        ConversationTurn(
            "session-current",
            "What did we discuss in this session?",
            "We discussed the current task",
            "2026-07-29T10:00:00",
            2,
        ),
    ]
    agent = make_agent(history, "session-current")

    context = agent._get_memory_context()

    assert "Preferred editor: VS Code" in context
    assert "=== CURRENT SESSION HISTORY ===" in context
    assert "What did we discuss in this session?" in context
    assert "My private detail from the old session" not in context
    assert "session-old" not in context


def test_new_session_uses_structured_memory_without_old_raw_history():
    history = ConversationHistory.__new__(ConversationHistory)
    history.conversations = [
        ConversationTurn(
            "session-old",
            "I work at TechCorp",
            "Thanks for sharing",
            "2026-07-28T10:00:00",
            1,
        )
    ]
    agent = make_agent(history, "session-new")

    context = agent._get_memory_context()

    assert "Preferred editor: VS Code" in context
    assert "I work at TechCorp" not in context
    assert "CURRENT SESSION HISTORY" not in context
    assert agent.memory_manager.load_count == 1
