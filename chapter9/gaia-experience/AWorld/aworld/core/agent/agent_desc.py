# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from typing import Dict, Any

from aworld.core.agent.base import AgentFactory
from aworld.logs.util import logger


def get_agent_desc() -> Dict[str, dict]:
    """Utility method of generate description of agents.

    The agent can also serve as a tool to be called.
    The standard protocol can be transformed based on the API of different llm.
    Define as follows:
    ```
    {
        "agent_name": {
            "desc": "An agent description.",
            "abilities": [
                {
                    "name": "ability name",
                    "desc": "ability description.",
                    "params": {
                        "param_name": {
                            "desc": "param description.",
                            "type": "param type, such as int, str, etc.",
                            "required": True | False
                        }
                    }
                }
            ]
        }
    }
    ```
    """

    descs = dict()
    for agent in AgentFactory:
        agent_val_dict = dict()
        descs[agent] = agent_val_dict

        agent_val_dict["desc"] = AgentFactory.desc(agent)
        abilities = []
        ability_dict = dict()
        # all agent has only `policy` ability now
        ability_dict["name"] = "policy"

        # The same as agent description.
        ability_dict["desc"] = AgentFactory.desc(agent)
        ability_dict["params"] = dict()

        # content in observation
        ability_dict["params"]["content"] = {
            "desc": ability_dict["desc"],#"The status information of the agent making the decision, which may be sourced from the env tool or another agent or self.",
            "type": "str",
            "required": True
        }
        ability_dict["params"]["info"] = {
            "desc": "Some extended information provided to the agent for decision-making.",
            "type": "str",
            "required": False
        }
        abilities.append(ability_dict)
        agent_val_dict["abilities"] = abilities
    return descs


def get_agent_desc_by_name(name: str) -> Dict[str, Any]:
    return get_agent_desc().get(name, None)


def agent_handoffs_desc(agent: 'Agent', use_all: bool = False) -> Dict[str, dict]:
    if not agent:
        if use_all:
            # use all agent description
            return get_agent_desc()
        logger.warning(f"no agent to gen description!")
        return {}

    desc = {}
    # agent.handoffs never is None
    for reachable in agent.handoffs:
        res = get_agent_desc_by_name(reachable)
        if not res:
            logger.warning(f"{reachable} can not find in the agent factory, ignored it.")
            continue
        desc[reachable] = res

    return desc
