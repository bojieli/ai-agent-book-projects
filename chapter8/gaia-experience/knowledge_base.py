"""
Knowledge Base for Experience Retrieval
This module provides indexing and retrieval capabilities for experiences.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import faiss
except ImportError:
    faiss = None
import pickle

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Knowledge base for storing and retrieving experiences using semantic search.
    """
    
    def __init__(
        self,
        index_path: str = "./kb_index",
        model_name: str = "all-MiniLM-L6-v2",
        embedding_dim: int = 384
    ):
        """
        Initialize the knowledge base.
        
        Args:
            index_path: Path to store the index files
            model_name: Name of the sentence transformer model
            embedding_dim: Dimension of the embeddings
        """
        self.index_path = index_path
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        
        if SentenceTransformer is None or faiss is None:
            self.encoder = None
        else:
            try:
                self.encoder = SentenceTransformer(model_name)
                # Derive the real embedding dimension from the loaded model so the
                # FAISS index matches it. A fixed 384 silently breaks any non-384
                # model chosen via --embedding-model / config.yaml (e.g.
                # all-mpnet-base-v2 = 768): index.add() then raises, is swallowed,
                # and every search falls back to keyword-only for the whole KB.
                model_dim = self.encoder.get_sentence_embedding_dimension()
                if model_dim:
                    self.embedding_dim = model_dim
            except Exception as e:
                logger.warning(f"Failed to load SentenceTransformer, falling back to simple search: {e}")
                self.encoder = None
        
        # Initialize FAISS index
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Create index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing index from disk."""
        index_file = os.path.join(self.index_path, "faiss.index")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        meta_file = os.path.join(self.index_path, "metadata.pkl")

        # Documents remain useful for keyword search even when the optional
        # semantic-search dependencies (or the FAISS file) are unavailable.
        # Load them independently so a keyword-only run survives a restart.
        if os.path.exists(docs_file):
            try:
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                if not isinstance(self.documents, list):
                    raise ValueError("Persisted documents must be a list")

                if os.path.exists(meta_file):
                    with open(meta_file, 'rb') as f:
                        self.metadata = pickle.load(f)
                    if not isinstance(self.metadata, list):
                        raise ValueError("Persisted metadata must be a list")
                else:
                    self.metadata = [{}] * len(self.documents)

                # Keep one metadata entry per document and tolerate older or
                # partially-written metadata files.
                self.metadata = [
                    item if isinstance(item, dict) else {}
                    for item in self.metadata[:len(self.documents)]
                ]
                self.metadata.extend(
                    {} for _ in range(len(self.documents) - len(self.metadata))
                )
            except Exception as e:
                logger.error(f"Failed to load persisted documents: {e}")
                self.documents = []
                self.metadata = []

        if not self.encoder:
            logger.info(f"Loaded knowledge base with {len(self.documents)} documents")
            return

        rebuild_reason = None
        if os.path.exists(index_file):
            try:
                self.index = faiss.read_index(index_file)
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")
                rebuild_reason = "FAISS index could not be loaded"
            else:
                if self.index.d != self.embedding_dim:
                    rebuild_reason = (
                        f"FAISS dimension {self.index.d} != model dimension "
                        f"{self.embedding_dim}"
                    )
                elif self.index.ntotal != len(self.documents):
                    rebuild_reason = (
                        f"FAISS row count {self.index.ntotal} != document count "
                        f"{len(self.documents)}"
                    )
        elif self.documents:
            rebuild_reason = "FAISS index is missing"

        if rebuild_reason:
            logger.warning(f"{rebuild_reason}; rebuilding from stored queries")
            self._rebuild_index_from_metadata()
        elif self.index is None:
            self._create_new_index()

        logger.info(f"Loaded knowledge base with {len(self.documents)} documents")
    
    def _create_new_index(self):
        """Create a new empty index."""
        if self.encoder:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        else:
            self.index = None

    def _rebuild_index_from_metadata(self):
        """Rebuild the FAISS index at the current embedding dimension by
        re-encoding the query texts persisted in metadata (used when a loaded
        index was built with a different embedding model). One embedding per
        document, in order, so index rows stay aligned with self.documents."""
        if not self.encoder or faiss is None:
            self.index = None
            return

        self.index = faiss.IndexFlatL2(self.embedding_dim)
        if not self.documents:
            return
        queries = [
            (self.metadata[i].get('query', '') if i < len(self.metadata) else '')
            for i in range(len(self.documents))
        ]
        try:
            embeddings = self.encoder.encode(queries)
            self.index.add(embeddings)
            self._save_index()
            logger.info(f"Rebuilt FAISS index with {self.index.ntotal} embeddings")
        except Exception as e:
            logger.error(f"Failed to rebuild FAISS index: {e}")
    
    def _save_index(self):
        """Save index to disk."""
        try:
            if self.encoder and self.index is not None:
                index_file = os.path.join(self.index_path, "faiss.index")
                faiss.write_index(self.index, index_file)
            
            docs_file = os.path.join(self.index_path, "documents.pkl")
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            meta_file = os.path.join(self.index_path, "metadata.pkl")
            with open(meta_file, 'wb') as f:
                pickle.dump(self.metadata, f)
                
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def index_gaia_validation(self, validation_file: str):
        """
        Index the GAIA validation file for experience retrieval.
        
        Args:
            validation_file: Path to gaia-validation.jsonl
        """
        if not os.path.exists(validation_file):
            logger.error(f"Validation file not found: {validation_file}")
            return
        
        logger.info(f"Indexing GAIA validation data from {validation_file}")
        
        # The index is persisted and reloaded by __init__ (_load_index), so
        # without this every run appends another full copy of the dataset and
        # search() starts returning the same document top_k times.
        existing_ids = {
            doc.get('task_id')
            for doc in self.documents
            if doc.get('source') == 'gaia_validation'
        }
        skipped = 0
        
        try:
            with open(validation_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        
                        # Extract relevant information
                        question = data.get('Question', '')
                        answer = data.get('Final answer', '')
                        level = data.get('Level', 0)
                        metadata = data.get('Annotator Metadata', {})
                        
                        task_id = data.get('task_id', f'gaia_{line_num}')
                        if task_id in existing_ids:
                            skipped += 1
                            continue
                        
                        # Create experience document
                        experience = {
                            'task_id': task_id,
                            'question': question,
                            'answer': answer,
                            'level': level,
                            'approach': self._extract_approach(metadata),
                            'tools_used': self._extract_tools(metadata),
                            'steps': metadata.get('Steps', ''),
                            'num_steps': metadata.get('Number of steps', '0'),
                            'source': 'gaia_validation'
                        }
                        
                        # Add to index
                        self.add_experience(question, experience)
                        existing_ids.add(task_id)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse line {line_num}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing line {line_num}: {e}")
            
            # Save the index after bulk indexing
            self._save_index()
            if skipped:
                logger.info(f"Skipped {skipped} GAIA records already present in the index")
            logger.info(f"Successfully indexed {len(self.documents)} experiences from GAIA validation")
            
        except Exception as e:
            logger.error(f"Failed to index validation file: {e}")
    
    def _extract_approach(self, metadata: Dict[str, Any]) -> str:
        """
        Extract approach from metadata steps.
        
        Args:
            metadata: Annotator metadata
            
        Returns:
            Summarized approach
        """
        steps = metadata.get('Steps', '')
        if not steps:
            return ""
        
        # Extract key actions from steps
        lines = steps.split('\n')
        key_actions = []
        
        for line in lines[:3]:  # Take first 3 steps as approach
            if line.strip():
                # Remove step numbers
                clean_line = line.strip()
                if clean_line[0].isdigit():
                    clean_line = clean_line.split('.', 1)[-1].strip()
                key_actions.append(clean_line)
        
        return " → ".join(key_actions) if key_actions else steps[:200]
    
    def _extract_tools(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Extract tools used from metadata.
        
        Args:
            metadata: Annotator metadata
            
        Returns:
            List of tools used
        """
        tools = metadata.get('Tools', '')
        if not tools:
            return []
        
        # Parse tools string
        tool_list = []
        
        # Handle numbered list format
        lines = tools.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Remove numbering
                if '. ' in line:
                    tool = line.split('. ', 1)[-1].strip()
                else:
                    tool = line
                
                if tool and tool not in ['', 'None']:
                    tool_list.append(tool)
        
        return tool_list
    
    def add_experience(self, query: str, experience: Dict[str, Any]):
        """
        Add an experience to the knowledge base.
        
        Args:
            query: The query/question for indexing
            experience: The experience data
        """
        # Store document
        self.documents.append(experience)
        self.metadata.append({
            'query': query,
            'task_id': experience.get('task_id', ''),
            'level': experience.get('level', 0)
        })
        
        # Create embedding and add to index if encoder is available
        if self.encoder and self.index:
            try:
                embedding = self.encoder.encode([query])
                self.index.add(embedding)
            except Exception as e:
                logger.error(f"Failed to create embedding: {e}")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant experiences.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant experiences
        """
        if top_k <= 0 or not self.documents:
            return []
        # If we have embeddings, use semantic search
        if self.encoder and self.index and self.index.ntotal > 0:
            try:
                query_embedding = self.encoder.encode([query])
                distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
                
                results = []
                for idx in indices[0]:
                    if 0 <= idx < len(self.documents):
                        results.append(self.documents[idx])
                
                return results
                
            except Exception as e:
                logger.error(f"Semantic search failed, falling back to keyword search: {e}")
        
        # Fallback to simple keyword search
        return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Simple keyword-based search fallback.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of relevant experiences
        """
        query_words = set(query.lower().split())
        scored_docs = []
        for doc in self.documents:
            tools = doc.get('tools_used')
            if tools is None:
                tools = []
            elif isinstance(tools, str):
                tools = [tools]
            elif not isinstance(tools, (list, tuple, set)):
                tools = [tools]
            tools_str = ' '.join(str(t) for t in tools if t is not None)
            doc_text = f"{doc.get('question', '')} {doc.get('approach', '')} {tools_str}"
            doc_words = set(doc_text.lower().split())
            # Calculate simple overlap score
            overlap = len(query_words & doc_words)
            if overlap > 0:
                scored_docs.append((overlap, doc))
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_documents': len(self.documents),
            'has_embeddings': self.encoder is not None,
            'index_size': self.index.ntotal if self.encoder and self.index else 0,
            'sources': {}
        }
        
        # Count by source
        for doc in self.documents:
            source = doc.get('source', 'unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        return stats
