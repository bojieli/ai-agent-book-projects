# Parallel Run

As the **first** agent framework that seamlessly supports running on different distributed computing engines, this README demonstrates how to perform parallel evaluation using **AWorld**.

## Prerequisites

- Python 3.11 or higher
- Ray and PySpark require separate installation:
  - `pip install ray` 
  - `pip install pyspark==3.5.0` (requires JDK 1.8.0_441)

## Setup

### 1. Prepare the LLM Service

```python
import os

# Set up LLM service using environment variables
os.environ["LLM_PROVIDER"] = "openai"  # Choose from: openai, anthropic, azure_openai
os.environ["LLM_MODEL_NAME"] = "gpt-4"
os.environ["LLM_API_KEY"] = "your-api-key"
os.environ["LLM_BASE_URL"] = "https://api.openai.com/v1"  # Optional for OpenAI
```

### 2. Prepare the Agent

```python
import os
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig

agent_config = AgentConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_base_url=os.getenv("LLM_BASE_URL"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)

my_agent = Agent(name="my_agent", conf=agent_config)
```

### 3. Prepare the Tasks

```python
from aworld.core.task import Task

tasks = [
    Task(input="who are you?", agent=my_agent, id="abcd"),
    Task(input="Hello World!", agent=my_agent, id="efgh"),
    Task(input="Nice to meet you.", agent=my_agent, id="ijkl")
]
```

## Running Tasks in Parallel

AWorld supports three different parallel execution engines. Choose the one that best fits your needs:

### Ray Engine (Recommended for distributed computing)

```python
from aworld.runner import Runners
from aworld.config import RunConfig, EngineName

res = Runners.sync_run_task(
    task=tasks,
    run_conf=RunConfig(
        engine_name=EngineName.RAY, 
        worker_num=len(tasks)
    )
)
```

### Spark Engine (For big data processing)

```python
res = Runners.sync_run_task(
    task=tasks,
    run_conf=RunConfig(
        engine_name=EngineName.SPARK, 
        in_local=True
    )
)
```

### Local Multiprocess Engine (For simple parallelization)

```python
res = Runners.sync_run_task(
    task=tasks,
    run_conf=RunConfig(
        engine_name=EngineName.LOCAL, 
        reuse_process=False
    )
)
```

## Complete Example

Here's a complete working example that demonstrates parallel task execution:

```python
import os
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig
from aworld.core.task import Task
from aworld.runner import Runners
from aworld.config import RunConfig, EngineName

# Setup
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_MODEL_NAME"] = "gpt-4"
os.environ["LLM_API_KEY"] = "your-api-key"

# Create agent
agent_config = AgentConfig(
    llm_provider=os.getenv("LLM_PROVIDER", "openai"),
    llm_model_name=os.getenv("LLM_MODEL_NAME"),
    llm_api_key=os.getenv("LLM_API_KEY"),
)
my_agent = Agent(name="my_agent", conf=agent_config)

# Create tasks
tasks = [
    Task(input="What is machine learning?", agent=my_agent, id="task1"),
    Task(input="Explain neural networks", agent=my_agent, id="task2"),
    Task(input="What is deep learning?", agent=my_agent, id="task3")
]

# Run in parallel
results = Runners.sync_run_task(
    task=tasks,
    run_conf=RunConfig(
        engine_name=EngineName.RAY,
        worker_num=len(tasks)
    )
)

# Process results
for result in results:
    print(f"Task {result.task_id}: {result.answer}")
```

## Engine Comparison

| Engine | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Ray** | Distributed computing, large-scale parallelization | Highly scalable, fault-tolerant | Requires Ray installation |
| **Spark** | Big data processing, batch jobs | Excellent for large datasets | Requires Spark and JDK |
| **Local** | Simple parallelization, development | No external dependencies | Limited to single machine |

## Notes

- The `worker_num` parameter should typically match the number of tasks for optimal performance
- For Spark engine, set `in_local=True` to run locally without a Spark cluster
- For Local engine, `reuse_process=False` creates new processes for each task, providing better isolation