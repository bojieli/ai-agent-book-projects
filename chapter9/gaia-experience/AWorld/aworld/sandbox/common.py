import asyncio
import logging
import abc
from typing import Dict, List, Any, Optional

from aworld.sandbox.base import Sandbox
from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxInfo
from aworld.sandbox.run.mcp_servers import McpServers


class BaseSandbox(Sandbox):
    """
    Base sandbox implementation with common functionality for all sandbox types.
    This class implements common methods and provides a foundation for specific sandbox implementations.
    """

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
        Initialize a new BaseSandbox instance.
        
        Args:
            sandbox_id: Unique identifier for the sandbox. If None, one will be generated.
            env_type: The environment type (LOCAL, K8S, SUPERCOMPUTER).
            metadata: Additional metadata for the sandbox.
            timeout: Timeout for sandbox operations.
            mcp_servers: List of MCP servers to use.
            mcp_config: Configuration for MCP servers.
        """
        super().__init__(
            sandbox_id=sandbox_id,
            env_type=env_type,
            metadata=metadata,
            timeout=timeout,
            mcp_servers=mcp_servers,
            mcp_config=mcp_config,
            black_tool_actions=black_tool_actions
        )
        self._logger = self._setup_logger()
        
    def _setup_logger(self):
        """
        Set up a logger for the sandbox instance.
        
        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(f"sandbox.{self.__class__.__name__}.{self.sandbox_id[:8]}")
        return logger
        
    def get_info(self) -> SandboxInfo:
        """
        Get information about the sandbox.
        
        Returns:
            SandboxInfo: Information about the sandbox.
        """
        return {
            "sandbox_id": self.sandbox_id,
            "status": self.status,
            "metadata": self.metadata,
            "env_type": self.env_type
        }
    
    @property
    def mcpservers(self) -> McpServers:
        """
        Module for running MCP servers in the sandbox.
        This property provides access to the MCP servers instance.
        
        Returns:
            McpServers: The MCP servers instance.
        """
        if hasattr(self, '_mcpservers'):
            return self._mcpservers
        return None
    
    @abc.abstractmethod
    async def cleanup(self) -> bool:
        """
        Clean up sandbox resources.
        This method must be implemented by subclasses to provide environment-specific cleanup.
        
        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        pass
    
    @abc.abstractmethod
    async def remove(self) -> bool:
        """
        Remove the sandbox.
        This method must be implemented by subclasses to provide environment-specific removal.
        
        Returns:
            bool: True if removal was successful, False otherwise.
        """
        pass 