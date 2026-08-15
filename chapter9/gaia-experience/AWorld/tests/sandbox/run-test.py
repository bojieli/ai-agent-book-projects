# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import json
import os

from dotenv import load_dotenv

from aworld.config.conf import AgentConfig, TaskConfig
from aworld.agents.llm_agent import Agent
from aworld.core.task import Task
from aworld.runner import Runners


async def run():
    load_dotenv()
    llm_provider = os.getenv("LLM_PROVIDER_WEATHER", "openai")
    llm_model_name = os.getenv("LLM_MODEL_NAME_WEATHER")
    llm_api_key = os.getenv("LLM_API_KEY_WEATHER")
    llm_base_url = os.getenv("LLM_BASE_URL_WEATHER")
    llm_temperature = os.getenv("LLM_TEMPERATURE_WEATHER", 0.0)

    agent_config = AgentConfig(
        llm_provider=llm_provider,
        llm_model_name=llm_model_name,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_temperature=llm_temperature,
    )
    mcp_servers = ["tavily-mcp"]

    path_cwd = os.path.dirname(os.path.abspath(__file__))
    mcp_path = os.path.join(path_cwd, "mcp.json")
    with open(mcp_path, "r") as f:
        mcp_config = json.load(f)

    search_sys_prompt = "You are a versatile assistant"
    search = Agent(
        conf=agent_config,
        name="search_agent",
        system_prompt=search_sys_prompt,
        mcp_config=mcp_config,
        mcp_servers=mcp_servers,
    )

    # Run agent
    task = Task(
        input="Use tavily-mcp to check what tourist attractions are in Hangzhou",
        agent=search,
        conf=TaskConfig(),
    )

    result = Runners.sync_run_task(task)
    print( "----------------------------------------------------------------------------------------------")
    print(result)
