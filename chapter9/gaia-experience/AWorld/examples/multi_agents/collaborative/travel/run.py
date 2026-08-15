# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os
from aworld.config.conf import AgentConfig, ToolConfig
from aworld.agents.llm_agent import Agent
from aworld.config import ModelConfig
from aworld.core.agent.swarm import TeamSwarm, Swarm, GraphBuildType
from aworld.core.task import Task
from aworld.runner import Runners
from examples.browser_use.agent import BrowserAgent
from examples.browser_use.config import BrowserAgentConfig
from examples.common.tools.common import Tools
from examples.common.tools.conf import BrowserToolConfig
from examples.common.tools.tool_action import SearchAction
from examples.multi_agents.collaborative.travel.prompts import *

# os.environ["LLM_PROVIDER"] = "openai"
# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"

model_config = ModelConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
    llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
)
agent_config = AgentConfig(
    llm_config=model_config,
    use_vision=False
)

plan = Agent(
    conf=agent_config,
    name="example_plan_agent",
    system_prompt=plan_sys_prompt,
    agent_prompt=plan_prompt,
    agent_names=['browser_agent'],
    step_reset=False
)

search = Agent(
    conf=agent_config,
    name="example_search_agent",
    desc="search ",
    system_prompt=search_sys_prompt,
    agent_prompt=search_prompt,
    tool_names=[Tools.SEARCH_API.value],
    black_tool_actions={Tools.SEARCH_API.value: [SearchAction.DUCK_GO.value.name, SearchAction.WIKI.value.name,
                                                 SearchAction.GOOGLE.value.name]}
)

write = Agent(
    conf=agent_config,
    name="example_write_agent",
    system_prompt=write_sys_prompt,
    agent_prompt=write_prompt,
    tool_names=[Tools.HTML.value],
)

browser_agent = BrowserAgent(
    name='browser_agent',
    desc="browser_agent can execute extract web info task and open local file task, if you want to use browser agent to open local file, you should give the specific absolutely file path in params.",
    conf=BrowserAgentConfig(
        llm_config=model_config,
        use_vision=False
    ),
    custom_executor=True,
    tool_names=[Tools.BROWSER.value]
)


def main():
    goal = """
        I need a 7-day Japan itinerary from April 2 to April 8 2025, departing from Hangzhou, We want to see beautiful cherry blossoms and experience traditional Japanese culture (kendo, tea ceremonies, Zen meditation). We would like to taste matcha in Uji and enjoy the hot springs in Kobe. I am planning to propose during this trip, so I need a special location recommendation. Please provide a detailed itinerary and create a simple HTML travel handbook that includes a 7-day Japan itinerary, an updated cherry blossom table, attraction descriptions, essential Japanese phrases, and travel tips for us to reference throughout our journey.
        you need search and extract different info 1 times, and then write, at last use browser agent goto the html url and then, complete the task.
        """
    swarm = Swarm((plan, search), (plan, browser_agent), (plan, write), build_type=GraphBuildType.HANDOFF)
    # swarm = TeamSwarm(plan, search, browser_agent, write)
    task = Task(
        swarm=swarm,
        input=goal,
        tools_conf={
            Tools.BROWSER.value: BrowserToolConfig(width=800, height=720, use_async=True, llm_config=model_config),
            Tools.HTML.value: ToolConfig(name="html", llm_config=model_config)
        },
        endless_threshold=5
    )

    Runners.sync_run_task(task)


if __name__ == '__main__':
    main()
