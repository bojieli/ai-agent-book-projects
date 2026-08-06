"""Regression tests: _execute_tool must return an error string to the model
instead of raising KeyError/JSONDecodeError on malformed LLM tool-call
arguments (missing required fields or truncated streamed JSON)."""
import asyncio
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import MultimodalAgent


def _make_agent():
    """Build a MultimodalAgent without __init__ (which needs API keys)."""
    agent = MultimodalAgent.__new__(MultimodalAgent)
    calls = []

    async def fake_analyze(path, query):
        calls.append((path, query))
        return "analysis ok"

    agent.tools = types.SimpleNamespace(
        analyze_image=fake_analyze,
        analyze_audio=fake_analyze,
        analyze_pdf=fake_analyze,
    )
    return agent, calls


def _run(agent, name, arguments):
    tool_call = {"id": "call_1", "function": {"name": name, "arguments": arguments}}
    return asyncio.run(agent._execute_tool(tool_call))


def test_missing_query_returns_error_not_keyerror():
    agent, calls = _make_agent()
    result = _run(agent, "analyze_image", json.dumps({"image_path": "cat.png"}))
    assert result.startswith("Error:")
    assert calls == []


def test_missing_path_returns_error_not_keyerror():
    agent, calls = _make_agent()
    result = _run(agent, "analyze_pdf", json.dumps({"query": "what is this?"}))
    assert result.startswith("Error:")
    assert calls == []


def test_malformed_json_returns_error_not_exception():
    agent, calls = _make_agent()
    result = _run(agent, "analyze_audio", '{"audio_path": "a.mp3", "que')
    assert result.startswith("Error:")
    assert calls == []


def test_valid_arguments_still_call_tool():
    agent, calls = _make_agent()
    result = _run(agent, "analyze_image", json.dumps({"image_path": "cat.png", "query": "describe"}))
    assert result == "analysis ok"
    assert calls == [("cat.png", "describe")]


def test_unknown_tool_still_reported():
    agent, _ = _make_agent()
    result = _run(agent, "analyze_video", json.dumps({}))
    assert "Unknown tool" in result
