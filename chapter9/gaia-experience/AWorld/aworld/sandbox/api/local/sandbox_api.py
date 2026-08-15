import logging
from typing import Dict, List, Any, Optional

from aworld.sandbox.api.base_sandbox_api import BaseSandboxApi
from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxLocalResponse
from aworld.sandbox.run.mcp_servers import McpServers


class LocalSandboxApi(BaseSandboxApi):
    """
    API implementation for local sandbox operations.
    """
    
    @classmethod
    def _create_sandbox(
        cls,
        env_type: int,
        env_config: Any,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
        black_tool_actions: Optional[Dict[str, List[str]]] = None
    ) -> SandboxLocalResponse:
        """
        Create a local sandbox based on the reference implementation.
        """
        try:
            if not mcp_servers:
                logging.info("_create_sandbox_by_local mcp_servers is not exist")
                return None
                
            return SandboxLocalResponse(
                status=SandboxStatus.RUNNING,
                mcp_config=mcp_config,
                env_type=SandboxEnvType.LOCAL
            )
        except Exception as e:
            logging.warning(f"Failed to create local sandbox: {e}")
            return None
    
    @classmethod
    def _get_mcp_configs(
        cls,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> Any:
        """
        Get MCP configurations for the sandbox.
        """
        try:
            # Create McpServers instance
           return mcp_config
        except Exception as e:
            logging.warning(f"Failed to get_mcp_configs: {e}")
            return None
    
    @classmethod
    async def _remove_sandbox(
        cls,
        sandbox_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> bool:
        """
        Remove the local sandbox.
        """
        # Local sandbox doesn't need special removal
        return True 