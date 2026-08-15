# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from typing import List
from aworld.core.tool.action_factory import ActionFactory
from aworld.core.common import ActionModel, ActionResult
from aworld.logs.util import logger
from examples.common.tools.android.action.adb_controller import ADBController
from aworld.core.tool.base import ToolActionExecutor


class AndroidToolActionExecutor(ToolActionExecutor):

    def __init__(self, controller: ADBController):
        self.controller = controller

    def execute_action(self, actions: List[ActionModel], **kwargs) -> list[ActionResult]:
        """Execute the specified android action sequence by agent policy.

        Args:
            actions: Tool action sequence.

        Returns:
            Browser action result list.
        """
        action_results = []
        for action in actions:
            action_result = self._exec(action, **kwargs)
            action_results.append(action_result)
        return action_results

    def _exec(self, action_model: ActionModel, **kwargs):
        action_name = action_model.action_name
        if action_name not in ActionFactory:
            action_name = action_model.tool_name + action_model.action_name
            if action_name not in ActionFactory:
                raise ValueError(f'Action {action_name} not found')

        action = ActionFactory(action_name)
        action_result = action.act(action_model, controller=self.controller, **kwargs)
        logger.info(f"{action_name} execute finished")
        return action_result
