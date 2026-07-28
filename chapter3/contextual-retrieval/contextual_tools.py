"""Enhanced tools for contextual retrieval with BM25 and semantic search

Educational implementation showing how contextual chunks improve both
BM25 (lexical) and embedding (semantic) retrieval.
"""

import json
import logging
import requests
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time
from rank_bm25 import BM25Okapi
import pickle
from pathlib import Path

from config import KnowledgeBaseConfig, KnowledgeBaseType
from tools import KnowledgeBaseTools, SearchResult
from contextual_chunking import ContextualChunk
# Shared tokenizer: 中文没有空格，原先的 .lower().split() 会把整段当成一个 token，
# 导致 BM25 在中文语料上几乎失效。统一改用 compare_retrieval.tokenize（jieba 分词）。
from compare_retrieval import tokenize as _bm25_tokenize

logger = logging.getLogger(__name__)


@dataclass
class ContextualSearchResult(SearchResult):
    """Enhanced search result with contextual information"""
    is_contextual: bool = False
    context_text: str = ""
    bm25_score: float = 0.0
    embedding_score: float = 0.0
    hybrid_score: float = 0.0
    retrieval_method: str = "hybrid"  # bm25, embedding, or hybrid
    
    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "is_contextual": self.is_contextual,
            "context_text": self.context_text,
            "bm25_score": self.bm25_score,
            "embedding_score": self.embedding_score,
            "hybrid_score": self.hybrid_score,
            "retrieval_method": self.retrieval_method
        })
        return base


