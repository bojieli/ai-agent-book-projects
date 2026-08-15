# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from typing import Tuple, List, Any

from aworld.core.tool.action_factory import ActionFactory
from aworld.core.common import ActionModel, ActionResult, Observation
from aworld.logs.util import logger
from aworld.core.tool.base import Tool, ToolActionExecutor


class BrowserToolActionExecutor(ToolActionExecutor):
    def __init__(self, tool: Tool = None):
        super(BrowserToolActionExecutor, self).__init__(tool)

    def execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[
        List[ActionResult], Any]:
        """Execute the specified browser action sequence by agent policy.

        Args:
            actions: Tool action sequence.

        Returns:
            Browser page and action result list.
        """
        action_results = []
        page = self.tool.page
        for action in actions:
            action_result, page = self._exec(action, **kwargs)
            action_results.append(action_result)
        return action_results, page

    async def async_execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[
        List[ActionResult], Any]:
        """Execute the specified browser action sequence by agent policy.

        Args:
            actions: Tool action sequence.

        Returns:
            Browser page and action result list.
        """
        action_results = []
        page = self.tool.page
        for action in actions:
            action_result, page = await self._async_exec(action, **kwargs)
            action_results.append(action_result)
        return action_results, page

    def _exec(self, action_model: ActionModel, **kwargs):
        action_name = action_model.action_name
        if action_name not in ActionFactory:
            raise ValueError(f'Action {action_name} not found')

        action = ActionFactory(action_name)
        action_result, page = action.act(action_model, page=self.tool.page, browser=self.tool.browser_context, **kwargs)
        logger.info(f"{action_name} execute finished")
        return action_result, page

    async def _async_exec(self, action_model: ActionModel, **kwargs):
        action_name = action_model.action_name
        if action_name not in ActionFactory:
            action_name = action_model.tool_name + action_model.action_name
            if action_name not in ActionFactory:
                raise ValueError(f'Action {action_name} not found')

        action = ActionFactory(action_name)
        action_result, page = await action.async_act(action_model, page=self.tool.page,
                                                     browser=self.tool.browser_context, **kwargs)
        logger.info(f"{action_name} execute finished")
        return action_result, page
