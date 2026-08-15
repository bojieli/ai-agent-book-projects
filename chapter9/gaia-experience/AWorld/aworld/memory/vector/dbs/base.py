from abc import ABC, abstractmethod
from typing import Optional, List

from aworld.memory.embeddings.base import EmbeddingsResults, EmbeddingsResult


class VectorDB(ABC):
    """Abstract base class for vector databases.
    
    This class defines the standard interface that all vector database implementations
    must follow. It provides methods for storing, retrieving, and searching vectors.
    """
    
    @abstractmethod
    def has_collection(self, collection_name: str) -> bool:
        """Check if a collection exists.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            bool: True if collection exists, False otherwise
        """
        pass
        
    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Delete a collection.
        
        Args:
            collection_name (str): Name of the collection to delete
        """
        pass
        
    @abstractmethod
    def search(
        self, collection_name: str, vectors: list[list[float | int]], filter: dict, threshold: float,  limit: int
    ) -> Optional[EmbeddingsResults]:
        """Search for nearest neighbors based on vector similarity.
        
        Args:
            collection_name (str): Name of the collection
            vectors (list[list[float | int]]): Query vectors
            filter (dict): Filter conditions
            threshold (float): Threshold for similarity search
            limit (int): Maximum number of results to return
            
        Returns:
            Optional[EmbeddingsResults]: Search results or None if collection doesn't exist
        """
        pass
        
    @abstractmethod
    def query(
        self, collection_name: str, filter: dict, limit: Optional[int] = None
    ) -> Optional[EmbeddingsResults]:
        """Query items from the collection based on filter.
        
        Args:
            collection_name (str): Name of the collection
            filter (dict): Filter conditions
            limit (Optional[int]): Maximum number of results to return
            
        Returns:
            Optional[EmbeddingsResults]: Query results or None if collection doesn't exist
        """
        pass
        
    @abstractmethod
    def get(self, collection_name: str) -> Optional[EmbeddingsResults]:
        """Get all items in the collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Optional[EmbeddingsResults]: All items in the collection or None if collection doesn't exist
        """
        pass
        
    @abstractmethod
    def insert(self, collection_name: str, items: list[EmbeddingsResult]):
        """Insert items into the collection.
        
        Args:
            collection_name (str): Name of the collection
            items (list[EmbeddingsResult]): List of embedding results to insert
        """
        pass
        
    @abstractmethod
    def upsert(self, collection_name: str, items: list[EmbeddingsResult]):
        """Update or insert items in the collection.
        
        Args:
            collection_name (str): Name of the collection
            items (list[EmbeddingsResult]): List of embedding results to upsert
        """
        pass
        
    @abstractmethod
    def delete(
        self,
        collection_name: str,
        ids: Optional[list[str]] = None,
        filter: Optional[dict] = None,
    ):
        """Delete items from the collection.
        
        Args:
            collection_name (str): Name of the collection
            ids (Optional[list[str]]): List of item IDs to delete
            filter (Optional[dict]): Filter conditions for items to delete
        """
        pass
        
    @abstractmethod
    def reset(self):
        """Reset the database.
        
        This will delete all collections and item entries.
        """
        pass 