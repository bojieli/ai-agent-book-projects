# Multi-agent

```python
from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig
from aworld.core.agent.swarm import Swarm, GraphBuildType

agent_conf = AgentConfig(...)
```

## Builder
Builder represents the way topology is constructed, which is related to runtime execution. 
Topology is the definition of structure. For the same topology structure, different builders 
will produce execution processes and different results.

```python
"""
Topology:
 ┌─────A─────┐     
 B     |     C
       D 
"""
A = Agent(name="A", conf=agent_conf)
B = Agent(name="B", conf=agent_conf)
C = Agent(name="C", conf=agent_conf)
D = Agent(name="D", conf=agent_conf)
```

### Workflow
Workflow is a special topological structure that can be executed deterministically, all nodes in the swarm 
will be executed. And the starting and ending nodes are **unique** and **indispensable**.

Define:
```python
# default is workflow
Swarm((A, B), (A, C), (A, D))
or
Swarm(A, [B, C, D])
```
The example means A is the start node, and the merge of B, C, and D is the end node.

### Handoff
Handoff using pure AI to drive the flow of the entire topology diagram, one agent's decision hands off 
control to another. Agents as tools, depending on the defined pairs of agents.

Define:
```python
Swarm((A, B), (A, C), (A, D), build_type=GraphBuildType.HANDOFF)
or
HandoffSwarm((A, B), (A, C), (A, D))
```
**NOTE**: Handoff supported tuple of paired agents forms only.

### Team
Team requires a leadership agent, and other agents follow its command. 
Team is a special case of handoff, which is the leader-follower mode.

Define:
```python
Swarm((A, B), (A, C), (A, D), build_type=GraphBuildType.TEAM)
or
TeamSwarm(A, B, C, D)
or
Swarm(B, C, D, root_agent=A, build_type=GraphBuildType.TEAM)
```
The root_agent or first agent A is the leader; other agents interact with the leader A.

### Debate
TODO

### Hybrid
Hybrid is not a new type of builder of topology. Due to the use of different builders for the same topology, 
the execution process varies, so hybrid builder is the fusion of **nested** topologies from different builders. 
That is, interaction between multi-agents with multi-agents in different build modes.
For example, in a `WorkflowSwarm`, one node can be a `TeamSwarm`, `HandoffSwarm` or other. Or a node in a 
`HandoffSwarm` can also be a `WorkflowSwarm` or other.

Example:
```python
A1 = Agent(name="A1", conf=agent_conf)
B1 = Agent(name="B1", conf=agent_conf)
C1 = Agent(name="C1", conf=agent_conf)
swarm1 = TeamSwarm(A1, B1, C1, build_type=GraphBuildType.TEAM)

Swarm(A, [B, C, swarm1], D)
```
The example shows that workflow swarm. After A completes execution, B, C, and swarm1(TeamSwarm) execute in parallel, 
swarm1 will run in plan-execute mode until the end of the swarm1, and finally D is executed.

## Topology
The topology structure of multi-agent is represented by Swarm, Swarm's topology is built based on 
various single agents，can use the topology type and build type Swarm to represent different structural types.

### Star
Each agent communicates with a single supervisor agent, also known as star topology, 
a special structure of tree topology, also referred to as a team topology in **Aworld**.

A plan agent with other executing agents is a typical example.
```python
"""
Star topology:
 ┌───── plan ───┐     
exec1         exec2
"""
plan = Agent(name="plan", conf=agent_conf)
exec1 = Agent(name="exec1", conf=agent_conf)
exec2 = Agent(name="exec2", conf=agent_conf)
```

We have two ways to construct this topology structure.
```python
swarm = Swarm((plan, exec1), (plan, exec2))
```
or use handoffs mechanism:
```python
plan = Agent(name="plan", conf=agent_conf, agent_names=['exec1', 'exec2'])
swarm = Swarm(plan, register_agents=[exec1, exec2])
```
or use team mechanism:
```python
# The order of the plan agent is the first.
swarm = TeamSwarm(plan, exec1, exec2,
                 build_type=GraphBuildType.TEAM)
```

Note: 
- Whether to execute exec1 or exec2 is decided by LLM.
- If you want to execute all defined nodes with certainty, you need to use the `workflow` pattern.
Like this will execute all the defined nodes:
```python
swarm = Swarm(plan, [exec1, exec2])
```
- If it is necessary to execute exec1, whether to execute exec2 depends on LLM, you can define it as:
```python
plan = Agent(name="plan", conf=agent_conf, agent_names=['exec1', 'exec2'])
swarm = Swarm((plan, exec1), register_agents=[exec2])
```
That means that **GraphBuildType.WORKFLOW** is set, all nodes within the swarm will be executed.

