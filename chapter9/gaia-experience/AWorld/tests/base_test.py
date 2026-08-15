
import os
import random
import sys
import json
from pathlib import Path
from typing import Optional
import unittest

from aworld.core.context.prompts.string_prompt_template import StringPromptTemplate

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aworld.core.context.base import Context
from aworld.config.conf import AgentConfig, ContextRuleConfig, ModelConfig
from aworld.agents.llm_agent import Agent
from aworld.runner import Runners
from aworld.core.agent.swarm import Swarm, TeamSwarm
from aworld.core.task import Task

# Set environment variables

os.environ["LLM_API_KEY"] = "lm-studio"
os.environ["LLM_BASE_URL"] = "http://localhost:1234/v1"
os.environ["LLM_MODEL_NAME"] = "qwen/qwen3-1.7b"

def assertIsNotNone(obj, msg=None):
    """Assert that an object is not None"""
    if obj is None:
        standard_msg = f"{obj} is None"
        raise Exception(standard_msg)

def assertEqual(first, second, msg=None):
    """Assert that two objects are equal"""
    if first != second:
        standard_msg = f"{first} != {second}"
        raise Exception(standard_msg)

def assertTrue(expr, msg=None):
    """Assert that an expression is True"""
    if not expr:
        standard_msg = f"{expr} is not True"
        raise Exception(standard_msg)

def assertIn(member, container, msg=None):
    """Assert that a member is in a container"""
    if member not in container:
        standard_msg = f"{member} not found in {container}"
        raise Exception(standard_msg)

def assertIsInstance(obj, cls, msg=None):
    """Assert that an object is an instance of a class"""
    if not isinstance(obj, cls):
        standard_msg = f"{obj} is not an instance of {cls}"
        raise Exception(standard_msg)

def init_agent(config_type: str = "1",
               system_prompt_template: Optional[StringPromptTemplate] = None,
                context_rule: ContextRuleConfig = None,
                name: str = "my_agent" + str(random.randint(0, 1000000))):
    
    if config_type == "1":
        conf = AgentConfig(
            llm_model_name=os.environ["LLM_MODEL_NAME"],
            llm_base_url=os.environ["LLM_BASE_URL"],
            llm_api_key=os.environ["LLM_API_KEY"]
        )
    else:
        conf = AgentConfig(
            llm_config=ModelConfig(
                llm_model_name=os.environ["LLM_MODEL_NAME"],
                llm_base_url=os.environ["LLM_BASE_URL"],
                llm_api_key=os.environ["LLM_API_KEY"]
            )
        )
    return Agent(
        conf=conf,
        name=name,
        system_prompt="You are a helpful assistant.",
        system_prompt_template=system_prompt_template,
        context_rule=context_rule
    )

def run_agent(input, agent: Agent):
    swarm = Swarm(agent, max_steps=1)
    return Runners.sync_run(
        input=input,
        swarm=swarm
    )

def run_multi_agent_as_team(input, agent1: Agent, agent2: Agent):
    swarm = TeamSwarm(agent1, agent2, max_steps=1)
    return Runners.sync_run(
        input=input,
        swarm=swarm
    )

def run_task(agent: Agent, context: Context = None, input: str = "What is an agent."):
    swarm = Swarm(agent, max_steps=1)
    task = Task(input=input,
                swarm=swarm, context=context)
    return Runners.sync_run_task(task)

