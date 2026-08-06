"""Regression test for SemanticRouter initialization with empty servers list."""
import sys
from pathlib import Path

# Add active-tool-selection to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "chapter4" / "active-tool-selection"))

from semantic_router import SemanticRouter


def test_semantic_router_empty_servers():
    router = SemanticRouter([])
    assert router.servers == []
    assert router.route_request("find a tool") == []
    assert router.retrieve("find a tool", top_k=5) == []
    
    details = router.get_routing_details("find a tool")
    assert details["final_tools"] == []
    assert details["stage1_servers"] == []
    assert details["stage2_tools"] == {}