### Tree
This is a generalization of the star topology and allows for more complex control flows.

#### Hierarchical
```python
"""
Hierarchical topology:
            ┌─────────── root ───────────┐
  ┌───── parent1 ───┐        ┌─────── parent2 ───────┐
leaf1_1         leaf1_2    leaf1_1                leaf2_2
"""

root = Agent(name="root", conf=agent_conf)
parent1 = Agent(name="parent1", conf=agent_conf)
parent2 = Agent(name="parent2", conf=agent_conf)
leaf1_1 = Agent(name="leaf1_1", conf=agent_conf)
leaf1_2 = Agent(name="leaf1_2", conf=agent_conf)
leaf2_1 = Agent(name="leaf2_1", conf=agent_conf)
leaf2_2 = Agent(name="leaf2_2", conf=agent_conf)
```

```python
swarm = Swarm((root, parent1), (root, parent2), 
              (parent1, leaf1_1), (parent1, leaf1_2), 
              (parent2, leaf2_1), (parent2, leaf2_2),
              build_type=GraphBuildType.HANDOFF)
```
or use agent handoff:
```python
root = Agent(name="root", conf=agent_conf, agent_names=['parent1', 'parent2'])
parent1 = Agent(name="parent1", conf=agent_conf, agent_names=['leaf1_1', 'leaf1_2'])
parent2 = Agent(name="parent2", conf=agent_conf, agent_names=['leaf2_1', 'leaf2_2'])

swarm = HandoffSwarm((root, parent1), (root, parent2),
                     register_agents=[leaf1_1, leaf1_2, leaf2_1, leaf2_2])
```

#### Map-reduce
If the topology structure becomes further complex:
```
            ┌─────────── root ───────────┐
  ┌───── parent1 ───┐        ┌────── parent2 ──────┐
leaf1_1         leaf1_2   leaf1_1               leaf2_2
  └─────result1─────┘        └───────result2───────┘   
            └───────────final───────────┘ 
```
We define it as **Map-reduce** topology, equivalent to workflow in terms of execution mode. 

Build in this way:

```python
result1 = Agent(name="result1", conf=agent_conf)
result2 = Agent(name="result2", conf=agent_conf)
final = Agent(name="final", conf=agent_conf)

swarm = Swarm(
    (root, [parent1, parent2]), 
    (parent1, [leaf1_1, leaf1_2]), 
    (parent2, [leaf2_1, leaf2_2]),
    ([leaf1_1, leaf1_2], result1), 
    ([leaf2_1, leaf2_2], result2),
    ([result1, result2], final)
)
```
Assuming there is a cycle final -> root in the topology, define it as:
```python
final = LoopableAgent(name="final", 
                      conf=agent_conf, 
                      max_run_times=5, 
                      loop_point=root.name(), 
                      stop_func=...)
```
`stop_func` is a function that determines whether to terminate prematurely.


### Mesh
Divided into a fully meshed topology and a partially meshed topology. 
Fully meshed topology means that each agent can communicate with every other agent, 
any agent can decide which other agent to call next.

```python
"""
Fully Meshed topology:
    ┌─────────── A ──────────┐
    B ───────────|────────── C 
    └─────────── D  ─────────┘
"""
A = Agent(name="A", conf=agent_conf)
B = Agent(name="B", conf=agent_conf)
C = Agent(name="C", conf=agent_conf)
D = Agent(name="D", conf=agent_conf)
```

Network topology need to use the `handoffs` mechanism:
```python
swarm = HandoffsSwarm((A, B), (B, A),
                      (A, C), (C, A),
                      (A, D), (D, A),
                      (B, C), (C, B),
                      (B, D), (D, B),
                      (C, D), (D, C))
```
If a few pairs are removed, it becomes a partially meshed topology.

### Ring
A ring topology structure is a closed loop formed by nodes.

```python
"""
Ring topology:
    ┌───────────> A >──────────┐
    B                          C 
    └───────────< D  <─────────┘
"""
A = Agent(name="A", conf=agent_conf)
B = Agent(name="B", conf=agent_conf)
C = Agent(name="C", conf=agent_conf)
D = Agent(name="D", conf=agent_conf)
```


```python
swarm = Swarm((A, C), (C, D), (D, B), (B, A))
```
**Note:**
- This defined loop can only be executed once.
- If you want to execute multiple times, need to define it as:

```python
B = LoopableAgent(name="B", max_run_times=5, stop_func=...)
swarm = Swarm((A, C), (C, D), (D, B))
```
### hybrid
A generalization of topology, supporting an arbitrary combination of topologies, internally capable of 
loops, parallel, serial dependencies, and groups.

## Execution