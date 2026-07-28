"""Vector index implementations using ANNOY and HNSW."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional
import numpy as np
import annoy
import hnswlib
import time
from logger import VectorSearchLogger


class VectorIndex(ABC):
    """Abstract base class for vector indexes."""
    
    @abstractmethod
    def add_item(self, doc_id: str, vector: np.ndarray) -> None:
        """Add an item to the index."""
        pass
    
    @abstractmethod
    def delete_item(self, doc_id: str) -> bool:
        """Delete an item from the index."""
        pass
    
    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[List[str], List[float]]:
        """Search for top-k similar items."""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """Get the current number of items in the index."""
        pass
    
    @abstractmethod
    def rebuild_index(self) -> None:
        """Rebuild the index if necessary."""
        pass


class AnnoyIndex(VectorIndex):
    """ANNOY-based vector index implementation."""
    
    def __init__(self, dimension: int, n_trees: int = 50, metric: str = "angular", 
                 logger: Optional[VectorSearchLogger] = None):
        """
        Initialize ANNOY index.
        
        Args:
            dimension: Dimension of vectors
            n_trees: Number of trees for ANNOY (affects precision/speed tradeoff)
            metric: Distance metric ('angular', 'euclidean', 'manhattan', 'hamming', 'dot')
            logger: Logger instance for educational output
        """
        self.dimension = dimension
        self.n_trees = n_trees
        self.metric = metric
        self.logger = logger
        
        # Create index
        self.index = annoy.AnnoyIndex(dimension, metric)
        
        # Mapping between internal indices and document IDs
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.vectors_cache: Dict[int, np.ndarray] = {}
        self.next_index = 0
        self.is_built = False
        
        if self.logger:
            self.logger.logger.info(f"📚 Initialized ANNOY index")
            self.logger.logger.debug(f"  - Dimension: {dimension}")
            self.logger.logger.debug(f"  - Number of trees: {n_trees}")
            self.logger.logger.debug(f"  - Metric: {metric}")
    
    def add_item(self, doc_id: str, vector: np.ndarray) -> None:
        """Add an item to the ANNOY index."""
        start_time = time.time()
        
        if doc_id in self.id_to_index:
            if self.logger:
                self.logger.logger.warning(f"Document {doc_id} already exists in index, updating...")
            # Remove old entry
            old_index = self.id_to_index[doc_id]
            del self.index_to_id[old_index]
            del self.vectors_cache[old_index]
        
        # Cache the vector only. ANNOY refuses new items once build() has run,
        # so the underlying index is (re)created from vectors_cache in
        # rebuild_index() instead of being mutated in place here.
        current_index = self.next_index

        # Update mappings
        self.id_to_index[doc_id] = current_index
        self.index_to_id[current_index] = doc_id
        self.vectors_cache[current_index] = vector.copy()
        self.next_index += 1
        
        # Mark index as needing rebuild
        self.is_built = False
        
        if self.logger:
            time_taken = time.time() - start_time
            self.logger.logger.debug(f"✅ Added document to ANNOY index in {time_taken:.4f}s")
            self.logger.logger.debug(f"  - Document ID: {doc_id}")
            self.logger.logger.debug(f"  - Internal index: {current_index}")
            self.logger.logger.debug(f"  - Index needs rebuild: True")
    
    def delete_item(self, doc_id: str) -> bool:
        """
        Delete an item from the index.
        Note: ANNOY doesn't support deletion, so we need to rebuild without the item.
        """
        if doc_id not in self.id_to_index:
            if self.logger:
                self.logger.logger.warning(f"Document {doc_id} not found in index")
            return False
        
        if self.logger:
            self.logger.logger.info(f"🗑️  Deleting from ANNOY index (requires rebuild)")
        
        # Remove from mappings
        old_index = self.id_to_index[doc_id]
        del self.id_to_index[doc_id]
        del self.index_to_id[old_index]
        del self.vectors_cache[old_index]
        
        # Rebuild index without the deleted item
        self._rebuild_without_deleted()
        
        if self.logger:
            self.logger.logger.debug(f"✅ Document {doc_id} deleted and index rebuilt")
        
        return True
    
    def _rebuild_without_deleted(self):
        """Rebuild the index without deleted items."""
        start_time = time.time()
        
        # Create new index
        new_index = annoy.AnnoyIndex(self.dimension, self.metric)
        
        # Create new mappings
        new_id_to_index = {}
        new_index_to_id = {}
        new_vectors_cache = {}
        
        # Add all remaining items to new index
        new_idx = 0
        for old_idx, doc_id in self.index_to_id.items():
            if old_idx in self.vectors_cache:
                vector = self.vectors_cache[old_idx]
                new_index.add_item(new_idx, vector.tolist())
                new_id_to_index[doc_id] = new_idx
                new_index_to_id[new_idx] = doc_id
                new_vectors_cache[new_idx] = vector
                new_idx += 1
        
        # Build the new index
        new_index.build(self.n_trees)
        
        # Replace old index with new one
        self.index = new_index
        self.id_to_index = new_id_to_index
        self.index_to_id = new_index_to_id
        self.vectors_cache = new_vectors_cache
        self.next_index = new_idx
        self.is_built = True
        
        if self.logger:
            time_taken = time.time() - start_time
            self.logger.logger.debug(f"  Rebuild completed in {time_taken:.4f}s")
            self.logger.logger.debug(f"  New index size: {len(self.id_to_index)} documents")
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[List[str], List[float]]:
        """Search for top-k similar items in the ANNOY index."""
        # Build index if needed
        if not self.is_built:
            self.rebuild_index()
        
        start_time = time.time()
        
        # Ensure we don't request more items than we have
        actual_k = min(top_k, len(self.index_to_id))
        
        if actual_k == 0:
            if self.logger:
                self.logger.logger.warning("Index is empty, returning no results")
            return [], []
        
        # Search in index
        indices, distances = self.index.get_nns_by_vector(
            query_vector.tolist(), actual_k, include_distances=True
        )
        
        # Convert indices to document IDs
        doc_ids = [self.index_to_id[idx] for idx in indices if idx in self.index_to_id]
        valid_distances = distances[:len(doc_ids)]
        
        if self.logger:
            time_taken = time.time() - start_time
            self.logger.logger.debug(f"⚡ ANNOY search completed in {time_taken:.4f}s")
            self.logger.logger.debug(f"  Retrieved {len(doc_ids)} results")
        
        return doc_ids, valid_distances
    
    def get_size(self) -> int:
        """Get the current number of items in the index."""
        return len(self.id_to_index)
    
    def rebuild_index(self) -> None:
        """Build/rebuild the ANNOY index."""
        if self.is_built:
            if self.logger:
                self.logger.logger.debug("Index already built, skipping rebuild")
            return

        start_time = time.time()

        if self.logger:
            self.logger.logger.info(f"🏗️  Building ANNOY index with {self.n_trees} trees")

        # ANNOY can neither accept items after a build nor be built twice, so
        # always construct a fresh index from the cached vectors.
        new_index = annoy.AnnoyIndex(self.dimension, self.metric)
        for internal_index, vector in self.vectors_cache.items():
            new_index.add_item(internal_index, vector.tolist())
        new_index.build(self.n_trees)
        self.index = new_index
        self.is_built = True
        
        if self.logger:
            time_taken = time.time() - start_time
            self.logger.logger.debug(f"✅ Index built in {time_taken:.4f}s")


class HNSWIndex(VectorIndex):
    """HNSW-based vector index implementation."""
    
    def __init__(self, dimension: int, max_elements: int = 100000, 
                 ef_construction: int = 200, M: int = 32, ef_search: int = 100,
                 space: str = "cosine", logger: Optional[VectorSearchLogger] = None):
        """
        Initialize HNSW index.
        
        Args:
            dimension: Dimension of vectors
            max_elements: Maximum number of elements
            ef_construction: Size of the dynamic list (affects build time/accuracy)
            M: Number of bi-directional links (affects memory/accuracy)
            ef_search: Size of the dynamic list for search (affects search time/accuracy)
            space: Distance metric ('l2', 'ip', 'cosine')
            logger: Logger instance for educational output
        """
        self.dimension = dimension
        self.max_elements = max_elements
        self.ef_construction = ef_construction
        self.M = M
        self.ef_search = ef_search
        self.space = space
        self.logger = logger
        
        # Create index
        self.index = hnswlib.Index(space=space, dim=dimension)
        self.index.init_index(max_elements=max_elements, ef_construction=ef_construction, M=M)
        self.index.set_ef(ef_search)
        
        # Mapping between document IDs and internal labels
        self.id_to_label: Dict[str, int] = {}
        self.label_to_id: Dict[int, str] = {}
        self.available_labels: List[int] = []
        self.next_label = 0
        
        if self.logger:
            self.logger.logger.info(f"📚 Initialized HNSW index")
            self.logger.logger.debug(f"  - Dimension: {dimension}")
            self.logger.logger.debug(f"  - Max elements: {max_elements}")
            self.logger.logger.debug(f"  - ef_construction: {ef_construction}")
            self.logger.logger.debug(f"  - M: {M}")
            self.logger.logger.debug(f"  - ef_search: {ef_search}")
            self.logger.logger.debug(f"  - Space: {space}")
    
    def add_item(self, doc_id: str, vector: np.ndarray) -> None:
        """Add an item to the HNSW index."""
        start_time = time.time()
        
        # Check if document already exists
        if doc_id in self.id_to_label:
            if self.logger:
                self.logger.logger.warning(f"Document {doc_id} already exists, updating...")
            # Remove old entry first
            self.delete_item(doc_id)
        
        # Get a label for this document
        if self.available_labels:
            label = self.available_labels.pop()
        else:
            label = self.next_label
            self.next_label += 1
        
        # Add to index
        self.index.add_items(vector.reshape(1, -1), np.array([label]))
        
        # Update mappings
        self.id_to_label[doc_id] = label
        self.label_to_id[label] = doc_id
        
        if self.logger:
            time_taken = time.time() - start_time
            self.logger.logger.debug(f"✅ Added document to HNSW index in {time_taken:.4f}s")
            self.logger.logger.debug(f"  - Document ID: {doc_id}")
            self.logger.logger.debug(f"  - Internal label: {label}")
            self.logger.logger.debug(f"  - Current index size: {self.index.get_current_count()}")
    
    def delete_item(self, doc_id: str) -> bool:
        """Delete an item from the HNSW index."""
        if doc_id not in self.id_to_label:
            if self.logger:
                self.logger.logger.warning(f"Document {doc_id} not found in index")
            return False
        
        start_time = time.time()
        
        # Get label and mark for deletion
        label = self.id_to_label[doc_id]
        
        try:
            # Mark as deleted in HNSW (soft delete)
            self.index.mark_deleted(label)
            
            # Update mappings
            del self.id_to_label[doc_id]
            del self.label_to_id[label]
            
            # Add label back to available labels for reuse
            self.available_labels.append(label)
            
            if self.logger:
                time_taken = time.time() - start_time
                self.logger.logger.debug(f"✅ Deleted document from HNSW index in {time_taken:.4f}s")
                self.logger.logger.debug(f"  - Document ID: {doc_id}")
                self.logger.logger.debug(f"  - Internal label: {label} (marked for reuse)")
                
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.logger.error(f"Error deleting document: {e}")
            return False
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[List[str], List[float]]:
        """Search for top-k similar items in the HNSW index."""
        start_time = time.time()
        
        # Ensure we don't request more items than we have
        actual_k = min(top_k, len(self.label_to_id))
        
        if actual_k == 0:
            if self.logger:
                self.logger.logger.warning("Index is empty, returning no results")
            return [], []
        
        # Search in index
        labels, distances = self.index.knn_query(query_vector.reshape(1, -1), k=actual_k)
        
        # Convert labels to document IDs
        doc_ids = []
        valid_distances = []
        for label, distance in zip(labels[0], distances[0]):
            if label in self.label_to_id:
                doc_ids.append(self.label_to_id[label])
                valid_distances.append(float(distance))
        
        if self.logger:
            time_taken = time.time() - start_time
            self.logger.logger.debug(f"⚡ HNSW search completed in {time_taken:.4f}s")
            self.logger.logger.debug(f"  Retrieved {len(doc_ids)} results")
            self.logger.logger.debug(f"  Search ef parameter: {self.ef_search}")
        
        return doc_ids, valid_distances
    
    def get_size(self) -> int:
        """Get the current number of items in the index."""
        return len(self.id_to_label)
    
    def rebuild_index(self) -> None:
        """HNSW doesn't require explicit rebuild."""
        if self.logger:
            self.logger.logger.debug("HNSW index doesn't require explicit rebuild")
        pass
