"""Mock Hybrid Dense+Sparse vector store — ACL filter BEFORE similarity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math
import re


@dataclass
class VectorDoc:
    doc_id: str
    org_domain: str
    classification: str
    acl_principals: list[str]
    text: str
    write_class: str = "domain"
    # mock embedding = bag-of-char hash dims
    dense: list[float] = field(default_factory=list)
    sparse: dict[str, float] = field(default_factory=dict)


def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\W+", text.lower()) if t]


def _dense(text: str, dim: int = 16) -> list[float]:
    v = [0.0] * dim
    for i, ch in enumerate(text[:200]):
        v[i % dim] += (ord(ch) % 13) / 13.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def _sparse(text: str) -> dict[str, float]:
    counts: dict[str, float] = {}
    for t in _tokenize(text):
        counts[t] = counts.get(t, 0.0) + 1.0
    return counts


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _sparse_score(q: dict[str, float], d: dict[str, float]) -> float:
    return sum(q.get(k, 0.0) * v for k, v in d.items())


class MockHybridIndex:
    def __init__(self) -> None:
        self.docs: list[VectorDoc] = []

    def upsert(self, doc: VectorDoc) -> None:
        doc.dense = _dense(doc.text)
        doc.sparse = _sparse(doc.text)
        self.docs = [d for d in self.docs if d.doc_id != doc.doc_id] + [doc]

    def search(
        self,
        *,
        query: str,
        user_id: str,
        org_domains: list[str],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        # ACL + domain FIRST
        candidates = [
            d
            for d in self.docs
            if d.org_domain in org_domains
            and (user_id in d.acl_principals or "*" in d.acl_principals)
        ]
        q_dense = _dense(query)
        q_sparse = _sparse(query)
        scored = []
        for d in candidates:
            score = 0.6 * _cos(q_dense, d.dense) + 0.4 * _sparse_score(q_sparse, d.sparse)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "doc_id": d.doc_id,
                "score": round(s, 4),
                "text": d.text,
                "org_domain": d.org_domain,
                "write_class": d.write_class,
            }
            for s, d in scored[:top_k]
        ]
