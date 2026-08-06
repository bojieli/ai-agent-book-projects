import pytest
"""
Test suite verifying choke-point fix for SystemHintAgent handling
None / empty / non-string error fields in tool results.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "chapter2" / "system-hint"))
from agent import SystemHintAgent


def _create_mock_agent(execute_return_value):
    agent = SystemHintAgent(api_key="mock_key", verbose=True)

    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "custom_tool"
    mock_tool_call.function.arguments = '{"param": "val"}'

    mock_message = MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "custom_tool", "arguments": '{"param": "val"}'},
            }
        ],
    }
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])

    agent._execute_tool = MagicMock(return_value=execute_return_value)

    mock_message_end = MagicMock(content="FINAL ANSWER: Done", tool_calls=None)
    mock_message_end.model_dump.return_value = {
        "role": "assistant",
        "content": "FINAL ANSWER: Done",
    }
    mock_choice_end = MagicMock(message=mock_message_end)
    mock_response_end = MagicMock(choices=[mock_choice_end])

    agent.client.chat.completions.create = MagicMock(
        side_effect=[mock_response, mock_response_end]
    )

    return agent


def test_system_hint_agent_handles_none_error_in_tool_result(caplog):
    agent = _create_mock_agent(({"success": False, "error": None}, None, 15.0))
    with caplog.at_level(logging.INFO):
        result = agent.execute_task("Perform test task")

    assert "error" not in result or "TypeError" not in result["error"]
    assert result.get("success") is True
    assert any("⚠️ Failed: Unknown error" in record.message for record in caplog.records)


def test_system_hint_agent_handles_empty_string_error_in_tool_result(caplog):
    agent = _create_mock_agent(({"success": False, "error": ""}, None, 15.0))
    with caplog.at_level(logging.INFO):
        result = agent.execute_task("Perform test task")

    assert result.get("success") is True
    assert any("⚠️ Failed: Unknown error" in record.message for record in caplog.records)


def test_system_hint_agent_handles_valid_error_string(caplog):
    agent = _create_mock_agent(({"success": False, "error": "Disk read timeout"}, None, 15.0))
    with caplog.at_level(logging.INFO):
        result = agent.execute_task("Perform test task")

    assert result.get("success") is True
    assert any("⚠️ Failed: Disk read timeout" in record.message for record in caplog.records)
