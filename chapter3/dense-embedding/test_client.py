"""Test client for the vector similarity search service."""

import requests
import json
import time
from typing import List, Dict, Any


class VectorSearchClient:
    """Client for testing the vector search service."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client."""
        self.base_url = base_url
    
    def index_document(self, text: str, doc_id: str = None, metadata: Dict = None) -> Dict:
        """Index a document."""
        response = requests.post(
            f"{self.base_url}/index",
            json={
                "text": text,
                "doc_id": doc_id,
                "metadata": metadata or {}
            }, timeout=30
        )
        return response.json()
    
    def search(self, query: str, top_k: int = 5, return_documents: bool = True) -> Dict:
        """Search for similar documents."""
        response = requests.post(
            f"{self.base_url}/search",
            json={
                "query": query,
                "top_k": top_k,
                "return_documents": return_documents
            }, timeout=30
        )
        return response.json()
    
    def delete_document(self, doc_id: str) -> Dict:
        """Delete a document."""
        response = requests.delete(
            f"{self.base_url}/index",
            json={"doc_id": doc_id}, timeout=30
        )
        return response.json()
    
    def get_stats(self) -> Dict:
        """Get service statistics."""
        response = requests.get(f"{self.base_url}/stats", timeout=30)
        return response.json()
    
    def list_documents(self, limit: int = 10) -> List[Dict]:
        """List documents in the store."""
        response = requests.get(f"{self.base_url}/documents", params={"limit": limit}, timeout=30)
        return response.json()


def run_demo():
    """Run a comprehensive demo of the vector search service."""
    print("=" * 80)
    print("🚀 Vector Similarity Search Service - Demo Client")
    print("=" * 80)
    
    # Initialize client
    client = VectorSearchClient()
    
    # Check service status
    print("\n📊 Checking service status...")
    try:
        response = requests.get("http://localhost:8000/", timeout=30)
        status = response.json()
        print(f"✅ Service is running")
        print(f"   - Index type: {status['index_type']}")
        print(f"   - Model: {status['model']}")
    except Exception as e:
        print(f"❌ Service is not running: {e}")
        print("Please start the service first with: python main.py")
        return
    
    # Sample documents
    documents = [
        {
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "metadata": {"category": "AI", "topic": "machine_learning"}
        },
        {
            "text": "Deep learning is a type of machine learning based on artificial neural networks with multiple layers that progressively extract higher-level features from raw input.",
            "metadata": {"category": "AI", "topic": "deep_learning"}
        },
        {
            "text": "Natural language processing (NLP) is a branch of AI that helps computers understand, interpret and manipulate human language.",
            "metadata": {"category": "AI", "topic": "nlp"}
        },
        {
            "text": "Computer vision enables machines to interpret and understand visual information from the world, similar to how humans use their eyes and brains.",
            "metadata": {"category": "AI", "topic": "computer_vision"}
        },
        {
            "text": "Reinforcement learning is an area of machine learning where an agent learns to make decisions by taking actions in an environment to maximize cumulative reward.",
            "metadata": {"category": "AI", "topic": "reinforcement_learning"}
        },
        {
            "text": "Python is a high-level programming language known for its simplicity and readability, widely used in data science and web development.",
            "metadata": {"category": "Programming", "topic": "python"}
        },
        {
            "text": "JavaScript is a versatile programming language primarily used for creating interactive web applications and running code in browsers.",
            "metadata": {"category": "Programming", "topic": "javascript"}
        },
        {
            "text": "Docker is a platform that uses containerization to package applications with their dependencies, ensuring consistency across different environments.",
            "metadata": {"category": "DevOps", "topic": "containerization"}
        },
        {
            "text": "Kubernetes is an open-source container orchestration platform that automates the deployment, scaling, and management of containerized applications.",
            "metadata": {"category": "DevOps", "topic": "orchestration"}
        },
        {
            "text": "The transformer architecture revolutionized NLP by introducing self-attention mechanisms that process sequences in parallel rather than sequentially.",
            "metadata": {"category": "AI", "topic": "transformers"}
        }
    ]
    
    # Index documents
    print("\n📝 Indexing documents...")
    doc_ids = []
    for i, doc in enumerate(documents, 1):
        print(f"  [{i}/{len(documents)}] Indexing: {doc['text'][:50]}...")
        result = client.index_document(
            text=doc["text"],
            metadata=doc["metadata"]
        )
        doc_ids.append(result["doc_id"])
        time.sleep(0.1)  # Small delay for demonstration
    
    print(f"\n✅ Indexed {len(documents)} documents")
    
    # Show statistics
    print("\n📊 Current statistics:")
    stats = client.get_stats()
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    # Perform searches
    queries = [
        "What is deep learning and neural networks?",
        "How to deploy applications with containers?",
        "Programming languages for web development",
        "Learning from environment and rewards",
        "Understanding human language with computers"
    ]
    
    print("\n🔍 Performing searches...")
    for query in queries:
        print(f"\n  Query: '{query}'")
        print("  " + "-" * 60)
        
        result = client.search(query, top_k=3)
        
        if result["success"]:
            print(f"  Found {result['total_results']} results in {result['search_time_ms']:.2f}ms:")
            for res in result["results"]:
                print(f"\n  Rank {res['rank']}: (Score: {res['score']:.4f})")
                print(f"    Text: {res['text'][:100]}...")
                if res.get("metadata"):
                    print(f"    Metadata: {res['metadata']}")
        else:
            print(f"  ❌ Search failed")
        
        time.sleep(0.5)  # Delay for readability
    
    # Test deletion
    print("\n🗑️  Testing document deletion...")
    if doc_ids:
        doc_to_delete = doc_ids[0]
        print(f"  Deleting document: {doc_to_delete}")
        delete_result = client.delete_document(doc_to_delete)
        print(f"  Result: {delete_result['message']}")
        print(f"  New index size: {delete_result['index_size']}")
    
    # List remaining documents
    print("\n📋 Listing documents (first 5)...")
    docs = client.list_documents(limit=5)
    for i, doc in enumerate(docs, 1):
        print(f"  {i}. ID: {doc['id'][:8]}... | Text: {doc['text'][:50]}...")
    
    print("\n" + "=" * 80)
    print("✅ Demo completed successfully!")
    print("=" * 80)


