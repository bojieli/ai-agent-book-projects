"""
Malformed tool-argument JSON must not abort execute_research or cause real dispatch to raise TypeError.
"""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

# Optional deps used at import time by web_tools.
sys.modules.setdefault("html2text", types.ModuleType("html2text"))
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compression_strategies import CompressionStrategy
from agent import ResearchAgent


def test_execute_research_survives_malformed_tool_arguments_json():
    with patch("agent.Config.resolve_llm", return_value=("k", "http://x", "m")), \
         patch("agent.OpenAI"), \
         patch("agent.WebTools") as mock_web_tools_cls, \
         patch("agent.ContextCompressor"):
        
        mock_web_tools = MagicMock()
        mock_web_tools_cls.return_value = mock_web_tools
        
        agent = ResearchAgent(
            api_key="k",
            compression_strategy=CompressionStrategy.NO_COMPRESSION,
            verbose=False,
            enable_streaming=False,
        )

    bad_call_search = {
        "id": "call-bad-search",
        "type": "function",
        "function": {
            "name": "search_web",
            "arguments": '{"query": "openai",}',  # trailing comma
        },
    }
    bad_call_fetch = {
        "id": "call-bad-fetch",
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "arguments": '{"url": "https://example.com",}',  # malformed JSON
        },
    }
    tool_msg = {"role": "assistant", "content": "searching", "tool_calls": [bad_call_search, bad_call_fetch]}
    final_msg = {"role": "assistant", "content": "FINAL ANSWER: ok", "tool_calls": None}

    agent._non_streaming_response = MagicMock(side_effect=[tool_msg, final_msg])

    # Do NOT mock _execute_tool, let real dispatch run over missing query/url arguments
    result = agent.execute_research(max_iterations=3)

    assert result.get("error") is None
    assert len(agent.trajectory.tool_calls) == 2
    assert agent.trajectory.tool_calls[0].result == {"error": "Missing required argument 'query' for search_web"}
    assert agent.trajectory.tool_calls[1].result == {"error": "Missing required argument 'url' for fetch_webpage"}

def test_execute_research_survives_non_dict_and_invalid_bytes_tool_arguments():
    """
    Non-dict JSON structures (lists, numbers) and invalid UTF-8 bytes must normalize to {} and not raise.
    """
    with patch("agent.Config.resolve_llm", return_value=("k", "http://x", "m")), \
         patch("agent.OpenAI"), \
         patch("agent.WebTools") as mock_web_tools_cls, \
         patch("agent.ContextCompressor"):
        
        mock_web_tools = MagicMock()
        mock_web_tools_cls.return_value = mock_web_tools
        
        agent = ResearchAgent(
            api_key="k",
            compression_strategy=CompressionStrategy.NO_COMPRESSION,
            verbose=False,
            enable_streaming=False,
        )

    non_dict_calls = [
        {"id": "c1", "type": "function", "function": {"name": "search_web", "arguments": "[]"}},
        {"id": "c2", "type": "function", "function": {"name": "fetch_webpage", "arguments": "123"}},
        {"id": "c3", "type": "function", "function": {"name": "search_web", "arguments": b"\x80\xff"}},
        {"id": "c4", "type": "function", "function": {"name": "fetch_webpage", "arguments": {"invalid": 1}}},
    ]
    tool_msg = {"role": "assistant", "content": "searching", "tool_calls": non_dict_calls}
    final_msg = {"role": "assistant", "content": "FINAL ANSWER: ok", "tool_calls": None}

    agent._non_streaming_response = MagicMock(side_effect=[tool_msg, final_msg])

    result = agent.execute_research(max_iterations=3)

    assert result.get("error") is None
    assert len(agent.trajectory.tool_calls) == 4
    assert agent.trajectory.tool_calls[0].arguments == {}
    assert agent.trajectory.tool_calls[1].arguments == {}
    assert agent.trajectory.tool_calls[2].arguments == {}
    assert agent.trajectory.tool_calls[3].arguments == {"invalid": 1}
    assert agent.trajectory.tool_calls[0].result == {"error": "Missing required argument 'query' for search_web"}
    assert agent.trajectory.tool_calls[1].result == {"error": "Missing required argument 'url' for fetch_webpage"}


def test_execute_research_survives_tool_execution_exceptions():
    """
    Tool execution exceptions in search_web or fetch_webpage must return error dicts with compressed=None and not abort loop.
    """
    with patch("agent.Config.resolve_llm", return_value=("k", "http://x", "m")), \
         patch("agent.OpenAI"), \
         patch("agent.WebTools") as mock_web_tools_cls, \
         patch("agent.ContextCompressor"):
        
        mock_web_tools = MagicMock()
        mock_web_tools.search_web.side_effect = RuntimeError("network connection failed")
        mock_web_tools.fetch_webpage.side_effect = RuntimeError("http 500 error")
        mock_web_tools_cls.return_value = mock_web_tools
        
        agent = ResearchAgent(
            api_key="k",
            compression_strategy=CompressionStrategy.NO_COMPRESSION,
            verbose=False,
            enable_streaming=False,
        )

    call_search = {"id": "c1", "type": "function", "function": {"name": "search_web", "arguments": '{"query": "test"}'}}
    call_fetch = {"id": "c2", "type": "function", "function": {"name": "fetch_webpage", "arguments": '{"url": "http://test.com"}'}}
    tool_msg = {"role": "assistant", "content": "searching", "tool_calls": [call_search, call_fetch]}
    final_msg = {"role": "assistant", "content": "FINAL ANSWER: ok", "tool_calls": None}

    agent._non_streaming_response = MagicMock(side_effect=[tool_msg, final_msg])

    result = agent.execute_research(max_iterations=3)

    assert result.get("error") is None
    assert len(agent.trajectory.tool_calls) == 2
    assert agent.trajectory.tool_calls[0].result == {"error": "Failed to execute search_web: network connection failed"}
    assert agent.trajectory.tool_calls[0].compressed_result is None
    assert agent.trajectory.tool_calls[1].result == {"error": "Failed to execute fetch_webpage: http 500 error"}
    assert agent.trajectory.tool_calls[1].compressed_result is None
