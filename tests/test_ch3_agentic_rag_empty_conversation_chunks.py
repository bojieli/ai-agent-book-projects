import sys
import os
import pytest

pytest.importorskip("openai")
pytest.importorskip("numpy")

sys.path.insert(0, os.path.abspath("chapter3/agentic-rag-for-user-memory"))

from tools import MemoryTools, ToolResult
from indexer import MemoryIndexer
from config import IndexConfig


def test_memory_tools_empty_conversation_chunks():
    """Contract: MemoryTools handles empty conversation chunks cleanly without raising ValueError."""
    config = IndexConfig()
    indexer = MemoryIndexer(config=config)
    # Ensure chunks dict is empty
    indexer.chunks = {}

    tools = MemoryTools(indexer)

    # 1. get_full_conversation on empty indexer
    result = tools.get_full_conversation("empty_conv_id", "test_id_1")
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "No chunks found" in result.error

    # 2. search_memory on empty indexer
    search_res = tools.search_memory("user preference")
    assert isinstance(search_res, ToolResult)
    assert search_res.success is True
    assert search_res.data["total_results"] == 0

    # 3. get_conversation_context on non-existent chunk
    context_res = tools.get_conversation_context("chunk_999")
    assert isinstance(context_res, ToolResult)
    assert context_res.success is False
    assert "not found" in context_res.error
