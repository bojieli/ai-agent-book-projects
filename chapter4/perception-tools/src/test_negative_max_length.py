"""Regression: negative max_length must not drop the last character."""
import asyncio
import json
import sys
import types
from pathlib import Path

import pytest


def _stub():
    for name in ["dotenv", "requests", "mcp", "mcp.types", "mcp.server", "mcp.server.fastmcp"]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["dotenv"].load_dotenv = lambda *a, **k: None
    class TextContent:
        def __init__(self, type=None, text=None):
            self.type = type
            self.text = text
    sys.modules["mcp.types"].TextContent = TextContent
    class FastMCP:
        def __init__(self, *a, **k): pass
        def tool(self, *a, **k):
            def deco(fn): return fn
            return deco
    sys.modules["mcp.server.fastmcp"].FastMCP = FastMCP


_stub()
from filesystem_tools import read_file  # noqa: E402


@pytest.mark.asyncio
async def test_negative_max_length_keeps_full_content(tmp_path: Path):
    path = tmp_path / "a.txt"
    path.write_text("hello world", encoding="utf-8")
    r = await read_file(str(path), max_length=-1)
    payload = json.loads(r.text if hasattr(r, "text") else r)
    msg = payload.get("message", payload)
    if isinstance(msg, dict) and "content" in msg:
        content = msg["content"]
    elif isinstance(msg, str):
        content = msg
    else:
        content = str(msg)
    assert "hello world" in content
