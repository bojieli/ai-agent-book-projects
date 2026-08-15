
We use the classic graph syntax to describe workflows in AWorld. 
The following are the basic scenarios for constructing agent workflows.

## Agent Native Workflow

### Sequential
```python
"""
Sequential Agent Pipeline: agent1 → agent2 → agent3

Executes agents in sequence where each agent's output becomes 
the next agent's input, enabling multi-step collaborative processing.
"""

swarm = Swarm([(agent1, agent2), (agent2, agent3)], root_agent=[agent1])
result: TaskResponse = Runners.run(input=question, swarm=swarm)
```

### Parallel
```python
"""
Parallel Agent Execution with Barrier Synchronization

    Input ──┬─→ agent1 ──┐
            │            ├──→ agent3 (barrier wait)
            └─→ agent2 ──┘

- agent1 and agent2 execute in parallel
- agent3 acts as a barrier, waiting for both agents
- agent3 processes combined outputs from agent1 and agent2
"""

swarm = Swarm([(agent1, agent3), (agent2, agent3)], root_agent=[agent1, agent2])
result: TaskResponse = Runners.run(input=question, swarm=swarm)
```

### Parallel Multi-Path 
```python
"""
Parallel Multi-Path Agent Execution

    Input ──→ agent1 ──┬──→ agent2 ──┐
                       │             │
                       └──→ agent3 ←─┘ (barrier wait for agent1 & agent2)

- Single input enters only through agent1
- agent1 distributes to both agent2 and agent3
- agent2 processes and feeds agent3
- agent3 waits for both agent1 and agent2 completion
- agent3 synthesizes outputs from both agent1 and agent2
"""

swarm = Swarm([(agent1, agent2), (agent1, agent3), (agent2, agent3)], root_agent=[agent1])
result: TaskResponse = Runners.run(input=question, swarm=swarm)
```

## Task Native Workflow
Task native workflow is further implemented for Isolating the agent runtimes and environments, 
in the distributed or other easy-to-overlap scenarios. 
Task native workflow is further implemented for isolating agent runtimes and environments, 
particularly useful in distributed or other scenarios where tool-isolation is required. 
```python
task1 = Task(input="my question", agent=agent1)
task2 = Task(agent=agent2)
task3 = Task(agent=agent3)
tasks = [task1, task2, task3]

result: Dict[str, TaskResponse] = Runners.run_task(tasks, RunConfig(sequence_dependent=True))
```