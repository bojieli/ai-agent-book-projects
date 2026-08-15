import os
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig
from aworld.core.task import Task
from aworld.runner import Runners
from aworld.config import RunConfig, EngineName

# Setup, need modify
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_MODEL_NAME"] = "gpt-4o"
os.environ["LLM_API_KEY"] = "your-api-key"
# os.environ["LLM_BASE_URL"] = "https://api.openai.com/v1"

# Create agent
agent_config = AgentConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_api_key=os.getenv("LLM_API_KEY"),
    # llm_base_url=os.getenv("LLM_BASE_URL")
)
my_agent = Agent(name="my_agent", conf=agent_config)

# Create tasks
tasks = [
    Task(input="What is machine learning?", agent=my_agent, id="task1"),
    Task(input="Explain neural networks", agent=my_agent, id="task2"),
    Task(input="What is deep learning?", agent=my_agent, id="task3")
]

# Run in parallel (default local run).
# If you want to run in a distributed environment, you need to submit a job to the Ray cluster.
results = Runners.sync_run_task(
    task=tasks,
    run_conf=RunConfig(
        engine_name=EngineName.RAY,
        worker_num=len(tasks)
    )
)

# Process results
for task_id, result in results.items():
    print(f"Task {task_id}: {result.answer}")