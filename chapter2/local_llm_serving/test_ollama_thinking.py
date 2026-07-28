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


if __name__ == "__main__":
    test_streaming_yields_ollama_thinking_field()
    print("ok")
