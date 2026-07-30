"""
Test script for Agentic RAG with structured index backends (RAPTOR and GraphRAG).
"""

import asyncio
import logging
import os
import pytest
from config import Config, KnowledgeBaseType
from agent import AgenticRAG

# These are manual end-to-end checks for separately launched RAPTOR/GraphRAG
# services, not hermetic unit tests.  Keep direct-script behavior intact while
# making the dependency explicit during normal pytest runs.
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_STRUCTURED_BACKEND_INTEGRATION") != "1",
    reason="set RUN_STRUCTURED_BACKEND_INTEGRATION=1 with port 4242 services running",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_raptor_backend():
    """Test Agentic RAG with RAPTOR tree-based backend"""
    print("\n" + "="*60)
    print("Testing RAPTOR Tree-Based Backend")
    print("="*60)
    
    # Configure for RAPTOR
    config = Config.from_env()
    config.knowledge_base.type = KnowledgeBaseType.RAPTOR
    config.knowledge_base.raptor_base_url = "http://localhost:4242"
    config.knowledge_base.raptor_top_k = 5
    config.llm.provider = "kimi"  # Use your preferred provider
    
    # Initialize agent
    agent = AgenticRAG(config)
    
    # Test queries
    test_queries = [
        "What are the x86 general-purpose registers?",
        "How does the MOV instruction work in Intel architecture?",
        "Explain SIMD instructions and their purpose",
        "What are control registers CR0-CR4 used for?",
        "How do I use SSE instructions for parallel processing?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        # Agentic mode (with tools)
        response = agent.query(query, stream=False)
        print(f"Response: {response[:500]}..." if len(response) > 500 else f"Response: {response}")
        
        # Clear history for next query
        agent.clear_history()


def test_graphrag_backend():
    """Test Agentic RAG with GraphRAG knowledge graph backend"""
    print("\n" + "="*60)
    print("Testing GraphRAG Knowledge Graph Backend")
    print("="*60)
    
    # Configure for GraphRAG
    config = Config.from_env()
    config.knowledge_base.type = KnowledgeBaseType.GRAPHRAG
    config.knowledge_base.graphrag_base_url = "http://localhost:4242"
    config.knowledge_base.graphrag_top_k = 5
    config.knowledge_base.graphrag_search_type = "hybrid"
    config.llm.provider = "kimi"  # Use your preferred provider
    
    # Initialize agent
    agent = AgenticRAG(config)
    
    # Test queries
    test_queries = [
        "What instructions modify the FLAGS register?",
        "Show me the relationship between MOV and LEA instructions",
        "What CPU features are related to virtualization?",
        "How are SSE and AVX instructions related?",
        "What components make up the execution environment?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        # Agentic mode (with tools)
        response = agent.query(query, stream=False)
        print(f"Response: {response[:500]}..." if len(response) > 500 else f"Response: {response}")
        
        # Clear history for next query
        agent.clear_history()


def compare_backends():
    """Compare results from different backends for the same query"""
    print("\n" + "="*60)
    print("Comparing Different Backend Results")
    print("="*60)
    
    query = "Explain the Intel x86 instruction format and its components"
    
    backends = [
        (KnowledgeBaseType.RAPTOR, "RAPTOR Tree-Based", "http://localhost:4242"),
        (KnowledgeBaseType.GRAPHRAG, "GraphRAG Knowledge Graph", "http://localhost:4242")
    ]
    
    results = {}
    
    for backend_type, backend_name, base_url in backends:
        print(f"\n{backend_name}:")
        print("-" * 40)
        
        # Configure for backend
        config = Config.from_env()
        config.knowledge_base.type = backend_type
        
        if backend_type == KnowledgeBaseType.RAPTOR:
            config.knowledge_base.raptor_base_url = base_url
        elif backend_type == KnowledgeBaseType.GRAPHRAG:
            config.knowledge_base.graphrag_base_url = base_url
            config.knowledge_base.graphrag_search_type = "hybrid"
        
        config.llm.provider = "kimi"
        
        # Initialize agent
        agent = AgenticRAG(config)
        
        # Query and store result
        response = agent.query(query, stream=False)
        results[backend_name] = response
        
        print(f"Response preview: {response[:300]}...")
    
    # Compare results
    print("\n" + "="*60)
    print("Comparison Summary")
    print("="*60)
    
    for backend_name, response in results.items():
        print(f"\n{backend_name}:")
        print(f"  Response length: {len(response)} characters")
        print(f"  Citations found: {'[Doc:' in response or '[Chunk:' in response}")
        
        # Count tool calls (approximate)
        tool_indicators = ["knowledge_base_search", "get_document"]
        tool_count = sum(1 for indicator in tool_indicators if indicator in str(response))
        print(f"  Estimated tool calls: {tool_count}")


def test_non_agentic_mode():
    """Test non-agentic mode with structured backends"""
    print("\n" + "="*60)
    print("Testing Non-Agentic Mode with Structured Backends")
    print("="*60)
    
    query = "What are the different types of Intel CPU registers?"
    
    # Test with RAPTOR
    print("\nRAPTOR (Non-Agentic):")
    config = Config.from_env()
    config.knowledge_base.type = KnowledgeBaseType.RAPTOR
    config.knowledge_base.raptor_base_url = "http://localhost:4242"
    
    agent = AgenticRAG(config)
    response = agent.query_non_agentic(query, stream=False)
    print(f"Response: {response[:400]}...")
    
    # Test with GraphRAG
    print("\nGraphRAG (Non-Agentic):")
    config.knowledge_base.type = KnowledgeBaseType.GRAPHRAG
    config.knowledge_base.graphrag_base_url = "http://localhost:4242"
    
    agent = AgenticRAG(config)
    response = agent.query_non_agentic(query, stream=False)
    print(f"Response: {response[:400]}...")


def main():
    """Run all tests"""
    print("Agentic RAG with Structured Index Backends Test Suite")
    print("=" * 60)
    
    # Make sure the structured-index API is running on port 4242
    print("\nNote: Make sure the structured-index API is running on port 4242")
    print("Run: cd ../structured-index && python main.py serve")
    
    input("\nPress Enter to start tests...")
    
    try:
        # Run tests
        test_raptor_backend()
        test_graphrag_backend()
        compare_backends()
        test_non_agentic_mode()
        
        print("\n" + "="*60)
        print("All tests completed successfully!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print("\nMake sure:")
        print("1. The structured-index API is running (python main.py serve)")
        print("2. Indexes have been built (python main.py build <document>)")
        print("3. Your API keys are configured in .env")


if __name__ == "__main__":
    main()