class ContextualKnowledgeBaseTools(KnowledgeBaseTools):
    """
    Enhanced knowledge base tools with contextual retrieval support.
    
    Key Educational Points:
    1. Dual Indexing: Maintains both contextual and non-contextual indexes
    2. BM25 Enhancement: Shows how context improves lexical matching
    3. Hybrid Search: Combines BM25 and semantic search with rank fusion
    4. Comparison Mode: Allows side-by-side evaluation of methods
    """
    
    def __init__(self, 
                 config: KnowledgeBaseConfig,
                 use_contextual: bool = True,
                 enable_comparison: bool = False):
        """
        Initialize contextual knowledge base tools.
        
        Args:
            config: Knowledge base configuration
            use_contextual: Whether to use contextual retrieval
            enable_comparison: Whether to enable comparison mode
        """
        super().__init__(config)
        self.use_contextual = use_contextual
        self.enable_comparison = enable_comparison
        
        # BM25 indexes for lexical search
        self.bm25_index = None
        self.bm25_contextual_index = None
        self.bm25_corpus = []
        self.bm25_contextual_corpus = []
        
        # Document and chunk storage
        self.chunk_store = {}  # chunk_id -> ContextualChunk
        self.contextual_chunk_store = {}  # chunk_id -> ContextualChunk (with context)
        
        # Index paths
        self.index_dir = Path("indexes")
        self.index_dir.mkdir(exist_ok=True)
        
        # Load existing indexes if available
        self._load_indexes()
        
        # Statistics
        self.search_stats = {
            "total_searches": 0,
            "contextual_searches": 0,
            "non_contextual_searches": 0,
            "comparison_searches": 0,
            "avg_retrieval_time": 0.0,
            "total_retrieval_time": 0.0
        }
        
        logger.info(f"Initialized ContextualKnowledgeBaseTools (contextual={use_contextual}, comparison={enable_comparison})")
    
    def index_contextual_chunks(self, chunks: List[ContextualChunk], rebuild_bm25: bool = True):
        """
        Index contextual chunks for both BM25 and semantic search.
        
        Educational Note:
        This demonstrates the dual indexing strategy:
        - BM25 index on contextualized text for better lexical matching
        - Semantic embeddings on contextualized text for richer meaning
        """
        logger.info(f"Indexing {len(chunks)} contextual chunks")
        start_time = time.time()
        
        # Store chunks
        for chunk in chunks:
            self.contextual_chunk_store[chunk.chunk_id] = chunk
            
            # Also store non-contextual version for comparison
            non_contextual_chunk = ContextualChunk(
                chunk_id=chunk.chunk_id + "_nc",
                doc_id=chunk.doc_id,
                text=chunk.text,
                context="",
                contextualized_text=chunk.text,
                chunk_index=chunk.chunk_index,
                char_count=len(chunk.text),
                metadata={"contextual": False}
            )
            self.chunk_store[non_contextual_chunk.chunk_id] = non_contextual_chunk
        
        # Build BM25 indexes
        if rebuild_bm25:
            self._build_bm25_indexes()
        
        # Index to retrieval pipeline (if local)
        if self.config.type == KnowledgeBaseType.LOCAL:
            self._index_chunks_to_pipeline(chunks)
        
        elapsed = time.time() - start_time
        logger.info(f"Indexed {len(chunks)} chunks in {elapsed:.2f}s")
        
        # Save indexes
        self._save_indexes()
    
    def _build_bm25_indexes(self):
        """
        Build BM25 indexes for both contextual and non-contextual chunks.
        
        Educational Note:
        BM25 uses TF-IDF with optimizations:
        - Term frequency saturation prevents common words from dominating
        - Document length normalization accounts for varying chunk sizes
        - The contextual version has richer vocabulary from added context
        """
        logger.info("Building BM25 indexes")
        
        # Build contextual BM25 index
        if self.contextual_chunk_store:
            contextual_texts = []
            for chunk in self.contextual_chunk_store.values():
                # Tokenize for BM25 (jieba 中文分词，兼容英文)
                tokens = _bm25_tokenize(chunk.contextualized_text)
                contextual_texts.append(tokens)
            
            self.bm25_contextual_corpus = contextual_texts
            self.bm25_contextual_index = BM25Okapi(contextual_texts)
            logger.info(f"Built contextual BM25 index with {len(contextual_texts)} documents")
        
        # Build non-contextual BM25 index
        if self.chunk_store:
            non_contextual_texts = []
            for chunk in self.chunk_store.values():
                tokens = _bm25_tokenize(chunk.text)
                non_contextual_texts.append(tokens)
            
            self.bm25_corpus = non_contextual_texts
            self.bm25_index = BM25Okapi(non_contextual_texts)
            logger.info(f"Built non-contextual BM25 index with {len(non_contextual_texts)} documents")
    
    def _index_chunks_to_pipeline(self, chunks: List[ContextualChunk]):
        """Index chunks to the retrieval pipeline"""
        for chunk in chunks:
            try:
                # Index contextual version
                if self.use_contextual:
                    response = requests.post(
                        f"{self.config.local_base_url}/index",
                        json={
                            "text": chunk.contextualized_text,
                            "doc_id": chunk.doc_id,
                            "metadata": {
                                "chunk_id": chunk.chunk_id,
                                "chunk_index": chunk.chunk_index,
                                "is_contextual": True,
                                "context": chunk.context[:200],  # Store truncated context
                                "original_text": chunk.text[:500]  # Store truncated original
                            }
                        }, timeout=30
                    )
                    response.raise_for_status()
                
                # Also index non-contextual version if in comparison mode
                if self.enable_comparison:
                    response = requests.post(
                        f"{self.config.local_base_url}/index",
                        json={
                            "text": chunk.text,
                            "doc_id": chunk.doc_id,
                            "metadata": {
                                "chunk_id": chunk.chunk_id + "_nc",
                                "chunk_index": chunk.chunk_index,
                                "is_contextual": False
                            }
                        }, timeout=30
                    )
                    response.raise_for_status()
                    
            except Exception as e:
                logger.error(f"Error indexing chunk {chunk.chunk_id}: {e}")
    
    def contextual_search(self, 
                         query: str, 
                         method: str = "hybrid",
                         top_k: int = 20) -> List[ContextualSearchResult]:
        """
        Perform contextual search using specified method.
        
        Args:
            query: Search query
            method: Search method - "bm25", "embedding", or "hybrid"
            top_k: Number of results to return
            
        Educational Note:
        This demonstrates three retrieval strategies:
        1. BM25: Pure lexical matching based on term frequency
        2. Embedding: Semantic similarity using vector embeddings
        3. Hybrid: Rank fusion combining both approaches
        """
        logger.info(f"Performing {method} search for: {query[:100]}...")
        start_time = time.time()
        
        results = []
        
        if method in ["bm25", "hybrid"]:
            bm25_results = self._search_bm25(query, self.use_contextual, top_k * 2)
            results.extend(bm25_results)
        
        if method in ["embedding", "hybrid"]:
            embedding_results = self._search_embeddings(query, self.use_contextual, top_k * 2)
            results.extend(embedding_results)
        
        if method == "hybrid":
            # Rank fusion: combine and deduplicate results
            results = self._rank_fusion(bm25_results, embedding_results, top_k)
        else:
            # Sort by score and limit
            results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
        
        # Update statistics
        elapsed = time.time() - start_time
        self.search_stats["total_searches"] += 1
        if self.use_contextual:
            self.search_stats["contextual_searches"] += 1
        else:
            self.search_stats["non_contextual_searches"] += 1
        self.search_stats["total_retrieval_time"] += elapsed
        self.search_stats["avg_retrieval_time"] = (
            self.search_stats["total_retrieval_time"] / self.search_stats["total_searches"]
        )
        
        logger.info(f"Search completed in {elapsed:.2f}s, returned {len(results)} results")
        
        return results
    
    def _search_bm25(self, query: str, use_contextual: bool, top_k: int) -> List[ContextualSearchResult]:
        """
        Perform BM25 search.
        
        Educational Note:
        BM25 excels at finding exact term matches and handles
        technical terms, IDs, and specific phrases well.
        Contextual chunks help by adding synonyms and related terms.
        """
        if use_contextual and self.bm25_contextual_index:
            index = self.bm25_contextual_index
            corpus = self.bm25_contextual_corpus
            chunk_store = self.contextual_chunk_store
        elif self.bm25_index:
            index = self.bm25_index
            corpus = self.bm25_corpus
            chunk_store = self.chunk_store
        else:
            logger.warning("BM25 index not available")
            return []
        
        # Tokenize query (jieba 中文分词，兼容英文)
        query_tokens = _bm25_tokenize(query)
        
        # Get BM25 scores
        scores = index.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        # Create results
        results = []
        chunk_list = list(chunk_store.values())
        
        for idx in top_indices:
            if idx < len(chunk_list) and scores[idx] > 0:
                chunk = chunk_list[idx]
                result = ContextualSearchResult(
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=float(scores[idx]),
                    is_contextual=use_contextual,
                    context_text=chunk.context if use_contextual else "",
                    bm25_score=float(scores[idx]),
                    retrieval_method="bm25",
                    metadata={"method": "bm25", "contextual": use_contextual}
                )
                results.append(result)
        
        return results
    
    def _search_embeddings(self, query: str, use_contextual: bool, top_k: int) -> List[ContextualSearchResult]:
        """
        Perform semantic search using embeddings.
        
        Educational Note:
        Embedding search captures semantic meaning and relationships.
        Contextual chunks provide richer semantic information,
        helping find conceptually related content even without exact matches.
        """
        try:
            # Use the retrieval pipeline for embedding search
            response = requests.post(
                f"{self.config.local_base_url}/search",
                json={
                    "query": query,
                    "mode": "embedding",  # Use embedding mode
                    "top_k": top_k,
                    "filter": {"is_contextual": use_contextual} if self.enable_comparison else None
                }, timeout=30
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            for item in data.get("results", []):
                # Map back to our chunk store
                chunk_id = item.get("metadata", {}).get("chunk_id", "")
                
                if use_contextual and chunk_id in self.contextual_chunk_store:
                    chunk = self.contextual_chunk_store[chunk_id]
                elif chunk_id in self.chunk_store:
                    chunk = self.chunk_store[chunk_id]
                else:
                    continue
                
                result = ContextualSearchResult(
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=item.get("score", 0.0),
                    is_contextual=use_contextual,
                    context_text=chunk.context if hasattr(chunk, 'context') else "",
                    embedding_score=item.get("score", 0.0),
                    retrieval_method="embedding",
                    metadata={"method": "embedding", "contextual": use_contextual}
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in embedding search: {e}")
            return []
    
    def _rank_fusion(self, 
                     bm25_results: List[ContextualSearchResult],
                     embedding_results: List[ContextualSearchResult],
                     top_k: int) -> List[ContextualSearchResult]:
        """
        Combine BM25 and embedding results using reciprocal rank fusion.
        
        Educational Note:
        Rank fusion combines different retrieval signals:
        - BM25 provides strong exact matching
        - Embeddings provide semantic understanding
        - The combination often outperforms either method alone
        
        We use Reciprocal Rank Fusion (RRF) which is simple but effective.
        """
        fusion_scores = {}
        chunk_map = {}
        
        # RRF constant (typically 60)
        k = 60
        
        # Process BM25 results
        for rank, result in enumerate(bm25_results):
            rrf_score = 1.0 / (k + rank + 1)
            fusion_scores[result.chunk_id] = fusion_scores.get(result.chunk_id, 0) + rrf_score
            chunk_map[result.chunk_id] = result
            result.bm25_score = result.score
        
        # Process embedding results
        for rank, result in enumerate(embedding_results):
            rrf_score = 1.0 / (k + rank + 1)
            
            if result.chunk_id in fusion_scores:
                # Update existing result
                fusion_scores[result.chunk_id] += rrf_score
                chunk_map[result.chunk_id].embedding_score = result.score
            else:
                # New result from embeddings only
                fusion_scores[result.chunk_id] = rrf_score
                chunk_map[result.chunk_id] = result
                result.embedding_score = result.score
        
        # Create final results sorted by fusion score
        final_results = []
        for chunk_id, fusion_score in sorted(fusion_scores.items(), 
                                            key=lambda x: x[1], 
                                            reverse=True)[:top_k]:
            result = chunk_map[chunk_id]
            result.hybrid_score = fusion_score
            result.score = fusion_score  # Use fusion score as main score
            result.retrieval_method = "hybrid"
            final_results.append(result)
        
        return final_results
    
    def compare_retrieval_methods(self, 
                                 query: str,
                                 top_k: int = 20) -> Dict[str, Any]:
        """
        Compare contextual vs non-contextual retrieval.
        
        Educational Note:
        This method demonstrates the improvement that contextual
        retrieval provides across different search methods.
        It's useful for evaluation and understanding when context helps most.
        """
        logger.info(f"Comparing retrieval methods for: {query[:100]}...")
        
        comparison_results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "top_k": top_k,
            "methods": {}
        }
        
        # Test each combination
        test_configs = [
            ("contextual_hybrid", True, "hybrid"),
            ("contextual_bm25", True, "bm25"),
            ("contextual_embedding", True, "embedding"),
            ("non_contextual_hybrid", False, "hybrid"),
            ("non_contextual_bm25", False, "bm25"),
            ("non_contextual_embedding", False, "embedding")
        ]
        
        for name, use_contextual, method in test_configs:
            # Temporarily set mode
            original_contextual = self.use_contextual
            self.use_contextual = use_contextual
            
            # Perform search
            start_time = time.time()
            results = self.contextual_search(query, method, top_k)
            elapsed = time.time() - start_time
            
            # Store results
            comparison_results["methods"][name] = {
                "results": [r.to_dict() for r in results[:5]],  # Top 5 for readability
                "total_results": len(results),
                "retrieval_time": elapsed,
                "avg_score": np.mean([r.score for r in results]) if results else 0,
                "max_score": max([r.score for r in results]) if results else 0
            }
            
            # Restore mode
            self.use_contextual = original_contextual
        
        # Add analysis
        comparison_results["analysis"] = self._analyze_comparison(comparison_results)
        
        # Update stats
        self.search_stats["comparison_searches"] += 1
        
        return comparison_results
    
    def _analyze_comparison(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze comparison results to highlight improvements"""
        analysis = {
            "contextual_improvement": {},
            "method_comparison": {},
            "recommendations": []
        }
        
        # Compare contextual vs non-contextual for each method
        for method in ["hybrid", "bm25", "embedding"]:
            contextual_key = f"contextual_{method}"
            non_contextual_key = f"non_contextual_{method}"
            
            if contextual_key in results["methods"] and non_contextual_key in results["methods"]:
                contextual = results["methods"][contextual_key]
                non_contextual = results["methods"][non_contextual_key]
                
                # Calculate improvement
                score_improvement = (
                    (contextual["avg_score"] - non_contextual["avg_score"]) 
                    / non_contextual["avg_score"] * 100 
                    if non_contextual["avg_score"] > 0 else 0
                )
                
                analysis["contextual_improvement"][method] = {
                    "score_improvement_pct": round(score_improvement, 2),
                    "contextual_avg_score": round(contextual["avg_score"], 4),
                    "non_contextual_avg_score": round(non_contextual["avg_score"], 4)
                }
        
        # Find best performing method
        best_method = max(
            results["methods"].items(),
            key=lambda x: x[1]["avg_score"]
        )
        analysis["best_method"] = best_method[0]
        
        # Generate recommendations
        if "hybrid" in analysis["contextual_improvement"]:
            if analysis["contextual_improvement"]["hybrid"]["score_improvement_pct"] > 10:
                analysis["recommendations"].append(
                    "Contextual retrieval shows significant improvement (>10%). "
                    "Consider using it for production."
                )
            
            if analysis["contextual_improvement"]["bm25"]["score_improvement_pct"] > \
               analysis["contextual_improvement"]["embedding"]["score_improvement_pct"]:
                analysis["recommendations"].append(
                    "Contextual enhancement helps BM25 more than embeddings. "
                    "The query might contain specific terms that benefit from context."
                )
        
        return analysis
    
    def _save_indexes(self):
        """Save BM25 indexes to disk"""
        try:
            # Save BM25 indexes
            if self.bm25_contextual_index:
                with open(self.index_dir / "bm25_contextual.pkl", "wb") as f:
                    pickle.dump({
                        "index": self.bm25_contextual_index,
                        "corpus": self.bm25_contextual_corpus
                    }, f)
            
            if self.bm25_index:
                with open(self.index_dir / "bm25_non_contextual.pkl", "wb") as f:
                    pickle.dump({
                        "index": self.bm25_index,
                        "corpus": self.bm25_corpus
                    }, f)
            
            # Save chunk stores
            with open(self.index_dir / "chunk_stores.json", "w") as f:
                json.dump({
                    "contextual": {k: v.to_dict() for k, v in self.contextual_chunk_store.items()},
                    "non_contextual": {k: v.to_dict() for k, v in self.chunk_store.items()}
                }, f, indent=2)
            
            logger.info("Indexes saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving indexes: {e}")
    
    def _load_indexes(self):
        """Load BM25 indexes from disk"""
        try:
            # Load BM25 indexes
            contextual_path = self.index_dir / "bm25_contextual.pkl"
            if contextual_path.exists():
                with open(contextual_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25_contextual_index = data["index"]
                    self.bm25_contextual_corpus = data["corpus"]
                logger.info("Loaded contextual BM25 index")
            
            non_contextual_path = self.index_dir / "bm25_non_contextual.pkl"
            if non_contextual_path.exists():
                with open(non_contextual_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25_index = data["index"]
                    self.bm25_corpus = data["corpus"]
                logger.info("Loaded non-contextual BM25 index")
            
            # Load chunk stores
            stores_path = self.index_dir / "chunk_stores.json"
            if stores_path.exists():
                with open(stores_path, "r") as f:
                    data = json.load(f)
                    
                    # Reconstruct contextual chunks
                    for chunk_id, chunk_dict in data.get("contextual", {}).items():
                        self.contextual_chunk_store[chunk_id] = ContextualChunk(
                            chunk_id=chunk_dict["chunk_id"],
                            doc_id=chunk_dict["doc_id"],
                            text=chunk_dict["text"],
                            context=chunk_dict["context"],
                            contextualized_text=chunk_dict["contextualized_text"],
                            chunk_index=chunk_dict["chunk_index"],
                            char_count=chunk_dict["char_count"],
                            context_tokens=chunk_dict.get("context_tokens", 0),
                            generation_time=chunk_dict.get("generation_time", 0),
                            metadata=chunk_dict.get("metadata", {})
                        )
                    
                    # Reconstruct non-contextual chunks
                    for chunk_id, chunk_dict in data.get("non_contextual", {}).items():
                        self.chunk_store[chunk_id] = ContextualChunk(
                            chunk_id=chunk_dict["chunk_id"],
                            doc_id=chunk_dict["doc_id"],
                            text=chunk_dict["text"],
                            context="",
                            contextualized_text=chunk_dict["text"],
                            chunk_index=chunk_dict["chunk_index"],
                            char_count=chunk_dict["char_count"],
                            metadata=chunk_dict.get("metadata", {})
                        )
                    
                logger.info(f"Loaded {len(self.contextual_chunk_store)} contextual chunks")
                logger.info(f"Loaded {len(self.chunk_store)} non-contextual chunks")
                
        except Exception as e:
            logger.info(f"No existing indexes found or error loading: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            "search_stats": self.search_stats,
            "index_stats": {
                "contextual_chunks": len(self.contextual_chunk_store),
                "non_contextual_chunks": len(self.chunk_store),
                "bm25_contextual_size": len(self.bm25_contextual_corpus) if self.bm25_contextual_corpus else 0,
                "bm25_non_contextual_size": len(self.bm25_corpus) if self.bm25_corpus else 0
            }
        }
        return stats
