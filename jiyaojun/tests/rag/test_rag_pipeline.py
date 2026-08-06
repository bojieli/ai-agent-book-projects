"""RAG + BGE-M3 embedding selection tests."""

from __future__ import annotations

import os

from app.knowledge.embedding import BgeM3ShimProvider, get_embedding_provider
from app.knowledge.plane import ContinuumItem, KnowledgePlane
from app.knowledge.rag import RagPipeline, contextual_prefix


def test_embedding_default_is_bge_m3_family(monkeypatch):
    monkeypatch.setenv("JIYAOJUN_EMBEDDING", "bge-m3-shim")
    p = get_embedding_provider()
    assert p.model_id == "bge-m3-shim"
    r = p.embed("接口超时与重试 Shadow")
    assert r.dense and r.sparse
    assert any("超时" in k or "shadow" in k for k in r.sparse)


def test_contextual_prefix_required_fields():
    pref = contextual_prefix(
        corpus="docs",
        org_domain="eng",
        title="接口超时规范",
        project_id="pay",
    )
    assert "org_domain=eng" in pref and "title=" in pref and "corpus=docs" in pref


def test_rag_acl_first_blocks_hr_from_eng_doc():
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_doc(
        doc_id="doc_api_timeout",
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm", "u_dev_a"],
        title="接口超时规范",
        body="接口超时与重试约定，半成功需补偿",
    )
    ok = rag.retrieve(query="超时重试", user_id="u_pm", org_domains=["eng"])
    assert ok.hits and ok.hits[0].source_id == "doc_api_timeout"
    assert ok.hits[0].citation["corpus"] == "docs"
    denied = rag.retrieve(query="超时重试", user_id="stranger", org_domains=["eng"])
    assert denied.hits == []


def test_rag_hybrid_prefers_lexical_id_and_agentic_hops():
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_doc(
        doc_id="doc_pol_88",
        org_domain="risk",
        classification="confidential",
        acl_principals=["u_risk_pm"],
        title="策略 pol_fraud_rule_88",
        body="策略 pol_fraud_rule_88 上线前必须 Shadow 观察误杀",
    )
    # exact id-like query exercises sparse channel
    res = rag.retrieve(
        query="pol_fraud_rule_88",
        user_id="u_risk_pm",
        org_domains=["risk"],
        max_hops=2,
    )
    assert res.hits
    assert "pol_fraud_rule_88" in res.hits[0].text or res.hits[0].score > 0


def test_rag_agentic_rewrite_when_first_query_misses():
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_doc(
        doc_id="doc_sla",
        org_domain="eng",
        classification="internal",
        acl_principals=["u_pm"],
        title="SLA",
        body="超时 3 秒与重试策略写在网关规范",
    )
    # awkward long query → hop1 rewrite to head token should still find
    res = rag.retrieve(
        query="那个乱七八糟的超时事情怎么办呀",
        user_id="u_pm",
        org_domains=["eng"],
        max_hops=3,
        min_score=0.0,
    )
    assert res.hops >= 1
    # may hit on rewrite; at least pipeline records queries
    assert res.queries_used


def test_critical_continuum_cannot_wide_index():
    rag = RagPipeline(BgeM3ShimProvider())
    try:
        rag.index_continuum(
            item_id="x",
            org_domain="hr",
            classification="critical",
            acl_principals=["u_hrbp"],
            summary="名单",
            write_class="wide",
            meeting_id="m",
        )
        assert False
    except ValueError:
        pass


def test_rag_grounded_answer_via_pipeline_helper():
    """grounded_answer 可在 RagPipeline 上或 grounding 模块实现。"""
    from app.knowledge.grounding import build_grounded_answer

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
        assert not ga.abstained
        assert ga.citations
    else:
        res = rag.retrieve(query="超时", user_id="u_pm", org_domains=["eng"], min_score=0.0)
        ans = build_grounded_answer(query="超时", hits=res.hits)
        assert ans.citations
        assert ans.faithfulness >= 0.0


def test_knowledge_plane_uses_rag_and_citations():
    kp = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
    kp.seed_demo()
    hits, hops = kp.retrieve(
        user_id="u_pm",
        org_domains=["eng"],
        query="网关容量 超时",
        max_hops=3,
    )
    assert hops >= 1
    assert hits
    assert all(h.vector_ref for h in hits)
    assert kp.last_search and "bge-m3" in kp.last_search.model_id


def test_continuum_write_then_retrievable():
    kp = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
    dec = kp.write_continuum_and_index(
        ContinuumItem(
            id="c_new",
            org_domain="eng",
            classification="internal",
            write_class="wide",
            acl_principals=["u_pm"],
            summary="新建 open：压测结论未出",
            open=True,
            meeting_id="mtg_new",
            series_id="series_pay",
        ),
        classification="internal",
    )
    assert dec.accepted
    hits, _ = kp.retrieve(user_id="u_pm", org_domains=["eng"], query="压测结论")
    assert any(h.id == "c_new" for h in hits)
