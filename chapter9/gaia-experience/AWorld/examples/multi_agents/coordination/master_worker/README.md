# TeamSwarm Example

This example demonstrates how to build a multi-agent collaborative system using the TeamSwarm feature in the AWorld framework. In this example, we create a team with three agents:

1. **PlanAgent** - The lead agent responsible for breaking down tasks and planning execution steps
2. **SearchAgent** - The execution agent responsible for performing web search tasks
3. **SummaryAgent** - The execution agent responsible for summarizing information and generating final reports

## File Structure

- `run_multi_action.py` - Main example code showing how to build and run the multi-action version of TeamSwarm
- `run.py` - Single-action version of the TeamSwarm example
- `prompts_multi_actions.py` - Contains prompt templates used by agents in the multi-action planning version
- `prompts_single_action.py` - Contains prompt templates used by agents in the single-action version

## Running the Examples

### Multi-action Planning Version
```bash
python run_multi_action.py
```

### Single-action Version
```bash
python run.py
```

## TeamSwarm Workflow

### Multi-action Planning Version
1. PlanAgent receives user input and plans multiple search and summary actions at once
2. PlanAgent breaks down complex problems into multiple sub-problems and plans search actions for each
3. SearchAgent executes the search actions according to the plan to gather comprehensive information
4. SummaryAgent synthesizes all collected information and generates a final report for the user
5. The entire workflow is planned upfront with consideration for dependencies between actions

### Single-action Version
1. PlanAgent receives user input and decides whether to execute a search or summary based on the current context
2. If more information is needed, PlanAgent calls SearchAgent to perform a search
3. If sufficient information has been collected, PlanAgent calls SummaryAgent to generate a summary
4. If a summary has been executed and results obtained, PlanAgent outputs the result without calling any tools

## Core Concepts

TeamSwarm is a special Swarm structure that requires a lead agent with other agents following its commands. In TeamSwarm:

- The first agent (or the agent specified by the root_agent parameter) is the leader
- Other agents act as executors, interacting with the leader
- The leader decides when and which executor to call

This structure is suitable for scenarios requiring a central coordinator to manage multiple specialized agents, such as the information search and summarization tasks in this example.

## Advantages of the Single-action Version

The single-action version of TeamSwarm has the following advantages compared to the multi-action planning version:

1. **More flexible decision-making** - Each decision is based on the latest context, allowing strategy adjustments based on real-time situations
2. **Better error recovery** - If a step fails, subsequent steps can be adjusted based on the failure results
3. **More efficient resource utilization** - Search is only performed when needed, avoiding unnecessary operations
4. **More natural interaction flow** - Simulates human thinking and decision-making processes by searching for information first and then summarizing 