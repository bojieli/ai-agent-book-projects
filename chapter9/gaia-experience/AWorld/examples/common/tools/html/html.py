# coding: utf-8

from aworld.tools.template_tool import TemplateTool
from examples.common.tools.tool_action import WriteAction
from aworld.core.tool.base import ToolFactory


@ToolFactory.register(name="html", desc="html tool", supported_action=WriteAction)
class HtmlTool(TemplateTool):
    """Html tool"""
