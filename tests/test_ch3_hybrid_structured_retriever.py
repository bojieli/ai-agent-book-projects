"""Unit tests for chapter3/structured-index/hybrid_retriever.py (HybridStructuredRetriever)."""

import importlib.util
import os
import sys
from pathlib import Path
import pytest

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
