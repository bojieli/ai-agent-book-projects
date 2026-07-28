"""
RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) implementation.
This creates a hierarchical tree structure with recursive summarization.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from tqdm import tqdm
import tiktoken
from sklearn.mixture import GaussianMixture
from sklearn.metrics.pairwise import cosine_similarity
import umap
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from loguru import logger

from config import RaptorConfig


@dataclass
class TreeNode:
    """Represents a node in the RAPTOR tree."""
    id: str
    level: int
    text: str
    summary: str
    embedding: Optional[np.ndarray]
    children: List[str]  # IDs of child nodes
    parent: Optional[str]  # ID of parent node


class RaptorIndexer:
    """RAPTOR tree-based document indexer with recursive summarization."""
    
    def __init__(self, config: RaptorConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key, base_url=config.base_url)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        try:
            # OpenRouter-style ids (e.g. "openai/gpt-5.6-luna") aren't known to
            # tiktoken; fall back to a general-purpose encoding for token counts.
            self.tokenizer = tiktoken.encoding_for_model(config.model_name)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Tree structure
        self.nodes: Dict[str, TreeNode] = {}
        self.root_nodes: List[str] = []
        
        # Ensure index directory exists
        self.config.index_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized RAPTOR indexer with model: {config.model_name}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        words = text.split()
        chunks = []
        step = max(1, self.config.chunk_size - self.config.chunk_overlap)
        
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + self.config.chunk_size])
            if chunk:
                chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for texts using sentence transformers."""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return np.array(embeddings)
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize text using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries focusing on key technical information."},
                    {"role": "user", "content": f"Summarize the following text in {max_length} words or less, focusing on the main technical concepts and important details:\n\n{text}"}
                ],
                max_tokens=max_length * 2,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            # Return truncated text as fallback
            words = text.split()[:max_length]
            return " ".join(words) + "..."
    
    def cluster_nodes(self, embeddings: np.ndarray, min_clusters: int = 2, max_clusters: int = 10) -> np.ndarray:
        """Cluster embeddings using Gaussian Mixture Model."""
        n_samples = len(embeddings)
        n_clusters = min(max(min_clusters, n_samples // 5), min(max_clusters, n_samples))
        
        if n_samples < 2:
            return np.zeros(n_samples)
        
        # Use UMAP for dimensionality reduction if needed
        if embeddings.shape[1] > 50:
            reducer = umap.UMAP(n_components=50, n_neighbors=min(15, n_samples-1))
            embeddings_reduced = reducer.fit_transform(embeddings)
        else:
            embeddings_reduced = embeddings
        
        # Perform clustering
        gmm = GaussianMixture(n_components=n_clusters, random_state=42)
        cluster_labels = gmm.fit_predict(embeddings_reduced)
        
        return cluster_labels
    
    def build_tree_level(self, node_ids: List[str]) -> List[str]:
        """Build one level of the tree by clustering and summarizing nodes."""
        if len(node_ids) <= 1:
            return node_ids
        
        # Get embeddings for nodes
        texts = [self.nodes[nid].text for nid in node_ids]
        embeddings = np.array([self.nodes[nid].embedding for nid in node_ids])
        
        # Cluster nodes
        cluster_labels = self.cluster_nodes(embeddings)
        
        # Group nodes by cluster
        clusters: Dict[int, List[str]] = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(node_ids[i])
        
        # Create parent nodes for each cluster
        parent_ids = []
        current_level = self.nodes[node_ids[0]].level + 1
        
        for cluster_id, child_ids in clusters.items():
            # Combine texts from child nodes
            combined_text = "\n\n".join([self.nodes[cid].text for cid in child_ids])
            
            # Create summary for parent node
            summary = self.summarize_text(combined_text, self.config.summarization_length)
            
            # Create embedding for summary
            summary_embedding = self.embedding_model.encode([summary])[0]
            
            # Create parent node
            parent_id = f"level{current_level}_cluster{cluster_id}"
            parent_node = TreeNode(
                id=parent_id,
                level=current_level,
                text=summary,
                summary=summary,
                embedding=summary_embedding,
                children=child_ids,
                parent=None
            )
            
            # Update child nodes to reference parent
            for child_id in child_ids:
                self.nodes[child_id].parent = parent_id
            
            self.nodes[parent_id] = parent_node
            parent_ids.append(parent_id)
        
        logger.info(f"Created {len(parent_ids)} parent nodes at level {current_level}")
        return parent_ids
    
    def build_index(self, text: str):
        """Build RAPTOR tree index from text."""
        logger.info("Building RAPTOR tree index...")
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        # Create leaf nodes from chunks
        logger.info("Creating leaf nodes...")
        leaf_ids = []
        for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
            # Create embedding
            embedding = self.embedding_model.encode([chunk])[0]
            
            # Create summary for chunk
            summary = self.summarize_text(chunk, max_length=100)
            
            # Create leaf node
            node_id = f"leaf_{i}"
            node = TreeNode(
                id=node_id,
                level=0,
                text=chunk,
                summary=summary,
                embedding=embedding,
                children=[],
                parent=None
            )
            self.nodes[node_id] = node
            leaf_ids.append(node_id)
        
        # Build tree levels
        current_level_ids = leaf_ids
        for level in range(self.config.tree_depth):
            if len(current_level_ids) <= 1:
                break
            
            logger.info(f"Building tree level {level + 1}...")
            current_level_ids = self.build_tree_level(current_level_ids)
        
        self.root_nodes = current_level_ids
        logger.info(f"RAPTOR tree built with {len(self.nodes)} nodes and {len(self.root_nodes)} root nodes")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the RAPTOR tree for relevant information."""
        # Create query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Calculate similarity with all nodes
        similarities = []
        for node_id, node in self.nodes.items():
            if node.embedding is not None:
                sim = cosine_similarity([query_embedding], [node.embedding])[0][0]
                similarities.append((node_id, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k results with different levels for diversity
        results = []
        levels_seen = set()
        
        for node_id, score in similarities:
            node = self.nodes[node_id]
            
            # Add diversity by including nodes from different levels
            if len(results) < top_k:
                results.append({
                    "node_id": node_id,
                    "level": node.level,
                    "text": node.text,
                    "summary": node.summary,
                    "score": float(score)
                })
                levels_seen.add(node.level)
            elif node.level not in levels_seen and len(results) < top_k * 2:
                # Include some diverse results from other levels
                results.append({
                    "node_id": node_id,
                    "level": node.level,
                    "text": node.text,
                    "summary": node.summary,
                    "score": float(score)
                })
                levels_seen.add(node.level)
        
        return results[:top_k]
    
    def save_index(self, path: Optional[Path] = None):
        """Save the RAPTOR tree index to disk."""
        save_path = path or self.config.index_dir / "raptor_index.pkl"
        
        # Convert nodes to serializable format
        serializable_nodes = {}
        for node_id, node in self.nodes.items():
            node_dict = asdict(node)
            # Convert numpy array to list for JSON serialization
            if node.embedding is not None:
                node_dict['embedding'] = node.embedding.tolist()
            serializable_nodes[node_id] = node_dict
        
        index_data = {
            'nodes': serializable_nodes,
            'root_nodes': self.root_nodes,
            'config': asdict(self.config)
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(index_data, f)
        
        logger.info(f"Saved RAPTOR index to {save_path}")
    
    def load_index(self, path: Optional[Path] = None):
        """Load RAPTOR tree index from disk."""
        load_path = path or self.config.index_dir / "raptor_index.pkl"
        
        with open(load_path, 'rb') as f:
            index_data = pickle.load(f)
        
        # Reconstruct nodes
        self.nodes = {}
        for node_id, node_dict in index_data['nodes'].items():
            # Convert list back to numpy array
            if node_dict['embedding'] is not None:
                node_dict['embedding'] = np.array(node_dict['embedding'])
            self.nodes[node_id] = TreeNode(**node_dict)
        
        self.root_nodes = index_data['root_nodes']
        logger.info(f"Loaded RAPTOR index from {load_path}")
    
    def get_tree_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAPTOR tree."""
        level_counts = {}
        for node in self.nodes.values():
            if node.level not in level_counts:
                level_counts[node.level] = 0
            level_counts[node.level] += 1
        
        return {
            "total_nodes": len(self.nodes),
            "root_nodes": len(self.root_nodes),
            "levels": len(level_counts),
            "nodes_per_level": level_counts,
            "average_children": sum(len(n.children) for n in self.nodes.values()) / max(1, len(self.nodes))
        }
