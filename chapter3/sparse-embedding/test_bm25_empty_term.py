import pytest
from bm25_engine import InvertedIndex, BM25, TextProcessor


def test_bm25_search_empty_term_in_query_terms_no_index_error():
    index = InvertedIndex()
    index.add_document(1, "hello world")
    bm25 = BM25(index)

    orig_tokenize = TextProcessor.tokenize
    try:
        TextProcessor.tokenize = lambda self, text, remove_stop_words=True: ["hello", ""]
        results = bm25.search("hello")
        assert len(results) == 1
        assert results[0][0] == 1
    finally:
        TextProcessor.tokenize = orig_tokenize
