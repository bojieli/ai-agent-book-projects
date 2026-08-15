# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig
from examples.common.tools.common import Tools

search_sys_prompt = "You are a helpful search agent."
search_prompt = """
    Please act as a search agent, constructing appropriate keywords and searach terms, using search toolkit to collect relevant information, including urls, webpage snapshots, etc.

    Here are the question: {task}

    pleas only use one action complete this task, at least results 6 pages.
    """

summary_sys_prompt = "You are a helpful general summary agent."

summary_prompt = """
Summarize the following text in one clear and concise paragraph, capturing the key ideas without missing critical points. 
Ensure the summary is easy to understand and avoids excessive detail.

Here are the content: 
{task}
"""

agent_config = AgentConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
    llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
)

search = Agent(
    conf=agent_config,
    name="search_agent",
    system_prompt=search_sys_prompt,
    agent_prompt=search_prompt,
    tool_names=[Tools.SEARCH_API.value]
)

summary = Agent(
    conf=agent_config,
    name="summary_agent",
    system_prompt=summary_sys_prompt,
    agent_prompt=summary_prompt
)
