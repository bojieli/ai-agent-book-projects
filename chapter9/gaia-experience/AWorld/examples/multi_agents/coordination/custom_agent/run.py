# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import os

from aworld.config.conf import ModelConfig, AgentConfig
from aworld.core.agent.swarm import Swarm, GraphBuildType
from aworld.core.task import Task
from aworld.runner import Runners
from examples.multi_agents.coordination.custom_agent.agent import PlanAgent, ExecuteAgent
from examples.multi_agents.coordination.custom_agent.mock import mock_dataset
from examples.common.tools.common import Agents, Tools

# os.environ["LLM_PROVIDER"] = "openai"
# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"
def main():
    test_sample = mock_dataset("gaia")

    model_config = ModelConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model_name=os.getenv("LLM_MODEL_NAME"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
    )

    agent1_config = AgentConfig(
        llm_config=model_config
    )
    agent1 = PlanAgent(conf=agent1_config, name=Agents.PLAN.value, step_reset=False)

    agent2_config = AgentConfig(

        llm_config=model_config
    )
    agent2 = ExecuteAgent(conf=agent2_config, name=Agents.EXECUTE.value, step_reset=False,
                          tool_names=[Tools.DOCUMENT_ANALYSIS.value])

    # Create swarm for multi-agents
    # define (head_node1, tail_node1), (head_node1, tail_node1) edge in the topology graph
    swarm = Swarm((agent1, agent2), build_type=GraphBuildType.HANDOFF)

    # Define a task
    task_id = 'task'
    task = Task(id=task_id, input=test_sample, swarm=swarm, endless_threshold=5)

    # Run task
    result = Runners.sync_run_task(task=task)

    print(f"Time cost: {result[task_id].time_cost}")
    print(f"Task Answer: {result[task_id].answer}")


if __name__ == '__main__':
    main()
