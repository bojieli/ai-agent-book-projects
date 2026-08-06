"""向量索引协议与 Qdrant 实现 — ACL-first dense+payload 过滤。"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.knowledge.embedding import (
    EmbeddingProvider,
    EmbeddingResult,
    cosine,
    get_embedding_provider,
    sparse_dot,
)

if TYPE_CHECKING:
    from app.knowledge.rag import RagChunk, RagHit


@runtime_checkable
class VectorIndex(Protocol):
    """可注入的混合检索索引；内存与 Qdrant 共用同一契约。"""

    embedder: EmbeddingProvider

    def upsert(self, chunk: RagChunk) -> RagChunk: ...

    def upsert_many(self, chunks: list[RagChunk]) -> list[RagChunk]: ...

    def drop_source(self, source_id: str) -> int: ...

    def search_once(
        self,
        query: str,
        *,
        user_id: str,
        org_domains: list[str],
        top_k: int = 5,
        corpora: list[str] | None = None,
        allow_write_classes: list[str] | None = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ) -> list[RagHit]: ...


def _point_id(chunk_id: str) -> str:
    """chunk_id → 稳定 Qdrant point id。"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def _chunk_to_payload(chunk: "RagChunk") -> dict[str, Any]:
    """RagChunk 序列化为 Qdrant payload（含 ACL 与 sparse 元数据）。"""
    return {
        "chunk_id": chunk.chunk_id,
        "corpus": chunk.corpus,
        "org_domain": chunk.org_domain,
        "classification": chunk.classification,
        "write_class": chunk.write_class,
        "acl_principals": list(chunk.acl_principals),
        "context_prefix": chunk.context_prefix,
        "body": chunk.body,
        "source_id": chunk.source_id,
        "vector_ref": chunk.vector_ref,
        "sparse": dict(chunk.sparse),
        "meta": dict(chunk.meta),
    }


def _payload_to_hit(
    payload: dict[str, Any],
    *,
    score: float,
    dense_score: float,
    sparse_score: float,
) -> RagHit:
    """payload → RagHit（与内存索引 citation 形状一致）。"""
    from app.knowledge.rag import RagHit

    meta = payload.get("meta") or {}
    sp = str(meta.get("speaker") or "")
    sec = str(meta.get("section") or "")
    return RagHit(
        chunk_id=str(payload["chunk_id"]),
        corpus=str(payload["corpus"]),
        source_id=str(payload["source_id"]),
        text=str(payload["body"]),
        score=round(score, 6),
        dense_score=round(dense_score, 6),
        sparse_score=round(sparse_score, 6),
        citation={
            "corpus": str(payload["corpus"]),
            "id": str(payload["source_id"]),
            "source_id": str(payload["source_id"]),
            "span": str(payload["chunk_id"]),
            "vector_ref": str(payload.get("vector_ref") or ""),
            "classification": str(payload["classification"]),
            "write_class": str(payload["write_class"]),
            "chunk_index": str(meta.get("chunk_index", 0)),
            "speaker": sp,
            "start_ms": str(meta.get("start_ms") if meta.get("start_ms") is not None else ""),
            "section": sec,
        },
    )


def _apply_rerank_boost(score: float, payload: dict[str, Any], query: str) -> float:
    """与 HybridRagIndex 一致的轻量 rerank 加分。"""
    meta = payload.get("meta") or {}
    corpus = str(payload.get("corpus") or "")
    if corpus == "continuum" and meta.get("open"):
        score += 0.05
    sp = str(meta.get("speaker") or "")
    if sp and sp in query:
        score += 0.03
    sec = str(meta.get("section") or "")
    if sec and "决议" in query and "决议" in sec:
        score += 0.03
    return score


