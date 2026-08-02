"""Contract tests for the Mem0 v3 companion helpers."""

from agent import MemoryClient, Mem0Agent, _extract_added_memories, _memory_filters


class FakeMemory:
    def __init__(self):
        self.calls = []

    def search(self, **kwargs):
        self.calls.append(("search", kwargs))
        return {"results": [{"id": "m1", "memory": "current fact"}]}

    def get_all(self, **kwargs):
        self.calls.append(("get_all", kwargs))
        return {"results": [{"id": "m1", "memory": "stored fact"}]}


class FakeMemoryClient(MemoryClient):
    def __init__(self):
        self.calls = []

    def get_all(self, **kwargs):
        self.calls.append(("get_all", kwargs))
        return {"results": [{"id": "m1", "memory": "cloud fact"}]}


def make_agent():
    agent = object.__new__(Mem0Agent)
    agent.memory = FakeMemory()
    return agent


def test_memory_filters_omit_empty_agent_id():
    assert _memory_filters("u1") == {"user_id": "u1"}
    assert _memory_filters("u1", "a1") == {"user_id": "u1", "agent_id": "a1"}


def test_search_uses_v3_filters_and_top_k():
    agent = make_agent()

    assert agent.search_memory("where", "u1", "a1", top_k=7)[0]["id"] == "m1"
    assert agent.memory.calls == [(
        "search",
        {
            "query": "where",
            "filters": {"user_id": "u1", "agent_id": "a1"},
            "top_k": 7,
        },
    )]


def test_get_all_uses_v3_filters_and_top_k():
    agent = make_agent()

    assert agent.get_all_memories("u1", top_k=42)[0]["id"] == "m1"
    assert agent.memory.calls == [(
        "get_all",
        {"filters": {"user_id": "u1"}, "top_k": 42},
    )]


def test_cloud_get_all_maps_top_k_to_page_size():
    agent = object.__new__(Mem0Agent)
    agent.memory = FakeMemoryClient()

    assert agent.get_all_memories("u1", top_k=42)[0]["id"] == "m1"
    assert agent.memory.calls == [(
        "get_all",
        {"filters": {"user_id": "u1"}, "page_size": 42},
    )]


def test_add_result_is_presented_as_added_memories_not_v2_decisions():
    result = {"results": [{"id": "m1", "memory": "new fact", "event": "ADD"}]}

    assert _extract_added_memories(result) == [
        {"id": "m1", "memory": "new fact"},
    ]
