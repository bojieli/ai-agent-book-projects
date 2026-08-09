"""Unit tests for HybridStructuredRetriever covering core requirements and edge cases."""

import numpy as np
import pytest

from hybrid_retriever import HybridStructuredRetriever, SearchResult


def test_relation_target_included_in_text_content():
    """Verify that relation matching includes target entity name."""
    retriever = HybridStructuredRetriever()
    retriever.add_graphrag_relationship(
        relation_id="rel_1",
        source="Attention",
        target="Transformer",
        type="USED_IN",
        description="Core mechanism for neural architecture",
    )

    results = retriever.retrieve("Transformer", top_k=5)
    assert len(results) == 1
    assert results[0].node_id == "rel_1"
    assert "Transformer" in results[0].citation.citation_label or "Transformer" in results[0].text or "Transformer" in results[0].citation.lineage[1]


def test_precision_calculation_unique_matched_words():
    """Verify precision calculation counts unique matched query terms rather than token frequencies."""
    retriever = HybridStructuredRetriever()
    # Node content repeats "python" 5 times
    retriever.add_raptor_node(
        node_id="n1",
        level=0,
        text="python python python python python tutorial",
    )

    # Query has 2 terms: python, fast
    query_terms = {"python", "fast"}
    node = retriever.unified_nodes["raptor_n1"]
    final_sc, lex_sc, sem_sc = retriever._compute_scores("python fast", query_terms, None, node)

    # Lexical score should be 1 matched query term / 2 total query terms = 0.5
    assert lex_sc == 0.5


def test_stringify_numeric_ids_in_citation():
    """Verify that numeric node IDs, children, parents, and entity_ids do not cause TypeError during citation building."""
    retriever = HybridStructuredRetriever()

    # Numeric IDs in RAPTOR node
    retriever.add_raptor_node(
        node_id=101,
        level=1,
        text="Hierarchical summary text",
        children=[201, 202],
        parent=50,
    )

    # Numeric IDs in GraphRAG community
    retriever.add_graphrag_community(
        community_id=99,
        entity_ids=[1, 2, 3],
        summary="Community summary text",
    )

    results = retriever.retrieve("summary text", top_k=5)
    assert len(results) == 2
    for res in results:
        assert isinstance(res.node_id, str)
        assert isinstance(res.citation.node_id, str)
        assert all(isinstance(lin, str) for lin in res.citation.lineage)


def test_cache_node_embeddings():
    """Verify that node embeddings computed via embedding_fn are cached in node['embedding']."""
    embed_count = 0

    def mock_embed(text: str) -> np.ndarray:
        nonlocal embed_count
        embed_count += 1
        return np.array([0.1, 0.2, 0.3])

    retriever = HybridStructuredRetriever(embedding_fn=mock_embed)
    retriever.add_raptor_node(
        node_id="n1",
        level=0,
        text="Machine learning models",
    )

    node = retriever.unified_nodes["raptor_n1"]
    assert node["embedding"] is None

    # First retrieval computes and caches embedding
    retriever.retrieve("Machine learning", top_k=5)
    assert node["embedding"] is not None
    assert isinstance(node["embedding"], np.ndarray)
    initial_count = embed_count

    # Second retrieval reuses cached embedding
    retriever.retrieve("Machine learning", top_k=5)
    # embed_count should increase by 1 for query vector only, not for node embedding
    assert embed_count == initial_count + 1


def test_top_k_zero_returns_empty_list():
    """Verify that top_k == 0 returns an empty list immediately."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node(node_id="n1", level=0, text="Sample text")

    assert retriever.retrieve("Sample", top_k=0) == []
    assert retriever.retrieve("Sample", top_k=-1) == []


def test_clamp_rrf_k():
    """Verify that rrf_k is clamped with max(1, int(rrf_k))."""
    retriever = HybridStructuredRetriever(rrf_k=0)
    assert retriever.rrf_k == 1

    retriever_neg = HybridStructuredRetriever(rrf_k=-10)
    assert retriever_neg.rrf_k == 1

    retriever.add_raptor_node(node_id="n1", level=0, text="Sample text")
    results = retriever.retrieve("Sample", rrf_k=-5)
    assert len(results) == 1
    assert results[0].score > 0


def test_parent_id_zero_in_citation_lineage():
    """Verify that parent ID 0 is preserved in citation lineage, not dropped by truthiness (Finding 12)."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node(
        node_id="child_node",
        level=1,
        text="Child content for retrieval",
        summary="Child summary for retrieval",
        parent=0,
    )

    results = retriever.retrieve("Child content", top_k=1)
    assert len(results) == 1
    parent_entries = [lin for lin in results[0].citation.lineage if lin.startswith("Parent:")]
    assert len(parent_entries) == 1
    assert "0" in parent_entries[0]
