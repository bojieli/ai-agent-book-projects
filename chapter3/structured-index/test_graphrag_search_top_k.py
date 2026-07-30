"""Regression test: GraphRAGIndexer.search must return empty list for non-positive top_k."""
import importlib
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np

import pytest


class STStub:
    def __init__(self, *args, **kwargs):
        self.encode_calls = 0

    def encode(self, texts, **kwargs):
        self.encode_calls += 1
        return np.array([[0.1, 0.2, 0.3]])


@dataclass
class GraphRAGConfig:
    llm_api_key: str = "test"
    base_url: str = "test"
    llm_model: str = "test"


_MISSING = object()
_STUBBED_MODULES = (
    "openai",
    "sentence_transformers",
    "pandas",
    "sklearn",
    "sklearn.metrics",
    "sklearn.metrics.pairwise",
    "loguru",
    "tqdm",
    "config",
    "networkx",
)


class GraphStub:
    def __init__(self):
        self._neighbors = {}

    def add_node(self, node):
        self._neighbors.setdefault(node, set())

    def __contains__(self, node):
        return node in self._neighbors

    def neighbors(self, node):
        return iter(self._neighbors[node])


@contextmanager
def _isolated_graphrag_module():
    modules = {name: types.ModuleType(name) for name in _STUBBED_MODULES}
    modules["openai"].OpenAI = object
    modules["sentence_transformers"].SentenceTransformer = STStub
    modules["sklearn"].__path__ = []
    modules["sklearn"].metrics = modules["sklearn.metrics"]
    modules["sklearn.metrics"].__path__ = []
    modules["sklearn.metrics"].pairwise = modules["sklearn.metrics.pairwise"]
    modules["sklearn.metrics.pairwise"].cosine_similarity = (
        lambda a, b: np.array([[0.95]])
    )
    modules["loguru"].logger = types.SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    modules["tqdm"].tqdm = lambda x, **k: x
    modules["config"].GraphRAGConfig = GraphRAGConfig
    modules["networkx"].Graph = GraphStub

    previous_module = sys.modules.pop("graphrag_indexer", _MISSING)
    try:
        with pytest.MonkeyPatch.context() as monkeypatch:
            for name, module in modules.items():
                monkeypatch.setitem(sys.modules, name, module)
            yield importlib.import_module("graphrag_indexer")
    finally:
        sys.modules.pop("graphrag_indexer", None)
        if previous_module is not _MISSING:
            sys.modules["graphrag_indexer"] = previous_module


@pytest.fixture
def graphrag_module():
    with _isolated_graphrag_module() as module:
        yield module


def _make_indexer(graphrag_module):
    indexer = graphrag_module.GraphRAGIndexer.__new__(
        graphrag_module.GraphRAGIndexer
    )
    indexer.config = graphrag_module.GraphRAGConfig()
    indexer.embedding_model = graphrag_module.SentenceTransformer()
    indexer.entities = {
        "e1": graphrag_module.Entity(
            "e1",
            "intel x86",
            "instruction",
            "intel x86 instruction",
            np.array([0.1, 0.2, 0.3]),
            {},
        ),
        "e2": graphrag_module.Entity(
            "e2",
            "registers",
            "register",
            "intel registers",
            np.array([0.1, 0.2, 0.3]),
            {},
        ),
        "e3": graphrag_module.Entity(
            "e3",
            "cpu flags",
            "feature",
            "cpu status flags",
            np.array([0.1, 0.2, 0.3]),
            {},
        ),
    }
    indexer.communities = {}
    indexer.graph = graphrag_module.nx.Graph()
    for entity_id in indexer.entities:
        indexer.graph.add_node(entity_id)
    return indexer


def test_search_nonpositive_top_k_returns_empty(graphrag_module):
    """Non-positive result limits return before query encoding."""
    indexer = _make_indexer(graphrag_module)
    assert indexer.search("intel", top_k=0) == []
    assert indexer.search("intel", top_k=-1) == []
    assert indexer.search("intel", top_k=-5) == []
    assert indexer.embedding_model.encode_calls == 0


def test_search_positive_top_k_returns_results(graphrag_module):
    """Positive result limits still run retrieval and cap the results."""
    indexer = _make_indexer(graphrag_module)
    results = indexer.search("intel", top_k=2)
    assert len(results) == 2
    assert results[0]["id"] in ("e1", "e2", "e3")
    assert results[1]["id"] in ("e1", "e2", "e3")


def test_dependency_stubs_are_restored():
    """Scoped dependency replacements leave neighboring collection unchanged."""
    tracked_modules = (*_STUBBED_MODULES, "graphrag_indexer")
    before = {
        name: sys.modules.get(name, _MISSING)
        for name in tracked_modules
    }

    with _isolated_graphrag_module() as module:
        assert sys.modules["graphrag_indexer"] is module
        for name in _STUBBED_MODULES:
            assert sys.modules[name] is not before[name]

    for name, previous_module in before.items():
        assert sys.modules.get(name, _MISSING) is previous_module
