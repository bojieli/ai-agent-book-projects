"""Hybrid Structured Retriever for RAPTOR Hierarchical Trees and GraphRAG Knowledge Graphs.

Merges RAPTOR tree summary nodes and GraphRAG entity-relation summaries into a unified retrieval index.
Performs Reciprocal Rank Fusion (RRF) scoring and evidence citation tracking across hierarchical and graph chunks.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np


@dataclass
class EvidenceCitation:
    """Represents evidence citation metadata tracking hierarchical and graph provenance."""
    source_type: str  # "raptor_tree", "graphrag_entity", "graphrag_relation", "graphrag_community"
    node_id: str
    citation_label: str
    hierarchical_level: Optional[int] = None
    entity_type: Optional[str] = None
    relation_type: Optional[str] = None
    community_level: Optional[int] = None
    lineage: List[str] = field(default_factory=list)
    snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence citation to dictionary format."""
        return {
            "source_type": self.source_type,
            "node_id": self.node_id,
            "citation_label": self.citation_label,
            "hierarchical_level": self.hierarchical_level,
            "entity_type": self.entity_type,
            "relation_type": self.relation_type,
            "community_level": self.community_level,
            "lineage": self.lineage,
            "snippet": self.snippet,
        }


@dataclass
class SearchResult:
    """Represents a unified hybrid search result item with RRF score and citation."""
    node_id: str
    text: str
    summary: str
    score: float  # Fused RRF score
    source_type: str
    citation: EvidenceCitation
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary format."""
        return {
            "node_id": self.node_id,
            "text": self.text,
            "summary": self.summary,
            "score": self.score,
            "source_type": self.source_type,
            "citation": self.citation.to_dict(),
            "metadata": self.metadata,
        }


class HybridStructuredRetriever:
    """Retriever that merges RAPTOR tree summaries and GraphRAG graph summaries into a hybrid index.
    
    Supports Reciprocal Rank Fusion (RRF) across hierarchical (RAPTOR) and knowledge graph (GraphRAG)
    indexes with evidence citation tracking for full auditability.
    """

    def __init__(
        self,
        rrf_k: int = 60,
        embedding_fn: Optional[Callable[[str], np.ndarray]] = None,
    ) -> None:
        """Initialize the HybridStructuredRetriever.

        Args:
            rrf_k: Smoothing constant for Reciprocal Rank Fusion (RRF). Default 60.
            embedding_fn: Optional callable to convert text into vector embeddings.
        """
        self.rrf_k = max(1, int(rrf_k))
        self.embedding_fn = embedding_fn

        # Internal node stores
        self.raptor_nodes: Dict[str, Dict[str, Any]] = {}
        self.graphrag_entities: Dict[str, Dict[str, Any]] = {}
        self.graphrag_relations: Dict[str, Dict[str, Any]] = {}
        self.graphrag_communities: Dict[str, Dict[str, Any]] = {}

        # Unified document registry
        self.unified_nodes: Dict[str, Dict[str, Any]] = {}

    def add_raptor_node(
        self,
        node_id: str,
        level: int,
        text: str,
        summary: str = "",
        embedding: Optional[np.ndarray] = None,
        children: Optional[List[str]] = None,
        parent: Optional[str] = None,
    ) -> None:
        """Add a RAPTOR tree summary node to the index."""
        record = {
            "id": str(node_id),
            "level": int(level),
            "text": str(text),
            "summary": str(summary or text),
            "embedding": embedding,
            "children": list(children or []),
            "parent": parent,
            "source_type": "raptor_tree",
        }
        self.raptor_nodes[str(node_id)] = record
        self.unified_nodes[f"raptor_{node_id}"] = record

    def add_graphrag_entity(
        self,
        entity_id: str,
        name: str,
        type: str = "GENERIC",
        description: str = "",
        embedding: Optional[np.ndarray] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a GraphRAG entity node to the index."""
        record = {
            "id": str(entity_id),
            "name": str(name),
            "type": str(type),
            "description": str(description),
            "embedding": embedding,
            "attributes": dict(attributes or {}),
            "source_type": "graphrag_entity",
        }
        self.graphrag_entities[str(entity_id)] = record
        self.unified_nodes[f"entity_{entity_id}"] = record

    def add_graphrag_relationship(
        self,
        relation_id: str,
        source: str,
        target: str,
        type: str = "RELATED_TO",
        description: str = "",
        weight: float = 1.0,
    ) -> None:
        """Add a GraphRAG relationship summary node to the index."""
        record = {
            "id": str(relation_id),
            "source": str(source),
            "target": str(target),
            "type": str(type),
            "description": str(description),
            "weight": float(weight),
            "source_type": "graphrag_relation",
        }
        self.graphrag_relations[str(relation_id)] = record
        self.unified_nodes[f"rel_{relation_id}"] = record

    def add_graphrag_community(
        self,
        community_id: str,
        entity_ids: List[str],
        summary: str,
        level: int = 0,
        embedding: Optional[np.ndarray] = None,
    ) -> None:
        """Add a GraphRAG community summary node to the index."""
        record = {
            "id": str(community_id),
            "entity_ids": list(entity_ids),
            "summary": str(summary),
            "level": int(level),
            "embedding": embedding,
            "source_type": "graphrag_community",
        }
        self.graphrag_communities[str(community_id)] = record
        self.unified_nodes[f"community_{community_id}"] = record

    def index_raptor_nodes(self, nodes: Sequence[Any]) -> None:
        """Bulk ingest RAPTOR tree nodes (objects or dicts)."""
        for node in nodes:
            if isinstance(node, dict):
                n_id = node.get("id") or node.get("node_id")
                level = node.get("level", 0)
                text = node.get("text", "")
                summary = node.get("summary", text)
                embedding = node.get("embedding")
                children = node.get("children", [])
                parent = node.get("parent")
            else:
                n_id = getattr(node, "id", getattr(node, "node_id", None))
                level = getattr(node, "level", 0)
                text = getattr(node, "text", "")
                summary = getattr(node, "summary", text)
                embedding = getattr(node, "embedding", None)
                children = getattr(node, "children", [])
                parent = getattr(node, "parent", None)
            if n_id is not None:
                self.add_raptor_node(
                    node_id=str(n_id),
                    level=level,
                    text=text,
                    summary=summary,
                    embedding=embedding,
                    children=children,
                    parent=parent,
                )

    def index_graphrag_data(
        self,
        entities: Optional[Sequence[Any]] = None,
        relationships: Optional[Sequence[Any]] = None,
        communities: Optional[Sequence[Any]] = None,
    ) -> None:
        """Bulk ingest GraphRAG entities, relationships, and communities."""
        if entities:
            for item in entities:
                if isinstance(item, dict):
                    e_id = item.get("id", item.get("entity_id"))
                    name = item.get("name", e_id)
                    e_type = item.get("type", "GENERIC")
                    desc = item.get("description", "")
                    emb = item.get("embedding")
                    attrs = item.get("attributes", {})
                else:
                    e_id = getattr(item, "id", getattr(item, "entity_id", None))
                    name = getattr(item, "name", str(e_id))
                    e_type = getattr(item, "type", "GENERIC")
                    desc = getattr(item, "description", "")
                    emb = getattr(item, "embedding", None)
                    attrs = getattr(item, "attributes", {})
                if e_id is not None:
                    self.add_graphrag_entity(e_id, name, e_type, desc, emb, attrs)

        if relationships:
            for item in relationships:
                if isinstance(item, dict):
                    r_id = item.get("id", item.get("relation_id"))
                    src = item.get("source", "")
                    tgt = item.get("target", "")
                    r_type = item.get("type", "RELATED_TO")
                    desc = item.get("description", "")
                    wt = item.get("weight", 1.0)
                else:
                    r_id = getattr(item, "id", getattr(item, "relation_id", None))
                    src = getattr(item, "source", "")
                    tgt = getattr(item, "target", "")
                    r_type = getattr(item, "type", "RELATED_TO")
                    desc = getattr(item, "description", "")
                    wt = getattr(item, "weight", 1.0)
                if r_id is not None:
                    self.add_graphrag_relationship(r_id, src, tgt, r_type, desc, wt)

        if communities:
            for item in communities:
                if isinstance(item, dict):
                    c_id = item.get("id", item.get("community_id"))
                    e_ids = item.get("entity_ids", [])
                    summ = item.get("summary", "")
                    lvl = item.get("level", 0)
                    emb = item.get("embedding")
                else:
                    c_id = getattr(item, "id", getattr(item, "community_id", None))
                    e_ids = getattr(item, "entity_ids", [])
                    summ = getattr(item, "summary", "")
                    lvl = getattr(item, "level", 0)
                    emb = getattr(item, "embedding", None)
                if c_id is not None:
                    self.add_graphrag_community(c_id, e_ids, summ, lvl, emb)

    def _compute_relevance_score(
        self, query: str, query_terms: set[str], query_vector: Optional[np.ndarray], node: Dict[str, Any]
    ) -> float:
        """Compute relevance score between query and node text/summary."""
        if not query_terms:
            return 0.0

        # Construct textual content for evaluation
        text_content = ""
        src_type = node.get("source_type")
        if src_type == "raptor_tree":
            text_content = f"{node.get('summary', '')} {node.get('text', '')}"
        elif src_type == "graphrag_entity":
            text_content = f"{node.get('name', '')} {node.get('type', '')} {node.get('description', '')}"
        elif src_type == "graphrag_relation":
            text_content = f"{node.get('source', '')} {node.get('type', '')} {node.get('description', '')}"
        elif src_type == "graphrag_community":
            text_content = f"{node.get('summary', '')}"

        if not text_content.strip():
            return 0.0

        # Vector similarity if embeddings available
        if query_vector is not None:
            try:
                n_emb = node.get("embedding")
                if n_emb is None and self.embedding_fn is not None:
                    n_emb = self.embedding_fn(text_content)
                if n_emb is not None:
                    q_norm = np.linalg.norm(query_vector)
                    n_norm = np.linalg.norm(n_emb)
                    if q_norm > 0 and n_norm > 0:
                        cos_sim = float(np.dot(query_vector, n_emb) / (q_norm * n_norm))
                        return max(0.0, cos_sim)
            except Exception:
                pass
        # Term overlap + TF-IDF-like scoring
        words = re.findall(r"\w+", text_content.lower())
        if not words:
            return 0.0

        word_counts = defaultdict(int)
        for w in words:
            word_counts[w] += 1

        matches = sum(word_counts[qt] for qt in query_terms if qt in word_counts)
        precision = matches / len(query_terms)
        coverage = matches / len(words)
        return float(precision * 0.8 + coverage * 0.2)

    def _build_citation(self, node: Dict[str, Any]) -> EvidenceCitation:
        """Construct structured evidence citation tracking provenance for a node."""
        src_type = node.get("source_type", "unknown")
        n_id = str(node.get("id", ""))

        if src_type == "raptor_tree":
            lvl = node.get("level", 0)
            label = f"[RAPTOR Tree Level {lvl} Node: {n_id}]"
            lineage = []
            if node.get("parent"):
                lineage.append(f"Parent: {node['parent']}")
            if node.get("children"):
                lineage.append(f"Children: {', '.join(node['children'])}")
            snippet = node.get("summary") or node.get("text") or ""
            return EvidenceCitation(
                source_type="raptor_tree",
                node_id=n_id,
                citation_label=label,
                hierarchical_level=lvl,
                lineage=lineage,
                snippet=snippet[:200],
            )

        elif src_type == "graphrag_entity":
            e_type = node.get("type", "GENERIC")
            e_name = node.get("name", n_id)
            label = f"[GraphRAG Entity: {e_name} (Type: {e_type})]"
            snippet = node.get("description", "")
            return EvidenceCitation(
                source_type="graphrag_entity",
                node_id=n_id,
                citation_label=label,
                entity_type=e_type,
                lineage=[f"EntityName: {e_name}"],
                snippet=snippet[:200],
            )

        elif src_type == "graphrag_relation":
            r_type = node.get("type", "RELATED_TO")
            src = node.get("source", "")
            tgt = node.get("target", "")
            label = f"[GraphRAG Relation: {src} --({r_type})--> {tgt}]"
            snippet = node.get("description", "")
            return EvidenceCitation(
                source_type="graphrag_relation",
                node_id=n_id,
                citation_label=label,
                relation_type=r_type,
                lineage=[f"Source: {src}", f"Target: {tgt}"],
                snippet=snippet[:200],
            )

        elif src_type == "graphrag_community":
            lvl = node.get("level", 0)
            e_ids = node.get("entity_ids", [])
            label = f"[GraphRAG Community Level {lvl}: {n_id}]"
            snippet = node.get("summary", "")
            return EvidenceCitation(
                source_type="graphrag_community",
                node_id=n_id,
                citation_label=label,
                community_level=lvl,
                lineage=[f"Entities: {', '.join(e_ids[:5])}"],
                snippet=snippet[:200],
            )

        return EvidenceCitation(
            source_type=src_type,
            node_id=n_id,
            citation_label=f"[Source: {src_type} Node: {n_id}]",
        )

    def retrieve(self, query: str, top_k: int = 5, rrf_k: Optional[int] = None) -> List[SearchResult]:
        """Retrieve and rank hybrid results using Reciprocal Rank Fusion (RRF).

        Args:
            query: The search query string.
            top_k: Number of top ranked results to return.
            rrf_k: Optional override for RRF k constant.

        Returns:
            List of SearchResult items ordered descending by fused RRF score.
        """
        k_val = rrf_k if rrf_k is not None else self.rrf_k
        top_k = max(1, int(top_k))

        if not query or not query.strip():
            return []

        query_terms = set(re.findall(r"\w+", query.lower()))
        query_vector = self.embedding_fn(query) if self.embedding_fn is not None else None

        # 1. Rank RAPTOR tree summary nodes
        raptor_scores: List[Tuple[str, float]] = []
        for key, node in self.unified_nodes.items():
            if node.get("source_type") == "raptor_tree":
                score = self._compute_relevance_score(query, query_terms, query_vector, node)
                if score > 0:
                    raptor_scores.append((key, score))
        raptor_scores.sort(key=lambda x: x[1], reverse=True)

        # 2. Rank GraphRAG graph summary nodes
        graphrag_scores: List[Tuple[str, float]] = []
        for key, node in self.unified_nodes.items():
            if node.get("source_type") in ("graphrag_entity", "graphrag_relation", "graphrag_community"):
                score = self._compute_relevance_score(query, query_terms, query_vector, node)
                if score > 0:
                    graphrag_scores.append((key, score))
        graphrag_scores.sort(key=lambda x: x[1], reverse=True)
        # Build rank lookups (1-indexed ranks)
        raptor_ranks = {item_key: rank + 1 for rank, (item_key, _) in enumerate(raptor_scores)}
        graphrag_ranks = {item_key: rank + 1 for rank, (item_key, _) in enumerate(graphrag_scores)}

        # 3. Perform Reciprocal Rank Fusion (RRF) scoring
        all_candidate_keys = set(raptor_ranks.keys()).union(set(graphrag_ranks.keys()))
        rrf_scores: Dict[str, float] = {}

        for key in all_candidate_keys:
            score = 0.0
            if key in raptor_ranks:
                score += 1.0 / (k_val + raptor_ranks[key])
            if key in graphrag_ranks:
                score += 1.0 / (k_val + graphrag_ranks[key])
            rrf_scores[key] = score

        # Sort candidate keys by RRF score descending
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        # 4. Construct final SearchResult objects with citations
        results: List[SearchResult] = []
        for key in sorted_keys[:top_k]:
            node = self.unified_nodes[key]
            citation = self._build_citation(node)

            src_type = node.get("source_type", "unknown")
            text = node.get("text") or node.get("description") or node.get("summary") or ""
            summary = node.get("summary") or node.get("description") or text

            res = SearchResult(
                node_id=str(node.get("id")),
                text=text,
                summary=summary,
                score=rrf_scores[key],
                source_type=src_type,
                citation=citation,
                metadata={
                    "raptor_rank": raptor_ranks.get(key),
                    "graphrag_rank": graphrag_ranks.get(key),
                    "raw_node": {k: v for k, v in node.items() if k != "embedding"},
                },
            )
            results.append(res)

        return results
