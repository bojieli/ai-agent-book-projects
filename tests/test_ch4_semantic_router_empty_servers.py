import pytest
pytest.importorskip("numpy")
"""Regression test for SemanticRouter initialization with empty servers list."""
import sys
from pathlib import Path

# Add active-tool-selection to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "chapter4" / "active-tool-selection"))

from semantic_router import SemanticRouter


def test_semantic_router_empty_servers():
    router = SemanticRouter([])
    assert router.servers == []
    assert router.server_embeddings is None
    assert router.route_request("find a tool") == []
    assert router.retrieve("find a tool", top_k=5) == []
    assert router._route_to_servers("find a tool", top_k=5) == []
    
    details = router.get_routing_details("find a tool")
    assert details["final_tools"] == []
    assert details["stage1_servers"] == []
    assert details["stage2_tools"] == {}


def test_semantic_router_servers_with_only_stop_words():
    class MockServer:
        name = "the"
        description = "a an in on at"
        tools = []

    router = SemanticRouter([MockServer()])
    assert router.server_embeddings is None
    assert router.route_request("query") == []
    assert router.retrieve("query", top_k=3) == []
    assert router._route_to_servers("query", top_k=3) == []
