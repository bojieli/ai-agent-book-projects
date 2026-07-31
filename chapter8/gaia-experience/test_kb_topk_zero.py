from unittest.mock import MagicMock
import pytest
import sys

# Optional import fallback test helper
def test_kb_search_nonpositive_top_k():
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.documents = [{"question": "q1", "approach": "a1", "tools_used": None}]
    kb.encoder = MagicMock()
    kb.index = MagicMock()
    kb.index.ntotal = 5

    assert kb.search("query", top_k=0) == []
    assert kb.search("query", top_k=-1) == []
    kb.encoder.encode.assert_not_called()
    kb.index.search.assert_not_called()


def test_kb_keyword_search_null_tools_used():
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.documents = [{"question": "q1", "approach": "a1", "tools_used": None}]
    kb.encoder = None
    kb.index = None

    results = kb.search("q1", top_k=1)
    assert len(results) == 1
    assert results[0]["question"] == "q1"
def test_kb_keyword_search_scalar_tools_used():
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.documents = [{"question": "q1", "approach": "a1", "tools_used": 123}]
    kb.encoder = None
    kb.index = None

    results = kb.search("q1", top_k=1)
    assert len(results) == 1
    assert results[0]["question"] == "q1"
