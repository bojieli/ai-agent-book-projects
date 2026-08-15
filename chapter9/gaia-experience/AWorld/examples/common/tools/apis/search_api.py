# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from pathlib import Path

from aworld.core.tool.base import ToolFactory
from aworld.tools.template_tool import TemplateTool
from examples.common.tools.tool_action import SearchAction


@ToolFactory.register(name="search_api",
                      desc="search tool",
                      supported_action=SearchAction,
                      conf_file_name=f'search_api_tool.yaml',
                      dir=f"{Path(__file__).parent.absolute()}")
class SearchTool(TemplateTool):
    """Search Tool"""
