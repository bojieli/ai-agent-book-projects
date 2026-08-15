import os
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aworld.core.agent.swarm import TeamSwarm
from aworld.runner import Runners
from examples.common.tools.common import Tools

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, ModelConfig

from examples.multi_agents.coordination.master_worker.prompts_single_action import (
    plan_sys_prompt, 
    search_sys_prompt,
    summary_sys_prompt
)

# Set environment variables, configure LLM model
# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"

def get_single_action_team_swarm(user_input):
    """
    Create a single-action version of TeamSwarm, consisting of PlanAgent, SearchAgent, and SummaryAgent
    
    In this version, PlanAgent generates only one action at a time, deciding whether to execute a search or summary based on the current context
    
    Args:
        user_input: User's input query
        
    Returns:
        TeamSwarm instance
    """
    # Create a unified Agent configuration
    agent_config = AgentConfig(
        llm_config=ModelConfig(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_model_name=os.getenv("LLM_MODEL_NAME"),
            llm_base_url=os.getenv("LLM_BASE_URL"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
        ),
        use_vision=False
    )

    # Create planning Agent, responsible for planning single execution steps based on context
    plan_agent = Agent(
        name="plan_agent",
        desc="Agent responsible for deciding whether to execute search or summary based on current context",
        conf=agent_config,
        system_prompt_template=plan_sys_prompt,
        use_planner=False,
        use_tools_in_prompt=False
    )

    # Create search Agent, responsible for executing web search tasks
    search_agent = Agent(
        name="search_agent",
        desc="Agent responsible for executing web search tasks",
        conf=agent_config,
        system_prompt_template=search_sys_prompt,
        tool_names=[Tools.SEARCH_API.value]
    )
    
    # Create summary Agent, responsible for summarizing information and generating final reports
    summary_agent = Agent(
        name="summary_agent",
        desc="Agent responsible for summarizing information and generating final reports",
        conf=agent_config,
        system_prompt_template=summary_sys_prompt,
    )

    # Create TeamSwarm, with plan_agent as the lead Agent and other Agents as executors
    # Increase maximum steps to support multiple rounds of interaction
    return TeamSwarm(plan_agent, search_agent, summary_agent, max_steps=10)
    

if __name__ == "__main__":
    # User input example
    user_input = "Please provide me with information about the latest developments in large language models"
    
    # Create single-action version of TeamSwarm
    swarm = get_single_action_team_swarm(user_input)
    
    # Run TeamSwarm
    result = Runners.sync_run(
        input=user_input,
        swarm=swarm
    )
    
    print("Single-action TeamSwarm execution result: ", result) 