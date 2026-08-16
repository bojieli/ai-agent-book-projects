import sys
from pathlib import Path
import pytest

pytest.importorskip("openai")
pytest.importorskip("numpy")

ch3_dir = Path(__file__).resolve().parent.parent / "chapter3" / "agentic-rag-for-user-memory"

# "tools" and "config" are names many chapters define. Importing them under the
# bare name leaves entries in sys.modules that later tests then pick up instead
# of their own module — chapter 5 sees this chapter's tools.py where it expects
# its tools/ package, and chapter 4's semantic router sees this config.py. So
# take the classes we need and put sys.path and sys.modules back as we found them.
_saved_path = list(sys.path)
_saved_modules = set(sys.modules)
sys.path.insert(0, str(ch3_dir))
try:
    from tools import MemoryTools, ToolResult  # noqa: E402
    from indexer import MemoryIndexer  # noqa: E402
    from config import IndexConfig  # noqa: E402
finally:
    for name in set(sys.modules) - _saved_modules:
        del sys.modules[name]
    sys.path[:] = _saved_path


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
