import abc
from typing import Dict, List, Any, Optional

from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxInfo, SandboxCreateResponse, EnvConfig
from aworld.sandbox.api.apibase import SandboxApiBase


class BaseSandboxApi(SandboxApiBase, abc.ABC):
    """
    Base class for sandbox API implementations.
    Defines the interface for interacting with different types of sandboxes.
    """
    
    @classmethod
    @abc.abstractmethod
    def _create_sandbox(
        cls,
        env_type: int,
        env_config: EnvConfig,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
    ) -> SandboxCreateResponse:
        """
        Create a sandbox based on the environment type and configuration.
        
        Args:
            env_type: The environment type (LOCAL, K8S, SUPERCOMPUTER).
            env_config: Environment configuration.
            mcp_servers: List of MCP servers to use.
            mcp_config: Configuration for MCP servers.
            
        Returns:
            SandboxCreateResponse: Response containing sandbox information.
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    def _get_mcp_configs(
        cls,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> Any:
        """
        Get MCP configurations for the sandbox.
        
        Args:
            mcp_servers: List of MCP servers to use.
            mcp_config: Configuration for MCP servers.
            metadata: Additional metadata for the sandbox.
            env_type: The environment type.
            
        Returns:
            Any: Updated MCP configuration.
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    async def _remove_sandbox(
        cls,
        sandbox_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> bool:
        """
        Remove the sandbox and clean up resources.
        
        Args:
            sandbox_id: Unique identifier for the sandbox.
            metadata: Metadata for the sandbox.
            env_type: The environment type.
            
        Returns:
            bool: True if removal was successful, False otherwise.
        """
        pass 