# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from examples.common.tools.tool_action import DocumentExecuteAction
from aworld.core.tool.action_factory import ActionFactory
from aworld.core.tool.action import ExecutableAction


@ActionFactory.register(name=DocumentExecuteAction.DOCUMENT_ANALYSIS.value.name,
                        desc=DocumentExecuteAction.DOCUMENT_ANALYSIS.value.desc,
                        tool_name="document_analysis")
class ExecuteAction(ExecutableAction):
    """Only one action, define it, implemented can be omitted. Act in tool."""
