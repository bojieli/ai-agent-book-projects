# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import json
import os
from typing import List, Dict, Any
from transformers import AutoTokenizer
from verl.experimental.agent_loop.agent_loop import AgentLoopBase, AgentLoopOutput, AgentLoopMetrics


async def to_agent_loop_output(tokenizer: AutoTokenizer,
                               messages: List[Dict[str, Any]],
                               response_length: int,
                               tools: Dict[str, Any] = None) -> AgentLoopOutput:
    """Convert messages to AgentLoopOutput.

    Args:
        tokenizer (AutoTokenizer): Tokenizer for tokenize messages.
        messages (List[Dict[str, Any]]): List of messages in OpenAI request format.
        response_length (int): Max length of response.
        tools: Tool list used by the agent.

    Returns:
        AgentLoopOutput: agent loop output trajectory used for training.
    """
    # Ensure tools is iterable for chat templates that iterate over tools
    if tools is None:
        tools = []

    # Normalize messages to satisfy chat templates expectations
    def _normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(msg)
        # content may be None when assistant only returns tool_calls; make it empty string
        if normalized.get("content") is None:
            normalized["content"] = ""
        # Ensure tool_calls.function.arguments is a string (many templates expect str)
        if isinstance(normalized.get("tool_calls"), list):
            fixed_calls = []
            for call in normalized["tool_calls"]:
                call_copy = dict(call)
                func = call_copy.get("function")
                if isinstance(func, dict):
                    func_copy = dict(func)
                    args_val = func_copy.get("arguments")
                    if not isinstance(args_val, (str, bytes)):
                        try:
                            func_copy["arguments"] = json.dumps(args_val, ensure_ascii=False)
                        except Exception:
                            func_copy["arguments"] = str(args_val)
                    call_copy["function"] = func_copy
                fixed_calls.append(call_copy)
            normalized["tool_calls"] = fixed_calls
        return normalized

    if not messages:
        return AgentLoopOutput(
            prompt_ids=[],
            response_ids=[],
            response_mask=[],
            num_turns=0,
            metrics={},
        )

    messages = [_normalize_message(m) for m in messages]
    num_turns = 0
    for i in range(len(messages)):
        if messages[i].get("role") == "system":
            continue
        # parallel tool calls are in single turn
        if i == 0 or messages[i].get("role") != messages[i - 1].get("role"):
            num_turns += 1

    prompt_ids = []
    response_ids = []
    response_mask = []
    chat_list = []
    loop = asyncio.get_running_loop()
    # system_prompt_prefix_ids = self.tokenizer.apply_chat_template([{}], add_generation_prompt=False, tokenize=True)
    i = 0
    try:
        while i < len(messages):
            if messages[i].get("role") == "system":
                chat_list.append(messages[i])
                i += 1
                continue
            # initial chat completion
            if messages[i].get("role") == "user":
                if i == 0 or messages[i - 1].get("role") == "system":
                    chat_list.append(messages[i])
                    prompt_ids = await loop.run_in_executor(
                        None,
                        lambda: tokenizer.apply_chat_template(
                            chat_list,
                            tools=tools,
                            add_generation_prompt=True,
                            tokenize=True,
                        ),
                    )
                else:
                    chat_list.append(messages[i])
                    cur_response_ids = await loop.run_in_executor(
                        None,
                        lambda: tokenizer.apply_chat_template(
                            chat_list,
                            add_generation_prompt=False,
                            tokenize=True,
                        ),
                    )
                    response_ids += cur_response_ids
                    response_mask += [0] * len(cur_response_ids)
                chat_list = []
                i += 1
                continue
            # assistant message
            if messages[i].get("role") == "assistant":
                chat_list.append(messages[i])
                cur_response_ids = await loop.run_in_executor(
                    None,
                    lambda: tokenizer.apply_chat_template(
                        chat_list,
                        add_generation_prompt=False,
                        tokenize=True,
                    ),
                )
                chat_list = []
                response_ids += cur_response_ids
                response_mask += [1] * len(cur_response_ids)
                i += 1
                continue
            # follow up chat completion with tool response:
            if messages[i].get("role") == "tool":
                last_assistant_message = messages[i - 1]
                chat_list.append(last_assistant_message)
                token_assistant = await loop.run_in_executor(
                    None,
                    lambda: tokenizer.apply_chat_template(
                        chat_list,
                        add_generation_prompt=False,
                        tokenize=True,
                    ),
                )
                while i < len(messages) and messages[i].get("role") == "tool":
                    chat_list.append(messages[i])
                    i += 1
                token_assistant_tool = await loop.run_in_executor(
                    None,
                    lambda: tokenizer.apply_chat_template(
                        chat_list,
                        add_generation_prompt=False,
                        tokenize=True,
                    ),
                )
                tool_response_ids = token_assistant_tool[len(token_assistant):]
                chat_list = []
                response_ids += tool_response_ids
                response_mask += [0] * len(tool_response_ids)
    except Exception as e:
        raise Exception(f"Failed to convert messages to agentloop_output: {messages}.Exception is: {e}")

    max_response_length = min(response_length, len(response_ids))
    output = AgentLoopOutput(
        prompt_ids=prompt_ids,
        response_ids=response_ids[:max_response_length],
        response_mask=response_mask[:max_response_length],
        num_turns=num_turns,
        metrics={},
    )
    return output


def get_agent_tool_env_and_servers(tool_config: Dict[str, Any] = None) -> tuple[Dict[str, Any], List[str]]:
    if not tool_config or not tool_config.get("url") or not tool_config.get("authorization"):
        tool_config["url"] = os.getenv("MCP_SERVER_URL")
        tool_config["authorization"] = f"Bearer {os.getenv('MCP_SERVER_TOKEN')}"
    url = tool_config.get("url")
    authorization = tool_config.get("authorization")
    mcp_servers_str = tool_config.get("mcp_servers", "")
    if not url or not authorization:
        raise ValueError("url, Authorization are required. Please set MCP_SERVER_URL and MCP_SERVER_TOKEN environment variable \
            or provide them in tool_config parameter.")
    server_name = tool_config.get('server_name', 'aworld-mcp')
    server_type = tool_config.get('type', 'streamable-http')
    timeout = tool_config.get('timeout', 600)
    sse_read_timeout = tool_config.get('sse_read_timeout', 600)
    client_session_timeout_seconds = tool_config.get('client_session_timeout_seconds', 600)
    mcp_config = {
        "mcpServers": {
            server_name: {
                "type": server_type,
                "url": url,
                "headers": {
                    "Authorization": authorization,
                    "MCP_SERVERS": mcp_servers_str,
                },
                "timeout": timeout,
                "sse_read_timeout": sse_read_timeout,
                "client_session_timeout_seconds": client_session_timeout_seconds,
            }
        }
    }
    servers = list(server_name for server_name in mcp_config.get("mcpServers", {}).keys())
    return mcp_config, servers
