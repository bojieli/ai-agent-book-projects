from __future__ import annotations

import json
import copy
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import GeneratedAgent


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(
                id="call-1",
                function=SimpleNamespace(
                    name="lookup_domain_fact",
                    arguments=json.dumps({"query": "purpose"}),
                ),
            )
            message = SimpleNamespace(content=None, tool_calls=[tool_call])
        else:
            assert kwargs["messages"][-1]["role"] == "tool"
            message = SimpleNamespace(content="Verified answer", tool_calls=[])
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=3)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def test_standard_tool_loop_keeps_assistant_call_and_tool_result():
    completions = FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    result = GeneratedAgent(model="test-model", client=client).run("What is your purpose?")
    assert result["ok"] is True
    assert result["answer"] == "Verified answer"
    second_messages = completions.calls[1]["messages"]
    assert second_messages[-2]["role"] == "assistant"
    assert second_messages[-2]["tool_calls"][0]["id"] == "call-1"
    assert second_messages[-1]["role"] == "tool"
    assert second_messages[-1]["tool_call_id"] == "call-1"
    assert result["messages"][:-1] == second_messages
    assert result["messages"][-1] == {
        "role": "assistant",
        "content": "Verified answer",
    }
    assert result["usage"] == {
        "prompt_tokens": 20,
        "cached_prompt_tokens": 0,
        "completion_tokens": 6,
        "requests": 2,
    }


def test_prior_multiturn_history_is_preserved_in_order():
    completions = FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    history = [
        {"role": "user", "content": "Remember owner Mei-Lin."},
        {"role": "assistant", "content": "Owner Mei-Lin retained."},
    ]

    result = GeneratedAgent(model="test-model", client=client).run(
        "Evaluate the release.", history=history
    )

    first_messages = completions.calls[0]["messages"]
    assert first_messages[1:3] == history
    assert result["messages"][1:3] == history