def run_performance_test():
    """Run a performance test."""
    print("\n" + "=" * 80)
    print("⚡ Performance Test")
    print("=" * 80)
    
    client = VectorSearchClient()
    
    # Generate test documents
    num_docs = 100
    print(f"\n📝 Indexing {num_docs} documents for performance testing...")
    
    start_time = time.time()
    for i in range(num_docs):
        text = f"This is test document number {i}. It contains various information about topic {i % 10}. " \
               f"The content is randomly generated for testing purposes. Keywords: test, document, {i}, performance."
        client.index_document(text)
        
        if (i + 1) % 20 == 0:
            print(f"  Indexed {i + 1}/{num_docs} documents...")
    
    index_time = time.time() - start_time
    print(f"\n✅ Indexing completed in {index_time:.2f} seconds")
    print(f"   Average: {index_time/num_docs*1000:.2f}ms per document")
    
    # Test search performance
    print(f"\n🔍 Testing search performance with 20 queries...")
    search_times = []
    
    for i in range(20):
        query = f"Find information about topic {i % 10} and document testing"
        start_time = time.time()
        result = client.search(query, top_k=10, return_documents=False)
        search_time = time.time() - start_time
        search_times.append(search_time)
    
    avg_search_time = sum(search_times) / len(search_times)
    min_search_time = min(search_times)
    max_search_time = max(search_times)
    
    print(f"\n📊 Search Performance Results:")
    print(f"   - Average search time: {avg_search_time*1000:.2f}ms")
    print(f"   - Min search time: {min_search_time*1000:.2f}ms")
    print(f"   - Max search time: {max_search_time*1000:.2f}ms")
    
    # Final stats
    stats = client.get_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   - Total documents: {stats['document_count']}")
    print(f"   - Index size: {stats['index_size']}")
    print(f"   - Index type: {stats['index_type']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--performance":
        run_performance_test()
    else:
        run_demo()
