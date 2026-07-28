"""Script to chunk and index local legal documents from laws directory

This script:
1. Cleans up existing indexes
2. Reads legal documents from local laws directory
3. Chunks them with paragraph-aware boundaries (soft limit 1024, hard limit 2048)
4. Indexes them in the retrieval pipeline
"""

import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import time
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RETRIEVAL_PIPELINE_URL = "http://localhost:4242"  # Default retrieval pipeline URL
LAWS_DIR = Path("laws")  # Local laws directory

# Chunking configuration
SOFT_LIMIT = 1024  # Soft character limit
HARD_LIMIT = 2048  # Hard character limit
MIN_CHUNK_SIZE = 500  # Minimum chunk size


@dataclass
class LegalChunk:
    """Represents a chunk of legal document"""
    chunk_id: str
    doc_id: str
    doc_title: str
    category: str  # e.g., "宪法", "民法典"
    text: str
    chunk_index: int
    char_count: int
    metadata: Dict[str, Any]


class LocalLegalIndexer:
    """Handles chunking and indexing of local legal documents"""
    
    def __init__(self, laws_dir: Path = LAWS_DIR, pipeline_url: str = RETRIEVAL_PIPELINE_URL):
        self.laws_dir = laws_dir
        self.pipeline_url = pipeline_url
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "chunks_indexed": 0,
            "errors": 0,
            "categories_processed": set()
        }
        
        # Document store for tracking
        self.doc_store_path = Path("document_store.json")
        
        logger.info(f"Initialized indexer for local laws in {laws_dir}")
        logger.info(f"Pipeline URL: {pipeline_url}")
    
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
            logger.info(f"Processing category: {category_name}")
            
            # Find all .md files in this category
            for md_file in category_dir.glob("*.md"):
                doc_info = {
                    "path": md_file,
                    "name": md_file.stem,  # filename without extension
                    "category": category_name,
                    "full_name": md_file.name
                }
                documents.append(doc_info)
        
        logger.info(f"Found {len(documents)} legal documents across {len(self.stats['categories_processed'])} categories")
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
    
    def chunk_document_smart(self, text: str, doc_id: str, doc_title: str, category: str) -> List[LegalChunk]:
        """
        Smart chunking that respects paragraph boundaries with soft and hard limits.
        
        Strategy:
        - Accumulate paragraphs until soft limit is exceeded
        - Keep adding if next paragraph fits within hard limit
        - Cut at paragraph boundary when possible
        - Force split at hard limit if necessary
        """
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # Handle oversized paragraphs
            if para_size > HARD_LIMIT:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    if len(chunk_text) >= MIN_CHUNK_SIZE:
                        chunks.append(self._create_chunk(
                            chunk_text, doc_id, doc_title, category, len(chunks)
                        ))
                    current_chunk = []
                    current_size = 0
                
                # Force split the oversized paragraph
                for i in range(0, para_size, SOFT_LIMIT):
                    sub_text = para[i:i + SOFT_LIMIT]
                    if len(sub_text) >= MIN_CHUNK_SIZE:
                        chunks.append(self._create_chunk(
                            sub_text, doc_id, doc_title, category, len(chunks)
                        ))
                continue
            
            # Check if adding this paragraph would exceed limits
            new_size = current_size + para_size + (4 if current_chunk else 0)  # Account for \n\n
            
            if new_size > SOFT_LIMIT and current_chunk:
                # Check if we can still fit it under hard limit
                if new_size <= HARD_LIMIT:
                    # Add it anyway (between soft and hard limit)
                    current_chunk.append(para)
                    current_size = new_size
                else:
                    # Save current chunk and start new one
                    chunk_text = '\n\n'.join(current_chunk)
                    if len(chunk_text) >= MIN_CHUNK_SIZE:
                        chunks.append(self._create_chunk(
                            chunk_text, doc_id, doc_title, category, len(chunks)
                        ))
                    
                    # Start new chunk
                    current_chunk = [para]
                    current_size = para_size
            else:
                # Add to current chunk
                current_chunk.append(para)
                current_size = new_size
        
        # Save final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= MIN_CHUNK_SIZE:
                chunks.append(self._create_chunk(
                    chunk_text, doc_id, doc_title, category, len(chunks)
                ))
        
        logger.info(f"Created {len(chunks)} chunks for {doc_title}")
        return chunks
    
    def _create_chunk(self, text: str, doc_id: str, doc_title: str, category: str, chunk_index: int) -> LegalChunk:
        """Create a LegalChunk object"""
        chunk_id = f"{doc_id}_chunk_{chunk_index}"
        
        # Extract section info if available
        section_info = self._extract_section_info(text)
        
        return LegalChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            doc_title=doc_title,
            category=category,
            text=text,
            chunk_index=chunk_index,
            char_count=len(text),
            metadata={
                "source": "local_laws",
                "document_type": "legal",
                "language": "zh-CN",
                "category": category,
                "section": section_info
            }
        )
    
    def _extract_section_info(self, text: str) -> Optional[str]:
        """Extract section/chapter/article information from legal text"""
        import re
        
        # Common patterns in Chinese legal documents
        patterns = [
            r'第[一二三四五六七八九十百千\d]+[章节条款篇编]',
            r'第[一二三四五六七八九十百千\d]+部分',
            r'[【\[]第[一二三四五六七八九十百千\d]+[章节条款篇编][】\]]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:200])  # Check first 200 chars
            if match:
                return match.group()
        
        return None
    
    def index_chunk(self, chunk: LegalChunk) -> bool:
        """Index a chunk in the retrieval pipeline"""
        try:
            # Prepare the indexing request
            index_data = {
                "text": chunk.text,
                "doc_id": chunk.chunk_id,
                "metadata": {
                    **chunk.metadata,
                    "doc_title": chunk.doc_title,
                    "category": chunk.category,
                    "chunk_index": chunk.chunk_index,
                    "char_count": chunk.char_count
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
                return True
            else:
                logger.warning(f"Failed to index chunk {chunk.chunk_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error indexing chunk {chunk.chunk_id}: {e}")
            self.stats["errors"] += 1
            return False
    
    def save_document_info(self, doc_info: Dict[str, Any], chunks: List[LegalChunk]):
        """Save document information to local store"""
        # Load existing store or create new
        if self.doc_store_path.exists():
            with open(self.doc_store_path, 'r', encoding='utf-8') as f:
                doc_store = json.load(f)
        else:
            doc_store = {}
        
        # Add document info
        doc_id = hashlib.md5(doc_info["full_name"].encode()).hexdigest()[:12]
        doc_store[doc_id] = {
            "title": doc_info["name"],
            "category": doc_info["category"],
            "file": str(doc_info["path"]),
            "chunks": len(chunks),
            "total_chars": sum(c.char_count for c in chunks),
            "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save store
        with open(self.doc_store_path, 'w', encoding='utf-8') as f:
            json.dump(doc_store, f, ensure_ascii=False, indent=2)
    
    def process_all_documents(self, max_docs: Optional[int] = None, categories: Optional[List[str]] = None):
        """Process all legal documents"""
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
            
            # Track category
            self.stats["categories_processed"].add(doc_info["category"])
            
            # Read document
            content = self.read_document(doc_info)
            if not content:
                continue
            
            # Generate document ID
            doc_id = hashlib.md5(doc_info["full_name"].encode()).hexdigest()[:12]
            
            # Chunk the document
            chunks = self.chunk_document_smart(
                content, 
                doc_id, 
                doc_info["name"],
                doc_info["category"]
            )
            self.stats["chunks_created"] += len(chunks)
            
            # Index each chunk
            indexed_count = 0
            for j, chunk in enumerate(chunks):
                if self.index_chunk(chunk):
                    indexed_count += 1
                
                # Progress update
                if (j + 1) % 10 == 0:
                    logger.debug(f"  Indexed {j + 1}/{len(chunks)} chunks")
            
            logger.info(f"  ✓ Indexed {indexed_count}/{len(chunks)} chunks successfully")
            
            # Save document info
            self.save_document_info(doc_info, chunks)
            
            self.stats["documents_processed"] += 1
        
        elapsed = time.time() - start_time
        
        # Print statistics
        self._print_statistics(elapsed)
    
    def _print_statistics(self, elapsed_time: float):
        """Print processing statistics"""
        print("\n" + "="*60)
        print("INDEXING COMPLETE")
        print("="*60)
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"Categories processed: {len(self.stats['categories_processed'])}")
        print(f"  - {', '.join(sorted(self.stats['categories_processed']))}")
        print(f"Documents processed: {self.stats['documents_processed']}")
        print(f"Chunks created: {self.stats['chunks_created']}")
        print(f"Chunks indexed: {self.stats['chunks_indexed']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.stats['chunks_created'] > 0:
            avg_chunks = self.stats['chunks_created'] / max(1, self.stats['documents_processed'])
            print(f"Average chunks per document: {avg_chunks:.1f}")
            
        if elapsed_time > 0 and self.stats['documents_processed'] > 0:
            docs_per_sec = self.stats['documents_processed'] / elapsed_time
            print(f"Processing speed: {docs_per_sec:.2f} docs/second")
        
        print("="*60 + "\n")
    
    def verify_indexing(self, test_queries: Optional[List[str]] = None):
        """Verify that indexing worked by performing test searches"""
        if not test_queries:
            test_queries = [
                "民法典",
                "合同法",
                "劳动法",
                "刑法",
                "宪法"
            ]
        
        print("\n" + "="*60)
        print("VERIFICATION TESTS")
        print("="*60)
        
        for query in test_queries:
            try:
                response = requests.post(
                    f"{self.pipeline_url}/search",
                    json={
                        "query": query,
                        "mode": "hybrid",
                        "top_k": 5,
                        "rerank_top_k": 3
                    }, timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"\n✓ Test search for '{query}':")
                    
                    if "results" in results:
                        print(f"  Found {len(results['results'])} results")
                        for i, result in enumerate(results['results'][:2]):
                            score = result.get('score', result.get('rerank_score', 'N/A'))
                            metadata = result.get('metadata', {})
                            print(f"  {i+1}. Score: {score}")
                            print(f"     Category: {metadata.get('category', 'Unknown')}")
                            print(f"     Doc: {metadata.get('doc_title', 'Unknown')}")
                            print(f"     Preview: {result.get('text', '')[:100]}...")
                    else:
                        print(f"  No results found")
                else:
                    print(f"✗ Test search for '{query}' failed: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Error testing '{query}': {e}")
        
        print("="*60 + "\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index local legal documents into retrieval pipeline")
    parser.add_argument("--pipeline-url", default=RETRIEVAL_PIPELINE_URL, help="Retrieval pipeline URL")
    parser.add_argument("--max-docs", type=int, help="Maximum number of documents to process")
    parser.add_argument("--categories", nargs="+", help="Specific categories to process (e.g., '宪法' '民法典')")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't clean existing indexes")
    parser.add_argument("--verify", action="store_true", help="Run verification tests after indexing")
    
    args = parser.parse_args()
    
    # Create indexer
    indexer = LocalLegalIndexer(pipeline_url=args.pipeline_url)
    
    # Skip cleanup if requested
    if args.no_cleanup:
        indexer.cleanup_existing_index = lambda: logger.info("Skipping cleanup (--no-cleanup flag)")
    
    # Process documents
    indexer.process_all_documents(
        max_docs=args.max_docs,
        categories=args.categories
    )
    
    # Run verification if requested
    if args.verify:
        indexer.verify_indexing()


if __name__ == "__main__":
    main()
