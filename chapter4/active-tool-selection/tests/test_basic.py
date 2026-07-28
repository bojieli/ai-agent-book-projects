"""
Basic tests to verify the active tool selection system works correctly.
Run without API key to test core functionality.
"""

from tool_knowledge_base import create_tool_knowledge_base, calculate_total_tokens, get_all_tools
from semantic_router import SemanticRouter, StructuredRequestParser


def test_knowledge_base():
    """Test that knowledge base loads correctly."""
    print("Testing Knowledge Base...")
    
    servers = create_tool_knowledge_base()
    all_tools = get_all_tools(servers)
    
    assert len(servers) == 8, f"Expected 8 servers, got {len(servers)}"
    assert len(all_tools) > 30, f"Expected 30+ tools, got {len(all_tools)}"
    
    # Check each server has tools
    for server in servers:
        assert len(server.tools) > 0, f"Server {server.name} has no tools"
        assert server.description, f"Server {server.name} missing description"
    
    # Check tool schemas
    for tool in all_tools:
        schema = tool.to_schema()
        assert 'type' in schema, f"Tool {tool.name} missing type"
        assert 'function' in schema, f"Tool {tool.name} missing function"
    
    total_tokens = calculate_total_tokens(all_tools)
    print(f"   ✓ Loaded {len(servers)} servers with {len(all_tools)} tools")
    print(f"   ✓ Estimated tokens: {total_tokens:,}")
    print()


def test_semantic_router():
    """Test semantic routing functionality."""
    print("Testing Semantic Router...")
    
    servers = create_tool_knowledge_base()
    router = SemanticRouter(servers)
    
    # Test server routing with realistic queries
    test_queries = [
        ("search for GitHub repositories", ["github"]),
        ("read a file from filesystem", ["filesystem"]),
        ("query database for users", ["database"]),
        ("send an email notification", ["communication"]),
        ("deploy to production environment", ["devops"])
    ]
    
    for query, expected_servers in test_queries:
        tools = router.route_request(query, top_k_servers=3, top_k_tools=3)
        assert len(tools) > 0, f"No tools found for query: {query}"
        
        # Check that tools are from expected servers
        tool_servers = {tool.server for tool in tools}
        assert any(exp in tool_servers for exp in expected_servers), \
            f"Expected servers {expected_servers}, got {tool_servers} for query: {query}"
    
    print(f"   ✓ Semantic routing working correctly")
    print(f"   ✓ All test queries matched appropriate servers")
    print()


def test_structured_request_parser():
    """Test structured request parsing."""
    print("Testing Structured Request Parser...")
    
    # Valid request
    valid_request = """
Some text before
<tool_request>
server: GitHub for repository operations
tool: search repositories by keywords
</tool_request>
Some text after
"""
    
    parsed = StructuredRequestParser.parse_request(valid_request)
    assert parsed is not None, "Failed to parse valid request"
    assert 'server' in parsed, "Missing server in parsed request"
    assert 'tool' in parsed, "Missing tool in parsed request"
    assert "GitHub" in parsed['server'], "Server description incorrect"
    assert "search" in parsed['tool'], "Tool description incorrect"
    
    # Invalid request (missing tags)
    invalid_request = "Just some text without proper tags"
    parsed_invalid = StructuredRequestParser.parse_request(invalid_request)
    assert parsed_invalid is None, "Should return None for invalid request"
    
    # Test formatting
    formatted = StructuredRequestParser.format_request(
        "GitHub operations", 
        "search repositories"
    )
    assert "<tool_request>" in formatted, "Missing opening tag"
    assert "</tool_request>" in formatted, "Missing closing tag"
    assert "server:" in formatted, "Missing server field"
    assert "tool:" in formatted, "Missing tool field"
    
    print(f"   ✓ Request parsing working correctly")
    print(f"   ✓ Request formatting working correctly")
    print()


def test_routing_details():
    """Test detailed routing information."""
    print("Testing Routing Details...")
    
    servers = create_tool_knowledge_base()
    router = SemanticRouter(servers)
    
    query = "I need to search for Python repositories on GitHub"
    details = router.get_routing_details(query, top_k_servers=3, top_k_tools=3)
    
    assert 'request' in details, "Missing request in details"
    assert 'stage1_servers' in details, "Missing stage1 in details"
    assert 'stage2_tools' in details, "Missing stage2 in details"
    assert 'final_tools' in details, "Missing final_tools in details"
    
    assert len(details['stage1_servers']) > 0, "No servers in stage1"
    assert len(details['final_tools']) > 0, "No final tools"
    
    # Check structure
    for server in details['stage1_servers']:
        assert 'name' in server, "Server missing name"
        assert 'score' in server, "Server missing score"
        assert 0 <= server['score'] <= 1, "Server score out of range"
    
    for tool in details['final_tools']:
        assert 'name' in tool, "Tool missing name"
        assert 'server' in tool, "Tool missing server"
        assert 'score' in tool, "Tool missing score"
    
    print(f"   ✓ Routing details structure correct")
    print(f"   ✓ Stage 1: {len(details['stage1_servers'])} servers")
    print(f"   ✓ Stage 2: {len(details['final_tools'])} final tools")
    print()


def test_tool_schemas():
    """Test that tool schemas are properly formatted for OpenAI."""
    print("Testing Tool Schemas...")
    
    servers = create_tool_knowledge_base()
    all_tools = get_all_tools(servers)
    
    for tool in all_tools:
        schema = tool.to_schema()
        
        # Check OpenAI function calling format
        assert schema['type'] == 'function', f"Tool {tool.name} has wrong type"
        assert 'function' in schema, f"Tool {tool.name} missing function"
        
        func = schema['function']
        assert 'name' in func, f"Tool {tool.name} missing name"
        assert 'description' in func, f"Tool {tool.name} missing description"
        assert 'parameters' in func, f"Tool {tool.name} missing parameters"
        
        params = func['parameters']
        assert params['type'] == 'object', f"Tool {tool.name} parameters not object type"
        assert 'properties' in params, f"Tool {tool.name} missing properties"
    
    print(f"   ✓ All {len(all_tools)} tool schemas properly formatted")
    print(f"   ✓ Compatible with OpenAI function calling")
    print()


def run_all_tests():
    """Run all basic tests."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              Active Tool Selection - Basic Tests                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    try:
        test_knowledge_base()
        test_semantic_router()
        test_structured_request_parser()
        test_routing_details()
        test_tool_schemas()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("The active tool selection system is working correctly!")
        print()
        print("Next steps:")
        print("  1. Configure your API key in .env")
        print("  2. Run 'python quickstart.py' for a demonstration")
        print("  3. Run 'python demo_comparison.py' for comprehensive comparison")
        print()
        
    except AssertionError as e:
        print()
        print("=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        raise
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        raise


if __name__ == "__main__":
    run_all_tests()