class QdrantHybridIndex:
    """Qdrant dense 检索 + payload ACL 过滤 + 应用层 sparse 重排。"""

    def __init__(
        self,
        *,
        url: str,
        collection: str,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self.embedder = embedder or get_embedding_provider()
        self.collection = collection
        self._client = QdrantClient(url=url, prefer_grpc=False)
        self._ensure_collection(VectorParams, Distance)

    def _ensure_collection(self, VectorParams: Any, Distance: Any) -> None:
        """集合不存在时按 embedder 维度创建。"""
        dim = getattr(self.embedder, "dim", None)
        if dim is None:
            probe = self.embedder.embed("dimension_probe")
            dim = probe.dim
        names = {c.name for c in self._client.get_collections().collections}
        if self.collection not in names:
            self._client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert(self, chunk: "RagChunk") -> "RagChunk":
        from qdrant_client.models import PointStruct

        emb: EmbeddingResult = self.embedder.embed(chunk.indexed_text)
        chunk.dense = emb.dense
        chunk.sparse = emb.sparse
        chunk.vector_ref = f"{emb.model_id}:{chunk.chunk_id}"
        self._client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=_point_id(chunk.chunk_id),
                    vector=chunk.dense,
                    payload=_chunk_to_payload(chunk),
                )
            ],
        )
        return chunk

    def upsert_many(self, chunks: list["RagChunk"]) -> list["RagChunk"]:
        return [self.upsert(c) for c in chunks]

    def drop_source(self, source_id: str) -> int:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        filt = Filter(
            must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]
        )
        self._client.delete(collection_name=self.collection, points_selector=filt)
        # Qdrant delete 不返回计数；以 1 表示已执行（调用方主要关心幂等删除）
        return 1

    def _acl_filter(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        corpora: list[str] | None,
        allow_write_classes: list[str] | None,
    ) -> Any:
        """ACL-first：检索前在 Qdrant 侧按 org/ACL/corpus 过滤。"""
        from qdrant_client.models import (
            FieldCondition,
            Filter,
            MatchAny,
            MatchValue,
        )

        must: list[Any] = [
            FieldCondition(key="org_domain", match=MatchAny(any=org_domains)),
            Filter(
                should=[
                    FieldCondition(
                        key="acl_principals", match=MatchValue(value=user_id)
                    ),
                    FieldCondition(key="acl_principals", match=MatchValue(value="*")),
                ]
            ),
        ]
        if corpora:
            must.append(FieldCondition(key="corpus", match=MatchAny(any=corpora)))
        if allow_write_classes:
            must.append(
                FieldCondition(
                    key="write_class", match=MatchAny(any=allow_write_classes)
                )
            )
        # invariant: critical + wide 不应存在
        must_not = Filter(
            must=[
                FieldCondition(
                    key="classification", match=MatchValue(value="critical")
                ),
                FieldCondition(key="write_class", match=MatchValue(value="wide")),
            ]
        )
        return Filter(must=must, must_not=[must_not])

    def search_once(
        self,
        query: str,
        *,
        user_id: str,
        org_domains: list[str],
        top_k: int = 5,
        corpora: list[str] | None = None,
        allow_write_classes: list[str] | None = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ) -> list[RagHit]:
        filt = self._acl_filter(
            user_id=user_id,
            org_domains=org_domains,
            corpora=corpora,
            allow_write_classes=allow_write_classes,
        )
        q = self.embedder.embed_query(query)
        # 多取候选以便 sparse 重排
        fetch_k = max(top_k * 4, top_k)
        response = self._client.query_points(
            collection_name=self.collection,
            query=q.dense,
            query_filter=filt,
            limit=fetch_k,
            with_payload=True,
        )
        results = response.points or []
        if not results:
            return []

        scored: list[RagHit] = []
        for pt in results:
            payload = pt.payload or {}
            sparse = payload.get("sparse") or {}
            if not isinstance(sparse, dict):
                sparse = {}
            ds = float(pt.score) if pt.score is not None else cosine(q.dense, [])
            ss = sparse_dot(q.sparse, {str(k): float(v) for k, v in sparse.items()})
            score = dense_weight * ds + sparse_weight * ss
            score = _apply_rerank_boost(score, payload, query)
            scored.append(
                _payload_to_hit(
                    payload,
                    score=score,
                    dense_score=ds,
                    sparse_score=ss,
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def close(self) -> None:
        """关闭底层客户端（测试/进程退出时可选调用）。"""
        close_fn = getattr(self._client, "close", None)
        if callable(close_fn):
            close_fn()


def qdrant_reachable(url: str) -> bool:
    """探测 Qdrant HTTP 是否可用（集成测试 skip 用）。"""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=url, prefer_grpc=False, timeout=3)
        client.get_collections()
        close_fn = getattr(client, "close", None)
        if callable(close_fn):
            close_fn()
        return True
    except Exception:
        return False
