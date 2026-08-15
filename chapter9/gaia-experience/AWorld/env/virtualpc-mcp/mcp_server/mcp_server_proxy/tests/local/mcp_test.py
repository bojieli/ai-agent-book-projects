import asyncio
import base64
import hashlib
import hmac
import json
import subprocess
import logging
import os
import time
from pathlib import Path
from typing import Any, AsyncGenerator

from mcp import ClientSession
from mcp.types import (
    LoggingMessageNotificationParams,
    ElicitResult,
    ElicitRequestParams,
)
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.context import RequestContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

LOCAL_MCP_TOKEN_SECRET = "123321"


def _jwt_part(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def gen_local_mcp_token(app: str = "mcp-gateway-debug") -> str:
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


if __name__ == "__main__":
    base_url, token = (
        "http://localhost:8000",
        gen_local_mcp_token(),
    )

    asyncio.run(McpClient.mcp_test_client(base_url, token))


class McpClient:

    async def mcp_test_client(
        base_url: str, token: str
    ) -> AsyncGenerator[ClientSession, None]:
        url = f"{base_url}/mcp"
        async with streamablehttp_client(
            url=url,
            headers={
                "Authorization": f"Bearer {token}",
                "MCP_SERVERS": "readweb-server,browser-server,browseruse-server,documents-csv-server,documents-docx-server,documents-pptx-server,documents-pdf-server,documents-txt-server,download-server,intelligence-code-server,intelligence-think-server,intelligence-guard-server,media-audio-server,media-image-server,media-video-server,parxiv-server,terminal-server,wayback-server,wiki-server,googlesearch-server",
                # "SESSION_ID": "CHAT_WLDEV",
            },
        ) as (
            read_stream,
            write_stream,
            get_session_id,
        ):

            async def logging_callback(params: LoggingMessageNotificationParams):
                logger.info(f"Receive logging callback: {params}")

            async def elicitation_callback(
                context: RequestContext["ClientSession", Any],
                params: ElicitRequestParams,
            ) -> ElicitResult:
                logger.info(f"Receive elicitation callback: {params}")
                return ElicitResult(action="accept", content={"user_name": "John"})

            async with ClientSession(
                read_stream=read_stream,
                write_stream=write_stream,
                logging_callback=logging_callback,
                elicitation_callback=elicitation_callback,
            ) as session:
                logger.info(f"MCP client connected: url={url}")
                await session.initialize()
                logger.info(
                    f"MCP client session initialized: url={url}, session_id={get_session_id()}"
                )

                yield session


    async def progress_callback(progress: float, total: float | None, message: str | None):
        logger.info(
            f"Receive progress callback: progress={progress}, total={total}, message={message}"
        )
        if "```tool_card" in message:
            data = json.loads(message.split("```tool_card")[1].split("```")[0])
            vnc_url = f"{base_url}{data.get('card_data').get('url')}"
            logger.info(f"VNC URL: {vnc_url}")
            subprocess.run(["open", vnc_url])
