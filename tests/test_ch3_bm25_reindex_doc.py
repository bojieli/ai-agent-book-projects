"""Regression test: re-indexing an existing doc_id in InvertedIndex must clear old terms and not inflate total_documents."""
import os
import sys

sys.path.insert(0, os.path.abspath("chapter3/sparse-embedding"))

from bm25_engine import InvertedIndex, BM25


def test_reindex_clears_old_terms_and_preserves_total_documents():
    index = InvertedIndex()
    index.add_document(1, "hello world")
    assert index.total_documents == 1
    assert "world" in index.index

    # Re-index doc 1 with new text missing 'world'
    index.add_document(1, "hello python")
    assert index.total_documents == 1, (
        f"total_documents was inflated on re-indexing: expected 1, got {index.total_documents}"
    )

    bm25 = BM25(index)
    results = bm25.search("world")
    matched_doc_ids = [r[0] for r in results]
    assert 1 not in matched_doc_ids, (
        f"Doc 1 was matched for term 'world' despite being re-indexed without it: {results}"
    )
