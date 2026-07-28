"""Reranker module using BGE-Reranker-v2 model."""

import torch
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from FlagEmbedding import FlagReranker
import logging
import time
import numpy as np
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from tqdm import tqdm

logger = logging.getLogger(__name__)

@dataclass
class RerankResult:
    """Result from reranking."""
    doc_id: str
    rerank_score: float
    original_dense_score: Optional[float] = None
    original_sparse_score: Optional[float] = None
    original_dense_rank: Optional[int] = None
    original_sparse_rank: Optional[int] = None
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None

class Reranker:
    """Reranker using BGE-Reranker-v2 model."""
    
    def _ensure_model_downloaded(self, model_name: str):
        """Check if model is cached and download if needed with progress.
        
        Args:
            model_name: HuggingFace model name
        """
        # Check cache directory
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        model_id = model_name.replace("/", "--")
        model_cache_path = cache_dir / f"models--{model_id}"
        
        if model_cache_path.exists() and any(model_cache_path.iterdir()):
            logger.info(f"Model already cached at {model_cache_path}")
            return
        
        logger.info(f"Model not found in cache. Downloading {model_name}...")
        logger.info("This is a one-time download. The model will be cached for future use.")
        
        try:
            # Use huggingface_hub to download with progress
            class DownloadProgressBar:
                def __init__(self):
                    self.pbar = None
                    self.total_size = 0
                    self.downloaded = 0
                
                def __call__(self, chunk_size: int):
                    if self.pbar is None:
                        return
                    self.downloaded += chunk_size
                    self.pbar.update(chunk_size)
                    
            # Download the model with progress tracking
            logger.info("Downloading model files...")
            snapshot_download(
                repo_id=model_name,
                cache_dir=cache_dir,
                resume_download=True,
                local_files_only=False
            )
            logger.info("Model download completed!")
            
        except Exception as e:
            logger.warning(f"Could not pre-download model: {e}")
            logger.info("Model will be downloaded automatically during initialization...")
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", 
                 device: str = None, 
                 use_fp16: bool = True,
                 max_length: int = 512):
        """Initialize the reranker.
        
        Args:
            model_name: HuggingFace model name
            device: Device to use (mps for Mac, cuda for GPU, cpu)
            use_fp16: Use half precision for faster inference
            max_length: Maximum sequence length
        """
        self.model_name = model_name
        
        # Auto-detect device if not specified
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        
        self.device = device
        self.use_fp16 = use_fp16 and device != "cpu"
        self.max_length = max_length
        
        logger.info(f"Initializing reranker with model: {model_name}")
        logger.info(f"Device: {device}, FP16: {self.use_fp16}")
        
        # Check if model needs to be downloaded
        self._ensure_model_downloaded(model_name)
        
        # Initialize the model
        logger.info("Loading reranker model into memory...")
        start_time = time.time()
        self.model = FlagReranker(
            model_name,
            use_fp16=self.use_fp16,
            device=device
        )
        elapsed = time.time() - start_time
        logger.info(f"Reranker initialized successfully in {elapsed:.2f}s")
    
    def rerank(self, 
               query: str, 
               documents: List[Dict[str, Any]], 
               top_k: int = 10,
               return_scores: bool = True) -> List[RerankResult]:
        """Rerank documents for a query.
        
        Args:
            query: The search query
            documents: List of documents with text and metadata
            top_k: Number of top results to return
            return_scores: Whether to return all scores for educational purposes
        
        Returns:
            List of reranked results
        """
        if not documents:
            return []
        
        start_time = time.time()
        logger.info(f"Reranking {len(documents)} documents for query: '{query[:50]}...'")
        
        # Prepare texts for reranking
        texts = []
        doc_info = []
        
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
                
            texts.append(text)
            doc_info.append({
                "doc_id": doc.get("doc_id"),
                "original_dense_score": doc.get("dense_score"),
                "original_sparse_score": doc.get("sparse_score"),
                "original_dense_rank": doc.get("dense_rank"),
                "original_sparse_rank": doc.get("sparse_rank"),
                "text": text,
                "metadata": doc.get("metadata", {})
            })
        
        if not texts:
            logger.warning("No valid texts to rerank")
            return []
        
        # Create query-document pairs
        pairs = [[query, text] for text in texts]
        
        # Get reranking scores
        try:
            scores = self.model.compute_score(pairs, max_length=self.max_length)
            
            # Convert to numpy array if needed
            if not isinstance(scores, np.ndarray):
                scores = np.array(scores)
            
            # Ensure scores is 1D. FlagReranker.compute_score returns a bare
            # float when exactly one pair is scored, which becomes a 0-d array
            # here — atleast_1d keeps the single-candidate case iterable.
            scores = np.atleast_1d(np.asarray(scores).squeeze())

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return []
        
        # Create results with scores
        results = []
        for i, score in enumerate(scores):
            info = doc_info[i]
            
            result = RerankResult(
                doc_id=info["doc_id"],
                rerank_score=float(score),
                original_dense_score=info["original_dense_score"],
                original_sparse_score=info["original_sparse_score"],
                original_dense_rank=info["original_dense_rank"],
                original_sparse_rank=info["original_sparse_rank"],
                text=info["text"] if return_scores else None,
                metadata=info["metadata"],
                debug_info={
                    "rerank_model": self.model_name,
                    "max_length": self.max_length,
                    "device": self.device
                }
            )
            results.append(result)
        
        # Sort by rerank score (descending)
        results.sort(key=lambda x: x.rerank_score, reverse=True)
        
        # Add final ranks
        for i, result in enumerate(results):
            if result.debug_info:
                result.debug_info["final_rank"] = i + 1
        
        elapsed_time = time.time() - start_time
        logger.info(f"Reranking completed in {elapsed_time:.2f}s")
        
        # Log score distribution for educational purposes
        if return_scores and results:
            scores_array = [r.rerank_score for r in results]
            logger.info(f"Rerank score distribution: min={min(scores_array):.3f}, "
                       f"max={max(scores_array):.3f}, mean={np.mean(scores_array):.3f}")
            
            # Log rank changes for top results
            for i, result in enumerate(results[:5]):
                changes = []
                if result.original_dense_rank:
                    dense_change = result.original_dense_rank - (i + 1)
                    changes.append(f"dense: {result.original_dense_rank}→{i+1} ({dense_change:+d})")
                if result.original_sparse_rank:
                    sparse_change = result.original_sparse_rank - (i + 1)
                    changes.append(f"sparse: {result.original_sparse_rank}→{i+1} ({sparse_change:+d})")
                
                if changes:
                    logger.debug(f"Doc {result.doc_id} rank changes: {', '.join(changes)}")
        
        # Return top_k results
        return results[:top_k]
    
    def batch_rerank(self, 
                     queries: List[str], 
                     documents_list: List[List[Dict[str, Any]]], 
                     top_k: int = 10,
                     batch_size: int = 32) -> List[List[RerankResult]]:
        """Rerank multiple queries in batch.
        
        Args:
            queries: List of queries
            documents_list: List of document lists (one per query)
            top_k: Number of top results per query
            batch_size: Batch size for processing
        
        Returns:
            List of reranked results for each query
        """
        all_results = []
        
        for query, documents in zip(queries, documents_list):
            results = self.rerank(query, documents, top_k)
            all_results.append(results)
        
        return all_results
