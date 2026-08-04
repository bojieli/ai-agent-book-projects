#!/usr/bin/env python3
"""Offline MCP v2 smoke test: start stdio, list tools, and call one tool."""

from __future__ import annotations

import asyncio
import os
import sys
from importlib.metadata import version
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
SERVER = HERE / "src" / "main.py"
PROTOCOL_VERSION = "2026-07-28"


async def smoke_test() -> None:
    sdk_version = version("mcp")
    if sdk_version.split(".", 1)[0] != "2":
        raise RuntimeError(f"Experiment 4-1 requires mcp>=2,<3; found {sdk_version}")

    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env=os.environ.copy(),
    )
    async with Client(stdio_client(parameters)) as client:
        if client.protocol_version != PROTOCOL_VERSION:
            raise RuntimeError(
                f"expected protocol {PROTOCOL_VERSION}, negotiated {client.protocol_version}"
            )

        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        if "file_reader" not in names:
            raise RuntimeError("tools/list did not return file_reader")

        result = await client.call_tool(
            "file_reader",
            arguments={"file_path": str(HERE / "requirements.txt"), "max_length": 2_000},
        )
        if result.is_error:
            raise RuntimeError(f"tools/call failed: {result.content!r}")

        server_name = client.server_info.name if client.server_info else None
        print(
            f"MCP smoke test passed: sdk={sdk_version}, "
            f"protocol={client.protocol_version}, server={server_name}, tools={len(names)}"
        )


if __name__ == "__main__":
    asyncio.run(smoke_test())
