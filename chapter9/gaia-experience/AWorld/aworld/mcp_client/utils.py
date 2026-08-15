import logging
from datetime import timedelta
from typing import List, Dict, Any
import json
import os
from contextlib import AsyncExitStack
import traceback

import requests
from aworld.core.context.base import Context
from mcp.types import TextContent, ImageContent

from aworld.core.common import ActionResult

from aworld.logs.util import logger
from aworld.mcp_client.server import MCPServer, MCPServerSse, MCPServerStdio, MCPServerStreamableHttp
from aworld.tools import get_function_tools
from aworld.utils.common import find_file

MCP_SERVERS_CONFIG = {}


def get_function_tool(sever_name: str) -> List[Dict[str, Any]]:
    openai_tools = []
    try:
        if not sever_name:
            return []
        tool_server = get_function_tools(sever_name)
        if not tool_server:
            return []
        tools = tool_server.list_tools()
        if not tools:
            return []
        for tool in tools:
            required = []
            properties = {}
            if tool.inputSchema and tool.inputSchema.get("properties"):
                required = tool.inputSchema.get("required", [])
                _properties = tool.inputSchema["properties"]
                for param_name, param_info in _properties.items():
                    param_type = (
                        param_info.get("type")
                        if param_info.get("type") != "str"
                           and param_info.get("type") is not None
                        else "string"
                    )
                    param_desc = param_info.get("description", "")
                    if param_type == "array":
                        # Handle array type parameters
                        items_info = param_info.get("items", {})
                        item_type = items_info.get("type", "string")

                        # Process nested array type parameters
                        if item_type == "array":
                            nested_items = items_info.get("items", {})
                            nested_type = nested_items.get("type", "string")

                            # If the nested type is an object
                            if nested_type == "object":
                                properties[param_name] = {
                                    "description": param_desc,
                                    "type": param_type,
                                    "items": {
                                        "type": item_type,
                                        "items": {
                                            "type": nested_type,
                                            "properties": nested_items.get(
                                                "properties", {}
                                            ),
                                            "required": nested_items.get(
                                                "required", []
                                            ),
                                        },
                                    },
                                }
                            else:
                                properties[param_name] = {
                                    "description": param_desc,
                                    "type": param_type,
                                    "items": {
                                        "type": item_type,
                                        "items": {"type": nested_type},
                                    },
                                }
                        # Process object type cases
                        elif item_type == "object":
                            properties[param_name] = {
                                "description": param_desc,
                                "type": param_type,
                                "items": {
                                    "type": item_type,
                                    "properties": items_info.get("properties", {}),
                                    "required": items_info.get("required", []),
                                },
                            }
                        # Process basic type cases
                        else:
                            if item_type == "str":
                                item_type = "string"
                            properties[param_name] = {
                                "description": param_desc,
                                "type": param_type,
                                "items": {"type": item_type},
                            }
                    else:
                        # Handle non-array type parameters
                        properties[param_name] = {
                            "description": param_desc,
                            "type": param_type,
                        }

            openai_function_schema = {
                "name": f"mcp__{sever_name}__{tool.name}",
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
            openai_tools.append(
                {
                    "type": "function",
                    "function": openai_function_schema,
                }
            )
        logging.info(
            f"✅ function_tool_server #({sever_name}) connected success，tools: {len(tools)}"
        )

    except Exception as e:
        logging.warning(
            f"server_name-get_function_tool:{sever_name} translate failed: {e}"
        )
        return []
    finally:
        return openai_tools


async def run(mcp_servers: list[MCPServer],black_tool_actions: Dict[str, List[str]] = None) -> List[Dict[str, Any]]:
    openai_tools = []
    for i, server in enumerate(mcp_servers):
        try:
            tools = await server.list_tools()
            for tool in tools:
                balck_server = server.name
                if server.name.startswith("mcp__"):
                    balck_server = server.name[5:] if len(server.name) > 5 else server.name
                if (black_tool_actions and
                        balck_server in black_tool_actions and
                        black_tool_actions[balck_server] and
                        tool.name in black_tool_actions[balck_server]):
                    logging.info(
                        f"server #{i + 1} ({balck_server}) black_tool_actions: {tool.name}"
                    )
                    continue
                required = []
                properties = {}
                if tool.inputSchema and tool.inputSchema.get("properties"):
                    required = tool.inputSchema.get("required", [])
                    _properties = tool.inputSchema["properties"]
                    for param_name, param_info in _properties.items():
                        param_type = (
                            param_info.get("type")
                            if param_info.get("type") != "str"
                               and param_info.get("type") is not None
                            else "string"
                        )
                        param_desc = param_info.get("description", "")
                        if param_type == "array":
                            # Handle array type parameters
                            items_info = param_info.get("items", {})
                            item_type = items_info.get("type", "string")

                            # Process nested array type parameters
                            if item_type == "array":
                                nested_items = items_info.get("items", {})
                                nested_type = nested_items.get("type", "string")

                                # If the nested type is an object
                                if nested_type == "object":
                                    properties[param_name] = {
                                        "description": param_desc,
                                        "type": param_type,
                                        "items": {
                                            "type": item_type,
                                            "items": {
                                                "type": nested_type,
                                                "properties": nested_items.get(
                                                    "properties", {}
                                                ),
                                                "required": nested_items.get(
                                                    "required", []
                                                ),
                                            },
                                        },
                                    }
                                else:
                                    properties[param_name] = {
                                        "description": param_desc,
                                        "type": param_type,
                                        "items": {
                                            "type": item_type,
                                            "items": {"type": nested_type},
                                        },
                                    }
                            # Process object type cases
                            elif item_type == "object":
                                properties[param_name] = {
                                    "description": param_desc,
                                    "type": param_type,
                                    "items": {
                                        "type": item_type,
                                        "properties": items_info.get("properties", {}),
                                        "required": items_info.get("required", []),
                                    },
                                }
                            # Process basic type cases
                            else:
                                if item_type == "str":
                                    item_type = "string"
                                properties[param_name] = {
                                    "description": param_desc,
                                    "type": param_type,
                                    "items": {"type": item_type},
                                }
                        else:
                            # Handle non-array type parameters
                            properties[param_name] = {
                                "description": param_desc,
                                "type": param_type,
                            }

                openai_function_schema = {
                    "name": f"{server.name}__{tool.name}",
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
                openai_tools.append(
                    {
                        "type": "function",
                        "function": openai_function_schema,
                    }
                )
            logging.info(
                f"✅ server #{i + 1} ({server.name}) connected success，tools: {len(tools)}"
            )

        except Exception as e:
            logging.warning(
                f"❌ server #{i + 1} ({server.name}) connect fail: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            continue

    return openai_tools


async def mcp_tool_desc_transform_v2(
        tools: List[str] = None, mcp_config: Dict[str, Any] = None, context: Context = None,
        server_instances: Dict[str, Any] = None,
        black_tool_actions: Dict[str, List[str]] = None
) -> List[Dict[str, Any]]:
    # todo sandbox mcp_config get from registry

    if not mcp_config:
        return []
    config = mcp_config
    global MCP_SERVERS_CONFIG
    MCP_SERVERS_CONFIG = config
    mcp_servers_config = config.get("mcpServers", {})
    server_configs = []
    openai_tools = []
    mcp_openai_tools = []

    for server_name, server_config in mcp_servers_config.items():
        # Skip disabled servers
        if server_config.get("disabled", False):
            continue

        if tools is None or server_name in tools:
            # Handle SSE server
            if "function_tool" == server_config.get("type", ""):
                try:
                    tmp_function_tool = get_function_tool(server_name)
                    openai_tools.extend(tmp_function_tool)
                except Exception as e:
                    logging.warning(f"server_name:{server_name} translate failed: {e}")
            elif "api" == server_config.get("type", ""):
                api_result = requests.get(server_config["url"] + "/list_tools")
                try:
                    if not api_result or not api_result.text:
                        continue
                        # return None
                    data = json.loads(api_result.text)
                    if not data or not data.get("tools"):
                        continue
                    for item in data.get("tools"):
                        tmp_function = {
                            "type": "function",
                            "function": {
                                "name": "mcp__" + server_name + "__" + item["name"],
                                "description": item["description"],
                                "parameters": {
                                    **item["parameters"],
                                    "properties": {
                                        k: v
                                        for k, v in item["parameters"]
                                        .get("properties", {})
                                        .items()
                                        if "default" not in v
                                    },
                                },
                            },
                        }
                        openai_tools.append(tmp_function)
                except Exception as e:
                    logging.warning(f"server_name:{server_name} translate failed: {e}")
            elif "sse" == server_config.get("type", ""):
                server_configs.append(
                    {
                        "name": "mcp__" + server_name,
                        "type": "sse",
                        "params": {
                            "url": server_config["url"],
                            "headers": server_config.get("headers"),
                            "timeout": server_config.get("timeout"),
                            "sse_read_timeout": server_config.get("sse_read_timeout"),
                            "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds")
                        },
                    }
                )

            elif "streamable-http" == server_config.get("type", ""):
                server_configs.append(
                    {
                        "name": "mcp__" + server_name,
                        "type": "streamable-http",
                        "params": {
                            "url": server_config["url"],
                            "headers": server_config.get("headers"),
                            "timeout": server_config.get("timeout"),
                            "sse_read_timeout": server_config.get("sse_read_timeout"),
                            "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds")
                        },
                    }
                )
            # Handle stdio server
            else:
                # elif "stdio" == server_config.get("type", ""):
                server_configs.append(
                    {
                        "name": "mcp__" + server_name,
                        "type": "stdio",
                        "params": {
                            "command": server_config["command"],
                            "args": server_config.get("args", []),
                            "env": server_config.get("env", {}),
                            "cwd": server_config.get("cwd"),
                            "encoding": server_config.get("encoding", "utf-8"),
                            "encoding_error_handler": server_config.get(
                                "encoding_error_handler", "strict"
                            ),
                            "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds")
                        },
                    }
                )

    if not server_configs:
        return openai_tools
    servers = []
    for server_config in server_configs:
        try:
            _mcp_openai_tools = []
            async with AsyncExitStack() as stack:
                if server_config["type"] == "sse":
                    params = server_config["params"].copy()
                    headers = params.get("headers") or {}
                    if context and context.session_id:
                        headers["SESSION_ID"] = context.session_id

                    if context and context.user:
                        headers["USER_ID"] = context.user
                    params["headers"] = headers

                    server = MCPServerSse(
                        name=server_config["name"], params=params
                    )
                elif server_config["type"] == "streamable-http":
                    params = server_config["params"].copy()
                    headers = params.get("headers") or {}
                    if context and context.session_id:
                        headers["SESSION_ID"] = context.session_id
                    if context and context.user:
                        headers["USER_ID"] = context.user
                    params["headers"] = headers
                    if "timeout" in params and not isinstance(params["timeout"], timedelta):
                        params["timeout"] = timedelta(seconds=float(params["timeout"]))
                    if "sse_read_timeout" in params and not isinstance(params["sse_read_timeout"], timedelta):
                        params["sse_read_timeout"] = timedelta(seconds=float(params["sse_read_timeout"]))
                    server = MCPServerStreamableHttp(
                        name=server_config["name"], params=params
                    )
                elif server_config["type"] == "stdio":
                    server = MCPServerStdio(
                        name=server_config["name"], params=server_config["params"]
                    )
                else:
                    logging.warning(
                        f"Unsupported MCP server type: {server_config['type']}"
                    )
                    continue

                server = await stack.enter_async_context(server)
                #servers.append(server)
                _mcp_openai_tools = await run([server],black_tool_actions)
            if _mcp_openai_tools:
                mcp_openai_tools.extend(_mcp_openai_tools)
        except BaseException as err:
            # single
            logging.warning(
                f"Failed to get tools for MCP server '{server_config['name']}'.\n"
                f"Error: {err}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            continue

    #async with AsyncExitStack() as stack:

        #mcp_openai_tools = await run(servers)

    if mcp_openai_tools:
        openai_tools.extend(mcp_openai_tools)

    return openai_tools


async def mcp_tool_desc_transform(
        tools: List[str] = None, mcp_config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    # todo sandbox mcp_config get from registry

    if not mcp_config:
        return []
    config = mcp_config
    global MCP_SERVERS_CONFIG
    MCP_SERVERS_CONFIG = config
    mcp_servers_config = config.get("mcpServers", {})
    server_configs = []
    openai_tools = []
    mcp_openai_tools = []

    for server_name, server_config in mcp_servers_config.items():
        # Skip disabled servers
        if server_config.get("disabled", False):
            continue

        if tools is None or server_name in tools:
            # Handle SSE server
            if "function_tool" == server_config.get("type", ""):
                try:
                    tmp_function_tool = get_function_tool(server_name)
                    openai_tools.extend(tmp_function_tool)
                except Exception as e:
                    logging.warning(f"server_name:{server_name} translate failed: {e}")
            elif "api" == server_config.get("type", ""):
                api_result = requests.get(server_config["url"] + "/list_tools")
                try:
                    if not api_result or not api_result.text:
                        continue
                        # return None
                    data = json.loads(api_result.text)
                    if not data or not data.get("tools"):
                        continue
                    for item in data.get("tools"):
                        tmp_function = {
                            "type": "function",
                            "function": {
                                "name": "mcp__" + server_name + "__" + item["name"],
                                "description": item["description"],
                                "parameters": {
                                    **item["parameters"],
                                    "properties": {
                                        k: v
                                        for k, v in item["parameters"]
                                        .get("properties", {})
                                        .items()
                                        if "default" not in v
                                    },
                                },
                            },
                        }
                        openai_tools.append(tmp_function)
                except Exception as e:
                    logging.warning(f"server_name:{server_name} translate failed: {e}")
            elif "sse" == server_config.get("type", ""):
                server_configs.append(
                    {
                        "name": "mcp__" + server_name,
                        "type": "sse",
                        "params": {
                            "url": server_config["url"],
                            "headers": server_config.get("headers"),
                            "timeout": server_config.get("timeout"),
                            "sse_read_timeout": server_config.get("sse_read_timeout"),
                            "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds")
                        },
                    }
                )

            elif "streamable-http" == server_config.get("type", ""):
                server_configs.append(
                    {
                        "name": "mcp__" + server_name,
                        "type": "streamable-http",
                        "params": {
                            "url": server_config["url"],
                            "headers": server_config.get("headers"),
                            "timeout": server_config.get("timeout"),
                            "sse_read_timeout": server_config.get("sse_read_timeout"),
                            "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds")
                        },
                    }
                )
            # Handle stdio server
            else:
                # elif "stdio" == server_config.get("type", ""):
                server_configs.append(
                    {
                        "name": "mcp__" + server_name,
                        "type": "stdio",
                        "params": {
                            "command": server_config["command"],
                            "args": server_config.get("args", []),
                            "env": server_config.get("env", {}),
                            "cwd": server_config.get("cwd"),
                            "encoding": server_config.get("encoding", "utf-8"),
                            "encoding_error_handler": server_config.get(
                                "encoding_error_handler", "strict"
                            ),
                            "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds")
                        },
                    }
                )

    if not server_configs:
        return openai_tools

    async with AsyncExitStack() as stack:
        servers = []
        for server_config in server_configs:
            try:
                if server_config["type"] == "sse":
                    server = MCPServerSse(
                        name=server_config["name"], params=server_config["params"]
                    )
                elif server_config["type"] == "streamable-http":
                    params = server_config["params"].copy()
                    if "timeout" in params and not isinstance(params["timeout"], timedelta):
                        params["timeout"] = timedelta(seconds=float(params["timeout"]))
                    if "sse_read_timeout" in params and not isinstance(params["sse_read_timeout"], timedelta):
                        params["sse_read_timeout"] = timedelta(seconds=float(params["sse_read_timeout"]))
                    server = MCPServerStreamableHttp(
                        name=server_config["name"], params=params
                    )
                elif server_config["type"] == "stdio":
                    server = MCPServerStdio(
                        name=server_config["name"], params=server_config["params"]
                    )
                else:
                    logging.warning(
                        f"Unsupported MCP server type: {server_config['type']}"
                    )
                    continue

                server = await stack.enter_async_context(server)
                servers.append(server)
            except BaseException as err:
                # single
                logging.error(
                    f"Failed to get tools for MCP server '{server_config['name']}'.\n"
                    f"Error: {err}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )

        mcp_openai_tools = await run(servers)

    if mcp_openai_tools:
        openai_tools.extend(mcp_openai_tools)

    return openai_tools


async def call_function_tool(
        server_name: str,
        tool_name: str,
        parameter: Dict[str, Any] = None,
        mcp_config: Dict[str, Any] = None,
) -> ActionResult:
    """Specifically handle API type server calls

    Args:
        server_name: Server name
        tool_name: Tool name
        parameter: Parameters
        mcp_config: MCP configuration

    Returns:
        ActionResult: Call result
    """
    action_result = ActionResult(
        tool_name=server_name, action_name=tool_name, content="", keep=True
    )
    try:
        tool_server = get_function_tools(server_name)
        if not tool_server:
            return action_result
        call_result_raw = tool_server.call_tool(tool_name, parameter)
        if call_result_raw and call_result_raw.content:
            if isinstance(call_result_raw.content[0], TextContent):
                action_result = ActionResult(
                    tool_name=server_name,
                    action_name=tool_name,
                    content=call_result_raw.content[0].text,
                    keep=True,
                    metadata=call_result_raw.content[0].model_extra.get("metadata", {}),
                )
            elif isinstance(call_result_raw.content[0], ImageContent):
                action_result = ActionResult(
                    tool_name=server_name,
                    action_name=tool_name,
                    content=f"data:image/jpeg;base64,{call_result_raw.content[0].data}",
                    keep=True,
                    metadata=call_result_raw.content[0].model_extra.get("metadata", {}),
                )

    except Exception as e:
        logging.warning(f"call_function_tool ({server_name})({tool_name}) failed: {e}")
        action_result = ActionResult(
            tool_name=server_name, action_name=tool_name, content="", keep=True
        )

    return action_result


async def call_api(
        server_name: str,
        tool_name: str,
        parameter: Dict[str, Any] = None,
        mcp_config: Dict[str, Any] = None,
) -> ActionResult:
    """Specifically handle API type server calls

    Args:
        server_name: Server name
        tool_name: Tool name
        parameter: Parameters
        mcp_config: MCP configuration

    Returns:
        ActionResult: Call result
    """
    action_result = ActionResult(
        tool_name=server_name, action_name=tool_name, content="", keep=True
    )

    if not mcp_config or mcp_config.get("mcpServers") is None:
        return action_result

    mcp_servers = mcp_config.get("mcpServers")
    if not mcp_servers.get(server_name):
        return action_result

    server_config = mcp_servers.get(server_name)
    if "api" != server_config.get("type", ""):
        logging.warning(
            f"Server {server_name} is not API type, should use call_tool instead"
        )
        return action_result

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url=server_config["url"] + "/" + tool_name, headers=headers, json=parameter
        )
        action_result = ActionResult(
            tool_name=server_name,
            action_name=tool_name,
            content=response.text,
            keep=True,
        )
    except Exception as e:
        logging.warning(f"call_api ({server_name})({tool_name}) failed: {e}")
        action_result = ActionResult(
            tool_name=server_name,
            action_name=tool_name,
            content=f"Error calling API: {str(e)}",
            keep=True,
        )

    return action_result


