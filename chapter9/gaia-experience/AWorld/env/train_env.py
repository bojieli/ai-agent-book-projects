import argparse
import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import shutil
import time
import traceback
from dotenv import dotenv_values, set_key
import httpx
from mcp import ClientSession
from mcp.types import (
    LoggingMessageNotificationParams,
    ElicitResult,
    ElicitRequestParams,
)
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.context import RequestContext

from aworld.utils.common import get_local_ip

logger = logging.getLogger(__name__)

LOCAL_MCP_TOKEN_SECRET = "123321"


def _jwt_part(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def gen_local_mcp_token(app: str = "local_debug") -> str:
    secret = os.getenv("MCP_GATEWAY_TOKEN_SECRET", LOCAL_MCP_TOKEN_SECRET)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"app": app, "version": 1, "time": time.time()}
    signing_input = f"{_jwt_part(header)}.{_jwt_part(payload)}"
    signature = hmac.new(
        secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{signing_input}.{encoded_signature}"


class TranEnv:

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.env_dir = self.base_dir / "env"
        self.mcp_config = None
        self.mcp_variables = None

    def get_env_config(self):
        if self.mcp_variables:
            url = f"http://{self.mcp_variables['ip']}:{self.mcp_variables['port']}/mcp"
            self.mcp_config = {
                "mcpServers": {
                    "virtualpc-mcp": {
                        "type": "streamable-http",
                        "url": url,
                        "headers": {
                            "Authorization": f"Bearer {self.mcp_variables['token']}",
                        },
                        "timeout": 600,
                        "sse_read_timeout": 600,
                        "client_session_timeout_seconds": 600,
                    }
                }
            }
            return self.mcp_config
        return None

    async def create_env(self, mode: str = "local", docker_dir: str = None) -> bool:
        if mode == "local":
            if not docker_dir:
                logger.error("You must provide --docker_dir to specify the Docker directory to build (relative to env).")
                return False

            image_ready = await self._build_image(docker_dir)
            assert image_ready, "Image is not ready!"

            service_ready = await self._start_service()
            assert service_ready, "Service config is not ready!"

            service_ready = await self._check_service_ready()
            assert service_ready, "Service is not ready!"

            self.mcp_variables = {
                "ip": get_local_ip(),
                "port": 8000,
                "token": gen_local_mcp_token(),
            }

            logger.info("✅ Service is ready!")
            return True
        else:
            logger.warning(f"Mode {mode} is not supported!")
            return False

    async def _build_image(self, docker_dir: str):
        try:
            # Use asyncio.create_subprocess_exec for async subprocess execution
            logger.info(f"Building {docker_dir} image...")
            process1 = await asyncio.create_subprocess_exec(
                "sh",
                "build-image.sh",
                cwd=self.env_dir / "virtualpc-mcp" / "mcp_server",
            )
            await process1.wait()

            if process1.returncode != 0:
                logger.error("Failed to build virtualpc-mcp image")
                return False

            target_dir = self.env_dir / docker_dir
            if not target_dir.exists():
                logger.error(f"Specified Docker directory does not exist: {target_dir}")
                return False

            process2 = await asyncio.create_subprocess_exec(
                "sh",
                "build-image.sh",
                cwd=target_dir,
            )
            await process2.wait()

            if process2.returncode != 0:
                logger.error(f"Failed to build {docker_dir} image")
                return False

            logger.info("All images built successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to build image: {traceback.format_exc()}")
            return False

    async def _start_service(self):
        try:
            logger.info("Starting virtualpc-mcp service...")
            process = await asyncio.create_subprocess_exec(
                "sh",
                "run-local.sh",
                cwd=self.env_dir / "virtualpc-mcp",
            )

            # Wait a bit for the service to start
            await asyncio.sleep(2)

            return True
        except Exception as e:
            logger.error(f"Failed to start service: {traceback.format_exc()}")
            return None

    async def _check_service_ready(self) -> bool:
        url = "http://localhost:8000/health"

        max_retries = 180
        for i in range(max_retries):
            try:
                # Try to establish MCP connection to check if service is ready
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    return True
            except Exception as e:
                logger.error(
                    f"Waiting for service ready: {(i+1)}/{max_retries} attempts"
                )
                await asyncio.sleep(10)
        else:
            logger.error(
                f"Service at {url} is not reachable after {max_retries} attempts."
            )
            return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Env construction")
    parser.add_argument("--docker_dir", help="Docker directory to build (relative to env, e.g., gaia-mcp-server)")

    async def main():
        try:
            args = parser.parse_args()
            if not args.docker_dir:
                parser.error("You must use --docker_dir to specify the Docker directory to build (e.g., gaia-mcp-server)")
            train_env = TranEnv()
            env_started = await train_env.create_env(docker_dir=args.docker_dir)
            if env_started:
                mcp_variables = json.dumps(train_env.mcp_variables, ensure_ascii=False, indent=4)
                print(mcp_variables)
        except Exception as e:
            logger.error(f"Failed to start env: {traceback.format_exc()}")


    asyncio.run(main())
