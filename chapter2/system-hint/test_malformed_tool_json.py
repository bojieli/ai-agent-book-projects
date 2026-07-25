"""Regression: malformed tool-argument JSON must not abort the ReAct loop."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from agent import SystemHintAgent, SystemHintConfig


def test_execute_task_survives_malformed_tool_arguments_json():
    config = SystemHintConfig(
        enable_timestamps=False,
        enable_tool_counter=False,
        enable_todo_list=False,
        enable_detailed_errors=False,
        enable_system_state=False,
        save_trajectory=False,
    )
    agent = SystemHintAgent(
        api_key="test-key",
        provider="kimi",
        config=config,
        verbose=False,
    )

    bad_call = SimpleNamespace(
        id="call-bad",
        function=SimpleNamespace(
            name="read_file",
            arguments='{"file_path": "x.txt",}',  # trailing comma
        ),
    )
    tool_msg = SimpleNamespace(
        content=None,
        tool_calls=[bad_call],
        model_dump=lambda: {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-bad",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": '{"file_path": "x.txt",}',
                    },
                }
            ],
        },
    )
    final_msg = SimpleNamespace(
        content="FINAL ANSWER: recovered",
        tool_calls=None,
        model_dump=lambda: {
            "role": "assistant",
            "content": "FINAL ANSWER: recovered",
        },
    )
    tool_turn = SimpleNamespace(choices=[SimpleNamespace(message=tool_msg)])
    final_turn = SimpleNamespace(choices=[SimpleNamespace(message=final_msg)])
    agent.client = MagicMock()
    agent.client.chat.completions.create = MagicMock(
        side_effect=[tool_turn, final_turn]
    )

    result = agent.execute_task("read something", max_iterations=5)

    assert "error" not in result or result.get("error") is None
    assert result.get("final_answer") == "recovered" or "recovered" in str(
        result.get("final_answer") or result
    )
    tool_roles = [m for m in agent.conversation_history if m.get("role") == "tool"]
    assert tool_roles
    assert "Invalid tool arguments" in tool_roles[0]["content"]
    assert agent.client.chat.completions.create.call_count == 2
