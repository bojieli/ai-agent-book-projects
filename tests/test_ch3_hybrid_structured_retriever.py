"""Unit tests for chapter3/structured-index/hybrid_retriever.py (HybridStructuredRetriever)."""

import importlib.util
import os
import sys
from pathlib import Path
import pytest

pytest.importorskip("numpy")
import numpy as np

# Dynamic import for hyphenated module path
_module_path = (
    Path(__file__).resolve().parent.parent
    / "chapter3"
    / "structured-index"
    / "hybrid_retriever.py"
)
_spec = importlib.util.spec_from_file_location("hybrid_retriever", _module_path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["hybrid_retriever"] = _mod
_spec.loader.exec_module(_mod)

HybridStructuredRetriever = _mod.HybridStructuredRetriever
SearchResult = _mod.SearchResult
EvidenceCitation = _mod.EvidenceCitation


def test_add_nodes_and_basic_retrieval():
    """Verify RAPTOR nodes and GraphRAG entities can be added and retrieved."""
    retriever = HybridStructuredRetriever(rrf_k=60)

    # Add RAPTOR tree summary node
    retriever.add_raptor_node(
        node_id="r1",
        level=2,
        text="Deep learning architectures utilize multi-layer neural networks.",
        summary="Overview of deep learning and multi-layer neural networks.",
        children=["r1_1", "r1_2"],
    )

    # Add GraphRAG entity
    retriever.add_graphrag_entity(
        entity_id="e1",
        name="Neural Network",
        type="ARCHITECTURE",
        description="A machine learning model inspired by biological neural circuits.",
    )

    # Add GraphRAG relationship
    retriever.add_graphrag_relationship(
        relation_id="rel1",
        source="Neural Network",
        target="Deep Learning",
        type="USED_IN",
        description="Neural networks serve as foundational models in deep learning.",
    )

    results = retriever.retrieve("deep learning neural network", top_k=5)

    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    assert results[0].score > 0.0

    # Verify citation details exist on all results
    for res in results:
        assert isinstance(res.citation, EvidenceCitation)
        assert res.citation.source_type in (
            "raptor_tree",
            "graphrag_entity",
            "graphrag_relation",
            "graphrag_community",
        )
        assert len(res.citation.citation_label) > 0


def test_rrf_scoring_order_and_fusion():
    """Verify Reciprocal Rank Fusion combines RAPTOR and GraphRAG rankings."""
    retriever = HybridStructuredRetriever(rrf_k=60)

    # RAPTOR node relevant to quantum computing
    retriever.add_raptor_node(
        node_id="rap_quantum",
        level=1,
        text="Quantum algorithms exploit superposition and entanglement.",
        summary="Quantum computing algorithms and superposition.",
    )

    # GraphRAG community summary relevant to quantum computing
    retriever.add_graphrag_community(
        community_id="comm_quantum",
        entity_ids=["Qubit", "QuantumGate"],
        summary="Community of quantum hardware components and quantum algorithms.",
        level=0,
    )

    # Irrelevant node
    retriever.add_raptor_node(
        node_id="rap_gardening",
        level=0,
        text="Gardening tips for growing organic tomatoes in summer.",
        summary="Organic tomato gardening guidance.",
    )

    results = retriever.retrieve("quantum algorithms superposition", top_k=2)

    assert len(results) == 2
    retrieved_ids = [r.node_id for r in results]

    assert "rap_quantum" in retrieved_ids or "comm_quantum" in retrieved_ids
    assert "rap_gardening" not in retrieved_ids

    # Check top score calculation aligns with 1 / (60 + rank)
    top_result = results[0]
    assert top_result.score >= 1.0 / 61.0


def test_bulk_ingest_objects_and_dicts():
    """Verify index_raptor_nodes and index_graphrag_data accept lists of dicts or objects."""
    retriever = HybridStructuredRetriever()

    raptor_nodes = [
        {
            "id": "r_node_10",
            "level": 3,
            "text": "Tree root summary of agent memory systems.",
            "summary": "Agent memory hierarchy overview.",
        }
    ]

    graph_entities = [
        {
            "id": "entity_agent",
            "name": "Autonomous Agent",
            "type": "CONCEPT",
            "description": "An entity that perceives its environment and takes actions.",
        }
    ]

    graph_relations = [
        {
            "id": "rel_mem",
            "source": "Autonomous Agent",
            "target": "Memory Store",
            "type": "HAS_COMPONENT",
            "description": "Agents rely on structured memory stores.",
        }
    ]

    retriever.index_raptor_nodes(raptor_nodes)
    retriever.index_graphrag_data(entities=graph_entities, relationships=graph_relations)

    results = retriever.retrieve("agent memory", top_k=3)
    assert len(results) == 3


def test_empty_query_and_edge_cases():
    """Verify empty queries return empty results and custom top_k bounds are respected."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node("1", 0, "Test content", "Test summary")

    assert retriever.retrieve("") == []
    assert retriever.retrieve("   ") == []

    res = retriever.retrieve("Test", top_k=1)
    assert len(res) <= 1
def test_relationship_target_matching():
    """Verify GraphRAG relationships match queries matching the target entity name."""
    retriever = HybridStructuredRetriever()
    retriever.add_graphrag_relationship(
        relation_id="rel_target",
        source="TransformerModel",
        target="AttentionMechanism",
        type="USES",
        description="Transformer models rely heavily on self-attention.",
    )

    results = retriever.retrieve("AttentionMechanism", top_k=1)
    assert len(results) == 1
    assert results[0].node_id == "rel_target"


def test_integer_ids_and_children_type_safety():
    """Verify integer children and entity_ids do not raise TypeError during citation building."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node(node_id="100", level=1, text="Text", children=[101, 102])
    retriever.add_graphrag_community(community_id="200", entity_ids=[201, 202], summary="Summary")

    results = retriever.retrieve("Text Summary", top_k=2)
    assert len(results) == 2
    for res in results:
        assert isinstance(res.citation.lineage[0], str)


def test_embedding_caching():
    """Verify embedding_fn output is cached on the node dictionary."""
    call_count = 0

    def mock_embed(text: str):
        nonlocal call_count
        call_count += 1
        return np.ones(8, dtype=np.float32)

    retriever = HybridStructuredRetriever(embedding_fn=mock_embed)
    retriever.add_raptor_node(node_id="embed_node", level=0, text="Embedding test text")

    # First retrieval computes embedding
    res1 = retriever.retrieve("Embedding test", top_k=1)
    first_calls = call_count
    assert first_calls > 0

    # Second retrieval reuses cached embedding without re-invoking embedding_fn for the node
    res2 = retriever.retrieve("Embedding test", top_k=1)
    assert call_count == first_calls + 1  # Only +1 for the query embedding


def test_precision_bounds_with_repeated_words():
    """Verify precision score is bounded <= 1.0 even when text contains repeated query terms."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node(
        node_id="rep_node",
        level=0,
        text="apple apple apple apple apple apple apple apple",
        summary="apple apple apple",
    )

    results = retriever.retrieve("apple", top_k=1)
    assert len(results) == 1
    assert results[0].score <= 1.0


def test_deterministic_rrf_ranking():
    """Verify RRF results order is 100% deterministic across multiple invocations."""
    retriever = HybridStructuredRetriever()
    for i in range(10):
        retriever.add_raptor_node(f"r_{i}", 0, f"Common topic text item {i}", f"Summary {i}")
        retriever.add_graphrag_entity(f"e_{i}", f"Entity {i}", "CONCEPT", f"Common topic text item {i}")

    res1 = [r.node_id for r in retriever.retrieve("Common topic text", top_k=5)]
    res2 = [r.node_id for r in retriever.retrieve("Common topic text", top_k=5)]
    assert res1 == res2
def test_index_raptor_nodes_id_zero():
    """Verify node ID 0 is not dropped during index_raptor_nodes."""
    retriever = HybridStructuredRetriever()
    retriever.index_raptor_nodes([{"id": 0, "text": "Zero ID text", "summary": "Zero ID summary"}])
    results = retriever.retrieve("Zero ID", top_k=1)
    assert len(results) == 1
    assert results[0].node_id == "0"


def test_negative_rrf_k_parameter():
    """Verify negative rrf_k override is safely clamped without division by zero."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node("node1", 0, "Quantum physics content", "Quantum physics summary")
    results = retriever.retrieve("Quantum physics", top_k=1, rrf_k=-1)
    assert len(results) == 1
    assert results[0].score > 0


def test_index_graphrag_data_none_id_fallback():
    """Verify items with explicit id=None fall back to entity_id/relation_id/community_id."""
    retriever = HybridStructuredRetriever()
    retriever.index_graphrag_data(
        entities=[{"id": None, "entity_id": "ent_1", "name": "Entity 1", "description": "GraphRAG entity test"}],
        relationships=[{"id": None, "relation_id": "rel_1", "source": "A", "target": "B", "description": "GraphRAG relation test"}],
        communities=[{"id": None, "community_id": "comm_1", "entity_ids": ["ent_1"], "summary": "GraphRAG community test"}],
    )
    res = retriever.retrieve("GraphRAG test", top_k=5)
    assert len(res) == 3


def test_top_k_zero():
    """Verify top_k=0 returns empty results list."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node("node1", 0, "Quantum physics content", "Quantum physics summary")
    results = retriever.retrieve("Quantum physics", top_k=0)
    assert results == []

def test_orthogonal_vector_scoring():
    """Verify semantic_score is 0.0 (not replaced by coverage) when orthogonal vector embedding is evaluated."""
    embedding_fn = lambda text: np.array([0.0, 1.0]) if text == "query" else np.array([1.0, 0.0])
    retriever = HybridStructuredRetriever(embedding_fn=embedding_fn)
    retriever.add_raptor_node("node1", 0, "query term content", "query term summary")
    results = retriever.retrieve("query", top_k=1)
    assert len(results) == 1
    # Semantic score should be 0.0 for orthogonal vector
    raw_score, lex_sc, sem_sc = retriever._compute_scores("query", {"query"}, np.array([0.0, 1.0]), retriever.unified_nodes["raptor_node1"])
    assert sem_sc == 0.0


def test_vector_dimension_mismatch_fallback():
    """Verify dimension mismatch during vector comparison safely falls back to coverage score."""
    embedding_fn = lambda text: np.array([1.0, 0.0, 0.0])  # 3D query vector
    retriever = HybridStructuredRetriever(embedding_fn=embedding_fn)
    # Node contains 2D embedding vector
    retriever.add_raptor_node("node1", 0, "query term content", "query term summary", embedding=np.array([1.0, 0.0]))
    results = retriever.retrieve("query", top_k=1)
    assert len(results) == 1
    # Should fall back to lexical / coverage scoring without crashing
    assert results[0].score > 0


def test_results_merged_by_score_not_source():
    """Verify results are ranked by score, not interleaved by source type (Finding 1)."""
    retriever = HybridStructuredRetriever()
    # Two RAPTOR nodes with strong lexical match
    retriever.add_raptor_node("rap_a", 0, "alpha beta gamma", "alpha beta gamma summary")
    retriever.add_raptor_node("rap_b", 0, "alpha beta delta", "alpha beta delta summary")
    # One GraphRAG entity with weaker match
    retriever.add_graphrag_entity("ent_weak", "alpha", "CONCEPT", "alpha description")

    results = retriever.retrieve("alpha beta gamma", top_k=3)
    # Top two results should both be RAPTOR nodes (higher lexical match), not interleaved
    assert results[0].source_type == "raptor_tree"
    assert results[1].source_type == "raptor_tree"
    # Scores must be in descending order
    assert results[0].score >= results[1].score >= results[2].score


def test_negative_vector_similarity_clamped_to_zero():
    """Verify negative cosine similarity is clamped to 0, not ranked above positive text relevance (Finding 10)."""
    # Embedding that produces negative cosine similarity for node text (no "query" in it)
    def mock_embed(text: str) -> np.ndarray:
        if "query" in text.lower():
            return np.array([1.0, 0.0])
        return np.array([-1.0, 0.0])  # Opposite direction → cos_sim = -1.0

    retriever = HybridStructuredRetriever(embedding_fn=mock_embed)
    # Node text must NOT contain "query" so mock_embed returns the opposite vector
    retriever.add_raptor_node("neg_node", 0, "term content", "term summary")

    _, _, sem_sc = retriever._compute_scores(
        "query term", {"query", "term"}, np.array([1.0, 0.0]), retriever.unified_nodes["raptor_neg_node"]
    )
    # Semantic score must be clamped to 0.0, not negative
    assert sem_sc == 0.0
    assert sem_sc >= 0.0


def test_mixed_vector_presence_consistent_scoring():
    """Verify nodes with and without vectors are scored on a consistent scale (Finding 11)."""
    def mock_embed(text: str) -> np.ndarray:
        if "fail" in text.lower():
            raise ValueError("cannot embed")
        return np.array([1.0, 0.0])

    retriever = HybridStructuredRetriever(embedding_fn=mock_embed)
    # Node A: has a pre-computed embedding aligned with query vector
    retriever.add_raptor_node(
        "node_a", 0, "common topic text", "common topic text",
        embedding=np.array([1.0, 0.0]),
    )
    # Node B: no pre-computed embedding; embedding_fn raises → falls back to lexical-only
    retriever.add_raptor_node(
        "node_b", 0, "fail common topic text", "fail common topic text",
    )

    results = retriever.retrieve("common topic", top_k=2)
    assert len(results) == 2
    # Both nodes should have positive scores (lexical match exists for both)
    for res in results:
        assert res.score > 0
    # Node A (has vector, aligned) should rank higher than Node B (no vector, lexical-only fallback)
    assert results[0].node_id == "node_a"


def test_parent_id_zero_preserved_in_citation():
    """Verify parent ID 0 is not dropped from citation lineage (Finding 12)."""
    retriever = HybridStructuredRetriever()
    retriever.add_raptor_node(
        node_id="child_1",
        level=1,
        text="Child node content",
        summary="Child node summary",
        parent=0,
    )

    results = retriever.retrieve("Child node", top_k=1)
    assert len(results) == 1
    citation = results[0].citation
    # Parent ID 0 must appear in lineage, not be dropped by truthiness check
    parent_entries = [lin for lin in citation.lineage if lin.startswith("Parent:")]
    assert len(parent_entries) == 1
    assert "0" in parent_entries[0]
