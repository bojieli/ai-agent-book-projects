from contextlib import AsyncExitStack
from datetime import timedelta
import json
import os
from pathlib import Path
import traceback
from typing import Any
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSessionT
from mcp.shared.context import LifespanContextT, RequestT
import logging
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from mcp.types import LoggingMessageNotificationParams
from .configs import mcp_servers_path


logger = logging.getLogger(__name__)


class MCPServerExecutor:
    def __init__(self, name: str, config: dict):
        self._name = name
        self._config = config
        self._session = None
        self._exit_stack = None
        self._lock = asyncio.Lock()
        self._init_event = asyncio.Event()
        self._terminate_event = asyncio.Event()

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Context[ServerSessionT, LifespanContextT, RequestT] | None = None,
        convert_result: bool = False,
    ) -> Any:
        """Call a tool by name with arguments."""

        await self._ensure_server_ready()

        async def progress_callback_adapter(
            progress: float, total: float | None, message: str | None
        ):
            logger.info(
                f"progress_callback: tool={name}, {progress}, {total}, {message}"
            )
            await self.progress_callback(
                progress=progress,
                total=total,
                message=message,
                context=context,
            )

        result = await self._session.call_tool(
            name, arguments, progress_callback=progress_callback_adapter
        )
        return result.content, result.structuredContent

    async def _ensure_server_ready(self):
        if not self._session:
            asyncio.create_task(self._start_tool_server())
            await self._init_event.wait()

    async def _start_tool_server(
        self,
    ):
        if self._session is not None:
            return
        async with self._lock:
            if self._session is not None:
                return

            name: str = self._name
            config: dict = self._config
            try:
                logger.info(f"Starting tool server {name} with config {config}")
                exit_stack = AsyncExitStack()
                await exit_stack.__aenter__()

                # Create client context and enter it
                if config.get("type") == "sse":
                    read_stream, write_stream = await exit_stack.enter_async_context(
                        sse_client(
                            url=config.get("url", ""),
                            headers=config.get("headers", {}),
                            timeout=config.get("timeout", 60 * 10),
                            sse_read_timeout=config.get("sse_read_timeout", 60 * 10),
                            auth=config.get("auth", None),
                        )
                    )

                elif config.get("type") == "streamable_http":
                    read_stream, write_stream, _ = await exit_stack.enter_async_context(
                        streamablehttp_client(
                            url=config.get("url", ""),
                            headers=config.get("headers", {}),
                            timeout=config.get("timeout", 60 * 10),
                            sse_read_timeout=config.get("sse_read_timeout", 60 * 10),
                            auth=config.get("auth", None),
                        )
                    )

                else:  # stdio
                    env = config.get("env", {})
                    env.update(os.environ)
                    server_params = StdioServerParameters(
                        command=config.get("command", ""),
                        args=config.get("args", []),
                        env=env,
                        cwd=str(Path(mcp_servers_path) / config.get("cwd", "")),
                    )
                    read_stream, write_stream = await exit_stack.enter_async_context(
                        stdio_client(server=server_params)
                    )

                async def log_callback(params: LoggingMessageNotificationParams):
                    logger.info(f"MCP Server {name} >>> {params}")

                # Create session and tool manager
                session = await exit_stack.enter_async_context(
                    ClientSession(
                        read_stream,
                        write_stream,
                        logging_callback=log_callback,
                        read_timeout_seconds=timedelta(
                            seconds=config.get("read_timeout", 60 * 10)
                        ),
                    )
                )
                await session.initialize()
                self._session = session
                self._exit_stack = exit_stack
                logger.info(f"Starting tool server success! {name}: {config}")
                self._init_event.set()
                await self._terminate_event.wait()
            except Exception as e:
                logger.error(
                    f"Error starting tool server {name}: {config}\n{traceback.format_exc()}"
                )
                self._init_event.set()
                try:
                    await self._exit_stack.aclose()
                except Exception:
                    pass
                raise e

    async def cleanup(self):
        self._terminate_event.set()
        self._session = None
        self._exit_stack = None

    async def progress_callback(
        self,
        progress: float,
        total: float | None,
        message: str | None,
        context: Context[ServerSessionT, LifespanContextT, RequestT] | None = None,
    ):

        def get_session_id() -> str:
            try:
                return context.request_context.request.headers.get("Mcp-Session-Id")
            except Exception as e:
                logger.error(f"Error getting session id: {e}")
                return None

        if "tool_call_card_novnc_window" == message:
            """Show the VNC window"""
            vnc_tool_card = {
                "type": "tool_call_card_novnc_window",
                "card_data": {
                    "title": "VNC Window",
                    "url": f"/novnc/{get_session_id()}/vnc.html?autoconnect=true&reconnect=true&quality=9&compression=9&show_dot=0&resize=local",
                    "token": get_session_id(),
                },
            }
            message = f"""\
\n\n
```tool_card
{json.dumps(vnc_tool_card, indent=2, ensure_ascii=False)}
```
\n\n
"""
        if context:
            await context.report_progress(
                progress=progress, total=total, message=message
            )
