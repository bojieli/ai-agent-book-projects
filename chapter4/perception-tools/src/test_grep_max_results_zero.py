"""Regression: grep_search(max_results=0) must return zero hits, not one."""
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
        def __init__(self, *a, **k):
            pass

        def tool(self, *a, **k):
            def deco(fn):
                return fn

            return deco

    sys.modules["mcp.server.fastmcp"].FastMCP = FastMCP


_stub()
from filesystem_tools import grep_search  # noqa: E402


@pytest.mark.asyncio
async def test_max_results_zero_returns_no_matches(tmp_path: Path):
    (tmp_path / "a.py").write_text("hello world\nhello again\n", encoding="utf-8")
    r = await grep_search("hello", str(tmp_path), max_results=0)
    payload = json.loads(r.text if hasattr(r, "text") else r)
    assert payload["success"] is True
    msg = payload["message"]
    assert msg["results"] == []
    assert msg["total_found"] == 0
    assert msg["truncated"] is False


@pytest.mark.asyncio
async def test_max_results_one_still_caps(tmp_path: Path):
    (tmp_path / "a.py").write_text("hello world\nhello again\n", encoding="utf-8")
    r = await grep_search("hello", str(tmp_path), max_results=1)
    payload = json.loads(r.text if hasattr(r, "text") else r)
    msg = payload["message"]
    assert msg["total_found"] == 1
    assert len(msg["results"]) == 1
    assert msg["truncated"] is True
