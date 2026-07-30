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

    bad_call = {
        "id": "call-bad",
        "type": "function",
        "function": {
            "name": "search_web",
            "arguments": '{"query": "openai",}',  # trailing comma
        },
    }
    tool_msg = {"role": "assistant", "content": "searching", "tool_calls": [bad_call]}
    final_msg = {"role": "assistant", "content": "FINAL ANSWER: ok", "tool_calls": None}

    agent._non_streaming_response = MagicMock(side_effect=[tool_msg, final_msg])

    # Do NOT mock _execute_tool, let real dispatch run over missing query arguments
    result = agent.execute_research(max_iterations=3)

    assert result.get("error") is None
    assert len(agent.trajectory.tool_calls) == 1
    assert agent.trajectory.tool_calls[0].result == {"error": "Missing required argument 'query' for search_web"}
