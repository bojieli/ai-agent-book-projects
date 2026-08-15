import pickle
from pathlib import Path
from unittest.mock import MagicMock


class FakeEncoder:
    def __init__(self, _model_name):
        self.encoded_queries = []

    def get_sentence_embedding_dimension(self):
        return 3

    def encode(self, queries):
        import numpy as np

        self.encoded_queries = list(queries)
        return np.zeros((len(queries), 3), dtype="float32")


class FakeIndex:
    def __init__(self, dimension, total=0):
        self.d = dimension
        self.ntotal = total

    def add(self, embeddings):
        self.ntotal += len(embeddings)


class FakeFaiss:
    def __init__(self, loaded_index=None):
        self.loaded_index = loaded_index

    def IndexFlatL2(self, dimension):
        return FakeIndex(dimension)

    def read_index(self, _path):
        return self.loaded_index

    def write_index(self, _index, path):
        Path(path).write_bytes(b"fake-faiss-index")


def test_kb_search_nonpositive_top_k():
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.documents = [{"question": "q1", "approach": "a1", "tools_used": None}]
    kb.encoder = MagicMock()
    kb.index = MagicMock()
    kb.index.ntotal = 5

    assert kb.search("query", top_k=0) == []
    assert kb.search("query", top_k=-1) == []
    kb.encoder.encode.assert_not_called()
    kb.index.search.assert_not_called()


def test_kb_keyword_search_null_tools_used():
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.documents = [{"question": "q1", "approach": "a1", "tools_used": None}]
    kb.encoder = None
    kb.index = None

    results = kb.search("q1", top_k=1)
    assert len(results) == 1
    assert results[0]["question"] == "q1"


def test_kb_keyword_search_scalar_tools_used():
    from knowledge_base import KnowledgeBase
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.documents = [{"question": "q1", "approach": "a1", "tools_used": 123}]
    kb.encoder = None
    kb.index = None

    results = kb.search("q1", top_k=1)
    assert len(results) == 1
    assert results[0]["question"] == "q1"


def test_kb_disables_encoder_when_faiss_is_missing(tmp_path, monkeypatch):
    import knowledge_base as knowledge_base_module

    class UnexpectedEncoder:
        def __init__(self, _model_name):
            raise AssertionError("encoder must not load without FAISS")

    monkeypatch.setattr(knowledge_base_module, "SentenceTransformer", UnexpectedEncoder)
    monkeypatch.setattr(knowledge_base_module, "faiss", None)

    kb = knowledge_base_module.KnowledgeBase(index_path=str(tmp_path))

    assert kb.encoder is None
    assert kb.index is None


def test_keyword_only_documents_survive_save_and_reload(tmp_path, monkeypatch):
    import knowledge_base as knowledge_base_module

    monkeypatch.setattr(knowledge_base_module, "SentenceTransformer", None)
    monkeypatch.setattr(knowledge_base_module, "faiss", None)

    first = knowledge_base_module.KnowledgeBase(index_path=str(tmp_path))
    first.add_experience(
        "persistent query",
        {
            "task_id": "task-1",
            "question": "persistent query",
            "approach": "keyword fallback",
            "tools_used": [],
        },
    )
    first._save_index()

    assert not (tmp_path / "faiss.index").exists()

    restored = knowledge_base_module.KnowledgeBase(index_path=str(tmp_path))

    assert restored.documents == first.documents
    assert restored.metadata == first.metadata
    assert restored.search("persistent", top_k=1) == first.documents

    fake_faiss = FakeFaiss()
    monkeypatch.setattr(knowledge_base_module, "SentenceTransformer", FakeEncoder)
    monkeypatch.setattr(knowledge_base_module, "faiss", fake_faiss)

    semantic_restore = knowledge_base_module.KnowledgeBase(index_path=str(tmp_path))

    assert semantic_restore.index.ntotal == 1
    assert semantic_restore.encoder.encoded_queries == ["persistent query"]


def test_stale_faiss_row_count_rebuilds_from_metadata(tmp_path, monkeypatch):
    import knowledge_base as knowledge_base_module

    documents = [
        {"question": "first", "tools_used": []},
        {"question": "second", "tools_used": []},
    ]
    metadata = [{"query": "first query"}, {"query": "second query"}]
    with (tmp_path / "documents.pkl").open("wb") as file:
        pickle.dump(documents, file)
    with (tmp_path / "metadata.pkl").open("wb") as file:
        pickle.dump(metadata, file)
    (tmp_path / "faiss.index").write_bytes(b"stale-faiss-index")

    fake_faiss = FakeFaiss(loaded_index=FakeIndex(dimension=3, total=1))
    monkeypatch.setattr(knowledge_base_module, "SentenceTransformer", FakeEncoder)
    monkeypatch.setattr(knowledge_base_module, "faiss", fake_faiss)

    restored = knowledge_base_module.KnowledgeBase(index_path=str(tmp_path))

    assert restored.index.ntotal == len(documents)
    assert restored.encoder.encoded_queries == ["first query", "second query"]
