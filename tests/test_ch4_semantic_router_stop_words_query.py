import sys
from pathlib import Path
import pytest

pytest.importorskip("numpy")
pytest.importorskip("sklearn")

# Add active-tool-selection to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "chapter4" / "active-tool-selection"))

from semantic_router import SemanticRouter
from tool_knowledge_base import ServerDefinition, ToolDefinition


def test_semantic_router_stop_words_query():
    tool1 = ToolDefinition("search_code", "search code in github repositories", {}, "github")
    tool2 = ToolDefinition("create_issue", "create a new issue", {}, "github")
    server = ServerDefinition("github", "repository platform", [tool1, tool2])

    router = SemanticRouter([server])

    # Query with only stop words
    stop_words_query = "the a an in on at for with"

    server_routes = router._route_to_servers(stop_words_query, top_k=5)
    assert len(server_routes) == 1
    assert server_routes[0][0] == server
    assert server_routes[0][1] == 0.0

    assert router._route_to_tools(server, stop_words_query, top_k=5) == []
    assert router.route_request(stop_words_query) == []
    assert router.retrieve(stop_words_query, top_k=5) == []

    details = router.get_routing_details(stop_words_query)
    assert details["final_tools"] == []
    assert details["stage2_tools"][server.name]["tools"] == []


def test_semantic_router_tool_only_query():
    tool1 = ToolDefinition("search_code", "search code in github repositories", {}, "github")
    tool2 = ToolDefinition("create_issue", "create a new issue", {}, "github")
    server = ServerDefinition("github", "repository platform", [tool1, tool2])

    router = SemanticRouter([server])

    # Word 'issue' is in tool description but not in server description ('repository platform')
    tools = router.route_request("create an issue")
    assert len(tools) == 1
    assert tools[0].name == "create_issue"


def test_semantic_router_tools_with_only_stop_words():
    tool = ToolDefinition("the", "a an in on at", {}, "stop_words_server")
    server = ServerDefinition("stop_words_server", "github search code", [tool])

    router = SemanticRouter([server])
    assert server._tool_embeddings is None
    assert router._route_to_tools(server, "search code", top_k=5) == []
