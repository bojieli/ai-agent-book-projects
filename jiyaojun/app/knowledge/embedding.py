"""Embedding providers — default BGE-M3 (ADR-011 / docs 09)."""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass
from typing import Protocol


@dataclass
class EmbeddingResult:
    dense: list[float]
    sparse: dict[str, float]
    model_id: str
    dim: int


class EmbeddingProvider(Protocol):
    model_id: str

    def embed(self, text: str) -> EmbeddingResult: ...

    def embed_query(self, text: str) -> EmbeddingResult:
        return self.embed(text)


def _tokenize_zh(text: str) -> list[str]:
    # keep CJK bigrams + latin tokens (fintech IDs, Shadow, PSI…)
    text = text.lower()
    latin = re.findall(r"[a-z0-9_./%-]+", text)
    chars = re.findall(r"[\u4e00-\u9fff]", text)
    bigrams = [chars[i] + chars[i + 1] for i in range(len(chars) - 1)] if len(chars) > 1 else chars
    return latin + bigrams


class BgeM3ShimProvider:
    """
    CI / no-weight stand-in that mirrors BGE-M3's dual-channel API
    (dense + lexical sparse). NOT a production embedding model.
    """

    model_id = "bge-m3-shim"
    dim = 64

    def embed(self, text: str) -> EmbeddingResult:
        toks = _tokenize_zh(text)
        dense = [0.0] * self.dim
        for t in toks:
            h = int(hashlib.sha256(t.encode()).hexdigest(), 16)
            dense[h % self.dim] += 1.0
            dense[(h // self.dim) % self.dim] += 0.5
        norm = math.sqrt(sum(x * x for x in dense)) or 1.0
        dense = [x / norm for x in dense]
        sparse: dict[str, float] = {}
        for t in toks:
            sparse[t] = sparse.get(t, 0.0) + 1.0
        # length-normalize sparse like lexical weights
        ssum = sum(sparse.values()) or 1.0
        sparse = {k: v / ssum for k, v in sparse.items()}
        return EmbeddingResult(dense=dense, sparse=sparse, model_id=self.model_id, dim=self.dim)

    def embed_query(self, text: str) -> EmbeddingResult:
        return self.embed(text)


class BgeM3Provider:
    """
    Real BGE-M3 via FlagEmbedding when installed.
    Falls back to shim with warning flag if import/weights unavailable.
    """

    model_id = "BAAI/bge-m3"
    dim = 1024

    def __init__(self) -> None:
        self._model = None
        self.using_fallback = False
        try:
            from FlagEmbedding import BGEM3FlagModel  # type: ignore

            self._model = BGEM3FlagModel(self.model_id, use_fp16=False)
        except Exception:
            self.using_fallback = True
            self._shim = BgeM3ShimProvider()

    def embed(self, text: str) -> EmbeddingResult:
        if self._model is None:
            r = self._shim.embed(text)
            return EmbeddingResult(
                dense=r.dense,
                sparse=r.sparse,
                model_id=f"{self.model_id}#fallback-shim",
                dim=r.dim,
            )
        out = self._model.encode(
            [text],
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        dense = out["dense_vecs"][0].tolist()
        # lexical_weights: list[dict[token_id -> weight]] or dict
        lw = out.get("lexical_weights") or out.get("sparse_vecs")
        sparse: dict[str, float] = {}
        if lw:
            raw = lw[0]
            if isinstance(raw, dict):
                sparse = {str(k): float(v) for k, v in raw.items()}
        return EmbeddingResult(dense=dense, sparse=sparse, model_id=self.model_id, dim=len(dense))

    def embed_query(self, text: str) -> EmbeddingResult:
        return self.embed(text)


def get_embedding_provider() -> EmbeddingProvider:
    """
    JIYAOJUN_EMBEDDING=
      - bge-m3       → try real BGE-M3 (fallback shim if unavailable)
      - bge-m3-shim  → deterministic dual-channel shim (default for CI)
    """
    mode = os.environ.get("JIYAOJUN_EMBEDDING", "bge-m3-shim").strip().lower()
    if mode in {"bge-m3", "bge_m3", "bge-m3-real"}:
        return BgeM3Provider()
    return BgeM3ShimProvider()


def embedding_report(provider: EmbeddingProvider | None = None) -> dict[str, str]:
    """暴露 provider_kind / model_id / fallback — 禁止误称 CI shim 为生产 BGE-M3。"""
    p = provider or get_embedding_provider()
    kind = "shim"
    fallback = "false"
    model_id = getattr(p, "model_id", "unknown")
    if isinstance(p, BgeM3Provider):
        kind = "bge-m3"
        if getattr(p, "using_fallback", False):
            kind = "bge-m3-fallback-shim"
            fallback = "true"
    elif isinstance(p, BgeM3ShimProvider):
        kind = "shim"
    return {
        "provider_kind": kind,
        "model_id": model_id,
        "fallback": fallback,
        "ci_default": "true" if kind == "shim" else "false",
    }


def cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(n))


def sparse_dot(q: dict[str, float], d: dict[str, float]) -> float:
    if len(q) > len(d):
        q, d = d, q
    return sum(v * d.get(k, 0.0) for k, v in q.items())
