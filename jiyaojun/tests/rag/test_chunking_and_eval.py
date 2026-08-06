"""Chunking + grounding + multi-chunk RAG tests."""

from __future__ import annotations

from app.knowledge.chunking import (
    ChunkConfig,
    chunk_document,
    chunk_text,
    parse_plain_transcript,
)
from app.knowledge.embedding import BgeM3ShimProvider
from app.knowledge.grounding import build_grounded_answer, score_faithfulness
from app.knowledge.plane import KnowledgePlane
from app.knowledge.rag import RagPipeline
from app.knowledge.transcript import TranscriptDocument
from app.planes.dialog.service import DialogPlane
from app.eval.retrieval_quality import ndcg_at_k


def test_chunk_respects_headings_and_speakers():
    text = """## 接口超时规范
### 超时与重试
接口超时 3 秒，最多重试两次。
### 灰度
PM：灰度先 1% canary。
DEV：观察错误率后再放量到 10%。
"""
    chunks = chunk_text(text, ChunkConfig(max_chars=200, overlap_chars=40))
    assert len(chunks) >= 1
    units = parse_plain_transcript(text)
    assert any(
        (getattr(u, "speaker", None) == "PM")
        or (isinstance(u, dict) and u.get("speaker") == "PM")
        for u in units
    )


def test_chunk_segments_keep_timestamps():
    segs = [
        {"speaker": "PM", "text": "先对齐超时。", "start_ms": 0, "end_ms": 2000},
        {"speaker": "DEV", "text": "保持三秒重试两次。", "start_ms": 2500, "end_ms": 8000},
        {"speaker": "PM", "text": "决议：按规范执行。", "start_ms": 8500, "end_ms": 12000},
    ]
    chunks = chunk_document(segments=segs, cfg=ChunkConfig(max_chars=120, overlap_chars=20))
    assert chunks
    assert any(c.start_ms is not None for c in chunks)


def test_index_doc_creates_multiple_chunks():
    rag = RagPipeline(
        BgeM3ShimProvider(),
        ChunkConfig(max_chars=160, overlap_chars=30),
    )
    out = rag.index_doc(
        doc_id="doc_long",
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm"],
        title="长规范",
        body=(
            "## A\n" + ("接口超时与重试。" * 20) + "\n"
            "## B\n" + ("灰度 canary 放量。" * 20)
        ),
    )
    assert len(out) >= 2
    assert all(c.chunk_id.startswith("docs:doc_long:") for c in out)


def test_transcript_index_and_retrieve_with_speaker_meta():
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_transcript(
        meeting_id="mtg_x",
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm"],
        title="对齐会",
        segments=[
            {
                "speaker": "PM",
                "text": "决议：网关容量未完成前不扩切流。",
                "start_ms": 1000,
            },
            {"speaker": "DEV", "text": "超时保持三秒。", "start_ms": 5000},
        ],
    )
    res = rag.retrieve(query="决议 切流", user_id="u_pm", org_domains=["eng"], min_score=0.0)
    assert res.hits
    assert "transcript:" in res.hits[0].citation.get("span", "") or res.hits[0].corpus == "transcript"


def test_grounded_answer_faithfulness():
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_doc(
        doc_id="d1",
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm"],
        title="SLA",
        body="接口超时 3 秒，最多重试 2 次。",
    )
    res = rag.retrieve(query="超时重试", user_id="u_pm", org_domains=["eng"], min_score=0.0)
    ans = build_grounded_answer(query="超时重试", hits=res.hits)
    assert ans.citations
    assert ans.faithfulness >= 0.5
    faith, claims, _ = score_faithfulness("接口超时 3 秒，最多重试 2 次。", res.hits)
    assert faith >= 0.5 and claims


def test_dialog_ask_returns_citations():
    kp = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
    kp.seed_demo()
    dialog = DialogPlane(kp)
    reply = dialog.ask(user_id="u_pm", org_domains=["eng"], query="接口超时重试")
    assert reply.text
    assert reply.retrieve_hops >= 1


def test_knowledge_plane_ingest_transcript():
    kp = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
    doc = TranscriptDocument(
        transcript_document_id="td1",
        meeting_id="m1",
        object_key="s3://x",
        hotword_profile_id="eng_default",
        segments=[{"speaker": "A", "text": "半成功需补偿任务", "start_ms": 0}],
    )
    chunks = kp.ingest_transcript(
        doc,
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm"],
        title="会",
    )
    assert chunks
    hits, _ = kp.retrieve(user_id="u_pm", org_domains=["eng"], query="半成功补偿")
    assert hits


def test_rag_grounded_answer_method():
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_doc(
        doc_id="d2",
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm"],
        title="SLA",
        body="接口超时 3 秒。",
    )
    if hasattr(rag, "grounded_answer"):
        ga = rag.grounded_answer(query="超时", user_id="u_pm", org_domains=["eng"], min_score=0.0)
        assert ga.citations
    else:
        res = rag.retrieve(query="超时", user_id="u_pm", org_domains=["eng"], min_score=0.0)
        ans = build_grounded_answer(query="超时", hits=res.hits)
        assert ans.citations


def test_ndcg_deduplicates_chunks_from_same_source():
    """同一文档的多个 chunk 不能把 source 级 nDCG 推到 1 以上。"""
    score = ndcg_at_k(
        ["doc_a", "doc_a", "doc_b", "irrelevant"],
        {"doc_a", "doc_b"},
        k=5,
    )
    assert 0.0 <= score <= 1.0
    assert score == 1.0
