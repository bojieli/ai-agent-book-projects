import json

import os
import traceback
import asyncio

from typing import Any, Dict, List, Tuple, Union

from mcp.types import TextContent, ImageContent

from aworld.core.common import ActionModel, ActionResult, Observation
from aworld.core.tool.base import ToolActionExecutor, Tool, AsyncTool
from aworld.logs.util import logger
from aworld.mcp_client.server import MCPServer, MCPServerSse
import aworld.mcp_client.utils as mcp_utils
from aworld.utils.common import sync_exec, find_file


class MCPToolExecutor(ToolActionExecutor):
    """A tool executor that uses MCP server to execute actions."""

    def __init__(self, tool: Union[Tool, AsyncTool] = None):
        """Initialize the MCP tool executor."""
        super().__init__(tool)
        self.initialized = False
        self.mcp_servers: Dict[str, MCPServer] = {}
        self._load_mcp_config()

    def _replace_env_variables(self, config):
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var_name = value[2:-1]
                    config[key] = os.getenv(env_var_name, value)
                    logger.info(f"Replaced {value} with {config[key]}")
                elif isinstance(value, dict) or isinstance(value, list):
                    self._replace_env_variables(value)
        elif isinstance(config, list):
            for index, item in enumerate(config):
                if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                    env_var_name = item[2:-1]
                    config[index] = os.getenv(env_var_name, item)
                    logger.info(f"Replaced {item} with {config[index]}")
                elif isinstance(item, dict) or isinstance(item, list):
                    self._replace_env_variables(item)

    def _load_mcp_config(self) -> None:
        """Load MCP server configurations from config file."""
        try:
            config_data = {}
            if mcp_utils.MCP_SERVERS_CONFIG:
                config_data=mcp_utils.MCP_SERVERS_CONFIG
            else:
                # Priority given to the running path.
                config_path = find_file(filename='mcp.json')
                if not os.path.exists(config_path):
                    # Use relative path for config file
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    config_path = os.path.normpath(os.path.join(current_dir, "../../config/mcp.json"))
                logger.info(f"mcp conf path: {config_path}")

                with open(config_path, "r") as f:
                    config_data = json.load(f)

                # Replace environment variables in the configuration
                self._replace_env_variables(config_data)

            # Load all server configurations
            for server_name, server_config in config_data.get("mcpServers", {}).items():
                # Skip disabled servers
                if server_config.get("disabled", False):
                    continue

                # Handle SSE server
                if "url" in server_config:
                    self.mcp_servers[server_name] = {
                        "type": "sse",
                        "url": server_config["url"],
                        "instance": None,
                        "timeout": server_config.get('timeout', 5.),
                        "sse_read_timeout": server_config.get('sse_read_timeout', 300.0),
                        "headers": server_config.get('headers')
                    }
                # Handle stdio server
                elif "command" in server_config:
                    self.mcp_servers[server_name] = {
                        "type": "stdio",
                        "command": server_config["command"],
                        "args": server_config.get("args", []),
                        "env": server_config.get("env", {}),
                        "cwd": server_config.get("cwd"),
                        "encoding": server_config.get("encoding", "utf-8"),
                        "encoding_error_handler": server_config.get("encoding_error_handler", "strict"),
                        "instance": None
                    }

            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to load MCP config: {traceback.format_exc()}")

    async def _get_or_create_server(self, server_name: str) -> MCPServer:
        """Get an existing MCP server instance or create a new one."""
        if server_name not in self.mcp_servers:
            raise ValueError(f"MCP server '{server_name}' not found in configuration")

        server_info = self.mcp_servers[server_name]

        # If an instance already exists, check if it's available and reuse it
        if server_info.get("instance"):
            return server_info["instance"]

        server_type = server_info.get("type", "sse")

        try:
            if server_type == "sse":
                # Create new SSE server instance
                server_params = {
                    "url": server_info["url"],
                    "timeout": server_info['timeout'],
                    "sse_read_timeout": server_info['sse_read_timeout'],
                    "headers": server_info['headers']
                }

                server = MCPServerSse(server_params, cache_tools_list=True, name=server_name)
            elif server_type == "stdio":
                # Create new stdio server instance
                server_params = {
                    "command": server_info["command"],
                    "args": server_info["args"],
                    "env": server_info["env"],
                    "cwd": server_info.get("cwd"),
                    "encoding": server_info["encoding"],
                    "encoding_error_handler": server_info["encoding_error_handler"]
                }

                from aworld.mcp_client.server import MCPServerStdio
                server = MCPServerStdio(server_params, cache_tools_list=True, name=server_name)
            else:
                raise ValueError(f"Unsupported MCP server type: {server_type}")

            # Try to connect, with special handling for cancellation exceptions
            try:
                await server.connect()
            except asyncio.CancelledError:
                # When the task is cancelled, ensure resources are cleaned up
                logger.warning(f"Connection to server '{server_name}' was cancelled")
                await server.cleanup()
                raise

            server_info["instance"] = server
            return server

        except asyncio.CancelledError:
            # Pass cancellation exceptions up to be handled by the caller
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{server_name}': {e}")
            raise

    async def async_execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[
        List[ActionResult], Any]:
        """Execute actions using the MCP server.

        Args:
            actions: A list of action models to execute
            **kwargs: Additional arguments

        Returns:
            A list of action results
        """
        if not self.initialized:
            raise RuntimeError("MCP Tool Executor not initialized")

        if not actions:
            return [], None

        results = []
        for action in actions:
            # Get server and operation information
            server_name = action.tool_name
            if not server_name:
                raise ValueError("Missing tool_name in action model")

            action_name = action.action_name
            if not action_name:
                raise ValueError("Missing action_name in action model")

            params = action.params or {}

            try:
                server = self.mcp_servers.get(server_name, {}).get('instance', None)
                if not server:
                    # Get or create MCP server
                    server = await self._get_or_create_server(server_name)

                # Call the tool and process results
                try:
                    result = await server.call_tool(action_name, params)

                    if result and result.content:
                        if isinstance(result.content[0], TextContent):
                            action_result = ActionResult(
                                content=result.content[0].text,
                                keep=True
                            )
                        elif isinstance(result.content[0], ImageContent):
                            action_result = ActionResult(
                                content=f"data:image/jpeg;base64,{result.content[0].data}",
                                keep=True
                            )
                        else:
                            action_result = ActionResult(
                                content="",
                                keep=True
                            )
                            logger.warning("Unsupported content type is error:")
                    else:
                        action_result = ActionResult(
                            content="",
                            keep=True
                        )
                        logger.warning("mcp result is null")

                    results.append(action_result)
                except asyncio.CancelledError:
                    # Log cancellation exception, reset server connection to avoid async context confusion
                    logger.warning(f"Tool call to {action_name} on {server_name} was cancelled")
                    if server_name in self.mcp_servers and self.mcp_servers[server_name].get("instance"):
                        try:
                            await self.mcp_servers[server_name]["instance"].cleanup()
                            self.mcp_servers[server_name]["instance"] = None
                        except Exception as cleanup_error:
                            logger.error(f"Error cleaning up server after cancellation: {cleanup_error}")
                    # Re-raise exception to notify upper level caller
                    raise

            except asyncio.CancelledError:
                # Pass cancellation exception
                logger.warning("Async execution was cancelled")
                raise

            except Exception as e:
                # Handle general errors
                error_msg = str(e)
                logger.error(f"Error executing MCP action: {error_msg}")
                action_result = ActionResult(
                    content=f"Error executing tool: {error_msg}",
                    keep=True
                )
                results.append(action_result)

        return results, None

    async def cleanup(self) -> None:
        """Clean up all MCP server connections."""
        for server_name, server_info in self.mcp_servers.items():
            if server_info.get("instance"):
                try:
                    await server_info["instance"].cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up MCP server {server_name}: {e}")

    async def close(self, keys: List[str] = []) -> None:
        if keys:
            for key in keys:
                if key in self.mcp_servers:
                    server_info = self.mcp_servers[key]
                    # Fixme: Have resources leak, MCP server may clean fail.
                    if server_info.get("type") == "stdio":
                        server_info["instance"] = None
                        continue

                    try:
                        await server_info["instance"].cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up MCP server {key}: {e}")

    def execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[
        List[ActionResult], Any]:
        return sync_exec(self.async_execute_action, actions, **kwargs)
