"""Regression: extract_csv_content must honor max_rows in data, not hard-cap at 100."""
import asyncio
import json
import sys
import types
from pathlib import Path

import pandas as pd
import pytest


def _stub_deps() -> None:
    for name in ["docx", "pptx", "PyPDF2", "dotenv"]:
        sys.modules.setdefault(name, types.ModuleType(name))
    sys.modules["docx"].Document = object
    sys.modules["pptx"].Presentation = object
    sys.modules["dotenv"].load_dotenv = lambda *a, **k: None

    mcp = types.ModuleType("mcp")
    mcp_types = types.ModuleType("mcp.types")

    class TextContent:
        def __init__(self, type=None, text=None):
            self.type = type
            self.text = text

    mcp_types.TextContent = TextContent
    sys.modules["mcp"] = mcp
    sys.modules["mcp.types"] = mcp_types


_stub_deps()

from document_processing_tools import extract_csv_content  # noqa: E402


@pytest.mark.asyncio
async def test_csv_data_honors_max_rows(tmp_path: Path):
    path = tmp_path / "t.csv"
    pd.DataFrame({"id": range(250)}).to_csv(path, index=False)
    r = await extract_csv_content(str(path), max_rows=1000)
    payload = json.loads(r.text)
    msg = payload["message"]
    assert msg["rows"] == 250
    assert len(msg["data"]) == 250
    assert msg["truncated"] is False
