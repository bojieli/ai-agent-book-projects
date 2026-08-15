# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import json
from typing import List, Tuple, Dict, Any

from aworld.core.tool.base import AsyncTool
from aworld.core.common import Observation, ActionModel, Config
from aworld.logs.util import logger
from aworld.tools.utils import build_observation


class TemplateTool(AsyncTool):
    def __init__(self, conf: Config, **kwargs) -> None:
        super(TemplateTool, self).__init__(conf, **kwargs)

    async def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
        Observation, dict[str, Any]]:
        # from options obtain user query
        return build_observation(observer=self.name(),
                                 ability='',
                                 content=options.get("query", None) if options else None), {}

    async def do_step(self,
                      action: List[ActionModel],
                      **kwargs) -> Tuple[Observation, float, bool, bool, Dict[str, Any]]:
        reward = 0
        fail_error = ""
        action_result = None

        invalid_acts: List[int] = []
        for i, act in enumerate(action):
            if act.tool_name != self.name():
                logger.warning(f"tool {act.tool_name} is not a {self.name()} tool!")
                invalid_acts.append(i)

        if invalid_acts:
            for i in invalid_acts:
                action[i] = None

        resp = ""
        try:
            action_result, resp = await self.action_executor.async_execute_action(action, **kwargs)
            reward = 1
        except Exception as e:
            fail_error = str(e)

        terminated = kwargs.get("terminated", False)
        for res in action_result:
            if res.is_done:
                terminated = res.is_done
                self._finished = True

        info = {"exception": fail_error}
        info.update(kwargs)
        if resp:
            resp = json.dumps(resp)
        else:
            resp = action_result[0].content

        observation = build_observation(observer=self.name(),
                                        action_result=action_result,
                                        ability=action[-1].action_name,
                                        content=resp)
        return (observation,
                reward,
                terminated,
                kwargs.get("truncated", False),
                info)

    async def close(self) -> None:
        pass

    async def finished(self) -> bool:
        # one time
        return True
