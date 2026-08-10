import importlib.util
import os
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

_module_path = (
    Path(__file__).resolve().parent.parent / "chapter1" / "search-codegen" / "agent.py"
)
_spec = importlib.util.spec_from_file_location("search_codegen_agent", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
GPT5NativeAgent = _module.GPT5NativeAgent


def test_output_text_handles_null_response():
    """Contract: _output_text returns empty string for None or non-dict response."""
    assert GPT5NativeAgent._output_text(None) == ""
    assert GPT5NativeAgent._output_text([]) == ""
    assert GPT5NativeAgent._output_text("invalid") == ""


def test_tool_items_handles_null_response():
    """Contract: _tool_items returns empty list for None or non-dict response."""
    assert GPT5NativeAgent._tool_items(None) == []
    assert GPT5NativeAgent._tool_items(42) == []


def test_citations_handles_null_response():
    """Contract: _citations returns empty list for None or non-dict response."""
    assert GPT5NativeAgent._citations(None) == []
    assert GPT5NativeAgent._citations(True) == []


def test_process_request_handles_null_response_body():
    """Contract: process_request handles status 200 with None response without raising AttributeError."""
    agent = GPT5NativeAgent(api_key="test-key")
    agent._post_responses = MagicMock(return_value=(200, None, None))

    result = agent.process_request("hello", dry_run=False)

    assert result["success"] is False
    assert result["error"] == {"type": "http_error", "message": "Empty response"}
    assert result["response"] is None
    assert result["tool_calls"] == []
    assert result["citations"] == []
    assert result["usage"] == {}
