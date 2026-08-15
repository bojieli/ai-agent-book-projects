# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import List, Dict, Any

from aworld.core.exceptions import AWorldRuntimeException

from aworld.core.agent.swarm import Swarm
from aworld.core.task import Task, TaskResponse
from aworld.utils.run_util import exec_tasks

from aworld.agents.llm_agent import Agent
from aworld.core.common import Observation, ActionModel


class TaskAgent(Agent):
    """Support for swarm execution of in the hybrid nested swarm."""

    def __init__(self,
                 swarm: Swarm,
                 **kwargs):
        super().__init__(**kwargs)
        self.swarm = swarm
        if not self.swarm:
            raise AWorldRuntimeException("no swarm in task agent.")

    def reset(self, options: Dict[str, Any] = None):
        super().reset(options)
        if not options:
            self.swarm.reset()
        else:
            self.swarm.reset(options.get("task"), options.get("context"), options.get("tools"))

    async def async_policy(self, observation: Observation, info: Dict[str, Any] = {}, **kwargs) -> List[ActionModel]:
        self._finished = False
        task = Task(input=observation.content, swarm=self.swarm)
        results = await exec_tasks([task])
        res = []
        for key, result in results.items():
            # result is TaskResponse
            if result.success:
                info = result.answer
            else:
                info = result.msg
            res.append(ActionModel(agent_name=self.id(), policy_info=info))

        self._finished = True
        return res
