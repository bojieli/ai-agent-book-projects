"""Document store for the retrieval pipeline."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DocumentStore:
    """In-memory document store for educational purposes."""
    
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.metadata_index: Dict[str, List[str]] = {}  # Index by metadata fields
        
    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a document to the store."""
        new_metadata = metadata or {}
        if doc_id in self.documents:
            old_metadata = self.documents[doc_id].get("metadata") or {}
            for key in list(old_metadata.keys()):
                if key not in new_metadata:
                    if key in self.metadata_index and doc_id in self.metadata_index[key]:
                        self.metadata_index[key].remove(doc_id)
                        if not self.metadata_index[key]:
                            del self.metadata_index[key]

        self.documents[doc_id] = {
            "doc_id": doc_id,
            "text": text,
            "metadata": new_metadata,
            "indexed_at": datetime.now().isoformat()
        }
        
        # Update metadata index
        for key in new_metadata:
            if key not in self.metadata_index:
                self.metadata_index[key] = []
            if doc_id not in self.metadata_index[key]:
                self.metadata_index[key].append(doc_id)
                    
        logger.debug(f"Added document {doc_id} to store")
        
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def get_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple documents by IDs."""
        docs = []
        for doc_id in doc_ids:
            doc = self.get_document(doc_id)
            if doc:
                docs.append(doc)
        return docs
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store."""
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            
            # Remove from metadata index
            if doc.get("metadata"):
                for key in doc["metadata"]:
                    if key in self.metadata_index and doc_id in self.metadata_index[key]:
                        self.metadata_index[key].remove(doc_id)
                        if not self.metadata_index[key]:
                            del self.metadata_index[key]
            
            del self.documents[doc_id]
            logger.debug(f"Deleted document {doc_id} from store")
            return True
        return False
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List documents with pagination."""
        doc_ids = list(self.documents.keys())[offset:offset + limit]
        return [self.documents[doc_id] for doc_id in doc_ids]
    
    def clear(self) -> None:
        """Clear all documents."""
        self.documents.clear()
        self.metadata_index.clear()
        logger.info("Cleared all documents from store")
        
    def size(self) -> int:
        """Get the number of documents."""
        return len(self.documents)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "total_documents": self.size(),
            "metadata_fields": list(self.metadata_index.keys()),
            "metadata_distribution": {
                key: len(values) for key, values in self.metadata_index.items()
            }
        }
