"""
Demo script for the Educational Sparse Vector Search Engine
Shows how to use the engine with sample documents and queries
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server URL
BASE_URL = "http://localhost:4241"


def wait_for_server(max_attempts=10):
    """Wait for server to be ready"""
    logger.info("Waiting for server to be ready...")
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/stats", timeout=30)
            if response.status_code == 200:
                logger.info("Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
    return False


def clear_index():
    """Clear the index before demo"""
    logger.info("Clearing existing index...")
    response = requests.delete(f"{BASE_URL}/index", timeout=30)
    if response.status_code == 200:
        logger.info("Index cleared successfully")
    return response.json()


def index_sample_documents():
    """Index a collection of sample documents"""
    logger.info("\n" + "="*50)
    logger.info("INDEXING SAMPLE DOCUMENTS")
    logger.info("="*50)
    
    sample_documents = [
        {
            "text": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            "metadata": {"title": "Python Programming", "category": "programming"}
        },
        {
            "text": "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It uses algorithms to identify patterns and make decisions.",
            "metadata": {"title": "Introduction to Machine Learning", "category": "AI"}
        },
        {
            "text": "Natural language processing (NLP) is a field of AI that focuses on the interaction between computers and human language. It involves tasks like text classification, sentiment analysis, and machine translation.",
            "metadata": {"title": "NLP Basics", "category": "AI"}
        },
        {
            "text": "Data structures are fundamental concepts in computer science that organize and store data efficiently. Common data structures include arrays, linked lists, trees, graphs, and hash tables.",
            "metadata": {"title": "Data Structures Overview", "category": "computer science"}
        },
        {
            "text": "JavaScript is a dynamic programming language commonly used for web development. It runs in browsers and on servers with Node.js, making it versatile for full-stack development.",
            "metadata": {"title": "JavaScript Essentials", "category": "programming"}
        },
        {
            "text": "Deep learning is a subset of machine learning that uses neural networks with multiple layers. It has achieved breakthrough results in computer vision, speech recognition, and natural language processing.",
            "metadata": {"title": "Deep Learning Introduction", "category": "AI"}
        },
        {
            "text": "Algorithms are step-by-step procedures for solving computational problems. Algorithm analysis involves studying their time and space complexity using Big O notation.",
            "metadata": {"title": "Algorithm Analysis", "category": "computer science"}
        },
        {
            "text": "Web development involves creating websites and web applications using technologies like HTML, CSS, JavaScript, and various frameworks. Modern web development often uses React, Vue, or Angular for frontend development.",
            "metadata": {"title": "Modern Web Development", "category": "web"}
        },
        {
            "text": "Databases are systems for storing and managing data. Relational databases use SQL and tables, while NoSQL databases offer flexible schemas for unstructured data. Popular choices include PostgreSQL, MongoDB, and Redis.",
            "metadata": {"title": "Database Systems", "category": "databases"}
        },
        {
            "text": "Cloud computing provides on-demand computing resources over the internet. Major providers like AWS, Google Cloud, and Azure offer services for storage, computation, and machine learning in the cloud.",
            "metadata": {"title": "Cloud Computing Basics", "category": "cloud"}
        }
    ]
    
    # Index documents
    doc_ids = []
    for i, doc in enumerate(sample_documents, 1):
        logger.info(f"\nIndexing document {i}/{len(sample_documents)}: {doc['metadata']['title']}")
        response = requests.post(
            f"{BASE_URL}/index",
            json={"text": doc["text"], "metadata": doc["metadata"]}, timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            doc_ids.append(result["doc_id"])
            logger.info(f"✓ Indexed with ID: {result['doc_id']}")
        else:
            logger.error(f"✗ Failed to index document")
    
    logger.info(f"\nSuccessfully indexed {len(doc_ids)} documents")
    return doc_ids


def show_statistics():
    """Display index statistics"""
    logger.info("\n" + "="*50)
    logger.info("INDEX STATISTICS")
    logger.info("="*50)
    
    response = requests.get(f"{BASE_URL}/stats", timeout=30)
    if response.status_code == 200:
        stats = response.json()
        logger.info(f"Total documents: {stats['total_documents']}")
        logger.info(f"Unique terms: {stats['unique_terms']}")
        logger.info(f"Total terms: {stats['total_terms']}")
        logger.info(f"Average document length: {stats['average_document_length']:.2f}")
        
        if 'terms_by_frequency' in stats:
            logger.info("\nTop 10 most frequent terms:")
            for term, freq in stats['terms_by_frequency']:
                logger.info(f"  - {term}: {freq} occurrences")
    
    return stats


def perform_searches():
    """Perform various search queries to demonstrate the engine"""
    logger.info("\n" + "="*50)
    logger.info("PERFORMING SEARCHES")
    logger.info("="*50)
    
    search_queries = [
        ("machine learning algorithms", 3),
        ("programming language", 5),
        ("database SQL", 3),
        ("web development JavaScript", 3),
        ("artificial intelligence", 5),
        ("data structures algorithms", 3),
        ("cloud computing AWS", 3),
        ("neural networks deep learning", 3)
    ]
    
    for query, top_k in search_queries:
        logger.info(f"\n{'─'*40}")
        logger.info(f"Query: '{query}' (top {top_k} results)")
        logger.info('─'*40)
        
        response = requests.post(
            f"{BASE_URL}/search",
            json={"query": query, "top_k": top_k}, timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            
            if not results:
                logger.info("No results found")
            else:
                for rank, result in enumerate(results, 1):
                    logger.info(f"\n  Rank {rank}:")
                    logger.info(f"    Score: {result['score']:.4f}")
                    logger.info(f"    Title: {result['metadata'].get('title', 'N/A')}")
                    logger.info(f"    Category: {result['metadata'].get('category', 'N/A')}")
                    logger.info(f"    Text preview: {result['text'][:100]}...")
                    logger.info(f"    Matched terms: {result['debug']['matched_terms']}")
                    logger.info(f"    Document length: {result['debug']['doc_length']} terms")
        else:
            logger.error(f"Search failed: {response.status_code}")
        
        time.sleep(0.5)  # Small delay between searches


def show_index_structure():
    """Display the internal structure of the index"""
    logger.info("\n" + "="*50)
    logger.info("INDEX STRUCTURE VISUALIZATION")
    logger.info("="*50)
    
    response = requests.get(f"{BASE_URL}/index/structure", timeout=30)
    if response.status_code == 200:
        data = response.json()
        
        # Show BM25 parameters
        logger.info("\nBM25 Parameters:")
        params = data['bm25_params']
        logger.info(f"  k1 (term frequency saturation): {params['k1']}")
        logger.info(f"  b (length normalization): {params['b']}")
        logger.info(f"  avgdl (average document length): {params['avgdl']:.2f}")
        
        # The actual structure is nested under 'structure' key
        structure = data.get('structure', {})
        
        # Show sample of inverted index
        logger.info("\nSample of Inverted Index (first 5 terms):")
        inv_index = structure.get('inverted_index', {})
        if inv_index:
            for i, (term, info) in enumerate(list(inv_index.items())[:5]):
                logger.info(f"  '{term}':")
                logger.info(f"    - Document frequency: {info['document_frequency']}")
                logger.info(f"    - Appears in documents: {info['document_ids']}")
        else:
            logger.info("  No inverted index data available")
        
        # Show document information
        logger.info("\nDocument Information:")
        doc_info = structure.get('document_info', {})
        if doc_info:
            for doc_id, info in list(doc_info.items())[:3]:  # Show first 3 documents
                logger.info(f"  Document {doc_id}:")
                logger.info(f"    - Length: {info['length']} terms")
                logger.info(f"    - Unique terms: {info['unique_terms']}")
                logger.info(f"    - Top terms: {[f'{term}({freq})' for term, freq in info['top_terms'][:5]]}")
        else:
            logger.info("  No document information available")
    
    return data


def test_specific_document_retrieval():
    """Test retrieving specific documents by ID"""
    logger.info("\n" + "="*50)
    logger.info("DOCUMENT RETRIEVAL TEST")
    logger.info("="*50)
    
    # Retrieve document with ID 0
    doc_id = 0
    logger.info(f"\nRetrieving document with ID {doc_id}...")
    
    response = requests.get(f"{BASE_URL}/document/{doc_id}", timeout=30)
    if response.status_code == 200:
        document = response.json()
        logger.info(f"Document {doc_id}:")
        logger.info(f"  Title: {document['metadata'].get('title', 'N/A')}")
        logger.info(f"  Category: {document['metadata'].get('category', 'N/A')}")
        logger.info(f"  Text: {document['text'][:150]}...")
    else:
        logger.error(f"Failed to retrieve document: {response.status_code}")


def main():
    """Run the complete demo"""
    logger.info("Starting Educational Sparse Vector Search Engine Demo")
    logger.info("Make sure the server is running (python server.py)")
    
    # Wait for server
    if not wait_for_server():
        logger.error("Server is not responding. Please start the server first.")
        return
    
    # Clear existing index
    clear_index()
    
    # Index sample documents
    doc_ids = index_sample_documents()
    
    # Show statistics
    show_statistics()
    
    # Show index structure
    show_index_structure()
    
    # Perform searches
    perform_searches()
    
    # Test document retrieval
    test_specific_document_retrieval()
    
    logger.info("\n" + "="*50)
    logger.info("DEMO COMPLETED")
    logger.info("="*50)
    logger.info("\nVisit http://localhost:8000 in your browser for the interactive UI")
    logger.info("API documentation available at http://localhost:8000/docs")


if __name__ == "__main__":
    main()
