import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta
import json
import logging
from pathlib import Path
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/workspace"],
}


async def server_session():
    async with AsyncExitStack() as exit_stack:
        # Create client context and enter it
        if config.get("type") == "sse":
            read_stream, write_stream = await exit_stack.enter_async_context(
                sse_client(
                    url=config.get("url", ""),
                    headers=config.get("headers", {}),
                    timeout=config.get("timeout", 60),
                    sse_read_timeout=config.get("sse_read_timeout", 60 * 5),
                    auth=config.get("auth", None),
                )
            )

        elif config.get("type") == "streamable_http":
            read_stream, write_stream, _ = await exit_stack.enter_async_context(
                streamablehttp_client(
                    url=config.get("url", ""),
                    headers=config.get("headers", {}),
                    timeout=config.get("timeout", 120),
                    sse_read_timeout=config.get("sse_read_timeout", 60 * 5),
                    auth=config.get("auth", None),
                )
            )

        else:  # stdio
            base_folder = Path(__file__).parent
            server_params = StdioServerParameters(
                command=config.get("command", ""),
                args=config.get("args", []),
                env=config.get("env", {}),
                cwd=str(base_folder / config.get("cwd", "")),
            )
            read_stream, write_stream = await exit_stack.enter_async_context(
                stdio_client(server=server_params)
            )

        # Create session and tool manager
        session = await exit_stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
                read_timeout_seconds=timedelta(seconds=config.get("read_timeout", 120)),
            )
        )
        await session.initialize()
        
        yield session
        
async def test():
    async for session in server_session():
        ls = await session.list_tools()
        assert ls and ls.tools, "list_tools return null"
        tools = ls.tools
        logger.info(f"list_tools return:\n  - {'\n  - '.join([t.name for t in tools])}")
        print(tools[0])

if __name__ == "__main__":
    asyncio.run(test())
