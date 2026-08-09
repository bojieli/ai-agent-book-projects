import pytest
import os
import sys

sys.path.insert(0, os.path.abspath("chapter3/sparse-embedding"))

from collections import Counter
from bm25_engine import InvertedIndex, BM25


def test_bm25_calculate_term_score_zero_avgdl():
    """Prove that calculating term score when avgdl is 0 handles division by zero safely."""
    index = InvertedIndex()
    bm25 = BM25(index)
    assert bm25.avgdl == 0
    index.term_frequency[1] = Counter({"python": 2})
    index.doc_lengths[1] = 5
    index.index["python"].add(1)

    score = bm25.calculate_term_score("python", doc_id=1)
    assert isinstance(score, float)


def test_bm25_calculate_raw_idf_n_less_than_df():
    """Prove that calculate_raw_idf when total_documents N < df does not raise math domain error."""
    index = InvertedIndex()
    index.index["python"].add(1)
    bm25 = BM25(index)

    idf = bm25.calculate_raw_idf("python")
    assert isinstance(idf, float)
