# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import copy
import inspect
import os.path
from typing import Dict, Any, List, Union

from aworld.core.context.base import Context
from aworld.logs.util import logger
from aworld.models.qwen_tokenizer import qwen_tokenizer
from aworld.models.openai_tokenizer import openai_tokenizer
from aworld.utils import import_package


def usage_process(usage: Dict[str, Union[int, Dict[str, int]]] = {}, context: Context = None):
    if not context:
        context = Context()

    stacks = inspect.stack()
    index = 0
    for idx, stack in enumerate(stacks):
        index = idx + 1
        file = os.path.basename(stack.filename)
        # supported use `llm.py` utility function only
        if 'call_llm_model' in stack.function and file == 'llm.py':
            break

    if index >= len(stacks):
        logger.warning("not category usage find to count")
    else:
        instance = stacks[index].frame.f_locals.get('self')
        name = getattr(instance, "_name", "unknown")
        usage[name] = copy.copy(usage)
    # total usage
    context.add_token(usage)


def num_tokens_from_string(string: str, model: str = "openai"):
    """Return the number of tokens used by a string."""
    import_package("tiktoken")
    import tiktoken
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(string))

def num_tokens_from_messages(messages, model="openai"):
    """Return the number of tokens used by a list of messages."""
    import_package("tiktoken")
    import tiktoken

    if model.lower() == "qwen":
        encoding = qwen_tokenizer
    elif model.lower() == "openai":
        encoding = openai_tokenizer
    else:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(
                f"{model} model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        if isinstance(message, str):
            num_tokens += len(encoding.encode(message))
        else:
            for key, value in message.items():
                num_tokens += len(encoding.encode(str(value)))
                if key == "name":
                    num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def truncate_tokens_from_messages(messages: List[Dict[str, Any]], max_tokens: int, keep_both_sides: bool = False, model: str = "gpt-4o"):
    import_package("tiktoken")
    import tiktoken

    if model.lower() == "qwen":
        return qwen_tokenizer.truncate(messages, max_tokens, keep_both_sides)
    elif model.lower() == "openai":
        return openai_tokenizer.truncate(messages, max_tokens, keep_both_sides)

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning(f"{model} model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    return encoding.truncate(messages, max_tokens, keep_both_sides)


def agent_desc_transform(agent_dict: Dict[str, Any],
                         agents: List[str] = None,
                         provider: str = 'openai',
                         strategy: str = 'min') -> List[Dict[str, Any]]:
    """Default implement transform framework standard protocol to openai protocol of agent description.

    Args:
        agent_dict: Dict of descriptions of agents that are registered in the agent factory.
        agents: Description of special agents to use.
        provider: Different descriptions formats need to be processed based on the provider.
        strategy: The value is `min` or `max`, when no special agents are provided, `min` indicates no content returned,
                 `max` means get all agents' descriptions.
    """
    agent_as_tools = []
    if not agents and strategy == 'min':
        return agent_as_tools
    if provider and 'openai' in provider:
        for agent_name, agent_info in agent_dict.items():
            if agents and agent_name not in agents:
                logger.debug(
                    f"{agent_name} can not supported in {agents}, you can set `tools` params to support it.")
                continue
            
            for action in agent_info["abilities"]:
                # Build parameter properties
                properties = {}
                required = []
                for param_name, param_info in action["params"].items():
                    properties[param_name] = {
                        "description": param_info["desc"],
                        "type": param_info["type"] if param_info["type"] != "str" else "string"
                    }
                    if param_info.get("required", False):
                        required.append(param_name)

                openai_function_schema = {
                    "name": f'{agent_name}', # __{action["name"]}
                    "description": action["desc"],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }

                agent_as_tools.append({
                    "type": "function",
                    "function": openai_function_schema
                })
    logger.debug(f"agent_desc_transform is {agent_as_tools}")
    return agent_as_tools


def tool_desc_transform(tool_dict: Dict[str, Any],
                        tools: List[str] = None,
                        black_tool_actions: Dict[str, List[str]] = {},
                        provider: str = 'openai',
                        strategy: str = 'min') -> List[Dict[str, Any]]:
    """Default implement transform framework standard protocol to openai protocol of tool description.

    Args:
        tool_dict: Dict of descriptions of tools that are registered in the agent factory.
        tools: Description of special tools to use.
        provider: Different descriptions formats need to be processed based on the provider.
        strategy: The value is `min` or `max`, when no special tools are provided, `min` indicates no content returned,
                 `max` means get all tools' descriptions.
    """
    openai_tools = []
    if not tools and strategy == 'min':
        return openai_tools

    if black_tool_actions is None:
        black_tool_actions = {}

    if provider and 'openai' in provider:
        for tool_name, tool_info in tool_dict.items():
            if tools and tool_name not in tools:
                logger.debug(
                    f"{tool_name} can not supported in {tools}, you can set `tools` params to support it.")
                continue

            black_actions = black_tool_actions.get(tool_name, [])
            for action in tool_info["actions"]:
                if action['name'] in black_actions:
                    continue
                # Build parameter properties
                properties = {}
                required = []
                for param_name, param_info in action["params"].items():
                    properties[param_name] = {
                        "description": param_info["desc"],
                        "type": param_info["type"] if param_info["type"] != "str" else "string"
                    }
                    if param_info.get("required", False):
                        required.append(param_name)

                openai_function_schema = {
                    "name": f'{tool_name}__{action["name"]}',
                    "description": action["desc"],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }

                openai_tools.append({
                    "type": "function",
                    "function": openai_function_schema
                })
    return openai_tools
