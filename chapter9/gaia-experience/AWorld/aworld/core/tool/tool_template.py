# coding: utf-8
# Copyright (c) 2025 inclusionAI.

# need tool's name, desc and cls params
TOOL_TEMPLATE = """
import json
from typing import List, Tuple, Dict, Any, Union

from aworld.config.conf import ToolConfig, ConfigDict
from aworld.core.tool.base import Tool, AsyncTool, ToolFactory
from aworld.core.common import Observation, ActionModel, ActionResult
from aworld.logs.util import logger
from aworld.tools.utils import build_observation


@ToolFactory.register(name="{name}", desc="{desc}", supported_action={action})
class {name}Tool({cls}):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, ToolConfig], **kwargs) -> None:
        super().__init__(conf, **kwargs)

    {async_flag}def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
        Observation, dict[str, Any]]:
        # from options obtain user query
        return build_observation(observer=self.name(),
                                 ability=''), dict()

    {async_flag}def do_step(self, action: List[ActionModel], **kwargs) -> Tuple[Observation, float, bool, bool, Dict[str, Any]]:
        reward = 0
        fail_error = ""
        action_result = None

        invalid_acts: List[int] = []
        for i, act in enumerate(action):
            if act.tool_name != "{name}":
                invalid_acts.append(i)

        if invalid_acts:
            for i in invalid_acts:
                action[i] = None

        resp = ""
        try:
            action_result, resp = {await_flag}self.action_executor.{async_underline}execute_action(action, **kwargs)
            reward = 1
        except Exception as e:
            fail_error = str(e)

        terminated = kwargs.get("terminated", False)
        if action_result:
            for res in action_result:
                if res.is_done:
                    terminated = res.is_done

        info = dict()
        info['exception'] = fail_error
        info.update(kwargs)
        if resp:
            resp = json.dumps(resp)
        else:
            resp = action_result[0].content

        action_result = [ActionResult(content=resp, keep=True, is_done=True)]
        observation = build_observation(observer=self.name(),
                                        ability=action[-1].action_name,
                                        content=resp,
                                        info=info)
        observation.action_result = action_result
        self._finished = True
        return (observation,
                reward,
                terminated,
                kwargs.get("truncated", False),
                dict())

    {async_flag}def close(self) -> None:
        pass

    {async_flag}def finished(self) -> bool:
        # one time
        return True
"""
