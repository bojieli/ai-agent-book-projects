# coding: utf-8
# Copyright (c) 2025 inclusionAI.

"""
This module defines decorators for creating MCP servers.
By using the @mcp_server decorator, you can convert a Python class into an MCP server,
where the class methods will be automatically converted into MCP tools.
"""

import inspect
import functools
import threading
from typing import Type, Dict, Any, Optional, Union, List

# Import FastMCP
from mcp.server import FastMCP

from aworld.core.factory import Factory
from aworld.logs.util import logger


# Save all decorated MCP server classes
class MCPServerRegistry(Factory):
    """Register all MCP server classes"""

    def __init__(self, type_name: str = None):
        super().__init__(type_name)
        self._instance = {}

    def register(self, name: str, cls: Type, **kwargs):
        """Register MCP server class"""
        self._cls[name] = cls

    def get_instance(self, name: str, *args, **kwargs):
        """Get MCP server instance"""
        if name not in self._instance:
            if name not in self._cls:
                raise ValueError(f"MCP server {name} not registered")
            self._instance[name] = self._cls[name](*args, **kwargs)
        return self._instance[name]


# Create global registry instance
MCPServers = MCPServerRegistry()


def extract_param_desc(method, param_name):
    """Extract parameter description from method docstring"""
    if not method.__doc__:
        return None

    param_docs = [
        line.strip() for line in method.__doc__.split('\n')
        if line.strip().startswith(f":param {param_name}:")
    ]
    if param_docs:
        return param_docs[0].replace(f":param {param_name}:", "").strip()
    return None


def mcp_server(name: str = None, **server_config):
    """
    Decorator to convert a class into an MCP server

    Args:
        name: Server name, if None, uses the class name
        **server_config: Server configuration parameters
            - mode: Server running mode, supports 'stdio' and 'sse' (default: 'sse')
            - host: Host address in SSE mode (default: '127.0.0.1')
            - port: Port number in SSE mode (default: 8888)
            - sse_path: Path in SSE mode (default: '/sse')
            - auto_start: Whether to automatically start the server (default: True)

    Example:
        @mcp_server(
            name="simple-calculator",
            mode="sse",
            host="localhost",
            port=8085,
            sse_path="/calculator/sse"
        )
        class Calculator:
            '''Server description'''

            def __init__(self):
                self.data = {}

            def get_data(self, key: str) -> str:
                '''Get data
                :param key: Data key
                :return: Data value
                '''
                return self.data.get(key, "")
    """
    # Extract server configuration or use defaults
    mode = server_config.get('mode', 'sse')
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 8888)
    sse_path = server_config.get('sse_path', '/sse')
    auto_start = server_config.get('auto_start', True)

    def decorator(cls):
        server_name = name or cls.__name__

        # Use class docstring as server description
        server_description = cls.__doc__ or f"{server_name} MCP Server"

        # Original initialization method
        original_init = cls.__init__

        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            # Call original initialization method
            original_init(self, *args, **kwargs)

            # Create FastMCP instance, set server name and description
            self._mcp = FastMCP(server_name, description=server_description.strip())

            # Tool name list for recording
            tool_names = []

            # Get all methods, filter out built-in and private methods
            for method_name, method in inspect.getmembers(self, inspect.ismethod):
                if not method_name.startswith('_') and method_name != 'run':
                    # Get method docstring as tool description
                    tool_description = method.__doc__ or f"{method_name} tool"
                    tool_description = tool_description.strip()

                    # Record tool name
                    tool_names.append(method_name)

                    # Create tool and register, using a function generator to ensure each method is correctly bound
                    def create_tool_wrapper(method_to_call):
                        # Check if method is async
                        is_async = inspect.iscoroutinefunction(method_to_call)

                        if is_async:
                            @self._mcp.tool(name=method_name, description=tool_description)
                            @functools.wraps(method_to_call)
                            async def wrapped_method(*args, **kwargs):
                                return await method_to_call(*args, **kwargs)
                        else:
                            @self._mcp.tool(name=method_name, description=tool_description)
                            @functools.wraps(method_to_call)
                            def wrapped_method(*args, **kwargs):
                                return method_to_call(*args, **kwargs)

                        return wrapped_method

                    # Create a dedicated wrapper for each method
                    create_tool_wrapper(method)

            # Print server information
            logger.info(f"Creating MCP server: {server_name}")
            logger.info(f"Server description: {server_description.strip()}")
            if tool_names:
                logger.info(f"Registered tools: {', '.join(tool_names)}")

            # Save configuration
            self._server_config = {
                'mode': mode,
                'host': host,
                'port': port,
                'sse_path': sse_path
            }

            # Auto start server if configured
            if auto_start:
                # Start server in a new thread to avoid blocking
                thread = threading.Thread(
                    target=self.run,
                    kwargs=self._server_config,
                    daemon=True
                )
                thread.start()
                logger.info(f"Server {server_name} started in a background thread")
                self._server_thread = thread

        # Replace initialization method
        cls.__init__ = new_init

        # Add method to run server
        def run(self, mode: str = mode, host: str = host, port: int = port, sse_path: str = sse_path):
            """
            Run MCP server

            Args:
                mode: Server running mode, supports 'stdio' and 'sse'
                host: Host address in SSE mode
                port: Port number in SSE mode
                sse_path: Path in SSE mode
            """
            if not hasattr(self, '_mcp') or self._mcp is None:
                raise RuntimeError("MCP server not initialized")

            # Run server according to mode
            if mode == "stdio":
                self._mcp.run(transport="stdio")
            elif mode == "sse":
                # Configure SSE mode settings
                self._mcp.settings.host = host
                self._mcp.settings.port = port
                self._mcp.settings.sse_path = sse_path

                # Print running information
                print(f"Running MCP server: {server_name}")
                print(f"Description: {server_description.strip()}")
                print(f"Address: http://{host}:{port}{sse_path}")

                self._mcp.run(transport="sse")
            else:
                raise ValueError(f"Unsupported mode: {mode}, supported modes are 'stdio' and 'sse'")

        cls.run = run

        # Add a stop method to gracefully stop the server
        def stop(self):
            """Stop the MCP server if it's running"""
            if hasattr(self, '_mcp') and self._mcp is not None:
                # TODO: Implement proper stopping mechanism based on FastMCP API
                logger.info(f"Stopping server {server_name}")
                # Currently there might not be a proper way to stop FastMCP server
                # This is a placeholder for future implementation

        cls.stop = stop

        # Register to MCP server registry
        MCPServers.register(server_name, cls)

        # Return modified class
        return cls

    return decorator 