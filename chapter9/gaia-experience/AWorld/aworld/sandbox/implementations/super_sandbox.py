import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional

from aworld.sandbox.common import BaseSandbox
from aworld.sandbox.api.super.sandbox_api import SuperSandboxApi
from aworld.sandbox.models import SandboxStatus, SandboxEnvType, SandboxInfo
from aworld.sandbox.run.mcp_servers import McpServers


class SuperSandbox(BaseSandbox, SuperSandboxApi):
    """
    Supercomputer sandbox implementation that runs on a supercomputer environment.
    """

    def __init__(
            self,
            sandbox_id: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None,
            timeout: Optional[int] = None,
            mcp_servers: Optional[List[str]] = None,
            mcp_config: Optional[Any] = None,
            **kwargs
    ):
        """
        Initialize a new SuperSandbox instance.
        
        Args:
            sandbox_id: Unique identifier for the sandbox. If None, one will be generated.
            metadata: Additional metadata for the sandbox.
            timeout: Timeout for sandbox operations.
            mcp_servers: List of MCP servers to use.
            mcp_config: Configuration for MCP servers.
            **kwargs: Additional parameters for specific sandbox types.
        """
        super().__init__(
            sandbox_id=sandbox_id,
            env_type=SandboxEnvType.SUPERCOMPUTER,
            metadata=metadata,
            timeout=timeout,
            mcp_servers=mcp_servers,
            mcp_config=mcp_config
        )

        if sandbox_id:
            if not self._metadata:
                return self
            else:
                raise ValueError("sandbox_id is not exist")

        # Initialize properties
        self._status = SandboxStatus.INIT
        self._timeout = timeout or self.default_sandbox_timeout
        self._metadata = metadata or {}
        self._env_type = SandboxEnvType.SUPERCOMPUTER
        self._mcp_servers = mcp_servers
        self._mcp_config = mcp_config
        
        # Ensure sandbox_id has a value in all cases
        self._sandbox_id = sandbox_id or str(uuid.uuid4())

        # If no sandbox_id provided, create a new sandbox
        if not sandbox_id:
            response = self._create_sandbox(
                env_type=self._env_type,
                env_config=None,
                mcp_servers=mcp_servers,
                mcp_config=mcp_config,
            )
            
            if not response:
                self._status = SandboxStatus.ERROR
                # If creation fails, keep the generated UUID as the ID
                logging.warning(f"Failed to create super sandbox, using generated ID: {self._sandbox_id}")
            else:
                self._sandbox_id = response.sandbox_id
                self._status = SandboxStatus.RUNNING
                self._metadata = {
                    "status": getattr(response, 'status', None),
                    "host": getattr(response, 'host', None),
                    "mcp_config": getattr(response, 'mcp_config', None),
                    "env_type": getattr(response, 'env_type', None),
                }
                self._mcp_config = getattr(response, 'mcp_config', None)
            
        # Initialize McpServers
        self._mcpservers = McpServers(
            mcp_servers,
            self._mcp_config,
            sandbox=self
        )

    async def remove(self) -> None:
        """
        Remove sandbox.
        """
        await self._remove_sandbox(
            sandbox_id=self.sandbox_id,
            metadata=self._metadata,
            env_type=self._env_type
        )
        
    async def cleanup(self) -> None:
        """
        Clean up Sandbox resources, including MCP server connections
        """
        try:
            if hasattr(self, '_mcpservers') and self._mcpservers:
                await self._mcpservers.cleanup()
                logging.info(f"Cleaned up MCP servers for sandbox {self.sandbox_id}")
        except Exception as e:
            logging.warning(f"Failed to cleanup MCP servers: {e}")
        
        # Call the original remove method
        try:
            await self.remove()
        except Exception as e:
            logging.warning(f"Failed to remove sandbox: {e}")
            
    def __del__(self):
        """
        Ensure resources are cleaned up when the object is garbage collected
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