from typing import List, Tuple, Optional
from pydantic import BaseModel, Field

from ..configs import cluster_name
from ..sessions import SessionId
import logging
import httpx
import traceback
import random
import asyncio
from typing import Optional
import json
from redis.asyncio import Redis
from ..utils.common_utils import check_container_server_health

logger = logging.getLogger(__name__)


class ContainerServer(BaseModel):
    """Container server configuration"""

    ip_addr: str = Field(description="IP address of the container server")
    port: int = Field(description="Manager port of the container server")
    token: Optional[str] = Field(
        default=None, description="Token of the container server"
    )
    cpu_load: Optional[List[float]] = Field(
        default=None, description="CPU load of the container server"
    )
    memory_usage: Optional[List[float]] = Field(
        default=None, description="Memory usage of the container server"
    )

    @property
    def server_id(self) -> str:
        return f"{self.ip_addr}:{self.port}"


class ContainerServerRepo:
    def __init__(self):
        self._container_servers: List[ContainerServer] = []

    async def initialize(self):
        pass

    async def get_server(self, container_server_id: str) -> ContainerServer | None:
        servers = await self.get_servers()
        return next(
            (s for s in servers if s.server_id == container_server_id),
            None,
        )

    async def get_servers(self) -> List[ContainerServer]:
        return self._container_servers

    async def add_server(self, server: ContainerServer):
        self._container_servers.append(server)

    async def remove_server(self, server: ContainerServer):
        self._container_servers.remove(server)


class ContainerServerRedisRepo(ContainerServerRepo):

    def __init__(self, redis_url: str):
        self._redis_client = Redis.from_url(redis_url)
        self._redis_key = f"{cluster_name}.container_servers"

    async def initialize(self):
        """Initialize the container server redis repo"""
        await self._redis_client.ping()

    async def get_servers(self) -> List[ContainerServer]:
        """Get all container servers from Redis"""
        try:
            # Get all server data from Redis hash
            server_data = await self._redis_client.hgetall(self._redis_key)
            servers = []

            for server_id, server_json in server_data.items():
                try:
                    server_dict = json.loads(server_json)
                    server = ContainerServer(**server_dict)
                    servers.append(server)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to deserialize server {server_id}: {e}")
                    continue

            return servers
        except Exception as e:
            logger.error(f"Failed to get servers from Redis: {e}")
            return []

    async def add_server(self, server: ContainerServer):
        """Add a container server to Redis"""
        try:
            server_json = json.dumps(server.model_dump())
            await self._redis_client.hset(
                self._redis_key, server.server_id, server_json
            )
            logger.info(
                f"Added server: server_id={server.server_id}, server_json={server_json}"
            )
        except Exception as e:
            logger.error(f"Failed to add server {server.server_id} to Redis: {e}")

    async def remove_server(self, server: ContainerServer):
        """Remove a container server from Redis"""
        try:
            await self._redis_client.hdel(self._redis_key, server.server_id)
            logger.info(f"Removed server: server_id={server.server_id}")
        except Exception as e:
            logger.error(f"Failed to remove server {server.server_id} from Redis: {e}")

    async def clear_all(self):
        """Clear all container servers from Redis"""
        try:
            await self._redis_client.delete(self._redis_key)
            logger.debug("Cleared all container servers from Redis")
        except Exception as e:
            logger.error(f"Failed to clear all servers from Redis: {e}")