async def get_server_instance(
        server_name: str, mcp_config: Dict[str, Any] = None,
        context: Context = None
) -> Any:
    """Get server instance, create a new one if it doesn't exist

    Args:
        server_name: Server name
        mcp_config: MCP configuration

    Returns:
        Server instance or None (if creation fails)
    """
    if not mcp_config or mcp_config.get("mcpServers") is None:
        return None

    mcp_servers = mcp_config.get("mcpServers")
    if not mcp_servers.get(server_name):
        return None

    server_config = mcp_servers.get(server_name)
    try:
        # API type servers use special handling, no need for persistent connections
        # Note: We've already handled API type in McpServers.call_tool method
        # Here we don't return None, but let the caller handle it
        if "api" == server_config.get("type", ""):
            logging.info(f"API server {server_name} doesn't need persistent connection")
            return None
        elif "sse" == server_config.get("type", ""):
            headers = server_config.get("headers") or {}
            if context and context.session_id:
                headers["SESSION_ID"] = context.session_id
            if context and context.user:
                headers["USER_ID"] = context.user
            server = MCPServerSse(
                name=server_name,
                params={
                    "url": server_config["url"],
                    "headers": headers,
                    "timeout": server_config.get("timeout", 5.0),
                    "sse_read_timeout": server_config.get("sse_read_timeout", 300.0),
                    "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds", 300.0),
                },
            )
            await server.connect()
            logging.info(f"Successfully connected to SSE server: {server_name}")
            return server
        elif "streamable-http" == server_config.get("type", ""):
            headers = server_config.get("headers") or {}
            if context and context.session_id:
                headers["SESSION_ID"] = context.session_id
            if context and context.user:
                headers["USER_ID"] = context.user
            server = MCPServerStreamableHttp(
                name=server_name,
                params={
                    "url": server_config["url"],
                    "headers": headers,
                    "timeout": timedelta(seconds=server_config.get("timeout", 120.0)),
                    "sse_read_timeout": timedelta(seconds=server_config.get("sse_read_timeout", 300.0)),
                },
            )
            await server.connect()
            logging.info(f"Successfully connected to STREAMABLE-HTTP server: {server_name}")
            return server
        else:  # stdio type
            params = {
                "command": server_config["command"],
                "args": server_config.get("args", []),
                "env": server_config.get("env", {}),
                "cwd": server_config.get("cwd"),
                "encoding": server_config.get("encoding", "utf-8"),
                "encoding_error_handler": server_config.get(
                    "encoding_error_handler", "strict"
                ),
                "client_session_timeout_seconds": server_config.get("client_session_timeout_seconds", 300.0),
            }
            server = MCPServerStdio(name=server_name, params=params)
            await server.connect()
            logging.info(f"Successfully connected to stdio server: {server_name}")
            return server
    except Exception as e:
        logging.warning(f"Failed to create server instance for {server_name}: {e}")
        return None


async def cleanup_server(server):
    """Clean up server connection

    Args:
        server: Server instance
    """
    try:
        if hasattr(server, "cleanup"):
            await server.cleanup()
        elif hasattr(server, "close"):
            await server.close()
        logging.info(
            f"Successfully cleaned up server: {getattr(server, 'name', 'unknown')}"
        )
    except Exception as e:
        logging.warning(f"Failed to cleanup server: {e}")
