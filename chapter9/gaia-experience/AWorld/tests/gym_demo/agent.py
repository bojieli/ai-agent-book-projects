# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from typing import Any, Dict, Union, List

from examples.common.tools.common import Tools
from aworld.config.conf import AgentConfig, ConfigDict
from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel


class GymDemoAgent(Agent):
    """Example agent"""

    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, AgentConfig], **kwargs):
        super(GymDemoAgent, self).__init__(conf=conf, **kwargs)

    def policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> Union[
        List[ActionModel], None]:
        import numpy as np

        env_id = observation.info.get('env_id')
        if env_id and env_id != 'CartPole-v1':
            raise ValueError("Unsupported env")

        res = np.random.randint(2)
        action = [ActionModel(agent_name=self.id(), tool_name=Tools.GYM.value, action_name="play", params={"result": res})]
        if observation.info.get("done"):
            self._finished = True
        return action

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> Union[
        List[ActionModel], None]:
        return self.policy(observation, info, **kwargs)
