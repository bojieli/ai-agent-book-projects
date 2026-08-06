"""RAG pipeline — ACL-first Hybrid Dense+Sparse + contextual chunks + bounded multi-hop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.knowledge.chunking import ChunkConfig, ContentKind, TextChunk, chunk_by_kind, detect_content_kind
from app.knowledge.embedding import (
    EmbeddingProvider,
    EmbeddingResult,
    cosine,
    get_embedding_provider,
    sparse_dot,
)
from app.knowledge.vector_store import VectorIndex


@dataclass
class RagChunk:
    chunk_id: str
    corpus: str  # docs | continuum | transcript
    org_domain: str
    classification: str
    write_class: str
    acl_principals: list[str]
    # contextual prefix required by 03 §2.4.2
    context_prefix: str
    body: str
    source_id: str
    vector_ref: str = ""
    dense: list[float] = field(default_factory=list)
    sparse: dict[str, float] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def indexed_text(self) -> str:
        return f"{self.context_prefix}\n{self.body}"


@dataclass
class RagHit:
    chunk_id: str
    corpus: str
    source_id: str
    text: str
    score: float
    dense_score: float
    sparse_score: float
    citation: dict[str, str]


@dataclass
class RagSearchResult:
    hits: list[RagHit]
    hops: int
    queries_used: list[str]
    model_id: str
    empty_reason: str | None = None


@dataclass
class GroundedAnswer:
    """检索增强回答（无 LLM 时基于摘录拼装，生产可换生成器）。"""

    query: str
    answer: str
    citations: list[dict[str, Any]]
    abstained: bool
    abstain_reason: str | None
    retrieval_hops: int
    model_id: str


def contextual_prefix(
    *,
    corpus: str,
    org_domain: str,
    title: str,
    project_id: str | None = None,
    meeting_id: str | None = None,
    series_id: str | None = None,
    chunk_index: int | None = None,
    section: str | None = None,
    speakers: list[str] | None = None,
) -> str:
    parts = [
        f"[corpus={corpus}]",
        f"[org_domain={org_domain}]",
        f"[title={title}]",
    ]
    if project_id:
        parts.append(f"[project={project_id}]")
    if series_id:
        parts.append(f"[series={series_id}]")
    if meeting_id:
        parts.append(f"[meeting={meeting_id}]")
    if section:
        parts.append(f"[section={section}]")
    if speakers:
        parts.append(f"[speakers={','.join(speakers[:5])}]")
    if chunk_index is not None:
        parts.append(f"[chunk={chunk_index}]")
    return " ".join(parts)


class HybridRagIndex(VectorIndex):
    def __init__(self, embedder: EmbeddingProvider | None = None) -> None:
        self.embedder = embedder or get_embedding_provider()
        self.chunks: dict[str, RagChunk] = {}

    def upsert(self, chunk: RagChunk) -> RagChunk:
        emb: EmbeddingResult = self.embedder.embed(chunk.indexed_text)
        chunk.dense = emb.dense
        chunk.sparse = emb.sparse
        chunk.vector_ref = f"{emb.model_id}:{chunk.chunk_id}"
        self.chunks[chunk.chunk_id] = chunk
        return chunk

    def upsert_many(self, chunks: list[RagChunk]) -> list[RagChunk]:
        return [self.upsert(c) for c in chunks]

    def drop_source(self, source_id: str) -> int:
        drop = [cid for cid, c in self.chunks.items() if c.source_id == source_id]
        for cid in drop:
            del self.chunks[cid]
        return len(drop)

    def _candidates(
        self,
        *,
        user_id: str,
        org_domains: list[str],
        corpora: list[str] | None,
        allow_write_classes: list[str] | None,
    ) -> list[RagChunk]:
        out = []
        for c in self.chunks.values():
            if corpora and c.corpus not in corpora:
                continue
            if c.org_domain not in org_domains:
                continue
            if allow_write_classes and c.write_class not in allow_write_classes:
                continue
            # ACL first — never score then filter as only defense
            if user_id not in c.acl_principals and "*" not in c.acl_principals:
                continue
            if c.classification == "critical" and c.write_class == "wide":
                continue  # invariant: should not exist; skip if corrupted
            out.append(c)
        return out

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
        cands = self._candidates(
            user_id=user_id,
            org_domains=org_domains,
            corpora=corpora,
            allow_write_classes=allow_write_classes,
        )
        if not cands:
            return []
        q = self.embedder.embed_query(query)
        scored: list[RagHit] = []
        for c in cands:
            ds = cosine(q.dense, c.dense)
            ss = sparse_dot(q.sparse, c.sparse)
            score = dense_weight * ds + sparse_weight * ss
            # light rerank: continuum open items / same domain already filtered
            if c.corpus == "continuum" and c.meta.get("open"):
                score += 0.05
            sp = str(c.meta.get("speaker") or "")
            if sp and sp in query:
                score += 0.03
            sec = str(c.meta.get("section") or "")
            if sec and "决议" in query and "决议" in sec:
                score += 0.03
            scored.append(
                RagHit(
                    chunk_id=c.chunk_id,
                    corpus=c.corpus,
                    source_id=c.source_id,
                    text=c.body,
                    score=round(score, 6),
                    dense_score=round(ds, 6),
                    sparse_score=round(ss, 6),
                    citation={
                        "corpus": c.corpus,
                        "id": c.source_id,
                        "source_id": c.source_id,
                        "span": c.chunk_id,
                        "vector_ref": c.vector_ref,
                        "classification": c.classification,
                        "write_class": c.write_class,
                        "chunk_index": str(c.meta.get("chunk_index", 0)),
                        "speaker": sp,
                        "start_ms": str(
                            c.meta.get("start_ms") if c.meta.get("start_ms") is not None else ""
                        ),
                        "section": sec,
                    },
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]


class RagPipeline:
    """Full Meeting Knowledge Plane retrieval (03 §2.4)."""

    def __init__(
        self,
        embedder: EmbeddingProvider | None = None,
        chunk_config: ChunkConfig | None = None,
        index: VectorIndex | None = None,
    ) -> None:
        self.index = index or HybridRagIndex(embedder)
        self.chunk_config = chunk_config or ChunkConfig()

    def _build_chunks(
        self,
        *,
        source_id: str,
        corpus: str,
        org_domain: str,
        classification: str,
        write_class: str,
        acl_principals: list[str],
        title: str,
        body: str,
        project_id: str | None = None,
        meeting_id: str | None = None,
        series_id: str | None = None,
        content_kind: ContentKind | None = None,
        segments: list[dict[str, Any]] | None = None,
        extra_meta: dict[str, Any] | None = None,
    ) -> list[RagChunk]:
        kind = content_kind or (ContentKind.TRANSCRIPT if segments else detect_content_kind(body))
        text_chunks: list[TextChunk] = chunk_by_kind(
            kind=kind,
            text=body,
            segments=segments,
            config=self.chunk_config,
        )
        if not text_chunks and body.strip():
            text_chunks = [
                TextChunk(index=0, body=body.strip(), meta={"kind": kind.value}),
            ]

        rag_chunks: list[RagChunk] = []
        for tc in text_chunks:
            speakers = tc.meta.get("speakers") or (
                [tc.meta["speaker"]] if tc.meta.get("speaker") else None
            )
            prefix = contextual_prefix(
                corpus=corpus,
                org_domain=org_domain,
                title=title,
                project_id=project_id,
                meeting_id=meeting_id,
                series_id=series_id,
                chunk_index=tc.index,
                section=tc.meta.get("section"),
                speakers=speakers,
            )
            meta = dict(extra_meta or {})
            meta.update(tc.meta)
            meta["chunk_index"] = tc.index
            meta["title"] = title
            rag_chunks.append(
                RagChunk(
                    chunk_id=f"{corpus}:{source_id}:{tc.index}",
                    corpus=corpus,
                    org_domain=org_domain,
                    classification=classification,
                    write_class=write_class,
                    acl_principals=acl_principals,
                    context_prefix=prefix,
                    body=tc.body,
                    source_id=source_id,
                    meta=meta,
                )
            )
        return rag_chunks

    def index_doc(
        self,
        *,
        doc_id: str,
        org_domain: str,
        classification: str,
        acl_principals: list[str],
        title: str,
        body: str,
        write_class: str = "domain",
        project_id: str | None = None,
        content_kind: ContentKind | None = None,
    ) -> list[RagChunk]:
        self.index.drop_source(doc_id)
        chunks = self._build_chunks(
            source_id=doc_id,
            corpus="docs",
            org_domain=org_domain,
            classification=classification,
            write_class=write_class,
            acl_principals=acl_principals,
            title=title,
            body=body,
            project_id=project_id,
            content_kind=content_kind,
        )
        return self.index.upsert_many(chunks)

    def index_transcript(
        self,
        *,
        meeting_id: str,
        org_domain: str,
        classification: str,
        acl_principals: list[str],
        segments: list[dict[str, Any]] | None = None,
        title: str = "meeting_transcript",
        write_class: str = "domain",
        series_id: str | None = None,
        transcript_id: str | None = None,
        body: str | None = None,
    ) -> list[RagChunk]:
        segs = list(segments or [])
        source_id = transcript_id or meeting_id
        self.index.drop_source(source_id)
        joined = body or "\n".join(
            f"{s.get('speaker', '未知')}：{s.get('text', '')}"
            for s in segs
            if s.get("text")
        )
        chunks = self._build_chunks(
            source_id=source_id,
            corpus="transcript",
            org_domain=org_domain,
            classification=classification,
            write_class=write_class,
            acl_principals=acl_principals,
            title=title,
            body=joined,
            meeting_id=meeting_id,
            series_id=series_id,
            content_kind=ContentKind.TRANSCRIPT,
            segments=segs or None,
            extra_meta={"meeting_id": meeting_id, "content_kind": "transcript"},
        )
        return self.index.upsert_many(chunks)

    def index_continuum(
        self,
        *,
        item_id: str,
        org_domain: str,
        classification: str,
        acl_principals: list[str],
        summary: str,
        write_class: str,
        meeting_id: str,
        series_id: str | None = None,
        open_item: bool = False,
    ) -> RagChunk | None:
        if write_class == "none":
            return None
        if classification == "critical" and write_class == "wide":
            raise ValueError("critical continuum cannot index as wide")
        chunks = self._build_chunks(
            source_id=item_id,
            corpus="continuum",
            org_domain=org_domain,
            classification=classification,
            write_class=write_class,
            acl_principals=acl_principals,
            title="meeting_continuum",
            body=summary,
            meeting_id=meeting_id,
            series_id=series_id,
            content_kind=ContentKind.PLAIN_DOC,
            extra_meta={"open": open_item, "meeting_id": meeting_id},
        )
        upserted = self.index.upsert_many(chunks)
        return upserted[0] if upserted else None

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        org_domains: list[str],
        max_hops: int = 3,
        top_k: int = 5,
        min_score: float = 0.01,
    ) -> RagSearchResult:
        queries = [query]
        hops = 0
        used: list[str] = []
        best: list[RagHit] = []
        model_id = getattr(self.index.embedder, "model_id", "unknown")

        while queries and hops < max_hops:
            q = queries.pop(0)
            used.append(q)
            hops += 1
            hits = self.index.search_once(
                q,
                user_id=user_id,
                org_domains=org_domains,
                top_k=top_k,
            )
            hits = [h for h in hits if h.score >= min_score]
            if hits:
                best = hits
                break
            # bounded multi-hop：确定性 rule rewrite（非 LLM Agentic）
            if hops < max_hops:
                rewrite = self._rule_rewrite_query(q, hop=hops)
                if rewrite and rewrite not in used:
                    queries.append(rewrite)

        return RagSearchResult(
            hits=best,
            hops=hops,
            queries_used=used,
            model_id=model_id,
            empty_reason=None if best else "no_hits_after_acl_and_hops",
        )

    def grounded_answer(
        self,
        *,
        query: str,
        user_id: str,
        org_domains: list[str],
        max_hops: int = 3,
        top_k: int = 5,
        min_score: float = 0.01,
        abstain_threshold: float = 0.02,
    ) -> "GroundedAnswer":
        """retrieve → build_grounded_answer（faithfulness + citations）。"""
        from app.knowledge.grounding import build_grounded_answer

        result = self.retrieve(
            query=query,
            user_id=user_id,
            org_domains=org_domains,
            max_hops=max_hops,
            top_k=top_k,
            min_score=min_score,
        )
        if not result.hits or result.hits[0].score < abstain_threshold:
            return build_grounded_answer(query=query, hits=[])
        return build_grounded_answer(query=query, hits=result.hits, max_evidence=top_k)

    @staticmethod
    def _rule_rewrite_query(query: str, hop: int) -> str:
        """Bounded multi-hop 确定性 query 改写（rule-based，非生产 LLM）。"""
        if hop == 1:
            # drop filler, keep head terms
            parts = [p for p in query.replace("，", " ").replace(",", " ").split() if len(p) > 1]
            return parts[0] if parts else query
        if hop == 2:
            for syn in (("超时", "SLA 重试"), ("灰度", "canary 发布"), ("整改", "台账 未关闭")):
                if syn[0] in query:
                    return f"{query} {syn[1]}"
            return f"{query} 规范 约定"
        return query
