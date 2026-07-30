"""Regression test: GraphRAGIndexer.search must return empty list for non-positive top_k."""
import sys
import types
from dataclasses import dataclass
import numpy as np


def _stub_graphrag_deps():
    mods = [
        "openai",
        "sentence_transformers",
        "pandas",
        "sklearn",
        "sklearn.metrics",
        "sklearn.metrics.pairwise",
        "loguru",
        "tqdm",
        "config",
    ]
    for name in mods:
        sys.modules.setdefault(name, types.ModuleType(name))

    sys.modules["openai"].OpenAI = object
    sys.modules["sklearn.metrics.pairwise"].cosine_similarity = (
        lambda a, b: np.array([[0.95]])
    )

    class STStub:
        def __init__(self, *args, **kwargs):
            self.encode_calls = 0

        def encode(self, texts, **kwargs):
            self.encode_calls += 1
            return np.array([[0.1, 0.2, 0.3]])

    sys.modules["sentence_transformers"].SentenceTransformer = STStub
    sys.modules["loguru"].logger = types.SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    sys.modules["tqdm"].tqdm = lambda x, **k: x

    @dataclass
    class GraphRAGConfig:
        llm_api_key: str = "test"
        base_url: str = "test"
        llm_model: str = "test"

    sys.modules["config"].GraphRAGConfig = GraphRAGConfig


_stub_graphrag_deps()

from graphrag_indexer import Entity, GraphRAGIndexer  # noqa: E402
import networkx as nx  # noqa: E402


def _make_indexer():
    indexer = GraphRAGIndexer.__new__(GraphRAGIndexer)
    indexer.config = sys.modules["config"].GraphRAGConfig()
    indexer.embedding_model = sys.modules[
        "sentence_transformers"
    ].SentenceTransformer()
    indexer.entities = {
        "e1": Entity(
            "e1",
            "intel x86",
            "instruction",
            "intel x86 instruction",
            np.array([0.1, 0.2, 0.3]),
            {},
        ),
        "e2": Entity(
            "e2",
            "registers",
            "register",
            "intel registers",
            np.array([0.1, 0.2, 0.3]),
            {},
        ),
        "e3": Entity(
            "e3",
            "cpu flags",
            "feature",
            "cpu status flags",
            np.array([0.1, 0.2, 0.3]),
            {},
        ),
    }
    indexer.communities = {}
    indexer.graph = nx.Graph()
    for eid in indexer.entities:
        indexer.graph.add_node(eid)
    return indexer


def test_search_nonpositive_top_k_returns_empty():
    indexer = _make_indexer()
    assert indexer.search("intel", top_k=0) == []
    assert indexer.search("intel", top_k=-1) == []
    assert indexer.search("intel", top_k=-5) == []
    assert indexer.embedding_model.encode_calls == 0


def test_search_positive_top_k_returns_results():
    indexer = _make_indexer()
    results = indexer.search("intel", top_k=2)
    assert len(results) == 2
    assert results[0]["id"] in ("e1", "e2", "e3")
    assert results[1]["id"] in ("e1", "e2", "e3")
