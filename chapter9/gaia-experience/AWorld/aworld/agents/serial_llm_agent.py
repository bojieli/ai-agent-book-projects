# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import List, Dict, Any, Callable

from aworld.core.event.base import Message

from aworld.utils.run_util import exec_agent

from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel, Config
from aworld.logs.util import logger


class SerialableAgent(Agent):
    """Support for serial execution of agents based on dependency relationships in the swarm.

    The parameters of the extension function are the agent itself, which can obtain internal information of the agent.
    `aggregate_func` function example:
    >>> def agg(agent: SerialableAgent, res: Dict[str, Any]) -> ActionModel:
    >>>     ...
    >>>     return ActionModel(agent_name=agent.id(), policy_info='...')
    """

    def __init__(self,
                 agents: List[Agent] = None,
                 aggregate_func: Callable[['SerialableAgent', Dict[str, Any]], ActionModel] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.agents = agents if agents else []
        self.aggregate_func = aggregate_func

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> List[ActionModel]:
        self.results = None
        results = {}
        action = ActionModel(agent_name=self.id(), policy_info=observation.content)
        if self.agents:
            for agent in self.agents:
                result = await exec_agent(observation.content, agent, self.context, sub_task=True)
                if result:
                    if result.success:
                        con = result.answer
                    else:
                        con = result.msg
                    action = ActionModel(agent_name=agent.id(), policy_info=con)
                    observation = self._action_to_observation(action, agent.id())
                    results[agent.id()] = con
                else:
                    raise Exception(f"{agent.id()} execute fail.")

        if self.aggregate_func:
            return [self.aggregate_func(self, results)]

        return [action]

    def _action_to_observation(self, policy: ActionModel, agent_name: str):
        if not policy:
            logger.warning("no agent policy, will use default error info.")
            return Observation(content=f"{agent_name} no policy")

        logger.debug(f"{policy.policy_info}")
        return Observation(content=policy.policy_info, observer=agent_name)

    def finished(self) -> bool:
        return all([agent.finished for agent in self.agents])
