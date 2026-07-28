"""
GraphRAG (Graph-based Retrieval Augmented Generation) implementation.
This creates a knowledge graph with entities, relationships, and community detection.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import numpy as np
from tqdm import tqdm
import networkx as nx
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
import re
from collections import defaultdict

from config import GraphRAGConfig


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""
    id: str
    name: str
    type: str
    description: str
    embedding: Optional[np.ndarray]
    attributes: Dict[str, Any]


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    id: str
    source: str  # Entity ID
    target: str  # Entity ID
    type: str
    description: str
    weight: float = 1.0


@dataclass
class Community:
    """Represents a community of related entities."""
    id: str
    entity_ids: List[str]
    summary: str
    embedding: Optional[np.ndarray]
    level: int


class GraphRAGIndexer:
    """GraphRAG knowledge graph indexer with entity extraction and community detection."""
    
    def __init__(self, config: GraphRAGConfig):
        self.config = config
        self.client = OpenAI(api_key=config.llm_api_key, base_url=config.base_url)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Knowledge graph components
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.communities: Dict[str, Community] = {}
        self.graph = nx.Graph()
        
        # Ensure directories exist
        self.config.index_dir.mkdir(parents=True, exist_ok=True)
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized GraphRAG indexer with model: {config.llm_model}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        # Split by sentences first for better context preservation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            words = sentence.split()
            if current_size + len(words) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                # Start new chunk with overlap. chunk_overlap is a WORD budget
                # (the same unit as chunk_size, which current_size is measured
                # in); len(current_chunk) is a SENTENCE count, so using it here
                # kept the whole previous chunk and the window never advanced.
                overlap: List[str] = []
                overlap_size = 0
                for prev in reversed(current_chunk):
                    prev_size = len(prev.split())
                    if overlap_size + prev_size > self.config.chunk_overlap:
                        break
                    overlap.insert(0, prev)
                    overlap_size += prev_size
                current_chunk = overlap
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += len(words)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def extract_entities_relationships(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """Extract entities and relationships from text using LLM."""
        prompt = f"""
        Extract entities and relationships from the following technical text about Intel x86/x64 architecture.
        Focus on instructions, registers, CPU features, and architectural concepts.
        
        For entities, identify:
        - Intel instructions (type: "instruction")
        - Registers (type: "register")
        - CPU features (type: "feature")
        - Architectural components (type: "component")
        - Data types (type: "datatype")
        
        For relationships, identify how entities are connected (e.g., "uses", "modifies", "depends_on", "part_of").
        
        Text: {text[:2000]}  # Limit text length for API
        
        Return the result as JSON with the following structure:
        {{
            "entities": [
                {{"name": "entity_name", "type": "entity_type", "description": "brief description"}}
            ],
            "relationships": [
                {{"source": "entity1", "target": "entity2", "type": "relationship_type", "description": "brief description"}}
            ]
        }}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing technical documentation and extracting structured knowledge."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("entities", []), data.get("relationships", [])
            else:
                logger.warning("Could not parse JSON from LLM response")
                return [], []
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return [], []
    
    def build_knowledge_graph(self, text: str):
        """Build knowledge graph from text."""
        logger.info("Building knowledge graph...")
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        # Extract entities and relationships from each chunk
        all_entities = {}
        all_relationships = []
        
        for i, chunk in enumerate(tqdm(chunks, desc="Extracting entities")):
            entities, relationships = self.extract_entities_relationships(chunk)
            
            # Process entities
            for entity_data in entities:
                entity_name = entity_data.get("name", "").lower()
                if entity_name and entity_name not in all_entities:
                    # Create embedding for entity description
                    desc = entity_data.get("description", entity_name)
                    embedding = self.embedding_model.encode([desc])[0]
                    
                    entity = Entity(
                        id=f"entity_{len(all_entities)}",
                        name=entity_name,
                        type=entity_data.get("type", "unknown"),
                        description=desc,
                        embedding=embedding,
                        attributes={"chunk_id": i}
                    )
                    all_entities[entity_name] = entity
                    self.entities[entity.id] = entity
            
            # Process relationships
            for rel_data in relationships:
                source_name = rel_data.get("source", "").lower()
                target_name = rel_data.get("target", "").lower()
                
                if source_name in all_entities and target_name in all_entities:
                    relationship = Relationship(
                        id=f"rel_{len(all_relationships)}",
                        source=all_entities[source_name].id,
                        target=all_entities[target_name].id,
                        type=rel_data.get("type", "related"),
                        description=rel_data.get("description", ""),
                        weight=1.0
                    )
                    all_relationships.append(relationship)
                    self.relationships.append(relationship)
        
        # Build NetworkX graph
        logger.info("Building NetworkX graph...")
        for entity_id, entity in self.entities.items():
            self.graph.add_node(entity_id, **asdict(entity))
        
        for rel in self.relationships:
            self.graph.add_edge(rel.source, rel.target, 
                              type=rel.type, 
                              description=rel.description,
                              weight=rel.weight)
        
        logger.info(f"Built graph with {len(self.entities)} entities and {len(self.relationships)} relationships")
    
    def detect_communities(self):
        """Detect communities in the knowledge graph."""
        logger.info("Detecting communities...")
        
        if len(self.graph.nodes) == 0:
            logger.warning("Graph is empty, cannot detect communities")
            return
        
        # Use different community detection algorithms
        if self.config.community_detection_algorithm == "leiden":
            try:
                import leidenalg
                import igraph as ig
                
                # Convert NetworkX to igraph
                ig_graph = ig.Graph.from_networkx(self.graph)
                partitions = leidenalg.find_partition(ig_graph, leidenalg.ModularityVertexPartition)
                communities = {}
                for i, community in enumerate(partitions):
                    communities[i] = [list(self.graph.nodes())[idx] for idx in community]
            except ImportError:
                logger.warning("Leiden algorithm not available, falling back to Louvain")
                communities = nx.community.louvain_communities(self.graph, seed=42)
                communities = {i: list(comm) for i, comm in enumerate(communities)}
        else:
            # Use Louvain algorithm
            communities = nx.community.louvain_communities(self.graph, seed=42)
            communities = {i: list(comm) for i, comm in enumerate(communities)}
        
        # Create community summaries
        for comm_id, entity_ids in communities.items():
            if not entity_ids:
                continue
            
            # Get entities in community
            community_entities = [self.entities[eid] for eid in entity_ids if eid in self.entities]
            
            # Create community summary
            entity_descriptions = [e.description for e in community_entities[:10]]  # Limit for API
            summary_prompt = f"""
            Summarize the following group of related entities from Intel x86/x64 documentation:
            
            Entities:
            {chr(10).join(entity_descriptions)}
            
            Provide a concise summary (max 150 words) describing what these entities have in common and their role in the architecture.
            """
            
            try:
                response = self.client.chat.completions.create(
                    model=self.config.summarization_model,
                    messages=[
                        {"role": "system", "content": "You are an expert at summarizing technical documentation."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.1
                )
                summary = response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Error creating community summary: {e}")
                summary = f"Community containing {len(entity_ids)} related entities"
            
            # Create embedding for community
            embedding = self.embedding_model.encode([summary])[0]
            
            community = Community(
                id=f"community_{comm_id}",
                entity_ids=entity_ids,
                summary=summary,
                embedding=embedding,
                level=0
            )
            self.communities[community.id] = community
        
        logger.info(f"Detected {len(self.communities)} communities")
    
    def hierarchical_summarization(self):
        """Create hierarchical summaries of communities."""
        if len(self.communities) <= 1:
            return
        
        logger.info("Creating hierarchical community summaries...")
        
        # Group communities by similarity. Snapshot the ids up front: the loop
        # below inserts the merged communities into self.communities, and
        # iterating the live dict raised "RuntimeError: dictionary changed size
        # during iteration". The snapshot also keeps i/j aligned with
        # similarity_matrix, which is built once from these same communities.
        community_ids = list(self.communities.keys())
        community_embeddings = np.array([self.communities[cid].embedding for cid in community_ids])
        similarity_matrix = cosine_similarity(community_embeddings)
        
        # Simple hierarchical clustering
        threshold = 0.7
        merged_communities = []
        processed = set()
        
        for i, comm_id in enumerate(community_ids):
            if comm_id in processed:
                continue
            
            # Find similar communities
            similar = []
            for j, other_id in enumerate(community_ids):
                if i != j and similarity_matrix[i][j] > threshold:
                    similar.append(other_id)
                    processed.add(other_id)
            
            if similar:
                # Merge communities
                merged_ids = [comm_id] + similar
                all_entities = []
                for mid in merged_ids:
                    all_entities.extend(self.communities[mid].entity_ids)
                
                # Create merged summary
                summaries = [self.communities[mid].summary for mid in merged_ids]
                merge_prompt = f"""
                Summarize these related community summaries into a higher-level summary:
                
                {chr(10).join(summaries)}
                
                Provide a concise summary (max 200 words) of the overarching theme.
                """
                
                try:
                    response = self.client.chat.completions.create(
                        model=self.config.summarization_model,
                        messages=[
                            {"role": "system", "content": "You are an expert at creating hierarchical summaries."},
                            {"role": "user", "content": merge_prompt}
                        ],
                        max_tokens=250,
                        temperature=0.1
                    )
                    merged_summary = response.choices[0].message.content.strip()
                except Exception as e:
                    logger.error(f"Error creating merged summary: {e}")
                    merged_summary = f"Higher-level community containing {len(all_entities)} entities"
                
                # Create new community
                merged_embedding = self.embedding_model.encode([merged_summary])[0]
                merged_community = Community(
                    id=f"merged_community_{len(merged_communities)}",
                    entity_ids=all_entities,
                    summary=merged_summary,
                    embedding=merged_embedding,
                    level=1
                )
                self.communities[merged_community.id] = merged_community
                merged_communities.append(merged_community)
        
        logger.info(f"Created {len(merged_communities)} hierarchical communities")
    
    def search(self, query: str, top_k: int = 5, search_type: str = "hybrid") -> List[Dict[str, Any]]:
        """
        Search the knowledge graph.
        
        Args:
            query: Search query
            top_k: Number of results to return
            search_type: "entity", "community", or "hybrid"
        """
        query_embedding = self.embedding_model.encode([query])[0]
        results = []
        
        if search_type in ["entity", "hybrid"]:
            # Search entities
            entity_scores = []
            for entity_id, entity in self.entities.items():
                if entity.embedding is not None:
                    score = cosine_similarity([query_embedding], [entity.embedding])[0][0]
                    entity_scores.append((entity_id, score))
            
            entity_scores.sort(key=lambda x: x[1], reverse=True)
            
            for entity_id, score in entity_scores[:top_k]:
                entity = self.entities[entity_id]
                
                # Get related entities
                neighbors = list(self.graph.neighbors(entity_id)) if entity_id in self.graph else []
                
                results.append({
                    "type": "entity",
                    "id": entity_id,
                    "name": entity.name,
                    "entity_type": entity.type,
                    "description": entity.description,
                    "score": float(score),
                    "related_entities": neighbors[:5]
                })
        
        if search_type in ["community", "hybrid"]:
            # Search communities
            community_scores = []
            for comm_id, community in self.communities.items():
                if community.embedding is not None:
                    score = cosine_similarity([query_embedding], [community.embedding])[0][0]
                    community_scores.append((comm_id, score))
            
            community_scores.sort(key=lambda x: x[1], reverse=True)
            
            for comm_id, score in community_scores[:top_k]:
                community = self.communities[comm_id]
                
                # Get sample entities from community
                sample_entities = []
                for entity_id in community.entity_ids[:5]:
                    if entity_id in self.entities:
                        entity = self.entities[entity_id]
                        sample_entities.append({
                            "name": entity.name,
                            "type": entity.type
                        })
                
                results.append({
                    "type": "community",
                    "id": comm_id,
                    "summary": community.summary,
                    "level": community.level,
                    "score": float(score),
                    "entity_count": len(community.entity_ids),
                    "sample_entities": sample_entities
                })
        
        # Sort all results by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def multi_hop_search(self, start_entity: str, max_hops: int = 2,
                         relation_filter: Optional[str] = None,
                         top_k: int = 10) -> List[Dict[str, Any]]:
        """
        多跳关系检索：沿知识图谱的关系边遍历，回答「A 通过什么与 B 相连」这类
        扁平向量检索无法表达的关系性问题（对应书中「多跳关系推理」）。

        与 search() 的区别：search() 只按嵌入相似度召回孤立的实体/社区，
        而本方法真正利用图结构，返回从起始实体出发的**关系路径**。

        Args:
            start_entity: 起始实体名（不区分大小写，按子串匹配）。
            max_hops: 最大跳数。
            relation_filter: 若指定，只保留终点边为该关系类型的路径。
            top_k: 返回的路径数上限。

        Returns:
            每条路径形如 {"target", "target_type", "hops", "path"}，
            path 是若干 {"source", "relation", "target"} 步骤。
        """
        # 按名字子串匹配定位起始节点
        start_id = None
        needle = start_entity.lower()
        for entity_id, entity in self.entities.items():
            if needle in entity.name.lower():
                start_id = entity_id
                break
        if start_id is None or start_id not in self.graph:
            logger.warning(f"multi_hop_search: 未找到起始实体 '{start_entity}'")
            return []

        # BFS 沿边遍历，收集 <= max_hops 跳的路径
        results: List[Dict[str, Any]] = []
        queue = [(start_id, [])]
        while queue and len(results) < top_k * 4:
            node_id, path = queue.pop(0)
            if len(path) >= max_hops:
                continue
            for neighbor in self.graph.neighbors(node_id):
                rel_type = self.graph[node_id][neighbor].get("type", "related")
                src_name = self.entities[node_id].name if node_id in self.entities else node_id
                dst_name = self.entities[neighbor].name if neighbor in self.entities else neighbor
                step = {"source": src_name, "relation": rel_type, "target": dst_name}
                new_path = path + [step]
                if relation_filter is None or rel_type == relation_filter:
                    results.append({
                        "target": dst_name,
                        "target_type": self.entities[neighbor].type if neighbor in self.entities else "unknown",
                        "hops": len(new_path),
                        "path": new_path,
                    })
                queue.append((neighbor, new_path))

        results.sort(key=lambda r: r["hops"])
        return results[:top_k]

    def save_index(self, path: Optional[Path] = None):
        """Save the knowledge graph index to disk."""
        save_path = path or self.config.index_dir / "graphrag_index.pkl"
        
        # Convert to serializable format
        index_data = {
            'entities': {eid: asdict(e) for eid, e in self.entities.items()},
            'relationships': [asdict(r) for r in self.relationships],
            'communities': {cid: asdict(c) for cid, c in self.communities.items()},
            'graph': nx.node_link_data(self.graph),
            'config': asdict(self.config)
        }
        
        # Convert numpy arrays to lists
        for entity in index_data['entities'].values():
            if entity['embedding'] is not None:
                entity['embedding'] = entity['embedding'].tolist()
        
        for community in index_data['communities'].values():
            if community['embedding'] is not None:
                community['embedding'] = community['embedding'].tolist()
        
        with open(save_path, 'wb') as f:
            pickle.dump(index_data, f)
        
        logger.info(f"Saved GraphRAG index to {save_path}")
    
    def load_index(self, path: Optional[Path] = None):
        """Load knowledge graph index from disk."""
        load_path = path or self.config.index_dir / "graphrag_index.pkl"
        
        with open(load_path, 'rb') as f:
            index_data = pickle.load(f)
        
        # Reconstruct entities
        self.entities = {}
        for eid, entity_dict in index_data['entities'].items():
            if entity_dict['embedding'] is not None:
                entity_dict['embedding'] = np.array(entity_dict['embedding'])
            self.entities[eid] = Entity(**entity_dict)
        
        # Reconstruct relationships
        self.relationships = [Relationship(**r) for r in index_data['relationships']]
        
        # Reconstruct communities
        self.communities = {}
        for cid, comm_dict in index_data['communities'].items():
            if comm_dict['embedding'] is not None:
                comm_dict['embedding'] = np.array(comm_dict['embedding'])
            self.communities[cid] = Community(**comm_dict)
        
        # Reconstruct graph
        self.graph = nx.node_link_graph(index_data['graph'])
        
        logger.info(f"Loaded GraphRAG index from {load_path}")
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        entity_types = defaultdict(int)
        for entity in self.entities.values():
            entity_types[entity.type] += 1
        
        rel_types = defaultdict(int)
        for rel in self.relationships:
            rel_types[rel.type] += 1
        
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "total_communities": len(self.communities),
            "entity_types": dict(entity_types),
            "relationship_types": dict(rel_types),
            "graph_density": nx.density(self.graph) if len(self.graph) > 0 else 0,
            "average_degree": sum(dict(self.graph.degree()).values()) / max(1, len(self.graph.nodes))
        }
