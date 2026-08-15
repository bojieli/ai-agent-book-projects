# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import Any, Callable

from aworld.agents.llm_agent import Agent


class LoopableAgent(Agent):
    """Support for loop agents in the swarm.

    The parameters of the extension function are the agent itself, which can obtain internal information of the agent.
    `stop_func` function example:
    >>> def stop(agent: LoopableAgent):
    >>>     ...

    `loop_point_finder` function example:
    >>> def find(agent: LoopableAgent):
    >>>     ...
    """
    max_run_times: int = 1
    cur_run_times: int = 0
    # The loop agent special the loop point (agent name)
    loop_point: str = None
    # Used to determine the loop point for multiple loops
    loop_point_finder: Callable[..., Any] = None
    # def stop(agent: LoopableAgent): ...
    stop_func: Callable[..., Any] = None

    @property
    def goto(self):
        """The next loop point is what the loop agent wants to reach."""
        if self.loop_point_finder:
            return self.loop_point_finder(self)
        if self.loop_point:
            return self.loop_point
        return self.id()

    @property
    def finished(self) -> bool:
        """Loop agent termination state detection, achieved loop count or termination condition."""
        if self.cur_run_times >= self.max_run_times or (self.stop_func and self.stop_func(self)):
            self._finished = True
            return True

        self._finished = False
        return False
