"""Regression: chunk_size=0 must not crash range() on long sentences.

Use the experiment's real configuration module.  The former process-global
``sys.modules['config']`` stub leaked into later test modules and made their
imports depend on pytest collection order.
"""

from config import ChunkingConfig
from chunking import DocumentChunker


def test_chunk_size_zero_long_unsplittable_sentence():
    cfg = ChunkingConfig(chunk_size=0, max_chunk_size=40, min_chunk_size=1)
    chunker = DocumentChunker(cfg)
    text = "alpha" * 80  # longer than max_chunk_size, no paragraph breaks
    chunks = chunker.chunk_text(text, doc_id="d1")
    assert isinstance(chunks, list)
    assert len(chunks) >= 1
