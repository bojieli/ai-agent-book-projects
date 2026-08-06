import pytest
"""Regression test: re-indexing an existing doc_id in InvertedIndex must clear old terms and not inflate total_documents."""
import os
import sys

sys.path.insert(0, os.path.abspath("chapter3/sparse-embedding"))

from bm25_engine import InvertedIndex, BM25  # noqa: E402


def test_reindex_maintains_doc_count_and_clears_stale_terms():
    index = InvertedIndex()
    index.add_document(1, "python database sql")
    assert index.total_documents == 1
    assert index.get_posting_list("database") == {1}
    assert index.document_frequency["database"] == 1

    # Re-index doc 1 with completely different terms
    index.add_document(1, "python web fasta")
    assert index.total_documents == 1
    assert index.get_posting_list("database") == set()
    assert "database" not in index.document_frequency
    assert index.get_posting_list("web") == {1}
    assert index.document_frequency["web"] == 1


def test_reindex_search_engine_bm25_scores():
    index = InvertedIndex()
    index.add_document(10, "machine learning deep learning")
    index.add_document(20, "quantum computing physics")
    assert index.total_documents == 2

    bm25 = BM25(index)
    results_before = bm25.search("machine learning")
    assert len(results_before) == 1
    assert results_before[0][0] == 10

    # Update document 10 to quantum physics
    index.add_document(10, "quantum physics mechanics")
    assert index.total_documents == 2

    # Search for machine learning should yield 0 results
    results_after_old = bm25.search("machine learning")
    assert len(results_after_old) == 0

    # Search for quantum should yield both 10 and 20
    results_after_new = bm25.search("quantum")
    doc_ids = {r[0] for r in results_after_new}
    assert doc_ids == {10, 20}
