# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio

from aworld.config import RunConfig

from aworld.config.conf import AgentConfig
from aworld.core.task import Task
from aworld.runner import Runners
from tests.gym_demo.agent import GymDemoAgent as GymAgent


async def main():
    agent = GymAgent(name="gym_agent", conf=AgentConfig(), tool_names=["gym"], feedback_tool_result=True)
    # It can also be used `ToolFactory` for simplification.
    task = Task(agent=agent,
                tools_conf={"gym": {"env_id": "CartPole-v1", "render_mode": "human", "render": True, "use_async": True}})
    res = await Runners.run_task(task=task, run_conf=RunConfig())


if __name__ == "__main__":
    # We use it as a showcase to demonstrate the framework's scalability.
    asyncio.run(main())
