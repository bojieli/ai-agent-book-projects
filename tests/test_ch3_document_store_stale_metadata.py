import pytest
import sys
from pathlib import Path

ch3_retrieval = Path(__file__).resolve().parent.parent / "chapter3" / "retrieval-pipeline"
if str(ch3_retrieval) not in sys.path:
    sys.path.insert(0, str(ch3_retrieval))

from document_store import DocumentStore  # noqa: E402


def test_add_document_clears_stale_metadata_keys():
    store = DocumentStore()
    store.add_document("doc1", "Text 1", {"author": "Alice", "category": "AI"})
    assert "author" in store.metadata_index
    assert "category" in store.metadata_index
    assert store.metadata_index["category"] == ["doc1"]

    store.add_document("doc1", "Updated Text 1", {"author": "Alice"})
    assert "author" in store.metadata_index
    assert "category" not in store.metadata_index
    assert store.get_stats()["metadata_fields"] == ["author"]


def test_add_document_clears_all_metadata_when_updated_with_none():
    store = DocumentStore()
    store.add_document("doc1", "Text 1", {"topic": "Math", "level": "Intro"})
    assert "topic" in store.metadata_index

    store.add_document("doc1", "Text 1 updated", None)
    assert "topic" not in store.metadata_index
    assert "level" not in store.metadata_index
    assert store.metadata_index == {}


def test_add_document_update_preserves_other_documents_index():
    store = DocumentStore()
    store.add_document("doc1", "Doc 1", {"tag": "shared", "extra": "doc1_only"})
    store.add_document("doc2", "Doc 2", {"tag": "shared"})

    assert store.metadata_index["tag"] == ["doc1", "doc2"]
    assert store.metadata_index["extra"] == ["doc1"]

    store.add_document("doc1", "Doc 1 v2", {"tag": "shared"})
    assert store.metadata_index["tag"] == ["doc1", "doc2"]
    assert "extra" not in store.metadata_index
