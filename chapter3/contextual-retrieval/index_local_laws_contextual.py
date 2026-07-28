"""Script to chunk and index local legal documents using Contextual Retrieval

This script:
1. Cleans up existing indexes
2. Reads legal documents from local laws directory  
3. Chunks them with paragraph-aware boundaries (soft limit 1024, hard limit 2048)
4. Generates contextual descriptions for each chunk
5. Indexes them with contextual enhancement
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import time
import requests

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import Config, ChunkingConfig, LLMConfig
from contextual_chunking import ContextualChunker, ContextualChunk

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RETRIEVAL_PIPELINE_URL = "http://localhost:4242"  # Default retrieval pipeline URL
LAWS_DIR = Path("laws")  # Local laws directory

# Custom chunking configuration for legal documents
LEGAL_CHUNKING_CONFIG = ChunkingConfig(
    chunk_size=1024,  # Soft limit
    max_chunk_size=2048,  # Hard limit
    chunk_overlap=200,
    respect_paragraph_boundary=True,
    min_chunk_size=500
)


class ContextualLegalIndexer:
    """Handles contextual chunking and indexing of local legal documents"""
    
    def __init__(self, 
                 laws_dir: Path = LAWS_DIR, 
                 pipeline_url: str = RETRIEVAL_PIPELINE_URL,
                 use_contextual: bool = True,
                 llm_config: Optional[LLMConfig] = None):
        self.laws_dir = laws_dir
        self.pipeline_url = pipeline_url
        self.use_contextual = use_contextual
        
        # Initialize contextual chunker
        self.chunker = ContextualChunker(
            chunking_config=LEGAL_CHUNKING_CONFIG,
            llm_config=llm_config or LLMConfig(),
            use_contextual=use_contextual
        )
        
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "contextual_chunks": 0,
            "chunks_indexed": 0,
            "total_context_tokens": 0,
            "errors": 0,
            "categories_processed": set()
        }
        
        # Document store for tracking (must match tools.py expectation)
        self.doc_store_path = Path("document_store.json")
        
        logger.info(f"Initialized contextual indexer for local laws in {laws_dir}")
        logger.info(f"Pipeline URL: {pipeline_url}")
        logger.info(f"Contextual mode: {use_contextual}")
    
    def cleanup_existing_index(self):
        """Clean up existing indexes and document store"""
        logger.info("Cleaning up existing indexes...")
        
        # Clean local document store
        if self.doc_store_path.exists():
            try:
                # Load existing store to get document IDs
                with open(self.doc_store_path, 'r', encoding='utf-8') as f:
                    existing_docs = json.load(f)
                    
                logger.info(f"Found {len(existing_docs)} existing documents in store")
                
                # Clear the store
                self.doc_store_path.unlink()
                logger.info("Cleared local document store")
                
            except Exception as e:
                logger.error(f"Error cleaning document store: {e}")
        
        # Try to clear the retrieval pipeline
        try:
            response = requests.delete(f"{self.pipeline_url}/clear", timeout=30)
            if response.status_code == 200:
                logger.info("Cleared retrieval pipeline index")
            else:
                logger.warning(f"Failed to clear pipeline: {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not clear retrieval pipeline: {e}")
        
        logger.info("Cleanup complete")
    
    def get_all_legal_documents(self) -> List[Dict[str, Any]]:
        """Get all legal documents from local laws directory"""
        documents = []
        
        if not self.laws_dir.exists():
            logger.error(f"Laws directory not found: {self.laws_dir}")
            return documents
        
        # Iterate through category directories
        for category_dir in sorted(self.laws_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            
            category_name = category_dir.name
            logger.info(f"Found category: {category_name}")
            
            # Find all .md files in this category
            for md_file in category_dir.glob("*.md"):
                doc_info = {
                    "path": md_file,
                    "name": md_file.stem,  # filename without extension
                    "category": category_name,
                    "full_name": md_file.name
                }
                documents.append(doc_info)
        
        logger.info(f"Found {len(documents)} legal documents")
        return documents
    
    def read_document(self, doc_info: Dict[str, Any]) -> Optional[str]:
        """Read a legal document from disk"""
        try:
            doc_path = doc_info["path"]
            content = doc_path.read_text(encoding='utf-8')
            logger.debug(f"Read {doc_info['name']} ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error reading {doc_info['name']}: {e}")
            self.stats["errors"] += 1
            return None
    
    def generate_document_id(self, doc_info: Dict[str, Any]) -> str:
        """
        Generate a semantically meaningful document ID from file name.
        
        Examples:
        - "宪法.md" -> "宪法"
        - "劳动法（2018-12-29）.md" -> "劳动法_2018-12-29"
        - "民法典/第一编_总则.md" -> "民法典_第一编_总则"
        """
        # Use the file stem (name without extension)
        base_name = doc_info["name"]
        
        # Clean up the name: remove problematic characters but keep Chinese and alphanumeric
        import re
        # Replace parentheses with underscore
        clean_name = base_name.replace('（', '_').replace('）', '')
        clean_name = clean_name.replace('(', '_').replace(')', '')
        # Replace spaces and other separators with underscore
        clean_name = re.sub(r'[\s\-]+', '_', clean_name)
        # Remove trailing underscores
        clean_name = clean_name.strip('_')
        
        # Don't add category prefix - just use the clean file name
        # This makes the IDs cleaner and more readable
        doc_id = clean_name
        
        # Ensure the ID is not too long
        if len(doc_id) > 100:
            # Truncate but keep it meaningful
            doc_id = doc_id[:97] + "..."
        
        logger.debug(f"Generated document ID: {doc_info['name']} -> {doc_id}")
        return doc_id
    
    def process_document(self, doc_info: Dict[str, Any], content: str, 
                        index_immediately: bool = True) -> List[ContextualChunk]:
        """Process a document using contextual chunking with optional immediate indexing"""
        # Generate semantically meaningful document ID
        doc_id = self.generate_document_id(doc_info)
        
        # Prepare document metadata
        doc_metadata = {
            "category": doc_info["category"],
            "file_name": doc_info["full_name"],
            "document_type": "legal",
            "language": "zh-CN"
        }
        
        # Create callback for immediate indexing if enabled
        indexed_chunks = []
        
        def on_chunk_ready(chunk: ContextualChunk):
            """Callback to index chunk immediately when ready"""
            # Update metadata
            chunk.metadata["category"] = doc_info["category"]
            chunk.metadata["doc_title"] = doc_info["name"]
            
            if index_immediately:
                # Index the chunk immediately
                success = self.index_chunk(chunk)
                if success:
                    logger.info(f"  → Indexed chunk {chunk.chunk_index + 1} immediately")
                    indexed_chunks.append(chunk)
                else:
                    logger.warning(f"  → Failed to index chunk {chunk.chunk_index + 1}")
        
        # Use the contextual chunker with callback
        logger.info(f"Chunking {doc_info['name']} with contextual enhancement...")
        chunks = self.chunker.chunk_document(
            text=content,
            doc_id=doc_id,
            doc_metadata=doc_metadata,
            on_chunk_ready=on_chunk_ready if index_immediately else None
        )
        
        # If not indexing immediately, update metadata for all chunks
        if not index_immediately:
            for chunk in chunks:
                chunk.metadata["category"] = doc_info["category"]
                chunk.metadata["doc_title"] = doc_info["name"]
        
        return chunks
    
    def index_chunk(self, chunk: ContextualChunk) -> bool:
        """Index a contextual chunk in the retrieval pipeline"""
        try:
            # Prepare the indexing request
            # Use contextualized text for better retrieval
            index_data = {
                "text": chunk.contextualized_text if self.use_contextual else chunk.text,
                "doc_id": chunk.chunk_id,
                "metadata": {
                    **chunk.metadata,
                    "original_text": chunk.text,
                    "context": chunk.context,
                    "chunk_index": chunk.chunk_index,
                    "char_count": chunk.char_count,
                    "contextual": self.use_contextual
                }
            }
            
            # Send to retrieval pipeline
            response = requests.post(
                f"{self.pipeline_url}/index",
                json=index_data,
                headers={"Content-Type": "application/json"}, timeout=30
            )
            
            if response.status_code == 200:
                self.stats["chunks_indexed"] += 1
                if chunk.context:
                    self.stats["contextual_chunks"] += 1
                
                # IMPORTANT: Save to document store immediately after successful indexing
                self.save_chunk_to_document_store(chunk)
                
                return True
            else:
                logger.warning(f"Failed to index chunk {chunk.chunk_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error indexing chunk {chunk.chunk_id}: {e}")
            self.stats["errors"] += 1
            return False
    
    def save_chunk_to_document_store(self, chunk: ContextualChunk):
        """Save individual chunk to document store immediately (compatible with tools.py)"""
        try:
            # Load existing store or create new
            if self.doc_store_path.exists():
                with open(self.doc_store_path, 'r', encoding='utf-8') as f:
                    doc_store = json.load(f)
            else:
                doc_store = {}
            
            # Save chunk in format expected by tools.py get_document method
            doc_store[chunk.chunk_id] = {
                "doc_id": chunk.chunk_id,
                "content": chunk.contextualized_text if self.use_contextual else chunk.text,
                "metadata": {
                    **chunk.metadata,
                    "original_text": chunk.text,
                    "context": chunk.context,
                    "chunk_index": chunk.chunk_index,
                    "char_count": chunk.char_count,
                    "contextual": self.use_contextual
                }
            }
            
            # Write immediately - this is critical per user requirement
            with open(self.doc_store_path, 'w', encoding='utf-8') as f:
                json.dump(doc_store, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved chunk {chunk.chunk_id} to document store")
            
        except Exception as e:
            logger.error(f"Error saving chunk {chunk.chunk_id} to document store: {e}")
    
    def save_document_info(self, doc_info: Dict[str, Any], chunks: List[ContextualChunk]):
        """Save document summary information to local store"""
        # Load existing store or create new
        if self.doc_store_path.exists():
            with open(self.doc_store_path, 'r', encoding='utf-8') as f:
                doc_store = json.load(f)
        else:
            doc_store = {}
        
        # Add document info with meaningful ID
        doc_id = self.generate_document_id(doc_info)
        
        # Calculate statistics
        total_context_tokens = sum(c.context_tokens for c in chunks)
        avg_context_tokens = total_context_tokens / len(chunks) if chunks else 0
        
        # Store document-level summary (compatible with tools.py format)
        doc_store[doc_id] = {
            "doc_id": doc_id,
            "content": f"Document: {doc_info['name']}\nCategory: {doc_info['category']}\n\nThis is a summary entry for the complete document. Individual chunks are stored separately.",
            "metadata": {
                "title": doc_info["name"],
                "category": doc_info["category"],
                "file": str(doc_info["path"]),
                "chunks": len(chunks),
                "contextual_chunks": sum(1 for c in chunks if c.context),
                "total_chars": sum(c.char_count for c in chunks),
                "total_context_tokens": total_context_tokens,
                "avg_context_tokens": avg_context_tokens,
                "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "chunk_ids": [c.chunk_id for c in chunks],
                "is_summary": True
            }
        }
        
        # Save store
        with open(self.doc_store_path, 'w', encoding='utf-8') as f:
            json.dump(doc_store, f, ensure_ascii=False, indent=2)
    
    def process_all_documents(self, 
                            max_docs: Optional[int] = None, 
                            categories: Optional[List[str]] = None,
                            batch_size: int = 10):
        """Process all legal documents with contextual chunking"""
        start_time = time.time()
        
        # Clean up first
        self.cleanup_existing_index()
        
        # Get all documents
        all_documents = self.get_all_legal_documents()
        
        # Filter by categories if specified
        if categories:
            all_documents = [d for d in all_documents if any(cat in d["category"] for cat in categories)]
        
        # Limit documents if specified
        if max_docs:
            all_documents = all_documents[:max_docs]
        
        logger.info(f"Processing {len(all_documents)} documents...")
        
        for i, doc_info in enumerate(all_documents):
            logger.info(f"\n[{i+1}/{len(all_documents)}] Processing: {doc_info['name']}")
            logger.info(f"  Category: {doc_info['category']}")
            
            # Track category
            self.stats["categories_processed"].add(doc_info["category"])
            
            # Read document
            content = self.read_document(doc_info)
            if not content:
                continue
            
            # Process with contextual chunking and immediate indexing
            try:
                # Process and index chunks immediately as they're generated
                chunks = self.process_document(doc_info, content, index_immediately=True)
                self.stats["chunks_created"] += len(chunks)
                
                # Log contextual stats
                if self.use_contextual:
                    contextual_count = sum(1 for c in chunks if c.context)
                    logger.info(f"  ✓ Created and indexed {len(chunks)} chunks ({contextual_count} with context)")
                else:
                    logger.info(f"  ✓ Created and indexed {len(chunks)} chunks (no context)")
                
                # Save document info immediately after processing
                self.save_document_info(doc_info, chunks)
                
                self.stats["documents_processed"] += 1
                
                # Update token statistics
                if self.use_contextual:
                    self.stats["total_context_tokens"] += sum(c.context_tokens for c in chunks)
                
            except Exception as e:
                logger.error(f"Error processing {doc_info['name']}: {e}")
                self.stats["errors"] += 1
        
        elapsed = time.time() - start_time
        
        # Get final chunker statistics
        chunker_stats = self.chunker.get_statistics()
        
        # Print statistics
        self._print_statistics(elapsed, chunker_stats)
    
    def _print_statistics(self, elapsed_time: float, chunker_stats: Dict[str, Any]):
        """Print processing statistics"""
        print("\n" + "="*60)
        print("CONTEXTUAL INDEXING COMPLETE")
        print("="*60)
        print(f"Mode: {'Contextual' if self.use_contextual else 'Non-contextual'}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"Categories processed: {len(self.stats['categories_processed'])}")
        
        # Show categories
        categories_list = sorted(self.stats['categories_processed'])
        for cat in categories_list:
            print(f"  • {cat}")
        
        print(f"\nDocuments processed: {self.stats['documents_processed']}")
        print(f"Chunks created: {self.stats['chunks_created']}")
        
        if self.use_contextual:
            print(f"Contextual chunks: {self.stats['contextual_chunks']}")
            print(f"Chunks indexed: {self.stats['chunks_indexed']}")
            
            # Token usage
            print(f"\nContext Generation Statistics:")
            print(f"  Total context tokens: {chunker_stats.get('total_context_tokens', 0):,}")
            print(f"  Average tokens per chunk: {chunker_stats.get('avg_context_tokens', 0):.1f}")
            print(f"  Total generation time: {chunker_stats.get('total_generation_time', 0):.2f}s")
            print(f"  Average time per chunk: {chunker_stats.get('avg_generation_time', 0):.2f}s")
            
            # Cache statistics
            print(f"\nCache Performance:")
            print(f"  Cache hits: {chunker_stats.get('cache_hits', 0)}")
            print(f"  Cache misses: {chunker_stats.get('cache_misses', 0)}")
            print(f"  Hit rate: {chunker_stats.get('cache_hit_rate', 0):.1%}")
            
            # Cost estimation
            print(f"\nCost Estimation:")
            print(f"  Estimated cost: ${chunker_stats.get('estimated_cost', 0):.2f}")
        else:
            print(f"Chunks indexed: {self.stats['chunks_indexed']}")
        
        print(f"\nErrors: {self.stats['errors']}")
        
        if self.stats['chunks_created'] > 0:
            avg_chunks = self.stats['chunks_created'] / max(1, self.stats['documents_processed'])
            print(f"Average chunks per document: {avg_chunks:.1f}")
            
        if elapsed_time > 0 and self.stats['documents_processed'] > 0:
            docs_per_min = (self.stats['documents_processed'] / elapsed_time) * 60
            print(f"Processing speed: {docs_per_min:.1f} docs/minute")
        
        print("="*60 + "\n")
    
    def compare_retrieval_methods(self, test_queries: Optional[List[str]] = None):
        """Compare contextual vs non-contextual retrieval"""
        if not test_queries:
            test_queries = [
                "什么是合同的成立条件",
                "劳动者的基本权利有哪些",
                "如何处理交通事故责任",
                "什么是正当防卫",
                "公司股东的权利和义务"
            ]
        
        print("\n" + "="*60)
        print("RETRIEVAL COMPARISON TEST")
        print("="*60)
        print(f"Mode: {'Contextual' if self.use_contextual else 'Non-contextual'}")
        
        for query in test_queries:
            try:
                response = requests.post(
                    f"{self.pipeline_url}/search",
                    json={
                        "query": query,
                        "mode": "hybrid",
                        "top_k": 10,
                        "rerank_top_k": 5
                    }, timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"\n✓ Query: '{query}'")
                    
                    if "results" in results:
                        print(f"  Found {len(results['results'])} results")
                        
                        # Show top 3 results
                        for i, result in enumerate(results['results'][:3]):
                            score = result.get('score', result.get('rerank_score', 'N/A'))
                            metadata = result.get('metadata', {})
                            
                            print(f"\n  Result {i+1}:")
                            print(f"    Score: {score}")
                            print(f"    Category: {metadata.get('category', 'Unknown')}")
                            print(f"    Document: {metadata.get('doc_title', 'Unknown')}")
                            
                            # Show context if available
                            if metadata.get('context'):
                                print(f"    Context: {metadata['context'][:100]}...")
                            
                            # Show text preview
                            text = result.get('text', '')
                            # If contextual, try to extract original text
                            if metadata.get('contextual') and metadata.get('original_text'):
                                text = metadata['original_text']
                            
                            print(f"    Preview: {text[:150]}...")
                    else:
                        print(f"  No results found")
                else:
                    print(f"✗ Query '{query}' failed: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Error testing '{query}': {e}")
        
        print("\n" + "="*60 + "\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index local legal documents with contextual retrieval")
    parser.add_argument("--pipeline-url", default=RETRIEVAL_PIPELINE_URL, help="Retrieval pipeline URL")
    parser.add_argument("--max-docs", type=int, help="Maximum number of documents to process")
    parser.add_argument("--categories", nargs="+", help="Specific categories to process")
    parser.add_argument("--no-contextual", action="store_true", help="Disable contextual enhancement")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't clean existing indexes")
    parser.add_argument("--compare", action="store_true", help="Run comparison test after indexing")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for indexing")
    parser.add_argument("--llm-provider", default="kimi", help="LLM provider for context generation")
    parser.add_argument("--llm-model", help="Specific LLM model to use")
    
    args = parser.parse_args()
    
    # Configure LLM if specified
    llm_config = None
    if args.llm_provider or args.llm_model:
        llm_config = LLMConfig(
            provider=args.llm_provider,
            model=args.llm_model
        )
    
    # Create indexer
    indexer = ContextualLegalIndexer(
        pipeline_url=args.pipeline_url,
        use_contextual=not args.no_contextual,
        llm_config=llm_config
    )
    
    # Skip cleanup if requested
    if args.no_cleanup:
        indexer.cleanup_existing_index = lambda: logger.info("Skipping cleanup (--no-cleanup flag)")
    
    # Process documents
    indexer.process_all_documents(
        max_docs=args.max_docs,
        categories=args.categories,
        batch_size=args.batch_size
    )
    
    # Run comparison test if requested
    if args.compare:
        indexer.compare_retrieval_methods()


if __name__ == "__main__":
    main()
