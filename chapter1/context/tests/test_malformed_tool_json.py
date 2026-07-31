"""Regression: malformed tool-argument JSON must not abort the ReAct loop."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from agent import ContextAwareAgent, ContextMode


def _choice(*, content=None, tool_calls=None):
    msg = SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
        reasoning_content=None,
        model_dump=lambda: {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in (tool_calls or [])
            ],
        },
    )
    return SimpleNamespace(message=msg)


def test_execute_task_survives_malformed_tool_arguments_json():
    agent = ContextAwareAgent("test-key", ContextMode.FULL, verbose=False)
    bad_call = SimpleNamespace(
        id="call-bad",
        function=SimpleNamespace(
            name="calculate",
            arguments='{"expression": "1+1",}',  # trailing comma
        ),
    )
    tool_turn = SimpleNamespace(choices=[_choice(tool_calls=[bad_call])])
    final_turn = SimpleNamespace(
        choices=[_choice(content="FINAL ANSWER: recovered")]
    )
    agent.client = MagicMock()
    agent.client.chat.completions.create = MagicMock(
        side_effect=[tool_turn, final_turn]
    )

    result = agent.execute_task("compute", max_iterations=5)

    assert result.get("error") is None
    assert "recovered" in (result.get("final_answer") or result.get("answer") or "")
    tool_roles = [m for m in agent.conversation_history if m.get("role") == "tool"]
    assert tool_roles
    assert "Invalid tool arguments" in tool_roles[0]["content"]
    assert agent.client.chat.completions.create.call_count == 2
