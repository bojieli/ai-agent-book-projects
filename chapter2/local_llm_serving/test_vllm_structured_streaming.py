"""Focused tests for fragmented structured tool calls in VLLMToolAgent.chat_stream."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from agent import VLLMToolAgent


def _chunk(content=None, tool_calls=None):
    delta = SimpleNamespace(content=content, tool_calls=tool_calls or [])
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def _fragment(index, *, call_id=None, name=None, arguments=None):
    return SimpleNamespace(
        index=index,
        id=call_id,
        type="function" if call_id else None,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _agent_with_streams(*streams):
    agent = VLLMToolAgent.__new__(VLLMToolAgent)
    agent.conversation_history = []
    agent.tool_registry = MagicMock()
    agent.tool_registry.get_tool_schemas.return_value = []
    agent._format_system_prompt_with_tools = MagicMock(return_value="system")
    agent.client = MagicMock()
    agent.client.chat.completions.create.side_effect = [iter(stream) for stream in streams]
    return agent


def test_stream_assembles_fragmented_parallel_tool_calls():
    agent = _agent_with_streams(
        [
            _chunk(tool_calls=[
                _fragment(0, call_id="call_weather", name="get_", arguments='{"city":'),
                _fragment(1, call_id="call_time", name="get_time", arguments="{"),
            ]),
            _chunk(tool_calls=[
                _fragment(0, name="weather", arguments='"Paris"}'),
                _fragment(1, arguments="}"),
            ]),
        ],
        [_chunk(content="Done")],
    )
    agent._execute_single_tool = MagicMock(
        side_effect=lambda call: (f'{call["name"]} result', False)
    )

    events = list(agent.chat_stream("Use both tools"))

    assert events == [
        {"type": "tool_call", "content": {"name": "get_weather", "arguments": {"city": "Paris"}}},
        {"type": "tool_call", "content": {"name": "get_time", "arguments": {}}},
        {"type": "tool_result", "content": "get_weather result"},
        {"type": "tool_result", "content": "get_time result"},
        {"type": "content", "content": "Done"},
    ]
    assert agent._execute_single_tool.call_count == 2

    create_calls = agent.client.chat.completions.create.call_args_list
    assert [call.kwargs["model"] for call in create_calls] == [
        "Qwen/Qwen3-0.6B",
        "Qwen/Qwen3-0.6B",
    ]
    second_turn_messages = create_calls[1].kwargs["messages"]
    assistant_message = next(message for message in second_turn_messages if message.get("tool_calls"))
    assert assistant_message["tool_calls"] == [
        {
            "id": "call_weather",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"city":"Paris"}'},
        },
        {
            "id": "call_time",
            "type": "function",
            "function": {"name": "get_time", "arguments": "{}"},
        },
    ]


def test_stream_reports_malformed_arguments_and_continues():
    agent = _agent_with_streams(
        [_chunk(tool_calls=[
            _fragment(0, call_id="call_bad", name="bad_tool", arguments="{bad")
        ])],
        [_chunk(content="Recovered")],
    )
    agent._execute_single_tool = MagicMock()

    events = list(agent.chat_stream("Try the tool"))

    assert [event["type"] for event in events] == ["tool_error", "content"]
    assert events[-1] == {"type": "content", "content": "Recovered"}
    agent._execute_single_tool.assert_not_called()
    error_message = next(
        message for message in agent.conversation_history
        if message.get("name") == "bad_tool"
    )
    assert "Tool call parse exception" in error_message["content"]
