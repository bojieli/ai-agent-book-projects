# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
from typing import List, Dict, Any, Callable

from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel
from aworld.core.event.base import Message
from aworld.utils.run_util import exec_agent


class ParallelizableAgent(Agent):
    """Support for parallel agents in the swarm.

    The parameters of the extension function are the agent itself, which can obtain internal information of the agent.
    `aggregate_func` function example:
    >>> def agg(agent: ParallelizableAgent, res: Dict[str, Any]) -> ActionModel:
    >>>     ...
    """

    def __init__(self,
                 agents: List[Agent] = None,
                 aggregate_func: Callable[['ParallelizableAgent', Dict[str, Any]], ActionModel] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.agents = agents if agents else []
        # The function of aggregating the results of the parallel execution of agents.
        self.aggregate_func = aggregate_func

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> List[ActionModel]:
        tasks = []
        if self.agents:
            for agent in self.agents:
                tasks.append(asyncio.create_task(exec_agent(observation.content, agent, self.context, sub_task=True)))

        results = await asyncio.gather(*tasks)
        res = []
        for idx, result in enumerate(results):
            if result.success:
                con = result.answer
            else:
                con = result.msg
            res.append(ActionModel(agent_name=self.agents[idx].id(), policy_info=con))

        if self.aggregate_func:
            res = [self.aggregate_func(self, {action.agent_name: action.policy_info for action in res})]
        return res

    async def _agent_result(self, actions: List[ActionModel], caller: str, input_message: Message):
        if self.aggregate_func:
            return super()._agent_result(actions, caller, input_message)

        if not actions:
            raise Exception(f'{self.id()} no action decision has been made.')

        action = ActionModel(agent_name=self.id(),
                             policy_info={action.agent_name: action.policy_info for action in actions})
        return Message(payload=[action],
                       caller=caller,
                       sender=self.id(),
                       receiver=actions[0].tool_name,
                       category=self.event_handler_name,
                       session_id=input_message.context.session_id if input_message.context else "",
                       headers=self._update_headers(input_message))

    def finished(self) -> bool:
        return all([agent.finished for agent in self.agents])
