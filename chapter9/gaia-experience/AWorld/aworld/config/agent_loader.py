# coding: utf-8
# Copyright (c) 2025 inclusionAI.
"""
Agent/Squad configuration loader from YAML.

Goals:
- Allow users to define agents and (optionally) a swarm topology in a single YAML file
- One function to load and construct Agents/Swarm
- Use existing config models (AgentConfig, ModelConfig, etc.) and utilities
- Support ${ENV_VAR} substitution in YAML values

YAML schema (minimal):

agents:
  researcher:
    system_prompt: "You specialize at researching."
    llm_config:
      llm_provider: openai
      llm_model_name: gpt-4o
      llm_api_key: ${OPENAI_API_KEY}
      llm_temperature: 0.1
  summarizer:
    system_prompt: "You specialize at summarizing."
    llm_config:
      llm_provider: openai
      llm_model_name: google/gemini-2.5-pro
      llm_api_key: ${OPENROUTER_API_KEY}
      llm_base_url: https://openrouter.ai/api/v1
      llm_temperature: 0.1

# Optional Swarm definition (choose one of the patterns below)
swarm:
  type: workflow  # or handoff, team
  order: [researcher, summarizer]          # for workflow
  # edges: [[researcher, summarizer]]      # for handoff
  # root: researcher                       # for team
  # members: [summarizer]
"""
from __future__ import annotations

import os
import re
from typing import Dict, Tuple, List, Any, Optional

import yaml

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig
from aworld.core.agent.swarm import Swarm, GraphBuildType
from aworld.logs.util import logger
from aworld.utils.common import replace_env_variables


def _replace_internal_vars(data: Any, vars_map: Dict[str, Any]) -> Any:
    """
    Replace placeholders of the form ${vars.KEY} using values from vars_map.
    - If the ENTIRE string is exactly "${vars.KEY}", return the raw value (preserve type, e.g., float/bool/int)
    - If used inside a longer string, perform string substitution
    Works recursively for dicts/lists/strings.
    """
    if not vars_map:
        return data

    pattern = re.compile(r"\$\{vars\.([A-Za-z0-9_]+)\}")
    full_pattern = re.compile(r"^\$\{vars\.([A-Za-z0-9_]+)\}$")

    def _recurse(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _recurse(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_recurse(v) for v in obj]
        if isinstance(obj, str):
            # Full match: preserve original type from vars_map
            m = full_pattern.match(obj)
            if m:
                key = m.group(1)
                if key in vars_map:
                    return vars_map[key]
                logger.warning(f"YAML vars: '${{vars.{key}}}' not found in top-level 'vars'")
                return obj

            # Partial substitution within a larger string -> stringify replacement
            def _sub(match: re.Match) -> str:
                key = match.group(1)
                if key in vars_map:
                    return str(vars_map[key])
                logger.warning(f"YAML vars: '${{vars.{key}}}' not found in top-level 'vars'")
                return match.group(0)
            return pattern.sub(_sub, obj)
        return obj

    return _recurse(data)


def _load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config YAML not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # 1) Replace ${ENV} placeholders from OS environment
    data = replace_env_variables(data)
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be a mapping (dict)")
    # 2) Replace ${vars.KEY} placeholders from YAML top-level 'vars'
    data = _replace_internal_vars(data, data.get("vars", {}))
    return data


def load_agents_from_yaml(path: str) -> Dict[str, Agent]:
    """
    Load agents defined in YAML and construct Agent instances.

    Returns a dict mapping agent names to Agent instances.
    Does not build a Swarm; use load_swarm_from_yaml for that.
    """
    data = _load_yaml(path)
    agents_conf = data.get("agents", {})
    if not isinstance(agents_conf, dict):
        raise ValueError("`agents` must be a mapping of name -> config")

    agents: Dict[str, Agent] = {}
    for name, conf_dict in agents_conf.items():
        if not isinstance(conf_dict, dict):
            raise ValueError(f"Agent `{name}` config must be a mapping")
        try:
            # Pydantic will parse nested llm_config, memory_config, etc.
            agent_conf = AgentConfig(**conf_dict)
            agent = Agent(name=name, conf=agent_conf)
            agents[name] = agent
        except Exception as e:
            logger.error(f"Failed to load agent `{name}` from YAML: {e}")
            raise
    return agents


def load_swarm_from_yaml(path: str) -> Tuple[Swarm, Dict[str, Agent]]:
    """
    Load agents and an optional swarm topology from YAML.

    Returns (swarm, agents_dict).
    If `swarm` section is missing, builds a default workflow in the order of YAML `agents` keys.
    """
    data = _load_yaml(path)
    agents = load_agents_from_yaml(path)

    swarm_conf: Optional[Dict[str, Any]] = data.get("swarm")
    if not swarm_conf:
        # Default: simple workflow in the order of agents declaration
        ordered = [agents[name] for name in data.get("agents", {}).keys()]
        if not ordered:
            raise ValueError("No agents defined to build a swarm")
        return Swarm(*ordered), agents

    stype = (swarm_conf.get("type") or GraphBuildType.WORKFLOW.value).lower()
    if stype not in {GraphBuildType.WORKFLOW.value, GraphBuildType.HANDOFF.value, GraphBuildType.TEAM.value}:
        raise ValueError(f"Unsupported swarm.type: {stype}")

    if stype == GraphBuildType.WORKFLOW.value:
        order: List[str] = swarm_conf.get("order") or list(data.get("agents", {}).keys())
        if not isinstance(order, list) or not order:
            raise ValueError("For workflow swarm, `order` must be a non-empty list of agent names")
        ordered_agents = [agents[name] for name in order]
        return Swarm(*ordered_agents), agents

    if stype == GraphBuildType.HANDOFF.value:
        edges: List[List[str]] = swarm_conf.get("edges") or []
        if not edges:
            raise ValueError("For handoff swarm, `edges` must be provided as [[left, right], ...]")
        pairs = []
        for a, b in edges:
            pairs.append((agents[a], agents[b]))
        return Swarm(*pairs, build_type=GraphBuildType.HANDOFF), agents

    # TEAM
    root: str = swarm_conf.get("root")
    members: List[str] = swarm_conf.get("members") or []
    if not root:
        # If root not specified, default to the first defined agent
        root = next(iter(data.get("agents", {}).keys()), None)
    if not root:
        raise ValueError("For team swarm, `root` or at least one agent must be defined")
    ordered = [agents[root]] + [agents[m] for m in members if m != root]
    return Swarm(*ordered, build_type=GraphBuildType.TEAM), agents

