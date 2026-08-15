import traceback
from typing import Any, Callable, Sequence
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.fastmcp.resources import Resource
from mcp.server.fastmcp.tools import Tool, ToolManager
from mcp.server.session import ServerSessionT
from mcp.shared.context import LifespanContextT, RequestT
from mcp.types import ContentBlock, ToolAnnotations
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata
import logging
from mcp.server.fastmcp.tools.base import Tool as ServerTool
from mcp.types import Tool as ClientTool

from .mcp_server_executor import MCPServerExecutor
from .mcp_server_loader import MCPServerLoader

logger = logging.getLogger(__name__)


class MCPServerProxy(FastMCP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mcp_tool_schema: dict[str, list[dict[str, Any]]] = {}
        self._mcp_server_executors: dict[str, MCPServerExecutor] = {}
        self._mcp_server_loader = MCPServerLoader()

    async def initialize(self):
        self._load_tool_schema()
        self._load_mcp_servers()

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[ContentBlock] | dict[str, Any]:
        """Call a tool by name with arguments."""
        try:
            context = self.get_context()
            request_mcp_server_executor = self._get_request_mcp_server_executor(
                tool_name=name
            )

            return await request_mcp_server_executor.call_tool(
                name, arguments, context=context, convert_result=True
            )
        except:
            logger.error(f"Error calling tool {name}: {traceback.format_exc()}")
            raise

    async def list_tools(self) -> list[ClientTool]:
        """List all available tools."""
        try:
            request_mcp_servers = self._get_request_mcp_servers()

            request_tools = [
                tool
                for server_name, server_tools in self._mcp_tool_schema.items()
                if server_name in request_mcp_servers
                for tool in server_tools
            ]

            return [
                ClientTool(
                    name=tool.get("name", ""),
                    title=tool.get("title", ""),
                    description=tool.get("description", ""),
                    inputSchema=tool.get("inputSchema", {}),
                    outputSchema=tool.get("outputSchema", {}),
                    annotations=tool.get("annotations", {}),
                    _meta=tool.get("_meta", {}),
                )
                for tool in request_tools
            ]
        except:
            logger.error(f"Error listing tools: {traceback.format_exc()}")
            raise

    def _load_tool_schema(self):
        self._mcp_tool_schema = self._mcp_server_loader.load_mcp_tool_schema()
        mcp_tool_schema = ""
        for server_name, server_tools in self._mcp_tool_schema.items():
            mcp_tool_schema += f"  {server_name}:\n"
            for tool in server_tools:
                mcp_tool_schema += f"    - {tool.get('name', '')}\n"
        logger.info(f"Loaded MCP tool schema: mcp_tool_schema={mcp_tool_schema}")

    def _load_mcp_servers(self):
        for name, config in self._mcp_server_loader.load_mcp_servers_config().items():
            self._mcp_server_executors[name] = MCPServerExecutor(name, config)
            logger.info(f"Added MCP server executor: {name}")

    def _get_request_mcp_servers(self) -> list[str]:
        context = self.get_context()
        request_servers = context.request_context.request.headers.get("MCP_SERVERS")
        if request_servers:
            return [server.strip() for server in request_servers.split(",")]
        return []

    def _get_request_mcp_server_executor(self, tool_name: str) -> MCPServerExecutor:
        request_mcp_servers = self._get_request_mcp_servers()

        request_tools = {
            server_name: tool
            for server_name, server_tools in self._mcp_tool_schema.items()
            if server_name in request_mcp_servers
            for tool in server_tools
            if tool.get("name", "") == tool_name
        }

        if not request_tools:
            raise ToolError(f"Tool {tool_name} not found")
        else:
            if len(request_tools) > 1:
                logger.warning(
                    f"Tool {tool_name} found in multiple MCP servers: {request_tools}"
                )
            server_name = list(request_tools.keys())[0]
            return self._mcp_server_executors[server_name]
