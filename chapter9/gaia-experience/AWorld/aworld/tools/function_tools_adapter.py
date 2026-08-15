# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import asyncio
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult, Tool as MCPTool

from aworld.core.common import ActionResult
from aworld.logs.util import logger
from aworld.mcp_client.server import MCPServer
from aworld.tools.function_tools import get_function_tools, FunctionToolsAdapter as BaseAdapter


class FunctionToolsMCPAdapter(MCPServer):
    """Adapter for FunctionTools to MCPServer interface
    
    This adapter allows FunctionTools to be used like a standard MCPServer,
    supporting list_tools and call_tool methods.
    """
    
    def __init__(self, name: str):
        """Initialize the adapter
        
        Args:
            name: Function tool server name
        """
        self._adapter = BaseAdapter(name)
        self._name = self._adapter.name
        self._connected = False
    
    @property
    def name(self) -> str:
        """Server name"""
        return self._name
    
    async def connect(self):
        """Connect to the server
        
        For FunctionTools, this is a no-op since no actual connection is needed.
        """
        self._connected = True
    
    async def cleanup(self):
        """Clean up server resources
        
        For FunctionTools, this is a no-op since there are no resources to clean up.
        """
        self._connected = False
    
    async def list_tools(self) -> List[MCPTool]:
        """List all tools and their descriptions
        
        Returns:
            List of tools
        """
        if not self._connected:
            await self.connect()
        
        # Directly return the tool list from FunctionTools, which now returns MCPTool objects
        return await self._adapter.list_tools()
    
    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> CallToolResult:
        """Call the specified tool function
        
        Args:
            tool_name: Tool name
            arguments: Tool parameters
            
        Returns:
            Tool call result
        """
        if not self._connected:
            await self.connect()
        
        # Use async method to call the tool
        return await self._adapter.call_tool(tool_name, arguments)


def get_function_tools_mcp_adapter(name: str) -> FunctionToolsMCPAdapter:
    """Get MCP adapter for FunctionTools
    
    Args:
        name: Function tool server name
        
    Returns:
        MCPServer adapter
        
    Raises:
        ValueError: When the function tool server with the specified name does not exist
    """
    function_tools = get_function_tools(name)
    if not function_tools:
        raise ValueError(f"FunctionTools '{name}' not found")
    
    return FunctionToolsMCPAdapter(name) 