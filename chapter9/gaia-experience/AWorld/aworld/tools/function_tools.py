# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import inspect
import json
import logging
import traceback
from typing import Any, Dict, List, Optional, Union, get_type_hints

from mcp.types import TextContent, ImageContent, CallToolResult
from mcp import Tool as MCPTool
from pydantic import Field, create_model
from pydantic.fields import FieldInfo  # Import FieldInfo type

from aworld.core.common import ActionResult
from aworld.logs.util import logger

# Global function tools server registry
_FUNCTION_TOOLS_REGISTRY = {}

def _register_function_tools(function_tools):
    """Register function tools server to global registry"""
    _FUNCTION_TOOLS_REGISTRY[function_tools.name] = function_tools
    logger.info(f"Registered FunctionTools server: {function_tools.name}")

def get_function_tools(name):
    """Get specified function tools server"""
    return _FUNCTION_TOOLS_REGISTRY.get(name)

def list_function_tools():
    """List all registered function tools servers"""
    return list(_FUNCTION_TOOLS_REGISTRY.keys())


class FunctionTools:
    """Function tools server, providing tool registration and calling mechanism similar to MCP
    
    Example:
        ```python
        # Create function tools server
        function = FunctionTools("my-server", description="My function tools server")
        
        # Define tool function
        @function.tool(description="Example search function")
        def search(query: str, limit: int = 10) -> str:
            # Actual search logic
            results = [f"Result {i} for {query}" for i in range(limit)]
            return json.dumps(results)
            
        # Using Field decorator
        @function.tool(description="Example search function")
        def search(
            query: str = Field(description="Search query"),
            limit: int = Field(10, description="Max results")
        ) -> str:
            # Actual search logic
            results = [f"Result {i} for {query}" for i in range(limit)]
            return json.dumps(results)
        ```
    """
    
    def __new__(cls, name: str, description: Optional[str] = None, version: str = "1.0"):
        """Implement singleton pattern, return existing instance if one with same name exists
        
        Args:
            name: Server name
            description: Server description
            version: Server version
        """
        # Check if instance with same name already exists
        if name in _FUNCTION_TOOLS_REGISTRY:
            logger.info(f"Returning existing FunctionTools instance: {name}")
            return _FUNCTION_TOOLS_REGISTRY[name]
        
        # Create new instance
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, name: str, description: Optional[str] = None, version: str = "1.0"):
        """Initialize function tools server
        
        Args:
            name: Server name
            description: Server description
            version: Server version
        """
        # Skip if already initialized
        if hasattr(self, 'name') and self.name == name:
            return
            
        self.name = name
        self.description = description or f"Function tools server: {name}"
        self.version = version
        self.tools = {}
        
        # Register server to global registry
        _register_function_tools(self)
    
    def tool(self, description: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None):
        """Tool function decorator
        
        Args:
            description: Tool description
            parameters: Additional parameter information to supplement auto-generated parameter schema
            
        Returns:
            Decorator function
        """
        def decorator(func):
            # Get function metadata
            tool_name = func.__name__
            tool_desc = description or f"Tool function: {tool_name}"
            
            # Auto-generate parameter schema from function signature
            param_schema = self._generate_param_schema(func, parameters)
            
            # Register tool
            self._register_tool(tool_name, func, tool_desc, param_schema)
            
            # Return original function, maintaining its callable nature
            return func
        return decorator
    
    def _register_tool(self, name: str, func, description: str, param_schema: Dict[str, Any]):
        """Register tool to server"""
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": param_schema,
            "is_async": inspect.iscoroutinefunction(func)
        }
        logger.info(f"Registered tool '{name}' to server '{self.name}'")
    
    def _generate_param_schema(self, func, additional_params: Optional[Dict[str, Any]] = None):
        """Generate parameter schema from function signature, maintaining MCP sample format"""
        # Get function signature and type annotations
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        properties = {}
        required = []
        
        # Process each parameter
        for name, param in sig.parameters.items():
            # Skip self parameter
            if name == 'self':
                continue
                
            param_type = type_hints.get(name, inspect.Parameter.empty)
            has_default = param.default != inspect.Parameter.empty
            
            # Build parameter properties
            param_info = self._type_to_schema(param_type)
            
            # Add title field - space-separated capitalized words
            param_info["title"] = " ".join(word.capitalize() for word in name.split("_"))
            
            # Handle Field decorator
            if has_default and isinstance(param.default, FieldInfo):
                field_info = param.default
                
                # Add description
                if field_info.description:
                    param_info["description"] = field_info.description
                
                # Only add default field when Field has actual default value
                if field_info.default is not None and field_info.default is not ...:
                    # Simple check to ensure it's not PydanticUndefined
                    if not str(field_info.default).endswith("PydanticUndefined"):
                        param_info["default"] = field_info.default
                    else:
                        # No actual default value, add to required
                        required.append(name)
                else:
                    # No default value, add to required
                    required.append(name)
            # Handle regular default values
            elif has_default and param.default is not None:
                param_info["default"] = param.default
            else:
                # Parameters without default values are required
                required.append(name)
            
            # Add description (if provided in additional_params)
            if additional_params and name in additional_params:
                param_info.update(additional_params[name])
            
            properties[name] = param_info
        
        # Special handling: ensure query_list is in required list
        if "query_list" in properties and "query_list" not in required:
            required.append("query_list")
        
        # Create schema consistent with MCP sample
        schema = {
            "properties": properties,
            "type": "object",
            "required": required,
            "title": func.__name__ + "Arguments"
        }
        
        return schema
    
    def _type_to_schema(self, type_hint):
        """Convert Python type to JSON Schema type"""
        import typing
        
        # Basic type mapping
        if type_hint == str:
            return {"type": "string"}
        elif type_hint == int:
            return {"type": "integer"}
        elif type_hint == float:
            return {"type": "number"}
        elif type_hint == bool:
            return {"type": "boolean"}
        elif type_hint == list or getattr(type_hint, "__origin__", None) == list:
            item_type = getattr(type_hint, "__args__", [None])[0]
            return {
                "type": "array",
                "items": self._type_to_schema(item_type)
            }
        elif type_hint == dict or getattr(type_hint, "__origin__", None) == dict:
            return {"type": "object"}
        else:
            # Default to string type
            return {"type": "string"}
    
    def list_tools(self) -> List[MCPTool]:
        """List all tools and their descriptions
        
        Returns:
            List of MCPTool objects
        """
        mcp_tools = []
        for name, info in self.tools.items():
            # Create MCPTool object, consistent with MCP sample format
            mcp_tool = MCPTool(
                name=name,
                description=info["description"],
                inputSchema=info["parameters"]
                # Don't set annotations field
            )
            mcp_tools.append(mcp_tool)
        
        return mcp_tools
    
    async def call_tool_async(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None):
        """Asynchronously call the specified tool function
        
        Args:
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool call result
            
        Raises:
            ValueError: When tool doesn't exist
            Exception: Exceptions during tool execution
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in server '{self.name}'")
        
        tool_info = self.tools[tool_name]
        func = tool_info["function"]
        is_async = tool_info["is_async"]
        arguments = arguments or {}
        
        # Filter parameters, only keep parameters defined in the function
        filtered_args = self._filter_arguments(func, arguments)
        
        try:
            # Call based on function type
            if is_async:
                # Async call
                result = await func(**filtered_args)
            else:
                # Sync call
                import asyncio
                # Use run_in_executor to run sync function, avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: func(**filtered_args))
                
            return self._format_result(result)
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {str(e)}")
            logger.debug(traceback.format_exc())
            # Return error message
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None):
        """Synchronously call the specified tool function
        
        For async tools, it will run in the event loop.
        
        Args:
            tool_name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool call result
            
        Raises:
            ValueError: When tool doesn't exist
            Exception: Exceptions during tool execution
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in server '{self.name}'")
        
        tool_info = self.tools[tool_name]
        func = tool_info["function"]
        is_async = tool_info["is_async"]
        arguments = arguments or {}
        
        # Filter parameters, only keep parameters defined in the function
        filtered_args = self._filter_arguments(func, arguments)
        
        try:
            # Call based on function type
            if is_async:
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    # If in a running event loop, schedule the coroutine
                    future = asyncio.run_coroutine_threadsafe(func(**filtered_args), loop)
                    result = future.result(timeout=60)
                else:
                    # If not in a running event loop, run it directly
                    result = asyncio.run(func(**filtered_args))
            else:
                # Sync call
                result = func(**filtered_args)
                
            return self._format_result(result)
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {str(e)}")
            logger.debug(traceback.format_exc())
            # Return error message
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    def _filter_arguments(self, func, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Filter arguments, only keep parameters defined in the function
        
        Args:
            func: Function to call
            arguments: Input argument dictionary
            
        Returns:
            Filtered argument dictionary
        """
        # Get function signature
        sig = inspect.signature(func)
        param_names = set(sig.parameters.keys())
        
        # Filter arguments
        filtered_args = {}
        for name, value in arguments.items():
            if name in param_names:
                filtered_args[name] = value
            else:
                # Log filtered arguments
                logger.debug(f"Filtered out argument '{name}' not defined in function {func.__name__}")
        
        return filtered_args
    
    def _format_result(self, result):
        """Format function return value to MCP compatible format"""
        # If result is already MCP type, return directly
        if isinstance(result, CallToolResult):
            return result
        
        # Create content list
        content = []
        
        # Handle different result types
        if isinstance(result, str):
            # String result
            content.append(TextContent(type="text", text=result))
        elif isinstance(result, bytes):
            # Image data
            import base64
            image_base64 = base64.b64encode(result).decode('utf-8')
            content.append(ImageContent(type="image", data=image_base64))
        elif isinstance(result, TextContent):
            # If already TextContent, use directly
            content.append(result)
        elif isinstance(result, dict):
            if result.get("type") in ["text", "image"]:
                # Dictionary already in content format
                if result["type"] == "text":
                    # Ensure text field is plain text, without type= format issues
                    text_content = result.get("text", "")
                    # If text field looks like serialized content, try to extract actual text
                    if isinstance(text_content, str) and text_content.startswith("type="):
                        # Try to extract actual text content
                        import re
                        match = re.search(r"text=['\"](.+?)['\"]", text_content)
                        if match:
                            text_content = match.group(1)
                    
                    content.append(TextContent(type="text", text=text_content))
                elif result["type"] == "image":
                    content.append(ImageContent(type="image", data=result.get("data", "")))
            elif "metadata" in result and "text" in result:
                # Special handling for results with metadata
                content.append(TextContent(
                    type="text", 
                    text=result["text"],
                    metadata=result["metadata"]
                ))
            else:
                # Other dictionary types, convert to JSON
                try:
                    content.append(TextContent(type="text", text=json.dumps(result, ensure_ascii=False)))
                except:
                    content.append(TextContent(type="text", text=str(result)))
        else:
            # Other types try JSON serialization
            try:
                content.append(TextContent(type="text", text=json.dumps(result, ensure_ascii=False)))
            except:
                content.append(TextContent(type="text", text=str(result)))
        
        return CallToolResult(content=content)


class FunctionToolsAdapter:
    """Adapter base class for adapting FunctionTools to MCPServer interface
    
    This class provides basic adaptation functionality, but needs to be inherited and extended in specific implementations.
    """
    
    def __init__(self, name: str):
        """Initialize adapter
        
        Args:
            name: Function tools server name
        """
        self._function_tools = get_function_tools(name)
        if not self._function_tools:
            raise ValueError(f"FunctionTools '{name}' not found")
        self._name = name
    
    @property
    def name(self) -> str:
        """Server name"""
        return self._name
    
    async def list_tools(self) -> List[MCPTool]:
        """List all tools and their descriptions"""
        return self._function_tools.list_tools()
    
    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None):
        """Asynchronously call the specified tool function"""
        return await self._function_tools.call_tool_async(tool_name, arguments)
    
    def to_action_result(self, result) -> ActionResult:
        """Convert call result to ActionResult
        
        This method is used to convert MCP call results to AWorld framework's ActionResult objects.
        
        Args:
            result: MCP call result
            
        Returns:
            ActionResult object
        """
        action_result = ActionResult(
            content="",
            keep=True
        )
        
        if result and result.content:
            if len(result.content) > 0:
                if isinstance(result.content[0], TextContent):
                    action_result = ActionResult(
                        content=result.content[0].text,
                        keep=True,
                        metadata=getattr(result.content[0], "metadata", {})
                    )
                elif isinstance(result.content[0], ImageContent):
                    action_result = ActionResult(
                        content=f"data:image/jpeg;base64,{result.content[0].data}",
                        keep=True,
                        metadata=getattr(result.content[0], "metadata", {})
                    )
        
        return action_result 