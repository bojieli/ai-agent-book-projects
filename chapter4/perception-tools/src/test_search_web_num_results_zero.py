"""Regression test for search_web num_results=0 handling.

Proves contract: Requesting zero search results short-circuits external search
providers and returns success with empty result list and count 0.
Locks out bug where max(1, min(num_results, 10)) clamped num_results=0 to 1.
"""

import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

def _stub():
    for name in ["dotenv", "mcp", "mcp.types", "mcp.server", "mcp.server.fastmcp"]:
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

from search_tools import search_web  # noqa: E402


@pytest.mark.asyncio
async def test_search_web_num_results_zero_returns_no_results():
    result = await search_web("Python", num_results=0)
    payload = json.loads(result.text if hasattr(result, "text") else result)
    assert payload["success"] is True
    message = payload["message"]
    assert message["results"] == []
    assert message["count"] == 0
    assert payload["metadata"]["total_results"] == 0


@pytest.mark.asyncio
async def test_search_web_num_results_negative_returns_no_results():
    result = await search_web("Python", num_results=-5)
    payload = json.loads(result.text if hasattr(result, "text") else result)
    assert payload["success"] is True
    message = payload["message"]
    assert message["results"] == []
    assert message["count"] == 0
    assert payload["metadata"]["total_results"] == 0
