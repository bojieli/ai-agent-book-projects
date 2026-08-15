# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from aworld.core.tool.action_factory import ActionFactory
from aworld.core.tool.action import ExecutableAction
from aworld.tools.tool_action import HumanExecuteAction


@ActionFactory.register(name=HumanExecuteAction.HUMAN_CONFIRM.value.name,
                        desc=HumanExecuteAction.HUMAN_CONFIRM.value.desc,
                        tool_name="human_confirm")
class ExecuteAction(ExecutableAction):
    """Only one action, define it, implemented can be omitted. Act in tool."""
