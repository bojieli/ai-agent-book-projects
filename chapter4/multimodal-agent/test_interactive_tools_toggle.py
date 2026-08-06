"""Regression tests for the interactive multimodal tools toggle."""

import asyncio
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import MultimodalAgent, MultimodalTools
from main import interactive_chat


def _run_commands(agent, *commands):
    with patch("builtins.input", side_effect=commands):
        asyncio.run(interactive_chat(agent))


def test_tools_on_configures_complete_tool_state():
    agent = MultimodalAgent(enable_tools=False)

    _run_commands(agent, "/tools on", "/quit")

    assert agent.enable_multimodal_tools is True
    assert isinstance(agent.tools, MultimodalTools)
    assert {
        definition["function"]["name"] for definition in agent.tool_definitions
    } == {"analyze_image", "analyze_audio", "analyze_pdf"}


def test_tools_off_disables_tool_execution():
    agent = MultimodalAgent(enable_tools=True)

    _run_commands(agent, "/tools off", "/quit")

    assert agent.enable_multimodal_tools is False
    assert agent.tools is None
