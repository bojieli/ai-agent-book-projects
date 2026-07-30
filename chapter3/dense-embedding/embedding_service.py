"""Embedding service using BGE-M3 model."""

import time
import numpy as np
from typing import List, Dict, Optional
from FlagEmbedding import BGEM3FlagModel
from logger import VectorSearchLogger, log_execution_time
import logging


class EmbeddingService:
    """Service for generating embeddings using BGE-M3 model."""
    
    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True, 
                 max_seq_length: int = 512, logger: Optional[VectorSearchLogger] = None):
        """
        Initialize the embedding service with BGE-M3 model.
        
        Args:
            model_name: Name of the BGE-M3 model
            use_fp16: Whether to use FP16 for inference
            max_seq_length: Maximum sequence length
            logger: Logger instance for educational output
        """
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.max_seq_length = max_seq_length
        self.logger = logger
        self.std_logger = logging.getLogger("vector_search")
        
        # Initialize the model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the BGE-M3 model."""
        start_time = time.time()
        
        if self.logger:
            self.logger.logger.info(f"🚀 Initializing BGE-M3 model: {self.model_name}")
            self.logger.logger.debug(f"  - Using FP16: {self.use_fp16}")
            self.logger.logger.debug(f"  - Max sequence length: {self.max_seq_length}")
        
        try:
            self.model = BGEM3FlagModel(
                self.model_name, 
                use_fp16=self.use_fp16
            )
            
            # Get embedding dimension by encoding a test sentence
            test_embedding = self.model.encode(["test"])
            if isinstance(test_embedding, dict):
                self.embedding_dim = test_embedding['dense_vecs'].shape[1]
            else:
                self.embedding_dim = test_embedding.shape[1]
            
            load_time = time.time() - start_time
            
            if self.logger:
                self.logger.logger.info(f"✅ Model loaded successfully in {load_time:.2f} seconds")
                self.logger.logger.debug(f"  - Embedding dimension: {self.embedding_dim}")
                self.logger.logger.debug(f"  - Model supports: dense, sparse, and multi-vector retrieval")
                
        except Exception as e:
            if self.logger:
                self.logger.logger.error(f"Failed to load model: {e}")
            raise
    
    @log_execution_time()
    def encode_text(self, text: str, return_sparse: bool = False, 
                   return_colbert: bool = False) -> Dict[str, np.ndarray]:
        """
        Encode a single text into embeddings.
        
        Args:
            text: Input text to encode
            return_sparse: Whether to return sparse embeddings
            return_colbert: Whether to return ColBERT embeddings
        
        Returns:
            Dictionary containing different types of embeddings
        """
        start_time = time.time()
        
        if self.logger:
            self.logger.logger.debug(f"📝 Encoding text (length: {len(text)} chars)")
            self.logger.logger.debug(f"  Text preview: {text[:100]}..." if len(text) > 100 else f"  Text: {text}")
        
        # Encode the text
        embeddings = self.model.encode(
            [text],
            return_dense=True,
            return_sparse=return_sparse,
            return_colbert_vecs=return_colbert
        )
        
        # Extract dense embeddings
        dense_vec = embeddings['dense_vecs'][0]
        
        result = {
            'dense': dense_vec,
            'dimension': len(dense_vec)
        }
        
        # Add sparse embeddings if requested
        if return_sparse and 'lexical_weights' in embeddings:
            result['sparse'] = embeddings['lexical_weights'][0]
            if self.logger:
                num_tokens = len(result['sparse'])
                self.logger.logger.debug(f"  Sparse embedding: {num_tokens} non-zero tokens")
        
        # Add ColBERT embeddings if requested  
        if return_colbert and 'colbert_vecs' in embeddings:
            result['colbert'] = embeddings['colbert_vecs'][0]
            if self.logger:
                colbert_shape = result['colbert'].shape
                self.logger.logger.debug(f"  ColBERT embedding shape: {colbert_shape}")
        
        encoding_time = time.time() - start_time
        
        if self.logger:
            self.logger.logger.debug(f"✅ Encoding completed in {encoding_time:.4f} seconds")
            self.logger.log_embedding_vector(dense_vec, sample_size=10)
        
        return result
    
    @log_execution_time()
    def encode_batch(self, texts: List[str], return_sparse: bool = False, 
                    return_colbert: bool = False) -> Dict[str, np.ndarray]:
        """
        Encode multiple texts into embeddings.
        
        Args:
            texts: List of input texts to encode
            return_sparse: Whether to return sparse embeddings
            return_colbert: Whether to return ColBERT embeddings
        
        Returns:
            Dictionary containing different types of embeddings for all texts
        """
        start_time = time.time()
        
        if self.logger:
            self.logger.logger.info(f"📚 Batch encoding {len(texts)} texts")
            total_chars = sum(len(t) for t in texts)
            self.logger.logger.debug(f"  Total characters: {total_chars}")
            avg_len = total_chars / len(texts) if texts else 0.0
            self.logger.logger.debug(f"  Average text length: {avg_len:.1f} chars")
        
        # Encode all texts
        embeddings = self.model.encode(
            texts,
            return_dense=True,
            return_sparse=return_sparse,
            return_colbert_vecs=return_colbert
        )
        
        result = {
            'dense': embeddings['dense_vecs'],
            'dimension': embeddings['dense_vecs'].shape[1],
            'num_texts': len(texts)
        }
        
        # Add sparse embeddings if requested
        if return_sparse and 'lexical_weights' in embeddings:
            result['sparse'] = embeddings['lexical_weights']
        
        # Add ColBERT embeddings if requested
        if return_colbert and 'colbert_vecs' in embeddings:
            result['colbert'] = embeddings['colbert_vecs']
        
        encoding_time = time.time() - start_time
        
        if self.logger:
            self.logger.logger.info(f"✅ Batch encoding completed in {encoding_time:.4f} seconds")
            avg_time = encoding_time / len(texts) if texts else 0.0
            self.logger.logger.debug(f"  Average time per text: {avg_time:.4f} seconds")
        
        return result
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self.embedding_dim
    
    def compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray, 
                          metric: str = "cosine") -> float:
        """
        Compute similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            metric: Similarity metric ('cosine', 'euclidean', 'dot')
        
        Returns:
            Similarity score
        """
        if metric == "cosine":
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            similarity = dot_product / (norm1 * norm2)
            
        elif metric == "euclidean":
            # Euclidean distance (negative for similarity)
            similarity = -np.linalg.norm(vec1 - vec2)
            
        elif metric == "dot":
            # Dot product
            similarity = np.dot(vec1, vec2)
            
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        if self.logger:
            self.logger.logger.debug(f"  Similarity ({metric}): {similarity:.6f}")
        
        return float(similarity)
