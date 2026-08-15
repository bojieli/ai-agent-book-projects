import asyncio
import json
import logging
import time
import traceback
from typing import List
from fastapi import Request, Response
import redis.asyncio as redis

from ..containers import ContainerServerManager

from ..utils.common_utils import get_remote_addr

from ..sessions import VpcSession, SessionId

from ..configs import cluster_name, debug_mode, redis_url

logger = logging.getLogger(__name__)


class SessionRepo:
    def __init__(self):
        self.sessions: List[VpcSession] = []

    async def initialize(self):
        pass

    async def get_bind_session(self, session_id: SessionId) -> VpcSession | None:
        return next(
            (v for v in await self.get_sessions() if v.is_bind(session_id)),
            None,
        )

    async def get_sessions(self) -> List[VpcSession]:
        return self.sessions

    async def update_vpc_session(self, vpc_session: VpcSession):
        pass

    async def remove_vpc_session(self, vpc_session: VpcSession):
        self.sessions.remove(vpc_session)


class SessionRedisRepo(SessionRepo):
    def __init__(self, redis_url: str):
        self._redis_client = redis.Redis.from_url(redis_url)
        self._sessions_key = f"{cluster_name}.vpc_sessions"

    async def initialize(self):
        await self._redis_client.ping()

    async def get_sessions(self) -> List[VpcSession]:
        """Get all VPC sessions from Redis"""
        sessions = []
        try:
            session_data = await self._redis_client.hgetall(self._sessions_key)
            for _, session_json in session_data.items():
                try:
                    if session_json:
                        session_data_str = session_json.decode("utf-8")
                        sessions.append(self._deserialize_vpc_session(session_data_str))
                except Exception as e:
                    logger.error(
                        f"Error deserializing VPC session: {traceback.format_exc()}"
                    )
        except Exception as e:
            logger.error(f"Error getting sessions: {traceback.format_exc()}")
        return sessions

    async def update_vpc_session(self, vpc_session: VpcSession):
        """Update VPC session in Redis"""
        try:
            session_json = self._serialize_vpc_session(vpc_session)
            await self._redis_client.hset(
                self._sessions_key, vpc_session.container_id, session_json
            )
        except Exception as e:
            logger.error(f"Error updating VPC session: {traceback.format_exc()}")

    async def remove_vpc_session(self, vpc_session: VpcSession):
        """Remove VPC session from Redis"""
        try:
            await self._redis_client.hdel(self._sessions_key, vpc_session.container_id)
        except Exception as e:
            logger.error(f"Error removing VPC session: {e}")

    def _serialize_vpc_session(self, vpc_session: VpcSession) -> str:
        """Serialize VpcSession to JSON string"""
        session_data = {
            "container_id": vpc_session.container_id,
            "container_ip_addr": vpc_session.container_ip_addr,
            "mcp_port": vpc_session.mcp_port,
            "novnc_port": vpc_session.novnc_port,
            "container_server_id": vpc_session.container_server_id,
            "mcp_session_ids": vpc_session.mcp_session_ids,
            "session_ids": vpc_session.session_ids,
        }
        return json.dumps(session_data)

    def _deserialize_vpc_session(self, session_json: str) -> VpcSession:
        """Deserialize JSON string to VpcSession"""
        session_data = json.loads(session_json)
        vpc_session = VpcSession(
            container_id=session_data.get("container_id", ""),
            container_ip_addr=session_data.get("container_ip_addr", ""),
            mcp_port=session_data.get("mcp_port", -1),
            novnc_port=session_data.get("novnc_port", -1),
            container_server_id=session_data.get("container_server_id", ""),
        )
        vpc_session.mcp_session_ids = session_data.get("mcp_session_ids", [])
        vpc_session.session_ids = session_data.get("session_ids", [])
        return vpc_session


