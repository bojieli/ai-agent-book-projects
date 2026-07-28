"""Contextual Chunking Module - Educational implementation of Anthropic's Contextual Retrieval

This module demonstrates the key insight from Anthropic's research:
- Traditional RAG destroys context by chunking documents
- Contextual Retrieval prepends chunk-specific context before embedding
- This preserves semantic meaning that would otherwise be lost
"""

import json
import hashlib
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import time
from openai import OpenAI
from config import ChunkingConfig, KnowledgeBaseConfig, KnowledgeBaseType, LLMConfig


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ContextualChunk:
    """Enhanced chunk with contextual information"""
    chunk_id: str
    doc_id: str
    text: str  # Original chunk text
    context: str  # Generated contextual description
    contextualized_text: str  # Context + original text
    chunk_index: int
    char_count: int
    context_tokens: int = 0  # Track token usage
    generation_time: float = 0.0  # Track generation time
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "context": self.context,
            "contextualized_text": self.contextualized_text,
            "chunk_index": self.chunk_index,
            "char_count": self.char_count,
            "context_tokens": self.context_tokens,
            "generation_time": self.generation_time,
            "metadata": self.metadata
        }


class ContextualChunker:
    """
    Implements contextual chunking inspired by Anthropic's Contextual Retrieval.
    
    Key Educational Points:
    1. Context Generation: Uses LLM to generate chunk-specific context
    2. Prepending Strategy: Context is prepended to chunks before embedding
    3. BM25 Enhancement: Contextual chunks improve both semantic and lexical search
    4. Cost Optimization: Uses caching strategies to reduce API costs
    """
    
    def __init__(self, 
                 chunking_config: Optional[ChunkingConfig] = None,
                 llm_config: Optional[LLMConfig] = None,
                 use_contextual: bool = True):
        """
        Initialize the contextual chunker.
        
        Args:
            chunking_config: Configuration for chunking parameters
            llm_config: LLM configuration for context generation
            use_contextual: Whether to generate contextual chunks (for comparison)
        """
        self.chunking_config = chunking_config or ChunkingConfig()
        self.llm_config = llm_config or LLMConfig()
        self.use_contextual = use_contextual
        
        # Initialize LLM client for context generation
        if self.use_contextual:
            self._init_llm_client()
        
        # Statistics tracking
        self.stats = {
            "total_chunks": 0,
            "contextual_chunks": 0,
            "total_context_tokens": 0,
            "total_generation_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Context cache to avoid regenerating for similar chunks
        self.context_cache = {}
        
        logger.info(f"Initialized ContextualChunker (contextual={use_contextual})")
    
    def _init_llm_client(self):
        """Initialize LLM client for context generation"""
        client_config, model = self.llm_config.get_client_config()
        base_url = client_config.pop("base_url", None)
        
        if base_url:
            self.client = OpenAI(base_url=base_url, **client_config)
        else:
            self.client = OpenAI(**client_config)
        
        self.model = model
        logger.info(f"Using {self.llm_config.provider} ({self.model}) for context generation")
    
    def chunk_document(self, 
                     text: str, 
                     doc_id: str,
                     doc_metadata: Optional[Dict[str, Any]] = None,
                     on_chunk_ready: Optional[callable] = None) -> List[ContextualChunk]:
        """
        Chunk a document with optional contextual enhancement.
        
        Educational Note:
        This is the core innovation - each chunk gets contextualized
        with information about its position and meaning within the document.
        
        Args:
            text: Full document text
            doc_id: Document identifier
            doc_metadata: Optional document metadata
            
        Returns:
            List of ContextualChunk objects
        """
        logger.info(f"Starting chunking for document {doc_id}")
        start_time = time.time()
        
        # Step 1: Create basic chunks
        basic_chunks = self._create_basic_chunks(text, doc_id)
        logger.info(f"Created {len(basic_chunks)} basic chunks")
        
        # Step 2: Generate contextual enhancements if enabled
        if self.use_contextual:
            contextual_chunks = self._generate_contextual_chunks(
                basic_chunks, text, doc_id, doc_metadata, on_chunk_ready
            )
        else:
            # Create non-contextual chunks for comparison
            contextual_chunks = []
            for chunk in basic_chunks:
                contextual_chunks.append(ContextualChunk(
                    chunk_id=chunk["chunk_id"],
                    doc_id=chunk["doc_id"],
                    text=chunk["text"],
                    context="",  # No context in non-contextual mode
                    contextualized_text=chunk["text"],  # Just the original text
                    chunk_index=chunk["chunk_index"],
                    char_count=chunk["char_count"],
                    metadata={"contextual": False}
                ))
        
        # Update statistics
        self.stats["total_chunks"] += len(contextual_chunks)
        if self.use_contextual:
            self.stats["contextual_chunks"] += len(contextual_chunks)
        
        elapsed = time.time() - start_time
        logger.info(f"Chunking completed in {elapsed:.2f}s")
        logger.info(f"Statistics: {json.dumps(self.stats, indent=2)}")
        
        return contextual_chunks
    
    def _create_basic_chunks(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Create basic chunks using traditional chunking"""
        chunks = []
        
        if self.chunking_config.respect_paragraph_boundary:
            chunks = self._chunk_by_paragraphs(text, doc_id)
        else:
            chunks = self._chunk_by_size(text, doc_id)
        
        return chunks
    
    def _chunk_by_paragraphs(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Chunk text respecting paragraph boundaries"""
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
            if para_size > self.chunking_config.max_chunk_size:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(self._create_basic_chunk(chunk_text, doc_id, len(chunks)))
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph into sentences
                sentences = self._split_into_sentences(para)
                for sent in sentences:
                    if len(sent) > self.chunking_config.max_chunk_size:
                        # Force split very long sentences
                        for i in range(0, len(sent), self.chunking_config.chunk_size):
                            sub_chunk = sent[i:i + self.chunking_config.chunk_size]
                            chunks.append(self._create_basic_chunk(sub_chunk, doc_id, len(chunks)))
                    else:
                        chunks.append(self._create_basic_chunk(sent, doc_id, len(chunks)))
                continue
            
            # Check if adding this paragraph exceeds chunk size
            if current_size + para_size > self.chunking_config.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(self._create_basic_chunk(chunk_text, doc_id, len(chunks)))
                
                # Start new chunk with overlap
                if self.chunking_config.chunk_overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1], para]
                    current_size = len(current_chunk[0]) + para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Save final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            if len(chunk_text) >= self.chunking_config.min_chunk_size:
                chunks.append(self._create_basic_chunk(chunk_text, doc_id, len(chunks)))
        
        return chunks
    
    def _chunk_by_size(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """Simple size-based chunking"""
        chunks = []
        
        for i in range(0, len(text), self.chunking_config.chunk_size - self.chunking_config.chunk_overlap):
            chunk_text = text[i:i + self.chunking_config.chunk_size]
            
            if len(chunk_text) >= self.chunking_config.min_chunk_size:
                chunks.append(self._create_basic_chunk(chunk_text, doc_id, len(chunks)))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        
        # Handle both English and Chinese sentence endings
        sentences = re.split(r'([。！？\.!?]+)', text)
        
        # Reconstruct sentences with their endings
        result = []
        # Step to the end of the list: re.split with a capturing group yields
        # [text, delim, text, delim, ..., trailing_text], so stopping at
        # len(sentences) - 1 dropped the trailing fragment whenever the text
        # did not end in terminal punctuation (and returned [] for text with
        # none at all). The strip-and-filter below still discards the empty
        # tail that re.split produces when the text does end in punctuation.
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])
        
        return [s.strip() for s in result if s.strip()]
    
    def _create_basic_chunk(self, text: str, doc_id: str, chunk_index: int) -> Dict[str, Any]:
        """Create a basic chunk dictionary"""
        chunk_id = f"{doc_id}_chunk_{chunk_index}"
        
        return {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "text": text,
            "chunk_index": chunk_index,
            "char_count": len(text),
            "hash": hashlib.md5(text.encode()).hexdigest()
        }
    
    def _generate_contextual_chunks(self,
                                   basic_chunks: List[Dict[str, Any]],
                                   full_document: str,
                                   doc_id: str,
                                   doc_metadata: Optional[Dict[str, Any]] = None,
                                   on_chunk_ready: Optional[callable] = None) -> List[ContextualChunk]:
        """
        Generate contextual enhancements for chunks.
        
        Educational Note:
        Following Anthropic's Contextual Retrieval approach:
        - Each chunk gets a concise context explaining its position in the document
        - Context is prepended to the chunk before embedding
        - This dramatically improves retrieval accuracy
        """
        contextual_chunks = []
        
        # No document summary needed - Anthropic's approach doesn't use it
        doc_summary = None
        
        for i, chunk in enumerate(basic_chunks):
            logger.info(f"Generating context for chunk {i+1}/{len(basic_chunks)}")
            
            # Check cache first
            chunk_hash = chunk["hash"]
            if chunk_hash in self.context_cache:
                context = self.context_cache[chunk_hash]
                generation_time = 0.0
                context_tokens = 0
                self.stats["cache_hits"] += 1
                logger.debug(f"Cache hit for chunk {chunk['chunk_id']}")
            else:
                # Generate new context using Anthropic's approach
                context, context_tokens, generation_time = self._generate_chunk_context(
                    chunk["text"],
                    full_document
                )
                
                # Cache the context
                self.context_cache[chunk_hash] = context
                self.stats["cache_misses"] += 1
                self.stats["total_context_tokens"] += context_tokens
                self.stats["total_generation_time"] += generation_time
            
            # Create contextual chunk
            contextualized_text = f"{context}\n\n{chunk['text']}" if context else chunk["text"]
            
            contextual_chunk = ContextualChunk(
                chunk_id=chunk["chunk_id"],
                doc_id=doc_id,
                text=chunk["text"],
                context=context,
                contextualized_text=contextualized_text,
                chunk_index=chunk["chunk_index"],
                char_count=len(contextualized_text),
                context_tokens=context_tokens,
                generation_time=generation_time,
                metadata={
                    "contextual": True,
                    "original_char_count": chunk["char_count"],
                    "context_char_count": len(context)
                }
            )
            
            contextual_chunks.append(contextual_chunk)
            
            # Call the callback immediately if provided
            if on_chunk_ready:
                try:
                    on_chunk_ready(contextual_chunk)
                except Exception as e:
                    logger.error(f"Error in on_chunk_ready callback: {e}")
            
            # Log progress
            if (i + 1) % 10 == 0:
                avg_time = self.stats["total_generation_time"] / (i + 1)
                logger.info(f"Progress: {i+1}/{len(basic_chunks)} chunks, avg time: {avg_time:.2f}s")
        
        return contextual_chunks
    
    def _generate_document_summary(self, document: str, doc_id: str) -> str:
        """
        DEPRECATED: Not used in Anthropic's Contextual Retrieval approach.
        
        Educational Note:
        Anthropic's research shows that document summaries don't significantly
        improve retrieval. Instead, they provide the full document directly
        when generating chunk-specific context. This allows the LLM to understand
        the exact context needed for each specific chunk.
        """
        # This method is kept for backward compatibility but returns empty string
        return ""
    
    def _generate_chunk_context(self,
                               chunk_text: str,
                               full_document: str) -> Tuple[str, int, float]:
        """
        Generate contextual description for a chunk using Anthropic's exact approach.
        
        This follows Anthropic's Contextual Retrieval template exactly:
        1. Provide the full document
        2. Show the specific chunk
        3. Ask for concise context to situate the chunk
        
        Returns:
            Tuple of (context, token_count, generation_time)
        """
        start_time = time.time()
        
        try:
            # Use the exact prompt from Anthropic's blog post
            # with added instruction to use the same language as the document
            prompt = f"""<document>
{full_document}
</document>

Here is the chunk we want to situate within the whole document

<chunk>
{chunk_text}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. You MUST use the same language as the document."""

            # Use the exact approach from Anthropic - no system message needed
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=_reasoning_safe_temperature(self.model, 0.3),  # Low temperature for consistency
                max_tokens=100  # Anthropic mentions 50-100 tokens typically
            )
            
            context = response.choices[0].message.content.strip()
            
            # Estimate token count (rough approximation)
            token_count = len(prompt.split()) + len(context.split())
            generation_time = time.time() - start_time
            
            logger.info(f"Generated context in {generation_time:.2f}s: {context}")
            
            return context, token_count, generation_time
            
        except Exception as e:
            logger.error(f"Error generating chunk context: {e}")
            return "", 0, time.time() - start_time
    
    def compare_retrieval_methods(self,
                                 query: str,
                                 contextual_chunks: List[ContextualChunk],
                                 non_contextual_chunks: List[ContextualChunk],
                                 top_k: int = 5) -> Dict[str, Any]:
        """
        Compare contextual vs non-contextual retrieval on the SAME query.

        Educational Note:
        This is the ``compare_retrieval_methods`` capability referenced in
        实验 3-11. It builds two BM25 indexes fully offline (no API / server):
          * contextual index over ``contextualized_text`` (前缀 + 原文)
          * plain index over the original chunk ``text``
        and returns the top-k ranked chunks under each, so the caller can see
        exactly how the contextual prefix re-ranks the same corpus.
        """
        from rank_bm25 import BM25Okapi
        import numpy as np
        from compare_retrieval import tokenize

        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "contextual_results": [],
            "non_contextual_results": [],
            "analysis": {}
        }

        def _rank(chunks: List[ContextualChunk], field: str):
            if not chunks:
                return []
            corpus = [tokenize(getattr(c, field)) for c in chunks]
            index = BM25Okapi(corpus)
            scores = index.get_scores(tokenize(query))
            order = np.argsort(scores)[::-1][:top_k]
            ranked = []
            for rank, idx in enumerate(order, 1):
                c = chunks[idx]
                ranked.append({
                    "chunk_id": c.chunk_id,
                    "score": float(scores[idx]),
                    "rank": rank,
                    "text": c.text[:200],
                    "context": c.context[:200],
                })
            return ranked

        results["contextual_results"] = _rank(contextual_chunks, "contextualized_text")
        results["non_contextual_results"] = _rank(non_contextual_chunks, "text")

        ctx_top = results["contextual_results"][0] if results["contextual_results"] else None
        plain_top = results["non_contextual_results"][0] if results["non_contextual_results"] else None
        results["analysis"] = {
            "contextual_top_chunk": ctx_top["chunk_id"] if ctx_top else None,
            "non_contextual_top_chunk": plain_top["chunk_id"] if plain_top else None,
            "contextual_top_score": ctx_top["score"] if ctx_top else 0.0,
            "non_contextual_top_score": plain_top["score"] if plain_top else 0.0,
            "top1_changed": bool(ctx_top and plain_top and ctx_top["chunk_id"] != plain_top["chunk_id"]),
        }

        logger.info(f"Compared retrieval methods for query: {query} | "
                    f"top1 changed={results['analysis']['top1_changed']}")

        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get chunking statistics"""
        stats = self.stats.copy()
        
        # Calculate averages
        if stats["contextual_chunks"] > 0:
            stats["avg_context_tokens"] = stats["total_context_tokens"] / stats["contextual_chunks"]
            stats["avg_generation_time"] = stats["total_generation_time"] / stats["contextual_chunks"]
        else:
            stats["avg_context_tokens"] = 0
            stats["avg_generation_time"] = 0
        
        # Cache efficiency
        total_cache_ops = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_ops > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_ops
        else:
            stats["cache_hit_rate"] = 0
        
        # Cost estimation
        if self.llm_config.provider == "openai":
            cost_per_1k = 0.03
        else:
            cost_per_1k = 0.01
        
        stats["estimated_cost"] = (stats["total_context_tokens"] / 1000) * cost_per_1k
        
        return stats
