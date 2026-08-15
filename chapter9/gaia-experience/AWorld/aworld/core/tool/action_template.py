# coding: utf-8
# Copyright (c) 2025 inclusionAI.

# need action's name, desc, tool_name and func/async_func

ACTION_TEMPLATE = """
import traceback
from typing import Tuple, Any, List, Dict

from aworld.core.common import ActionModel, ActionResult
from aworld.core.tool.action import ExecutableAction
from aworld.core.tool.action_factory import ActionFactory
from aworld.logs.util import logger
from aworld.utils.async_func import async_func


@ActionFactory.register(name="{name}",
                        desc="{desc}",
                        tool_name="{tool_name}")
class {name}Act(ExecutableAction):
    # only for function to tool.
    def act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        try:
            res = {func}(**action.params)
            if not res:
                raise ValueError(f"{func} no result return.")
            return ActionResult(content=res, success=True), None
        except Exception as e:
            logger.error(traceback.format_exc())
            return ActionResult(content=str(e), error=str(e)), None
        

    async def async_act(self, action: ActionModel, **kwargs) -> Tuple[ActionResult, Any]:
        try:
            res = await {call_func}(**action.params)
            if not res:
                raise ValueError(f"{func} no result return.")
            return ActionResult(content=res, success=True), None
        except Exception as e:
            logger.error(traceback.format_exc())
            return ActionResult(content=str(e), error=str(e)), None
"""
