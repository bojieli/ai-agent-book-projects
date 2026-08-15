import asyncio
import logging
import re
import traceback
from typing import List, Optional

from fastapi import Request
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel, Field
from ..utils.proxy_utils import proxy_pass_bytes, proxy_pass_lines

logger = logging.getLogger(__name__)


class SessionId(BaseModel):
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID from mcp client, used for multi step session affinity",
    )
    mcp_session_id: Optional[str] = Field(
        default=None,
        description="MCP Session ID for mcp client session",
    )

    @classmethod
    def from_request(cls, request: Request) -> "SessionId":
        """Create SessionId from request headers"""
        return cls(
            session_id=request.headers.get("SESSION_ID"),
            mcp_session_id=request.headers.get("Mcp-Session-Id"),
        )


class VpcSession(BaseModel):
    """Represents a persistent HTTP connection to a backend server"""

    container_id: str = Field(description="Container ID")
    container_ip_addr: str = Field(description="Container IP")
    mcp_port: int = Field(description="MCP Port")
    novnc_port: int = Field(description="NoVNC Port")
    container_server_id: str = Field(description="Container Server ID")
    mcp_session_ids: List[str] = Field(default=[], description="MCP Session IDs")
    session_ids: List[str] = Field(default=[], description="Session IDs")

    def is_bind(self, session_id: SessionId) -> bool:
        """Check if the session id matches the session connection"""
        return (
            session_id.mcp_session_id in self.mcp_session_ids
            or session_id.session_id in self.session_ids
        )

    def _get_client(self):
        """Establish connection to backend server"""
        return httpx.AsyncClient(
            timeout=httpx.Timeout(360, connect=30, pool=30),
            limits=httpx.Limits(
                max_keepalive_connections=30,
                max_connections=30,
                keepalive_expiry=600.0,  # Keep alive for 1 hour
            ),
            http2=True,  # Enable HTTP/2 for better multiplexing
        )

    async def forward_request(
        self, method: str, headers: dict, content: bytes
    ) -> StreamingResponse:
        """Send request through the persistent connection with true streaming proxy"""
        try:
            client = self._get_client()
            await client.__aenter__()
            return await proxy_pass_lines(
                client=client,
                method=method,
                url=f"http://{self.container_ip_addr}:{self.mcp_port}/mcp",
                headers=headers,
                content=content,
            )
        except Exception as e:
            logger.error(
                f"Connection error to {self.container_ip_addr}:{self.mcp_port}: {e}"
            )
            raise

    async def novnc_proxy(self, request: Request) -> StreamingResponse:
        """
        Proxy the request to the VNC server.
        """
        try:
            client = self._get_client()
            await client.__aenter__()
            # Remove the prefix "/novnc/{session_id}" from the URL path
            target_url = re.sub(r"^/novnc/[^/]+", "", request.url.path) or "/"
            return await proxy_pass_bytes(
                client=client,
                method=request.method,
                url=f"http://{self.container_ip_addr}:{self.novnc_port}{target_url}",
                headers=dict(request.headers),
                content=await request.body(),
            )
        except:
            logger.error(
                f"Connection error to {self.container_ip_addr}:{self.mcp_port}: {traceback.format_exc()}"
            )
            raise
