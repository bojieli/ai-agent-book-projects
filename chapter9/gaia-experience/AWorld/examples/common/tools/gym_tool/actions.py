# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from examples.common.tools.tool_action import GymAction
from aworld.core.tool.action_factory import ActionFactory
from aworld.core.tool.action import ExecutableAction


@ActionFactory.register(name=GymAction.PLAY.value.name,
                        desc=GymAction.PLAY.value.desc,
                        tool_name="openai_gym")
class Play(ExecutableAction):
    """"""