class ContainerServerManager:

    def __init__(
        self, container_server_repo: ContainerServerRepo = ContainerServerRepo()
    ):
        self._container_server_repo: ContainerServerRepo = container_server_repo

    async def create_container(
        self, session_id: SessionId
    ) -> Tuple[str, str, int, int, str]:
        """
        Create a new container for the session id
        Return: (container_id, container_ip, container_mcp_port, container_novnc_port, container_server_id)
        """
        container_server = await self._select_container_server()
        if not container_server:
            raise Exception("No container servers available")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"http://{container_server.ip_addr}:{container_server.port}/api/container/create",
                    json={
                        "token": container_server.token,
                        "session_id": session_id.session_id,
                    },
                    timeout=httpx.Timeout(300.0),
                )
                response.raise_for_status()
                ret = response.json()
                logger.info(f"Create container response: {ret}")
                if ret.pop("status") == "success":
                    return (
                        ret.get("data", {}).get("container_id"),
                        ret.get("data", {}).get("ip_addr"),
                        ret.get("data", {}).get("mcp_port"),
                        ret.get("data", {}).get("novnc_port"),
                        container_server.server_id,
                    )
                else:
                    raise Exception(ret.get("message", "Failed to create container"))
            except Exception as e:
                logger.error(
                    f"Failed to create container, remote.addr={container_server.ip_addr}: {traceback.format_exc()}"
                )
                raise

    async def shutdown_container(
        self, container_server_id: str, container_id: str
    ) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                container_server = await self._container_server_repo.get_server(
                    container_server_id
                )
                assert (
                    container_server
                ), f"Container server not found! container_server_id={container_server_id}"

                container_server_url = (
                    f"http://{container_server.ip_addr}:{container_server.port}"
                )
                response = await client.post(
                    f"{container_server_url}/api/container/shutdown",
                    json={
                        "token": container_server.token,
                        "container_id": container_id,
                    },
                    timeout=httpx.Timeout(60.0),
                )
                response.raise_for_status()
                ret = response.json()
                logger.info(f"Shutdown container response: {ret}")
                return ret.pop("status") == "success"
            except Exception as e:
                logger.error(f"Failed to shutdown container! {traceback.format_exc()}")
                raise

    async def _select_container_server(self) -> Optional[ContainerServer]:
        """Select a container server for the request"""
        servers = await self._container_server_repo.get_servers()
        if not servers:
            logger.error("No container servers available")
            return None

        # Use the first available backend (can be enhanced with load balancing logic)
        server = None
        for i in range(10):
            server = random.choice(servers)
            if await check_container_server_health(ip=server.ip_addr, port=server.port):
                return server
            else:
                logger.warning(
                    f"Container server {server.ip_addr}:{server.port} is not healthy, retry {i+1}/10"
                )
                await asyncio.sleep(1)
        return None

    async def shutdown(self):
        """Shutdown the container server manager"""
        pass

    async def register_container_server(self, new_server: ContainerServer) -> bool:
        """Register a container server"""
        assert new_server, "server is required"
        assert (
            new_server.ip_addr and new_server.port
        ), "ip_addr and manager_port are required"

        # Check for duplicate using list comprehension
        servers = await self._container_server_repo.get_servers()
        if any(s.server_id == new_server.server_id for s in servers):
            logger.debug(
                f"Container server already registered: {new_server.ip_addr}:{new_server.port}"
            )
            return False

        if not await check_container_server_health(
            ip=new_server.ip_addr, port=new_server.port
        ):
            logger.info(
                f"Container server not healthy: {new_server.ip_addr}:{new_server.port}"
            )
            return False

        # Add new server
        await self._container_server_repo.add_server(new_server)
        current_servers = await self._container_server_repo.get_servers()
        logger.info(
            f"Container server register success! current_servers={current_servers}"
        )
        return True

    async def initialize(self):
        """Initialize the container server manager"""

        await self._container_server_repo.initialize()

        async def health_check_task():
            while True:
                invalid_servers = []
                servers = await self._container_server_repo.get_servers()
                for s in servers:
                    if not await check_container_server_health(
                        ip=s.ip_addr, port=s.port
                    ):
                        invalid_servers.append(s)

                if invalid_servers:
                    for s in invalid_servers:
                        await self._container_server_repo.remove_server(s)
                    current_servers = await self._container_server_repo.get_servers()
                    logger.warning(
                        f"Container server health check failed: invalid_servers={invalid_servers}, current_container_servers={current_servers}"
                    )

                await asyncio.sleep(10)

        asyncio.create_task(health_check_task())

    async def get_container_servers(self) -> List[ContainerServer]:
        """Get all container servers"""
        return await self._container_server_repo.get_servers()


async def container_server_manager_builder():
    from ..configs import redis_url

    if redis_url:
        container_server_manager = ContainerServerManager(
            ContainerServerRedisRepo(redis_url)
        )
    else:
        container_server_manager = ContainerServerManager(ContainerServerRepo())

    await container_server_manager.initialize()
    return container_server_manager
