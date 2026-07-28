"""Unit tests for ReAct formatting, tools, and the agent loop."""

from unittest.mock import Mock

import agent as agent_module
from agent import WebSearchAgent, _reasoning_safe_temperature, format_trace_step


def build_agent(*choices):
    """Create an Agent without constructing a real OpenAI client."""
    instance = WebSearchAgent.__new__(WebSearchAgent)
    instance.verbose = False
    instance.using_openrouter = False
    instance.trace = []
    instance.conversation_history = []
    instance._chat = Mock(side_effect=choices)
    return instance


def test_format_trace_step_formats_action_with_unicode_arguments():
    rendered = format_trace_step(
        {
            "iteration": 2,
            "type": "action",
            "tool": "$web_search",
            "args": {"query": "서울 날씨"},
        }
    )

    assert rendered == (
        '🔧 [2] 行动: 调用工具 $web_search  参数={"query": "서울 날씨"}'
    )


def test_format_trace_step_truncates_long_content():
    rendered = format_trace_step(
        {"iteration": 1, "type": "thought", "content": "abcdef"},
        max_len=3,
    )

    assert rendered == "💭 [1] 思考: abc…（省略 3 字）"


def test_reasoning_models_force_supported_temperature():
    assert _reasoning_safe_temperature("kimi-k3", 0.2) == 1
    assert _reasoning_safe_temperature("openai/gpt-5.6-luna", 0.2) == 1
    assert _reasoning_safe_temperature("deepseek-chat", 0.2) == 0.2


def test_tool_definition_is_available_for_moonshot_only():
    instance = WebSearchAgent.__new__(WebSearchAgent)
    instance.using_openrouter = False

    assert instance._get_tools() == [
        {
            "type": "builtin_function",
            "function": {"name": "$web_search"},
        }
    ]

    instance.using_openrouter = True
    assert instance._get_tools() == []


def test_agent_loop_records_tool_flow_and_final_answer(
    monkeypatch, make_choice, make_tool_call
):
    tool_call = make_tool_call(arguments={"query": "Moonshot caching"})
    tool_choice = make_choice(
        finish_reason="tool_calls",
        reasoning_content="공식 설명을 검색해야 한다.",
        tool_calls=[tool_call],
    )
    answer_choice = make_choice(content="Context Caching 설명입니다.")
    instance = build_agent(tool_choice, answer_choice)
    search = Mock(return_value={"query": "Moonshot caching"})
    monkeypatch.setattr(agent_module, "search_impl", search)

    answer = instance.search_and_answer("Context Caching이 뭐야?")

    assert answer == "Context Caching 설명입니다."
    assert [step["type"] for step in instance.get_trace()] == [
        "thought",
        "action",
        "observation",
        "answer",
    ]
    search.assert_called_once_with({"query": "Moonshot caching"})
    assert instance._chat.call_count == 2
    assert instance.conversation_history[2] == {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "$web_search",
                    "arguments": '{"query": "Moonshot caching"}',
                },
            }
        ],
    }
    assert instance.conversation_history[3] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "name": "$web_search",
        "content": '{"query": "Moonshot caching"}',
    }
    assert instance.conversation_history[-1] == {
        "role": "assistant",
        "content": answer,
    }


def test_agent_loop_handles_multiple_tool_calls(make_choice, make_tool_call):
    first = make_tool_call(arguments={"query": "first"}, call_id="call-1")
    second = make_tool_call(arguments={"query": "second"}, call_id="call-2")
    instance = build_agent(
        make_choice(finish_reason="tool_calls", tool_calls=[first, second]),
        make_choice(content="combined answer"),
    )

    assert instance.search_and_answer("compare") == "combined answer"
    assert [step["type"] for step in instance.get_trace()] == [
        "action",
        "observation",
        "action",
        "observation",
        "answer",
    ]
    tool_messages = [
        message
        for message in instance.conversation_history
        if message["role"] == "tool"
    ]
    assert [message["tool_call_id"] for message in tool_messages] == [
        "call-1",
        "call-2",
    ]


def test_agent_loop_stops_at_iteration_limit(make_choice, make_tool_call):
    instance = build_agent(
        make_choice(
            finish_reason="tool_calls",
            tool_calls=[make_tool_call()],
        )
    )

    answer = instance.search_and_answer("keep searching", max_iterations=1)

    assert answer == "抱歉，搜索过程超过了最大迭代次数，请稍后重试。"
    assert instance._chat.call_count == 1


def test_agent_loop_returns_a_readable_error():
    instance = build_agent()
    instance._chat = Mock(side_effect=RuntimeError("provider unavailable"))

    answer = instance.search_and_answer("question")

    assert answer == "搜索过程中出现错误: provider unavailable"
    assert instance.get_trace() == []


def test_agent_loop_marks_truncated_empty_answer(make_choice):
    """finish_reason=length with empty content must not masquerade as
    the misleading 'couldn't get enough info' response."""
    instance = build_agent(make_choice(finish_reason="length", content=""))

    answer = instance.search_and_answer("question")

    assert "无法获取足够" not in answer
    assert "截断" in answer
    assert instance.get_trace()[-1]["type"] == "answer"


def test_agent_loop_marks_truncated_partial_answer(make_choice):
    """A partial answer cut off by max_tokens is returned WITH a truncation
    marker, never presented as a complete answer."""
    instance = build_agent(
        make_choice(finish_reason="length", content="部分答案，被截")
    )

    answer = instance.search_and_answer("question")

    assert answer.startswith("部分答案，被截")
    assert "截断" in answer
    # conversation_history retains the truncation marker (stores final, not the
    # bare partial), so get_conversation_history() doesn't lose the semantics.
    assert instance.conversation_history[-1]["role"] == "assistant"
    assert "截断" in instance.conversation_history[-1]["content"]


def test_agent_loop_survives_malformed_tool_arguments_json(monkeypatch, make_choice):
    """Slightly invalid tool JSON must not abort the ReAct loop."""
    from types import SimpleNamespace

    bad_call = SimpleNamespace(
        id="call-bad",
        function=SimpleNamespace(
            name="$web_search",
            arguments='{"query": "moonshot",}',  # trailing comma
        ),
    )
    tool_choice = make_choice(finish_reason="tool_calls", tool_calls=[bad_call])
    answer_choice = make_choice(content="recovered answer")
    instance = build_agent(tool_choice, answer_choice)
    search = Mock(return_value={"ok": True})
    monkeypatch.setattr(agent_module, "search_impl", search)

    answer = instance.search_and_answer("what is caching?")

    assert answer == "recovered answer"
    search.assert_called_once_with({})
    assert any(step["type"] == "action" for step in instance.get_trace())
