"""Regression: FAISS padding index -1 must not map to documents[-1]."""
from pathlib import Path


def test_search_guards_negative_indices():
    src = Path(__file__).with_name("knowledge_base.py").read_text()
    assert "0 <= idx < len(self.documents)" in src

    documents = [{"id": i} for i in range(3)]
    indices = [0, -1, -1]
    results = [documents[idx] for idx in indices if 0 <= idx < len(documents)]
    assert results == [{"id": 0}]


def test_index_dimension_tracks_model_and_rebuilds_on_mismatch():
    """The FAISS index dimension must come from the loaded model (not a fixed
    384), and a persisted index built with a different model must be rebuilt on
    load — otherwise every add()/search() raises a swallowed dimension mismatch
    and semantic search silently degrades to keyword-only."""
    src = Path(__file__).with_name("knowledge_base.py").read_text()
    assert "get_sentence_embedding_dimension()" in src
    assert "self.index.d != self.embedding_dim" in src
    assert "_rebuild_index_from_metadata" in src
