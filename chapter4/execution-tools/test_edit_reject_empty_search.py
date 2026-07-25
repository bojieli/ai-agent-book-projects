"""Regression: edit_file must reject empty search text (not insert at start)."""
import tempfile
from pathlib import Path

import pytest

from llm_helper import LLMHelper
from file_tools import FileTools


@pytest.mark.asyncio
async def test_empty_search_rejected():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td).resolve()
        tools = FileTools(LLMHelper())
        tools.workspace_dir = root
        target = root / "note.txt"
        target.write_text("hello world\n", encoding="utf-8")

        result = await tools.edit_file(path="note.txt", search="", replace="INJECT")
        assert result["success"] is False
        assert "empty" in result["error"].lower()
        assert target.read_text(encoding="utf-8") == "hello world\n"


@pytest.mark.asyncio
async def test_normal_edit_still_works():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td).resolve()
        tools = FileTools(LLMHelper())
        tools.workspace_dir = root
        target = root / "note.txt"
        target.write_text("hello world\n", encoding="utf-8")

        result = await tools.edit_file(
            path="note.txt", search="hello", replace="hi"
        )
        assert result["success"] is True
        assert target.read_text(encoding="utf-8") == "hi world\n"
