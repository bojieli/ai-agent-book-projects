import pytest
from bm25_engine import TextProcessor


def test_tokenize_preserves_apostrophe_contractions():
    processor = TextProcessor()
    tokens = processor.tokenize("don't user's it's text")
    assert "don't" in tokens
    assert "user's" in tokens
    assert "it's" in tokens
