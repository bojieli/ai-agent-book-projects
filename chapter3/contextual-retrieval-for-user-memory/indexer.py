"""RAG Indexer for User Memory Conversations

This module handles indexing of conversation chunks using the retrieval pipeline service.
Interfaces with the existing retrieval pipeline on port 4242.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from config import IndexConfig, IndexMode
from chunker import ConversationChunk


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from searching the index"""
    chunk_id: str
    score: float
    chunk: ConversationChunk
    match_type: str  # "dense", "sparse", or "hybrid"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "score": self.score,
            "match_type": self.match_type,
            "conversation_id": self.chunk.conversation_id,
            "test_id": self.chunk.test_id,
            "rounds": f"{self.chunk.start_round}-{self.chunk.end_round}",
            "text": self.chunk.to_text()
        }


class MemoryIndexer:
    """Indexes and searches conversation chunks using the retrieval pipeline service"""
    
    def __init__(self, config: Optional[IndexConfig] = None):
        """
        Initialize the indexer
        
        Args:
            config: Index configuration
        """
        self.config = config or IndexConfig()
        self.chunks: Dict[str, ConversationChunk] = {}
        self.chunk_texts: Dict[str, str] = {}  # Map chunk_id to prepared text
        self.doc_id_mapping: Dict[str, str] = {}  # Map generated doc_id to our chunk_id
        
        # Retrieval pipeline URL
        self.retrieval_url = "http://localhost:4242"
        
        # Create directories
        Path(self.config.index_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.config.chunk_store_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Check retrieval pipeline availability
        self._check_retrieval_pipeline()
        
        logger.info(f"Initialized indexer with mode: {self.config.mode}")
    
    def _check_retrieval_pipeline(self):
        """Check if the retrieval pipeline service is available"""
        try:
            response = requests.get(f"{self.retrieval_url}/health", timeout=2)
            if response.status_code == 200:
                logger.info("✓ Retrieval pipeline service is available")
            else:
                logger.warning(f"Retrieval pipeline returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Retrieval pipeline service not available at {self.retrieval_url}: {e}")
            logger.info("Note: The retrieval pipeline needs to be running. Start it with:")
            logger.info("  cd projects/week3/retrieval-pipeline && python api_server.py")
    
    def add_chunks(self, chunks: List[ConversationChunk], rebuild: bool = True):
        """
        Add conversation chunks to the index
        
        Args:
            chunks: List of conversation chunks to index
            rebuild: Whether to rebuild indexes after adding (for retrieval pipeline)
        """
        documents = []
        
        for chunk in chunks:
            chunk_id = chunk.chunk_id
            
            # Store chunk locally
            self.chunks[chunk_id] = chunk
            
            # Prepare text for indexing
            chunk_text = self._prepare_chunk_text(chunk)
            self.chunk_texts[chunk_id] = chunk_text
            
            # Prepare document for retrieval pipeline
            doc = {
                "text": chunk_text,
                "metadata": {
                    "doc_id": chunk_id,
                    "test_id": chunk.test_id,
                    "conversation_id": chunk.conversation_id,
                    "chunk_index": chunk.chunk_index,
                    "start_round": chunk.start_round,
                    "end_round": chunk.end_round,
                    **chunk.metadata
                }
            }
            documents.append(doc)
            logger.debug(f"Added chunk {chunk_id} to index")
        
        if rebuild and documents:
            self._index_documents(documents)
        
        logger.info(f"Added {len(chunks)} chunks to index. Total chunks: {len(self.chunks)}")
    
    def _prepare_chunk_text(self, chunk: ConversationChunk) -> str:
        """
        Prepare chunk text for indexing with contextual enrichment
        
        Args:
            chunk: Conversation chunk
            
        Returns:
            Enriched text for indexing
        """
        if not self.config.enable_contextual:
            return chunk.to_text()
        
        # Build enriched text with contextual information
        lines = []
        
        # Add test case context
        lines.append(f"Test Case: {chunk.test_id}")
        lines.append(f"Conversation: {chunk.conversation_id}")
        
        # Add metadata as searchable text
        if chunk.metadata:
            for key, value in chunk.metadata.items():
                lines.append(f"{key}: {value}")
        
        # Add the main chunk content
        lines.append(chunk.to_text())
        
        # Add semantic tags for better retrieval
        lines.append(self._generate_semantic_tags(chunk))
        
        return "\n".join(lines)
    
    def _generate_semantic_tags(self, chunk: ConversationChunk) -> str:
        """
        Generate semantic tags for better retrieval
        
        Args:
            chunk: Conversation chunk
            
        Returns:
            Semantic tags as string
        """
        tags = []
        
        # Analyze content for common topics
        content = chunk.to_text().lower()
        
        # Financial topics
        if any(word in content for word in ["account", "bank", "credit", "loan", "payment"]):
            tags.append("financial")
        
        # Insurance topics
        if any(word in content for word in ["insurance", "claim", "policy", "coverage"]):
            tags.append("insurance")
        
        # Medical topics
        if any(word in content for word in ["medical", "doctor", "appointment", "prescription"]):
            tags.append("medical")
        
        # Travel topics
        if any(word in content for word in ["flight", "hotel", "travel", "booking", "reservation"]):
            tags.append("travel")
        
        # Add position tags
        if chunk.chunk_index == 0:
            tags.append("conversation_start")
        
        # Add round count tags
        round_count = chunk.end_round - chunk.start_round + 1
        if round_count < 10:
            tags.append("short_segment")
        elif round_count > 30:
            tags.append("long_segment")
        
        return f"Tags: {', '.join(tags)}" if tags else ""
    
    def _index_documents(self, documents: List[Dict[str, Any]]):
        """Send documents to the retrieval pipeline for indexing"""
        try:
            # First, clear existing index
            clear_response = requests.post(f"{self.retrieval_url}/clear", timeout=30)
            if clear_response.status_code == 200:
                logger.info("Cleared existing index")
            
            # Index documents one by one (retrieval pipeline expects individual documents)
            indexed_count = 0
            failed_count = 0
            
            for doc in documents:
                try:
                    response = requests.post(
                        f"{self.retrieval_url}/index",
                        json=doc  # Send individual document, timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        generated_doc_id = result.get("doc_id")
                        our_chunk_id = doc.get("metadata", {}).get("doc_id")
                        
                        # Store the mapping between generated doc_id and our chunk_id
                        if generated_doc_id and our_chunk_id:
                            self.doc_id_mapping[generated_doc_id] = our_chunk_id
                            
                        indexed_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to index document: {doc.get('metadata', {}).get('doc_id', 'unknown')}")
                        
                except requests.exceptions.RequestException as e:
                    failed_count += 1
                    logger.warning(f"Error indexing document: {e}")
            
            logger.info(f"Indexed {indexed_count} documents successfully ({failed_count} failed)")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to retrieval pipeline: {e}")
            logger.info("Make sure the retrieval pipeline is running on port 4242")
    
    def build_indexes(self):
        """Build or rebuild indexes by sending all chunks to retrieval pipeline"""
        if not self.chunks:
            logger.warning("No chunks to index")
            return
        
        # Prepare all documents
        documents = []
        for chunk_id, chunk in self.chunks.items():
            chunk_text = self.chunk_texts.get(chunk_id) or self._prepare_chunk_text(chunk)
            doc = {
                "text": chunk_text,
                "metadata": {
                    "doc_id": chunk_id,
                    "test_id": chunk.test_id,
                    "conversation_id": chunk.conversation_id,
                    "chunk_index": chunk.chunk_index,
                    "start_round": chunk.start_round,
                    "end_round": chunk.end_round,
                    **chunk.metadata
                }
            }
            documents.append(doc)
        
        # Send to retrieval pipeline
        self._index_documents(documents)
        logger.info("Index building complete")
    
    def search(self,
              query: str,
              top_k: int = 3,
              mode: Optional[IndexMode] = None) -> List[SearchResult]:
        """
        Search the index for relevant chunks using retrieval pipeline
        
        Args:
            query: Search query
            top_k: Number of results to return
            mode: Search mode (uses config default if not specified)
            
        Returns:
            List of search results
        """
        mode = mode or self.config.mode
        
        # Map IndexMode to retrieval pipeline mode strings
        mode_map = {
            IndexMode.DENSE: "dense",
            IndexMode.SPARSE: "sparse", 
            IndexMode.HYBRID: "hybrid"
        }
        
        search_mode = mode_map.get(mode, "hybrid")
        
        if not top_k or top_k < 1:
            top_k = 3
        
        try:
            # Query the retrieval pipeline
            # Note: The pipeline has two top_k parameters:
            # - top_k: for initial retrieval (we set to max(20, top_k))
            # - rerank_top_k: for final results (we set to the requested top_k)
            response = requests.post(
                f"{self.retrieval_url}/search",
                json={
                    "query": query,
                    "mode": search_mode,
                    "top_k": max(20, top_k),  # Retrieve more candidates for better reranking
                    "rerank_top_k": top_k,    # Return the requested number of results
                    "skip_reranking": False    # Always use reranking for better quality
                }, timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Get results based on mode
            if search_mode == "hybrid" and "reranked_results" in data:
                search_results = data["reranked_results"]
            elif search_mode == "dense" and "dense_results" in data:
                search_results = data["dense_results"]
            elif search_mode == "sparse" and "sparse_results" in data:
                search_results = data["sparse_results"]
            else:
                # Fallback to any available results
                search_results = (data.get("reranked_results", []) or 
                                data.get("dense_results", []) or 
                                data.get("sparse_results", []))
            
            # Convert to SearchResult objects
            results = []
            for item in search_results:
                # Try to get our chunk_id from different sources
                chunk_id = None
                
                # First, check if metadata contains our doc_id
                metadata = item.get("metadata", {})
                if metadata.get("doc_id"):
                    chunk_id = metadata.get("doc_id")
                else:
                    # Fall back to doc_id mapping
                    generated_doc_id = item.get("doc_id", "")
                    chunk_id = self.doc_id_mapping.get(generated_doc_id)
                
                # Get chunk from local storage
                if chunk_id and chunk_id in self.chunks:
                    chunk = self.chunks[chunk_id]
                    
                    # Get score based on result type
                    score = item.get("rerank_score", item.get("score", 0.0))
                    
                    results.append(SearchResult(
                        chunk_id=chunk_id,
                        score=float(score),
                        chunk=chunk,
                        match_type=search_mode
                    ))
                else:
                    # Log warning but don't fail
                    doc_id = item.get("doc_id", "unknown")
                    if chunk_id:
                        logger.debug(f"Chunk {chunk_id} not found in local storage")
                    else:
                        logger.debug(f"No mapping found for doc_id {doc_id}")
            
            logger.info(f"Search returned {len(results)} results from retrieval pipeline")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching via retrieval pipeline: {e}")
            logger.info("Falling back to empty results. Ensure retrieval pipeline is running.")
            return []
    
    def save_index(self, path: Optional[str] = None):
        """
        Save the chunks and metadata to disk
        
        Args:
            path: Path to save index (uses config default if not specified)
        """
        path = path or self.config.index_path
        
        # Save chunks
        chunks_data = {
            chunk_id: chunk.to_dict() 
            for chunk_id, chunk in self.chunks.items()
        }
        
        with open(f"{path}_chunks.json", 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        
        # Save chunk texts
        with open(f"{path}_texts.json", 'w', encoding='utf-8') as f:
            json.dump(self.chunk_texts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Chunks saved to {path}. Total chunks: {len(self.chunks)}")
    
    def load_index(self, path: Optional[str] = None):
        """
        Load chunks from disk and re-index in retrieval pipeline
        
        Args:
            path: Path to load index from (uses config default if not specified)
        """
        path = path or self.config.index_path
        
        try:
            # Load chunks
            with open(f"{path}_chunks.json", 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            self.chunks = {}
            for chunk_id, chunk_dict in chunks_data.items():
                # Convert messages
                from chunker import ConversationMessage
                messages = []
                for msg_data in chunk_dict.get('messages', []):
                    messages.append(ConversationMessage(**msg_data))
                
                # Create chunk
                chunk = ConversationChunk(
                    chunk_id=chunk_dict['chunk_id'],
                    conversation_id=chunk_dict['conversation_id'],
                    test_id=chunk_dict['test_id'],
                    chunk_index=chunk_dict['chunk_index'],
                    start_round=chunk_dict['start_round'],
                    end_round=chunk_dict['end_round'],
                    messages=messages,
                    metadata=chunk_dict.get('metadata', {}),
                    context_before=chunk_dict.get('context_before'),
                    context_after=chunk_dict.get('context_after'),
                    created_at=chunk_dict.get('created_at', '')
                )
                self.chunks[chunk_id] = chunk
            
            # Load chunk texts if available
            texts_path = f"{path}_texts.json"
            if Path(texts_path).exists():
                with open(texts_path, 'r', encoding='utf-8') as f:
                    self.chunk_texts = json.load(f)
            else:
                # Regenerate texts if not saved
                self.chunk_texts = {}
                for chunk_id, chunk in self.chunks.items():
                    self.chunk_texts[chunk_id] = self._prepare_chunk_text(chunk)
            
            logger.info(f"Loaded {len(self.chunks)} chunks from {path}")
            
            # Re-index in retrieval pipeline
            self.build_indexes()
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
