"""Tools for knowledge base interaction"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from config import KnowledgeBaseConfig, KnowledgeBaseType


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result from knowledge base"""
    doc_id: str
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": self.score,
            "metadata": self.metadata or {}
        }


class KnowledgeBaseTools:
    """Tools for interacting with knowledge base"""
    
    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        self.document_store = {}  # In-memory store for documents
        self._offline_retriever = None  # Lazily built in-process BM25 index

        # Load document store if exists
        try:
            with open(config.document_store_path, 'r', encoding='utf-8') as f:
                self.document_store = json.load(f)
        except FileNotFoundError:
            logger.info("No existing document store found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading document store: {e}")
    
    def save_document_store(self):
        """Save document store to disk"""
        try:
            with open(self.config.document_store_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_store, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving document store: {e}")
    
    def knowledge_base_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the knowledge base with a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            List of matching document chunks with scores
        """
        try:
            if self.config.type == KnowledgeBaseType.OFFLINE:
                return self._search_offline(query)
            elif self.config.type == KnowledgeBaseType.LOCAL:
                return self._search_local(query)
            elif self.config.type == KnowledgeBaseType.DIFY:
                return self._search_dify(query)
            elif self.config.type == KnowledgeBaseType.RAPTOR:
                return self._search_raptor(query)
            elif self.config.type == KnowledgeBaseType.GRAPHRAG:
                return self._search_graphrag(query)
            else:
                raise ValueError(f"Unsupported knowledge base type: {self.config.type}")
        except Exception as e:
            logger.error(f"Error in knowledge base search: {e}")
            return []
    
    def _get_offline_retriever(self):
        """Lazily build the in-process BM25 retriever over the local corpus."""
        if self._offline_retriever is None:
            from offline_retriever import OfflineRetriever
            self._offline_retriever = OfflineRetriever(self.config.offline_corpus_path)
        return self._offline_retriever

    def _search_offline(self, query: str) -> List[Dict[str, Any]]:
        """Search the in-process BM25 index (no server, no API key required)."""
        retriever = self._get_offline_retriever()
        results = retriever.search(query, self.config.offline_top_k)
        logger.info(f"Offline BM25 search returned {len(results)} results")
        return results

    def _search_local(self, query: str) -> List[Dict[str, Any]]:
        """Search using local retrieval pipeline"""
        try:
            response = requests.post(
                f"{self.config.local_base_url}/search",
                json={
                    "query": query,
                    "mode": "hybrid",
                    "top_k": self.config.local_top_k,
                    "rerank": True
                }, timeout=30
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            # The retrieval pipeline returns results in different keys based on mode
            # For hybrid mode, we want the reranked_results
            search_results = data.get("reranked_results", [])
            
            # If no reranked results, fall back to dense or sparse results
            if not search_results:
                search_results = data.get("dense_results", [])
            if not search_results:
                search_results = data.get("sparse_results", [])
                
            for item in search_results:
                # Extract doc_id and chunk_id from the result
                doc_id = item.get("doc_id", "")
                chunk_id = item.get("chunk_id", f"{doc_id}_chunk_{len(results)}")
                
                # Get the text field and score based on result type
                text = item.get("text", "")
                score = item.get("rerank_score", item.get("score", 0.0))
                
                result = SearchResult(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=text,
                    score=score,
                    metadata=item.get("metadata", {})
                )
                results.append(result.to_dict())
            
            logger.info(f"Local search returned {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to local retrieval pipeline: {e}")
            return []
    
    def _search_dify(self, query: str) -> List[Dict[str, Any]]:
        """Search using Dify API"""
        if not self.config.dify_api_key:
            logger.error("Dify API key not configured")
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "top_k": self.config.dify_top_k
            }
            
            if self.config.dify_dataset_id:
                payload["dataset_id"] = self.config.dify_dataset_id
            
            response = requests.post(
                f"{self.config.dify_base_url}/datasets/search",
                headers=headers,
                json=payload, timeout=30
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            for item in data.get("data", {}).get("records", []):
                doc_id = item.get("document_id", "")
                chunk_id = item.get("segment_id", f"{doc_id}_chunk_{len(results)}")
                
                result = SearchResult(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=item.get("content", ""),
                    score=item.get("score", 0.0),
                    metadata=item.get("metadata", {})
                )
                results.append(result.to_dict())
            
            logger.info(f"Dify search returned {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Dify API: {e}")
            return []
    
    def _search_raptor(self, query: str) -> List[Dict[str, Any]]:
        """Search using RAPTOR tree-based index"""
        try:
            response = requests.post(
                f"{self.config.raptor_base_url}/query",
                json={
                    "query": query,
                    "index_type": "raptor",
                    "top_k": self.config.raptor_top_k
                }, timeout=30
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            for i, item in enumerate(data.get("results", [])):
                # RAPTOR returns tree nodes with levels and summaries
                doc_id = item.get("node_id", f"raptor_node_{i}")
                chunk_id = f"{doc_id}_level_{item.get('level', 0)}"
                
                # Use summary if available, otherwise use text
                text_content = item.get("summary", item.get("text", ""))
                
                result = SearchResult(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=text_content,
                    score=item.get("score", 0.0),
                    metadata={
                        "level": item.get("level", 0),
                        "source": "raptor"
                    }
                )
                results.append(result.to_dict())
            
            logger.info(f"RAPTOR search returned {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to RAPTOR index: {e}")
            return []
    
    def _search_graphrag(self, query: str) -> List[Dict[str, Any]]:
        """Search using GraphRAG knowledge graph index"""
        try:
            response = requests.post(
                f"{self.config.graphrag_base_url}/query",
                json={
                    "query": query,
                    "index_type": "graphrag",
                    "top_k": self.config.graphrag_top_k,
                    "search_type": self.config.graphrag_search_type
                }, timeout=30
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            for i, item in enumerate(data.get("results", [])):
                # GraphRAG returns entities or communities
                result_type = item.get("type", "unknown")
                
                if result_type == "entity":
                    doc_id = item.get("id", f"entity_{i}")
                    chunk_id = f"{doc_id}_{item.get('entity_type', 'unknown')}"
                    text_content = f"{item.get('name', '')}. {item.get('description', '')}"
                    metadata = {
                        "type": "entity",
                        "entity_type": item.get("entity_type"),
                        "related_entities": item.get("related_entities", [])
                    }
                else:  # community
                    doc_id = item.get("id", f"community_{i}")
                    chunk_id = f"{doc_id}_level_{item.get('level', 0)}"
                    text_content = item.get("summary", "")
                    metadata = {
                        "type": "community",
                        "level": item.get("level", 0),
                        "entity_count": item.get("entity_count", 0),
                        "sample_entities": item.get("sample_entities", [])
                    }
                
                result = SearchResult(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=text_content,
                    score=item.get("score", 0.0),
                    metadata={**metadata, "source": "graphrag"}
                )
                results.append(result.to_dict())
            
            logger.info(f"GraphRAG search returned {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to GraphRAG index: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve the entire document from the knowledge base.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Full document content and metadata
        """
        try:
            # First check local document store
            if doc_id in self.document_store:
                return self.document_store[doc_id]
            
            if self.config.type == KnowledgeBaseType.OFFLINE:
                return self._get_offline_retriever().get_document(doc_id)
            elif self.config.type == KnowledgeBaseType.LOCAL:
                return self._get_document_local(doc_id)
            elif self.config.type == KnowledgeBaseType.DIFY:
                return self._get_document_dify(doc_id)
            elif self.config.type == KnowledgeBaseType.RAPTOR:
                return self._get_document_raptor(doc_id)
            elif self.config.type == KnowledgeBaseType.GRAPHRAG:
                return self._get_document_graphrag(doc_id)
            else:
                raise ValueError(f"Unsupported knowledge base type: {self.config.type}")
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return {"error": f"Document {doc_id} not found"}
    
    def _get_document_local(self, doc_id: str) -> Dict[str, Any]:
        """Get document from local retrieval pipeline"""
        try:
            response = requests.get(
                f"{self.config.local_base_url}/documents/{doc_id}", timeout=30
            )
            
            if response.status_code == 404:
                return {"error": f"Document {doc_id} not found"}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting document from local pipeline: {e}")
            return {"error": str(e)}
    
    def _get_document_dify(self, doc_id: str) -> Dict[str, Any]:
        """Get document from Dify"""
        if not self.config.dify_api_key:
            return {"error": "Dify API key not configured"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.config.dify_base_url}/documents/{doc_id}",
                headers=headers, timeout=30
            )
            
            if response.status_code == 404:
                return {"error": f"Document {doc_id} not found"}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting document from Dify: {e}")
            return {"error": str(e)}
    
    def _get_document_raptor(self, doc_id: str) -> Dict[str, Any]:
        """Get document/node from RAPTOR index"""
        try:
            # For RAPTOR, we perform a targeted search for the specific node
            response = requests.post(
                f"{self.config.raptor_base_url}/query",
                json={
                    "query": f"node:{doc_id}",  # Specific node query
                    "index_type": "raptor",
                    "top_k": 1
                }, timeout=30
            )
            
            if response.status_code == 404:
                return {"error": f"Document {doc_id} not found"}
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return {
                    "doc_id": doc_id,
                    "content": result.get("text", ""),
                    "metadata": {
                        "summary": result.get("summary", ""),
                        "level": result.get("level", 0),
                        "source": "raptor"
                    }
                }
            
            return {"error": f"Document {doc_id} not found"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting document from RAPTOR: {e}")
            return {"error": str(e)}
    
    def _get_document_graphrag(self, doc_id: str) -> Dict[str, Any]:
        """Get entity or community from GraphRAG index"""
        try:
            # For GraphRAG, we perform a targeted search for the specific entity/community
            response = requests.post(
                f"{self.config.graphrag_base_url}/query",
                json={
                    "query": f"id:{doc_id}",  # Specific ID query
                    "index_type": "graphrag",
                    "top_k": 1,
                    "search_type": "hybrid"
                }, timeout=30
            )
            
            if response.status_code == 404:
                return {"error": f"Document {doc_id} not found"}
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                content = ""
                metadata = {"source": "graphrag"}
                
                if result.get("type") == "entity":
                    content = f"{result.get('name', '')}\n\n{result.get('description', '')}"
                    metadata.update({
                        "type": "entity",
                        "entity_type": result.get("entity_type"),
                        "related_entities": result.get("related_entities", [])
                    })
                else:  # community
                    content = result.get("summary", "")
                    metadata.update({
                        "type": "community",
                        "level": result.get("level", 0),
                        "entity_count": result.get("entity_count", 0),
                        "sample_entities": result.get("sample_entities", [])
                    })
                
                return {
                    "doc_id": doc_id,
                    "content": content,
                    "metadata": metadata
                }
            
            return {"error": f"Document {doc_id} not found"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting document from GraphRAG: {e}")
            return {"error": str(e)}
    
    def add_document(self, doc_id: str, content: str, metadata: Optional[Dict] = None):
        """Add a document to the local store"""
        self.document_store[doc_id] = {
            "doc_id": doc_id,
            "content": content,
            "metadata": metadata or {}
        }
        self.save_document_store()


# Tool function definitions for agent
def get_tool_definitions() -> List[Dict[str, Any]]:
    """Get OpenAI-format tool definitions"""
    return [
        {
            "type": "function",
            "function": {
                "name": "knowledge_base_search",
                "description": "Search the knowledge base for relevant information using a natural language query. Returns top-matching document chunks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query to find relevant information"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "get_document",
                "description": "Retrieve the complete content of a specific document from the knowledge base using its document ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "The unique identifier of the document to retrieve"
                        }
                    },
                    "required": ["doc_id"]
                }
            }
        }
    ]
