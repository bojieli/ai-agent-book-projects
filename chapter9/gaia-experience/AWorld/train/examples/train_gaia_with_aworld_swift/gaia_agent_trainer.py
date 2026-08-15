# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import Union

from aworld.agents.llm_agent import Agent
from aworld.core.agent.swarm import Swarm
from train.adapter.swift.aworld_agent_trainer import AworldTrainer

GAIA_SYSTEM_PROMPT = """
You are an all-capable AI assistant, aimed at solving any task presented by the user.
"""


class GaiaTrainer(AworldTrainer):
    def build_agents(self) -> Union[Agent, Swarm]:
        return Agent(
            name="gaia_super_agent",
            system_prompt=GAIA_SYSTEM_PROMPT,
        )
