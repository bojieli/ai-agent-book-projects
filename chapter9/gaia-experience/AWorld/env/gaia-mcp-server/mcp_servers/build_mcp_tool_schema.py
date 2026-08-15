#!/usr/bin/env python3
"""Script to generate mcp_tool_schema.json"""

import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta
import json
import logging
from pathlib import Path
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _list_tools(name: str, config: dict):
    logger.info(f"Starting tool server {name} with config {config}")
    async with AsyncExitStack() as exit_stack:
        try:
            if config.get("type") == "sse":
                read_stream, write_stream = await exit_stack.enter_async_context(
                    sse_client(
                        url=config.get("url", ""),
                        headers=config.get("headers", {}),
                        timeout=config.get("timeout", 5),
                        sse_read_timeout=config.get("sse_read_timeout", 60 * 5),
                        auth=config.get("auth", None),
                    )
                )

            elif config.get("type") == "streamable_http":
                read_stream, write_stream, _ = await exit_stack.enter_async_context(
                    streamablehttp_client(
                        url=config.get("url", ""),
                        headers=config.get("headers", {}),
                        timeout=config.get("timeout", 60),
                        sse_read_timeout=config.get("sse_read_timeout", 60 * 5),
                        auth=config.get("auth", None),
                    )
                )

            else:  # stdio
                base_folder = (
                    Path(__file__).resolve().parent
                )
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
                    read_timeout_seconds=timedelta(
                        seconds=config.get("read_timeout", 60)
                    ),
                )
            )
            await session.initialize()
            result = await session.list_tools()
            return name, result.tools if result else []
        except Exception as e:
            logger.error(f"Error starting tool server {name}: {config}, {e}")
            return name, []


async def list_mcp_server_tools():
    from mcp_config import mcp_config as config

    json_tools = {}
    for server_name, server_config in config.get("mcpServers", {}).items():
        result = await _list_tools(server_name, server_config)
        name, tools = result
        logger.info(f"Result for {name}: {tools}")

        tools_dict = [
            {
                "name": tool.name,
                "title": tool.title,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
                "outputSchema": tool.outputSchema,
                "annotations": (
                    {
                        "title": tool.annotations.title,
                        "readOnlyHint": tool.annotations.readOnlyHint,
                        "destructiveHint": tool.annotations.destructiveHint,
                        "idempotentHint": tool.annotations.idempotentHint,
                        "openWorldHint": tool.annotations.openWorldHint,
                    }
                    if tool.annotations
                    else None
                ),
                "meta": tool.meta,
            }
            for tool in tools
        ]
        json_tools[name] = tools_dict

    if json_tools:
        with open(Path(__file__).resolve().parent / "mcp_tool_schema.json", "w") as f:
            f.write(json.dumps(json_tools, indent=4, ensure_ascii=False))
    else:
        logger.error("No results for list_results!")


if __name__ == "__main__":
    asyncio.run(list_mcp_server_tools())
