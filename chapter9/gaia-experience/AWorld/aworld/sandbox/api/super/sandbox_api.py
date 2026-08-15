import logging
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

from aworld.sandbox.api.base_sandbox_api import BaseSandboxApi
from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxSuperResponse
from aworld.sandbox.run.mcp_servers import McpServers


class SuperSandboxApi(BaseSandboxApi):
    """
    API implementation for supercomputer sandbox operations.
    """
    
    @classmethod
    def _create_sandbox(
        cls,
        env_type: int,
        env_config: Any,
        mcp_servers: Optional[List[str]] = None,
        mcp_config: Optional[Any] = None,
    ) -> SandboxSuperResponse:
        """
        Create a supercomputer sandbox based on the reference implementation.
        """
        try:
            if not mcp_servers:
                logging.info("_create_sandbox_by_super mcp_servers is not exist")
                return None
                
            load_dotenv()
            host = os.getenv("SUPERCOMPUTER_HOST")
            
            if not host:
                logging.warning("_create_sandbox_by_super SUPERCOMPUTER_HOST is null")
                return None
                
            metadata = {
                "status": SandboxStatus.RUNNING,
                "host": host,
            }
            
            response = cls._get_mcp_configs(
                mcp_servers=mcp_servers,
                mcp_config=mcp_config,
                metadata=metadata,
                env_type=SandboxEnvType.SUPERCOMPUTER
            )
            
            if not response:
                return None

            return SandboxSuperResponse(
                status=SandboxStatus.RUNNING,
                host=host,
                mcp_config=mcp_config,
                env_type=SandboxEnvType.SUPERCOMPUTER
            )
            
        except Exception as e:
            logging.warning(f"Failed to create supercomputer sandbox: {e}")
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
            if not metadata or not metadata.get("host"):
                return mcp_config
            host = metadata.get("host")

            if not mcp_servers:
                return None
            if not mcp_config or mcp_config.get("mcpServers") is None:
                mcp_config = {
                    "mcpServers": {}
                }
            _mcp_servers = mcp_config.get("mcpServers")

            for server in mcp_servers:
                if server not in _mcp_servers:
                    _mcp_servers[server] = {
                        "type": "sse",
                        "url": f"{host}/{server}/sse"
                    }

            return mcp_config
        except Exception as e:
            logging.warning(f"Failed to get_mcp_configs_from_super: {e}")
            return None

    
    @classmethod
    async def _remove_sandbox(
        cls,
        sandbox_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        env_type: Optional[int] = None,
    ) -> bool:
        """
        Remove the supercomputer sandbox.
        """
        # Supercomputer sandbox doesn't need special removal
        return True 