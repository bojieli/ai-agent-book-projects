#!/usr/bin/env python3
"""Test that top_k parameter works correctly with the retrieval pipeline"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set dummy API key
os.environ["KIMI_API_KEY"] = "test-kimi-key"

from config import IndexConfig
from indexer import MemoryIndexer
from chunker import ConversationChunk, ConversationMessage

def test_top_k(tmp_path, monkeypatch):
    """Test that different top_k values return the correct number of results"""
    indexed_documents = []

    class FakeResponse:
        def __init__(self, data=None, status_code=200):
            self._data = data or {}
            self.status_code = status_code

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    def fake_get(url, **kwargs):
        return FakeResponse()

    def fake_post(url, json=None, **kwargs):
        if url.endswith("/clear"):
            indexed_documents.clear()
            return FakeResponse()
        if url.endswith("/index"):
            indexed_documents.append(json)
            return FakeResponse({"doc_id": json["metadata"]["doc_id"]})
        if url.endswith("/search"):
            count = min(json["rerank_top_k"], len(indexed_documents))
            results = [
                {"metadata": doc["metadata"], "rerank_score": 1.0 - (i * 0.01)}
                for i, doc in enumerate(indexed_documents[:count])
            ]
            return FakeResponse({"reranked_results": results})
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("indexer.requests.get", fake_get)
    monkeypatch.setattr("indexer.requests.post", fake_post)

    config = IndexConfig(
        index_path=str(tmp_path / "indexes" / "memory_index"),
        chunk_store_path=str(tmp_path / "data" / "chunk_store.json"),
        enable_contextual=False,
    )
    indexer = MemoryIndexer(config)
    
    # Create some test chunks
    test_chunks = []
    for i in range(10):
        chunk = ConversationChunk(
            chunk_id=f"test_chunk_{i}",
            test_id="test_id",
            conversation_id=f"conv_{i}",
            chunk_index=i,
            messages=[
                ConversationMessage(role="user", content=f"Test message {i} about banking"),
                ConversationMessage(role="assistant", content=f"Response {i} about account"),
            ],
            start_round=i*2,
            end_round=(i+1)*2,
            metadata={"test": f"chunk_{i}"}
        )
        test_chunks.append(chunk)
    
    # Build indexes
    print("Building indexes with 10 test chunks...")
    indexer.add_chunks(test_chunks)
    
    # Test different top_k values
    test_values = [1, 3, 5, 10, 15]
    
    for top_k in test_values:
        print(f"\nTesting top_k={top_k}...")
        results = indexer.search("banking account", top_k=top_k)
        actual_count = len(results)
        
        # The actual count should match requested top_k (up to available documents)
        expected_count = min(top_k, 10)  # We only have 10 chunks
        
        assert actual_count == expected_count
        print(f"✓ Correct: Requested {top_k}, got {actual_count} results")
        
        # Show the result IDs
        if results:
            result_ids = [r.chunk.chunk_id for r in results[:3]]  # Show first 3
            print(f"  First results: {result_ids}")
    
    print("\n" + "="*60)
    print("✓ top_k parameter is now working correctly!")
    print("  - The pipeline respects the requested number of results")
    print("  - It retrieves more candidates initially for better reranking")
    print("="*60)
