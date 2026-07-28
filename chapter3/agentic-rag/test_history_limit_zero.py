"""conversation_history_limit=0 must omit history, not include all via [-0:]."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from agent import AgenticRAG


def test_history_limit_zero_omits_history():
    agent = object.__new__(AgenticRAG)
    agent.config = SimpleNamespace(
        agent=SimpleNamespace(conversation_history_limit=0)
    )
    agent._get_system_prompt = lambda: "sys"
    agent.conversation_history = [
        {"role": "user", "content": "old1"},
        {"role": "assistant", "content": "old2"},
    ]
    msgs = agent._build_messages("new question")
    assert msgs == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "new question"},
    ]


def test_positive_history_limit_still_keeps_tail():
    agent = object.__new__(AgenticRAG)
    agent.config = SimpleNamespace(
        agent=SimpleNamespace(conversation_history_limit=1)
    )
    agent._get_system_prompt = lambda: "sys"
    agent.conversation_history = [
        {"role": "user", "content": "old1"},
        {"role": "assistant", "content": "old2"},
    ]
    msgs = agent._build_messages("new question")
    assert msgs == [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "old2"},
        {"role": "user", "content": "new question"},
    ]
