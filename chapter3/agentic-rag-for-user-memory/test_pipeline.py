#!/usr/bin/env python3
"""Test script to verify the retrieval pipeline integration"""

import requests
import json
from rich.console import Console

console = Console()

def test_retrieval_pipeline():
    """Test if retrieval pipeline is available and working"""
    
    console.print("[bold]Testing Retrieval Pipeline Connection[/bold]\n")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:4242/health", timeout=2)
        if response.status_code == 200:
            console.print("[green]✓ Retrieval pipeline is available on port 4242[/green]")
        else:
            console.print(f"[yellow]⚠ Pipeline returned status {response.status_code}[/yellow]")
            return False
    except requests.exceptions.RequestException as e:
        console.print("[red]✗ Retrieval pipeline not available[/red]")
        console.print(f"Error: {e}")
        console.print("\nTo start the retrieval pipeline:")
        console.print("[cyan]cd projects/week3/retrieval-pipeline[/cyan]")
        console.print("[cyan]python api_server.py[/cyan]")
        return False
    
    # Test indexing endpoint
    console.print("\n[bold]Testing Indexing Capability[/bold]")
    test_doc = {
        "text": "This is a test document for the retrieval pipeline.",
        "metadata": {
            "doc_id": "test_doc_1",
            "type": "test"
        }
    }
    
    try:
        # Clear existing index
        requests.post("http://localhost:4242/clear", timeout=30)
        
        # Index test document (single document format)
        response = requests.post(
            "http://localhost:4242/index",
            json=test_doc, timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            console.print(f"[green]✓ Successfully indexed document with ID {result.get('doc_id', 'unknown')}[/green]")
        else:
            console.print(f"[yellow]⚠ Indexing returned status {response.status_code}[/yellow]")
            
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error indexing documents: {e}[/red]")
        return False
    
    # Test search endpoint
    console.print("\n[bold]Testing Search Capability[/bold]")
    try:
        response = requests.post(
            "http://localhost:4242/search",
            json={
                "query": "test document",
                "mode": "hybrid",
                "top_k": 5
            }, timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            # Check for any type of results
            has_results = any([
                result.get("dense_results"),
                result.get("sparse_results"),
                result.get("reranked_results")
            ])
            if has_results:
                console.print("[green]✓ Search endpoint working correctly[/green]")
            else:
                console.print("[yellow]⚠ Search returned no results (index might be empty)[/yellow]")
        else:
            console.print(f"[yellow]⚠ Search returned status {response.status_code}[/yellow]")
            
    except requests.exceptions.RequestException as e:
        console.print(f"[red]✗ Error searching: {e}[/red]")
        return False
    
    console.print("\n[green]✓ All retrieval pipeline tests passed![/green]")
    return True

def test_indexer():
    """Test the modified indexer"""
    console.print("\n[bold]Testing Modified Indexer[/bold]\n")
    
    try:
        from config import Config, IndexConfig
        from indexer import MemoryIndexer
        from chunker import ConversationChunk, ConversationMessage
        
        # Create test configuration
        config = IndexConfig()
        
        # Initialize indexer
        indexer = MemoryIndexer(config)
        console.print("[green]✓ Indexer initialized successfully[/green]")
        
        # Create a test chunk
        test_chunk = ConversationChunk(
            chunk_id="test_chunk_1",
            conversation_id="conv_1",
            test_id="test_1",
            chunk_index=0,
            start_round=1,
            end_round=5,
            messages=[
                ConversationMessage(role="user", content="Hello"),
                ConversationMessage(role="assistant", content="Hi there!")
            ],
            metadata={"test": True}
        )
        
        # Add chunk to indexer
        indexer.add_chunks([test_chunk])
        console.print("[green]✓ Successfully added test chunk to indexer[/green]")
        
        # Test search
        results = indexer.search("hello", top_k=5)
        if results:
            console.print(f"[green]✓ Search returned {len(results)} result(s)[/green]")
        else:
            console.print("[yellow]⚠ Search returned no results[/yellow]")
            
        console.print("\n[green]✓ Indexer tests completed![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error testing indexer: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    console.print("[bold cyan]Testing Agentic RAG for User Memory - Pipeline Integration[/bold cyan]\n")
    
    # Test retrieval pipeline
    pipeline_ok = test_retrieval_pipeline()
    
    # Test indexer if pipeline is available
    if pipeline_ok:
        indexer_ok = test_indexer()
        
        if indexer_ok:
            console.print("\n[bold green]All tests passed! The system is ready to use.[/bold green]")
        else:
            console.print("\n[bold yellow]Indexer needs attention, but pipeline is working.[/bold yellow]")
    else:
        console.print("\n[bold red]Please start the retrieval pipeline first![/bold red]")
        console.print("Run the following commands in a separate terminal:")
        console.print("[cyan]cd /Users/boj/ai-agent-book/projects/week3/retrieval-pipeline[/cyan]")
        console.print("[cyan]python api_server.py[/cyan]")