class SessionConnectionManager:
    """Manages session connections to container servers"""

    def __init__(
        self,
        container_server_manager: ContainerServerManager,
        session_repo: SessionRepo = SessionRepo(),
    ):
        self._session_repo: SessionRepo = session_repo
        self.container_server_manager: ContainerServerManager = container_server_manager

    async def initialize(self):
        """Initialize the session connection manager"""
        await self._session_repo.initialize()

    async def get_session(self, session_id: SessionId) -> VpcSession | None:
        return await self._session_repo.get_bind_session(session_id)

    async def create_vpc_session(self, session_id: SessionId) -> VpcSession:
        """Get the session connection"""
        vpc_session = await self.get_session(session_id)
        if not vpc_session:
            logger.info(f"Create new vpc session: session_id={session_id}")
            (
                container_id,
                container_ip_addr,
                container_mcp_port,
                container_novnc_port,
                container_server_id,
            ) = await self.container_server_manager.create_container(session_id)

            vpc_session = VpcSession(
                container_id=container_id,
                container_ip_addr=container_ip_addr,
                mcp_port=container_mcp_port,
                novnc_port=container_novnc_port,
                container_server_id=container_server_id,
            )

        return vpc_session

    async def forward_request(
        self,
        request: Request,
        session_id: SessionId,
    ) -> Response:
        vpc_session = await self.get_session(session_id)
        assert vpc_session, f"Vpc session not found! session_id={session_id}"
        return await self._forward_request(request, vpc_session)

    async def _forward_request(
        self, request: Request, vpc_session: VpcSession
    ) -> Response:
        """Forward the request through the persistent connection"""
        try:
            headers = dict(request.headers)

            # Remove headers that should not be forwarded or can cause conflicts
            for header in [
                "host",
                "connection",
                "upgrade",
            ]:
                headers.pop(header, None)

            # Forward request through connection
            backend_response = await vpc_session.forward_request(
                method=request.method, headers=headers, content=await request.body()
            )
            return backend_response

        except Exception as e:
            logger.error(
                f"Unexpected error forwarding request: {traceback.format_exc()}"
            )
            raise e

    async def handle_initialize_request(self, request: Request) -> Response:
        # Handle session init
        logger.info(
            f"MCP client session initialize request: remote.addr={get_remote_addr(request)}, request.headers={request.headers}"
        )
        time_start = time.time()

        session_id = SessionId.from_request(request)

        vpc_session = None
        if debug_mode:
            vpc_session = VpcSession(
                container_server_id="http://mcp-server-debug:4242",
                container_ip_addr="mcp-server-debug",
                mcp_port=4242,
                novnc_port=5901,
                container_id="mcp-server-debug",
            )
            logger.info(
                f"Gateway debug mode, skip container creation, default mcp_server connection={vpc_session}"
            )
        else:
            vpc_session = await self.create_vpc_session(session_id)

        # Forward request through the new persistent connection
        response = await self._forward_request(request, vpc_session)
        mcp_session_id = response.headers.get("Mcp-Session-Id")
        assert (
            mcp_session_id
        ), "Mcp session id is required in initialize response header!"

        session_id.mcp_session_id = mcp_session_id

        # Bind session to VPC
        if (
            session_id.mcp_session_id
            and session_id.mcp_session_id not in vpc_session.mcp_session_ids
        ):
            vpc_session.mcp_session_ids.append(session_id.mcp_session_id)
        if (
            session_id.session_id
            and session_id.session_id not in vpc_session.session_ids
        ):
            vpc_session.session_ids.append(session_id.session_id)
        await self._session_repo.update_vpc_session(vpc_session)

        logger.info(
            f"Client session initialize success: session_id={session_id}, vpc_session.container_id={vpc_session.container_id}, time_cost_sec={time.time() - time_start}"
        )
        return response

    async def handle_delete_request(
        self, request: Request, session_id: SessionId
    ) -> Response:
        """Handle session delete request"""
        logger.info(
            f"McpClient session release request: {get_remote_addr(request)}, session_id={session_id}"
        )
        mcp_response = await self.forward_request(request, session_id)
        await self._release_mcp_session(session_id)
        return mcp_response

    async def _release_mcp_session(self, session_id: SessionId):
        """Release the mcp session"""
        vpc_session = await self._session_repo.get_bind_session(session_id)
        assert vpc_session, "Mcp session not found"
        assert session_id.mcp_session_id, "Mcp session id is required"
        assert vpc_session.is_bind(session_id), "Mcp session id not bind to vpc_session"
        vpc_session.mcp_session_ids.remove(session_id.mcp_session_id)

        if session_id.session_id:
            # Release MCP Session only
            vpc_session.mcp_session_ids.remove(session_id.mcp_session_id)
            await self._session_repo.update_vpc_session(vpc_session)
        else:
            await self._session_repo.remove_vpc_session(vpc_session)
            asyncio.create_task(
                self.container_server_manager.shutdown_container(
                    container_server_id=vpc_session.container_server_id,
                    container_id=vpc_session.container_id,
                )
            )

    async def shutdown(self):
        """Shutdown the session connection manager"""
        pass

    async def get_sessions(self) -> List[VpcSession]:
        """Get all sessions"""
        return await self._session_repo.get_sessions()


async def session_connection_manager_builder(
    container_server_manager: ContainerServerManager,
):
    if redis_url:
        session_connection_manager = SessionConnectionManager(
            container_server_manager, SessionRedisRepo(redis_url)
        )
    else:
        session_connection_manager = SessionConnectionManager(container_server_manager)

    await session_connection_manager.initialize()
    return session_connection_manager
