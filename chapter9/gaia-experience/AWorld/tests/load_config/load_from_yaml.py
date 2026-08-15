# coding: utf-8
# Example: load agents and swarm from a YAML file and run

from aworld.config.agent_loader import load_agents_from_yaml, load_swarm_from_yaml
from aworld.runner import Runners

if __name__ == "__main__":
    # You can change the config path as needed
    swarm, agents = load_swarm_from_yaml("examples/load_config/agents.yaml")

    # Access a specific agent if needed
    summarizer = agents["summarizer"]

    # Run with the constructed swarm
    result = Runners.sync_run(
        input="hello who are you?",
        swarm=swarm,
    )

    print("Result:", result)

