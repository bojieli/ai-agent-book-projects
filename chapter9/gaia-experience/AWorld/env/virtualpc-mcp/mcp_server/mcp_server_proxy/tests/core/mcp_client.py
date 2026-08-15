import asyncio
import json
import subprocess
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, List

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


async def mcp_client(
    url: str,
    token: str,
    session_id: str = None,
    mcp_servers: List[str] = [
        "readweb-server",
        "browser-server",
        "browseruse-server",
        "documents-csv-server",
        "documents-docx-server",
        "documents-pptx-server",
        "documents-pdf-server",
        "documents-txt-server",
        "download-server",
        "intelligence-code-server",
        "intelligence-think-server",
        "intelligence-guard-server",
        "media-audio-server",
        "media-image-server",
        "media-video-server",
        "parxiv-server",
        "terminal-server",
        "wayback-server",
        "wiki-server",
        "googlesearch-server",
    ],
) -> AsyncGenerator[ClientSession, None]:
    headers = {
        "Authorization": f"Bearer {token}",
        "MCP_SERVERS": ",".join(mcp_servers),
    }
    if session_id:
        headers["SESSION_ID"] = session_id

    async with streamablehttp_client(
        url=url,
        headers=headers,
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
