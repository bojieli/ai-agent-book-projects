import abc
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional

from aworld.sandbox.api.setup import SandboxSetup
from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxInfo
from aworld.sandbox.run.mcp_servers import McpServers


class Sandbox(SandboxSetup):
    """
    Sandbox abstract base class that defines the interface for all sandbox implementations.
    A sandbox provides an isolated environment for executing code and operations.
    """
    
    default_sandbox_timeout = 3000
    
    @property
    def sandbox_id(self) -> str:
        """
        Returns the unique identifier of the sandbox.
        """
        return self._sandbox_id

    @property
    def status(self) -> SandboxStatus:
        """
        Returns the current status of the sandbox.
        """
        return self._status

    @property
    def timeout(self) -> int:
        """
        Returns the timeout value for sandbox operations.
        """
        return self._timeout

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns the sandbox metadata.
        """
        return self._metadata

    @property
    def env_type(self) -> SandboxEnvType:
        """
        Returns the environment type of the sandbox.
        """
        return self._env_type

    @property
    def mcp_config(self) -> Any:
        """
        Returns the MCP configuration.
        """
        return self._mcp_config

    @property
    def mcp_servers(self) -> List[str]:
        """
        Returns the list of MCP servers.
        """
        return self._mcp_servers

    @property
    def black_tool_actions(self) -> Dict[str, List[str]]:
        """
        Returns the list of black-listed tools.
        """
        return self._black_tool_actions
    
    @property
    @abc.abstractmethod
    def mcpservers(self) -> McpServers:
        """
        Module for running MCP in the sandbox.
        
        Returns:
            McpServers: The MCP servers instance.
        """
        pass


    def __init__(
            self,
            sandbox_id: Optional[str] = None,
            env_type: Optional[int] = None,
            metadata: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = None,
            mcp_servers: Optional[List[str]] = None,
            mcp_config: Optional[Any] = None,
            black_tool_actions: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize a new Sandbox instance.
        
        Args:
            sandbox_id: Unique identifier for the sandbox. If None, one will be generated.
            env_type: The environment type (LOCAL, K8S, SUPERCOMPUTER).
            metadata: Additional metadata for the sandbox.
            timeout: Timeout for sandbox operations.
            mcp_servers: List of MCP servers to use.
            mcp_config: Configuration for MCP servers.
        """
        # Initialize basic attributes
        self._sandbox_id = sandbox_id or str(uuid.uuid4())
        self._status = SandboxStatus.INIT
        self._timeout = timeout or self.default_sandbox_timeout
        self._metadata = metadata or {}
        self._env_type = env_type or SandboxEnvType.LOCAL
        self._mcp_servers = mcp_servers or []
        self._mcp_config = mcp_config or {}
        self._black_tool_actions = black_tool_actions or {}
        
    @abc.abstractmethod
    def get_info(self) -> SandboxInfo:
        """
        Returns information about the sandbox.
        
        Returns:
            SandboxInfo: Information about the sandbox.
        """
        pass
    
    @abc.abstractmethod
    async def remove(self) -> bool:
        """
        Remove the sandbox and clean up all resources.
        
        Returns:
            bool: True if removal was successful, False otherwise.
        """
        pass
    
    @abc.abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up the sandbox resources.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        pass
    
    def __del__(self):
        """
        Ensure resources are cleaned up when the object is garbage collected.
        """
        try:
            # Handle the case where an event loop already exists
            try:
                loop = asyncio.get_running_loop()
                logging.warning("Cannot clean up sandbox in __del__ when event loop is already running")
                return
            except RuntimeError:
                # No running event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.cleanup())
                loop.close()
        except Exception as e:
            logging.warning(f"Failed to cleanup sandbox resources during garbage collection: {e}")