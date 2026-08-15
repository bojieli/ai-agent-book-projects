import asyncio
import traceback
from typing import Tuple
import docker
import logging
import socket

logger = logging.getLogger(__name__)

client = docker.from_env(timeout=600)


async def login_async(registry_url: str, username: str, password: str):
    try:
        return await asyncio.to_thread(login, registry_url, username, password)
    except Exception as e:
        logger.error(f"Error in login_async: {e}")
        raise


async def pull_async(image_id: str):
    try:
        return await asyncio.to_thread(pull, image_id)
    except Exception as e:
        logger.error(f"Error in pull_async: {e}")
        raise


async def run_async(
    image_id: str,
    container_name: str,
    ports: dict[int, str] = {},
    network: str = "",
    volumes: dict[str, str] = {},
    environments: dict[str, str] = {},
):
    try:
        return await asyncio.to_thread(
            run, image_id, container_name, ports, network, volumes, environments
        )
    except Exception as e:
        logger.error(f"Error in run_async: {e}")
        raise


async def exec_async(container_id: str, cmd: list[str]) -> Tuple[int, str]:
    try:
        return await asyncio.to_thread(exec, container_id, cmd)
    except Exception as e:
        logger.error(f"Error in exec_async: {e}")
        raise


async def stop_async(container_id: str):
    try:
        return await asyncio.to_thread(stop, container_id)
    except Exception as e:
        logger.error(f"Error in stop_async: {e}")
        raise


async def check_health(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.reload()
        return container.health == "healthy"
    except Exception as e:
        logger.error(f"Error in check_health: {e}")
        return False


async def get_container_ip(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.reload()
        nets = container.attrs["NetworkSettings"]["Networks"]
        net = list(nets.values())[0]
        return net["IPAddress"]
    except Exception as e:
        logger.error(f"Error in get_container_ip: {e}")
        return None


async def build_image_async(image_id: str, dockerfile: str, context_path: str):
    async def build():
        try:
            cmd = [
                "docker",
                "build",
                "--platform",
                "linux/amd64",
                "-t",
                image_id,
                "-f",
                dockerfile,
                context_path,
            ]
            p = await asyncio.subprocess.create_subprocess_exec(
                *cmd,
                cwd=context_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            assert p.stdout is not None
            while True:
                line = await p.stdout.readline()
                if not line:
                    break
                logger.info(line.decode(errors="ignore").rstrip())

            rc = await p.wait()
            if rc == 0:
                logger.info("Build mcp server image success!")
                return
            else:
                raise Exception(f"Build mcp server image error! return code: {rc}")
        except Exception as e:
            logger.error(f"Build mcp server image error! {e}")
            raise

    for _ in range(3):
        try:
            await build()
            break
        except Exception as e:
            await asyncio.sleep(1)
    else:
        logger.info(f"Build mcp server image failed after 3 times!")
        raise Exception("Build mcp server image failed after 3 times!")


def pull(image_id: str):
    logger.info(f"Pulling image {image_id}")
    try:
        if client.images.get(image_id):
            logger.info(f"Image {image_id} already exists, skipping pull")
            return
        img = client.images.pull(image_id)
        logger.info(f"Pulled image {image_id}, {img}")
    except:
        logger.error(f"Failed to pull image {image_id}\n{traceback.format_exc()}")
        raise


def run(
    image_id: str,
    container_name: str,
    ports: dict[int, str] = {},
    network: str = "",
    volumes: dict[str, str] = {},
    environments: dict[str, str] = {},
):
    logger.info(
        f"Creating container {container_name} with args: {{'name': {container_name}, 'image': {image_id}, 'ports': {ports}, 'volumes': {volumes}, 'environments': {environments}}}"
    )
    try:
        container = client.containers.run(
            name=container_name,
            image=image_id,
            detach=True,
            auto_remove=True,
            ports=ports,
            network=network,
            volumes=volumes,
            environment=environments,
            cpu_period=100000,
            cpu_quota=90000,
            mem_limit="2G",
        )
        logger.info(f"Created container {container_name} response: {container}")
        return container
    except:
        logger.error(
            f"Failed to create container {container_name} with image {image_id}\n{traceback.format_exc()}"
        )
        raise


def exec(container_id: str, cmd: list[str]) -> Tuple[int, str]:
    logger.info(f"Executing command {cmd} on container {container_id}")
    try:
        container = client.containers.get(container_id)
        exit_code, output = container.exec_run(cmd)
        logger.info(
            f"Command {cmd} executed on container {container_id} with result: {exit_code} {output}"
        )
        return exit_code, output
    except:
        logger.error(
            f"Failed to execute command {cmd} on container {container_id}\n{traceback.format_exc()}"
        )
        raise


def stop(container_id: str):
    logger.info(f"Stop container {container_id}")
    try:
        container = client.containers.get(container_id)
        container.stop()
        logger.info(f"Stopped container {container_id}")
    except:
        logger.error(
            f"Failed to stop container {container_id}\n{traceback.format_exc()}"
        )
        raise


def login(registry_url: str, username: str, password: str):
    logger.info(f"Logging in to {registry_url} with username {username}")
    try:
        result = client.login(
            registry=registry_url, username=username, password=password
        )
        logger.info(
            f"Logged in to {registry_url} with username {username} result: {result}"
        )
    except:
        logger.error(
            f"Failed to login to {registry_url} with username {username}\n{traceback.format_exc()}"
        )
        raise


def get_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        return port
