from functools import cache
import socket
import logging
import traceback
import asyncio
import uuid
import httpx
import threading

from .dockers import docker_helper

from .configs import (
    container_server_port,
    docker_registry_url,
    docker_registry_user_name,
    docker_registry_password,
    mcp_server_image_id,
    gateway_server_addr,
    docker_mode,
    debug_mode,
)

logger = logging.getLogger(__name__)


token = str(uuid.uuid4())


async def wait_docker_ready(timeout: int = 30):
    for i in range(timeout):
        try:
            cmd = ["docker", "ps"]
            p = await asyncio.subprocess.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await p.communicate()
            if p.returncode == 0:
                logger.info(f"Docker daemon is ready! \n{stdout.decode()}")
                return
            else:
                logger.warning(f"Docker daemon is not ready! {stdout.decode()}")
        except:
            logger.error(f"Docker daemon is not ready! {traceback.format_exc()}")
        await asyncio.sleep(1)
    else:
        logger.error(f"Docker daemon is not ready after {timeout} seconds!")
        raise Exception(f"Docker daemon is not ready after {timeout} seconds!")


async def start_container_server_register_task():
    register_url = f"{gateway_server_addr}/api/container_server/register"
    local_ip_addr = get_local_ip()

    async def register():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    register_url,
                    json={
                        "token": token,
                        "ip_addr": local_ip_addr,
                        "port": container_server_port,
                        "cpu_load": [],
                        "memory_usage": [],
                    },
                    timeout=10.0,
                )

            response.raise_for_status()

        except Exception as e:
            logger.error(f"Register container server failed: {register_url}, {e}")
            raise

    async def init_register():
        for _ in range(20):
            try:
                await register()
                logger.info(f"Init register success")
                break
            except:
                await asyncio.sleep(3)
        else:
            logger.error(f"Init register failed after 20 times!")
            raise Exception(f"Init register failed after 20 times!")

    await init_register()

    async def update_register():
        while True:
            try:
                await register()
            except:
                logger.error(f"Update register failed: {traceback.format_exc()}")
            await asyncio.sleep(10)

    asyncio.create_task(update_register())


async def load_mcp_server_image():
    if docker_registry_url and docker_registry_user_name and docker_registry_password:
        await docker_helper.login_async(
            registry_url=docker_registry_url,
            username=docker_registry_user_name,
            password=docker_registry_password,
        )
    if not debug_mode:
        await docker_helper.pull_async(mcp_server_image_id)


async def start_mcp_server_life_cycle_manager():
    pass


async def clean_mcp_server_container():
    pass


async def create_mcp_server_container():
    mcp_port = docker_helper.get_available_port()
    novnc_port = docker_helper.get_available_port()
    ip_addr = get_local_ip()

    container_name = f"mcp_server_{str(uuid.uuid4()).replace('-', '')}"
    logger.info(
        f"Create mcp server container: {container_name}, image_id: {mcp_server_image_id}, mcp_port: {mcp_port}, novnc_port: {novnc_port}"
    )
    try:
        ports = {4242: f"{mcp_port}", 5901: f"{novnc_port}"}

        network = ""
        if docker_mode == "host":
            network = "visualvirtualpc_virtualpc-network"

        container = await docker_helper.run_async(
            image_id=mcp_server_image_id,
            container_name=container_name,
            ports=ports,
            network=network,
        )

        logger.info(
            f"Create mcp server container success, waiting for Ready: {container.id}, ip_addr: {ip_addr}, mcp_port: {mcp_port}, novnc_port: {novnc_port}"
        )

        def tail_logs():
            logs = container.logs(stream=True, tail=100, follow=True)
            try:
                buffer = []
                for line in logs:
                    buffer.append(line.decode())
                    if len(buffer) >= 20:
                        logger.info(f"VPC[{container.name}] >>> \n{'> '.join(buffer)}\n")
                        buffer.clear()
                if buffer:
                    logger.info(f"VPC[{container.name}] >>> \n{'> '.join(buffer)}\n")
                logger.info(f"VPC [{container.name}] logs end!")
            except Exception as e:
                logger.error(f"Error in tail_logs: {e}")

        # Start log tailing in background thread
        log_thread = threading.Thread(
            target=tail_logs, name=f"VPC_{container.name}_logs", daemon=True
        )
        log_thread.start()

        async def health_check(timeout: float = 3.0):
            try:
                # async with httpx.AsyncClient() as client:
                #     response = await client.get(
                #         f"http://{ip_addr}:{mcp_port}/health",
                #         timeout=httpx.Timeout(timeout),
                #     )
                #     response.raise_for_status()
                #     return True
                return await docker_helper.check_health(container.id)
            except Exception as e:
                logger.error(f"Check mcp server health error! {e}")
                return False

        max_check = 30
        for i in range(max_check):
            if await health_check():
                logger.info(
                    f"MCP server {ip_addr}:{mcp_port} is ready: {i+1}/{max_check}"
                )
                break
            else:
                logger.warning(
                    f"MCP server {ip_addr}:{mcp_port} is not ready: {i+1}/{max_check}"
                )
                await asyncio.sleep(3)
        else:
            logger.error(
                f"MCP server {ip_addr}:{mcp_port} is not ready after {max_check} times!"
            )
            raise Exception(
                f"MCP server {ip_addr}:{mcp_port} is not ready after {max_check} times!"
            )

        if docker_mode == "host":
            ip_addr = await docker_helper.get_container_ip(container.id)
            mcp_port = 4242
            novnc_port = 5901

        return container.id, ip_addr, mcp_port, novnc_port
    except:
        logger.error(f"Create mcp server container failed: {traceback.format_exc()}")
        raise


async def shutdown_mcp_server_container(container_id: str):
    try:
        await docker_helper.stop_async(container_id)
    except:
        logger.error(f"Shutdown mcp server container failed: {traceback.format_exc()}")
        raise


@cache
def get_local_ip() -> str | None:
    try:
        host_name = socket.gethostname()
        _, _, ip_list = socket.gethostbyname_ex(host_name)
        for ip in ip_list:
            if not ip.startswith("127."):
                return ip
    except Exception as e:
        logger.error(f"Get local ip failed: {traceback.format_exc()}")

    raise RuntimeError("Get local ip failed")
