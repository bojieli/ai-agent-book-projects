"""Regression tests for providers that end streams with ``choices=[]``."""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import UserMemoryAgent
from conversational_agent import ConversationConfig, ConversationalAgent


class StubCompletions:
    def create(self, **kwargs):
        return [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(delta=SimpleNamespace(content="Hello"))
                ]
            ),
            SimpleNamespace(choices=[]),
        ]


def stub_client():
    return SimpleNamespace(
        chat=SimpleNamespace(completions=StubCompletions())
    )


def test_conversational_agent_ignores_empty_choices_chunk():
    agent = ConversationalAgent.__new__(ConversationalAgent)
    agent.config = ConversationConfig(
        enable_memory_context=False,
        enable_conversation_history=False,
    )
    agent.verbose = False
    agent.model = "test-model"
    agent.client = stub_client()
    agent.conversation = []
    agent.conversation_history = None
    agent.session_id = "session-test"

    assert agent.chat("Hi") == "Hello"
    assert agent.conversation[-1] == {
        "role": "assistant",
        "content": "Hello",
    }


def test_user_memory_agent_ignores_empty_choices_chunk():
    agent = UserMemoryAgent.__new__(UserMemoryAgent)
    agent._get_memory_context = lambda: ""
    agent.model = "test-model"
    agent.client = stub_client()
    agent.conversation = []
    agent.conversation_history = None
    agent.session_id = "session-test"

    assert agent._chat_stream("Hi") == "Hello"
    assert agent.conversation[-1] == {
        "role": "assistant",
        "content": "Hello",
    }
