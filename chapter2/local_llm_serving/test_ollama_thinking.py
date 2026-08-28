#!/usr/bin/env python3
"""Regression tests for Ollama thinking stream handling."""

import sys
import types


fake_ollama_module = types.ModuleType("ollama")
setattr(fake_ollama_module, "Client", lambda: None)
sys.modules.setdefault("ollama", fake_ollama_module)

from ollama_native import OllamaNativeAgent


class FakeOllamaClient:
    def chat(self, **kwargs):
        self.last_kwargs = kwargs
        return iter([
            {"message": {"thinking": "Need current data. "}},
            {"message": {"content": "Final answer."}},
        ])


class FakeToolCallingClient:
    def __init__(self, stream):
        self.stream = stream
        self.calls = 0
        self.message_snapshots = []

    def chat(self, **kwargs):
        self.calls += 1
        self.message_snapshots.append([message.copy() for message in kwargs["messages"]])
        if self.calls == 1:
            message = {
                "thinking": "I need two tools.",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "first_tool", "arguments": {"value": 1}}},
                    {"function": {"name": "second_tool", "arguments": {"value": 2}}},
                ],
            }
        else:
            message = {"thinking": "Both results are ready.", "content": "Done."}
        return iter([{"message": message}]) if self.stream else {"message": message}


def test_streaming_yields_ollama_thinking_field():
    agent = OllamaNativeAgent(model="qwen3:0.6b")
    fake_client = FakeOllamaClient()
    agent.client = fake_client

    chunks = list(agent.chat_stream("hello", use_tools=False, temperature=0.1))

    assert fake_client.last_kwargs.get("think") is True

    thinking_event = {"type": "thinking", "content": "Need current data. "}
    content_event = {"type": "content", "content": "Final answer."}

    assert thinking_event in chunks
    assert content_event in chunks

    # Verify ordering: thinking must be emitted before final content
    assert chunks.index(thinking_event) < chunks.index(content_event), \
        f"thinking (at index {chunks.index(thinking_event)}) should come " \
        f"before content (at index {chunks.index(content_event)})"


def test_streaming_history_preserves_assistant_turn_before_tool_results():
    agent = OllamaNativeAgent(model="qwen3:0.6b")
    agent.client = FakeToolCallingClient(stream=True)
    agent._execute_tool_calls = lambda _calls: ["first result", "second result"]

    chunks = list(agent.chat_stream("use both tools"))

    assert [message["role"] for message in agent.conversation_history] == [
        "user", "assistant", "tool", "tool", "assistant"
    ]
    assert agent.conversation_history[1] == {
        "role": "assistant",
        "content": "",
        "thinking": "I need two tools.",
        "tool_calls": [
            {"function": {"name": "first_tool", "arguments": {"value": 1}}},
            {"function": {"name": "second_tool", "arguments": {"value": 2}}},
        ],
    }
    assert agent.conversation_history[2:4] == [
        {"role": "tool", "tool_name": "first_tool", "content": "first result"},
        {"role": "tool", "tool_name": "second_tool", "content": "second result"},
    ]
    assert agent.conversation_history[4] == {
        "role": "assistant",
        "content": "Done.",
        "thinking": "Both results are ready.",
    }
    assert agent.client.message_snapshots[1] == agent.conversation_history[:4]
    assert [chunk["content"] for chunk in chunks if chunk["type"] == "tool_result"] == [
        "first result", "second result"
    ]


def test_non_streaming_history_preserves_thinking_and_tool_names():
    agent = OllamaNativeAgent(model="qwen3:0.6b")
    agent.client = FakeToolCallingClient(stream=False)
    agent._execute_tool_calls = lambda _calls: ["first result", "second result"]

    response = agent.chat("use both tools")

    assert response == "Done."
    assert [message["role"] for message in agent.conversation_history] == [
        "user", "assistant", "tool", "tool", "assistant"
    ]
    assert agent.conversation_history[1]["thinking"] == "I need two tools."
    assert len(agent.conversation_history[1]["tool_calls"]) == 2
    assert [message["tool_name"] for message in agent.conversation_history[2:4]] == [
        "first_tool", "second_tool"
    ]
    assert agent.conversation_history[4] == {
        "role": "assistant",
        "content": "Done.",
        "thinking": "Both results are ready.",
    }
    assert agent.client.message_snapshots[1] == agent.conversation_history[:4]


if __name__ == "__main__":
    test_streaming_yields_ollama_thinking_field()
    print("ok")
