# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import asyncio
import inspect
from typing import Any, Dict, List, Tuple, Union

from aworld.core.common import ActionModel, ActionResult
from aworld.core.tool.base import ToolActionExecutor, Tool, AsyncTool
from aworld.logs.util import logger
from aworld.tools.function_tools import get_function_tools


class FunctionToolsExecutor(ToolActionExecutor):
    """Function Tools Executor
    
    This executor is used to execute tools defined by FunctionTools in the AWorld framework.
    """
    
    def __init__(self, tool: Union[Tool, AsyncTool] = None):
        """Initialize the executor
        
        Args:
            tool: Tool instance
        """
        super().__init__(tool)
        self.function_tools_cache = {}
    
    def execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[List[ActionResult], Any]:
        """Synchronously execute tool actions
        
        Args:
            actions: List of actions
            **kwargs: Additional parameters
            
        Returns:
            List of execution results and additional information
        """
        # For synchronous execution, we use asyncio to run the async method
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_execute_action(actions, **kwargs))
    
    async def async_execute_action(self, actions: List[ActionModel], **kwargs) -> Tuple[List[ActionResult], Any]:
        """Asynchronously execute tool actions
        
        Args:
            actions: List of actions
            **kwargs: Additional parameters
            
        Returns:
            List of execution results and additional information
        """
        results = []
        
        for action in actions:
            # Parse action name, format: server_name.tool_name
            if "." not in action.name:
                logger.warning(f"Invalid action name format: {action.name}, expected: server_name.tool_name")
                results.append(ActionResult(
                    content=f"Error: Invalid action name format: {action.name}",
                    keep=False
                ))
                continue
            
            server_name, tool_name = action.name.split(".", 1)
            
            # Get function tools server
            function_tools = self.function_tools_cache.get(server_name)
            if not function_tools:
                function_tools = get_function_tools(server_name)
                if not function_tools:
                    logger.warning(f"FunctionTools server not found: {server_name}")
                    results.append(ActionResult(
                        content=f"Error: FunctionTools server not found: {server_name}",
                        keep=False
                    ))
                    continue
                self.function_tools_cache[server_name] = function_tools
            
            # Check if the tool exists
            if tool_name not in function_tools.tools:
                logger.warning(f"Tool not found: {tool_name} in server {server_name}")
                results.append(ActionResult(
                    content=f"Error: Tool not found: {tool_name}",
                    keep=False
                ))
                continue
            
            # Get tool function
            tool_info = function_tools.tools[tool_name]
            func = tool_info["function"]
            
            try:
                # Parse arguments
                arguments = action.arguments or {}
                
                # Check if the function is asynchronous
                is_async = inspect.iscoroutinefunction(func)
                
                # Call the function
                if is_async:
                    # Asynchronous call
                    result = await func(**arguments)
                else:
                    # Synchronous call
                    result = func(**arguments)
                
                # Process the result
                mcp_result = function_tools._format_result(result)
                action_result = ActionResult(
                    content="",
                    keep=True
                )
                
                # Extract content from MCP result
                if mcp_result and mcp_result.content:
                    if len(mcp_result.content) > 0:
                        from mcp.types import TextContent, ImageContent
                        
                        if isinstance(mcp_result.content[0], TextContent):
                            action_result = ActionResult(
                                content=mcp_result.content[0].text,
                                keep=True,
                                metadata=getattr(mcp_result.content[0], "metadata", {})
                            )
                        elif isinstance(mcp_result.content[0], ImageContent):
                            action_result = ActionResult(
                                content=f"data:image/jpeg;base64,{mcp_result.content[0].data}",
                                keep=True,
                                metadata=getattr(mcp_result.content[0], "metadata", {})
                            )
                
                results.append(action_result)
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                import traceback
                logger.debug(traceback.format_exc())
                
                results.append(ActionResult(
                    content=f"Error: {str(e)}",
                    keep=False
                ))
        
        return results, None 