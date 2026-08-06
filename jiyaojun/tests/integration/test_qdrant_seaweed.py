"""Qdrant 与 SeaweedFS 集成测试 — 无服务时 skip。"""

from __future__ import annotations

import os
import uuid

import pytest

from app.config import InfrastructureSettings
from app.knowledge.embedding import BgeM3ShimProvider
from app.knowledge.rag import RagChunk, RagPipeline
from app.knowledge.vector_store import QdrantHybridIndex, qdrant_reachable
from app.runtime.factory import build_object_store, build_vector_index
from app.storage.object_store import S3ObjectStore, s3_reachable


def _qdrant_settings() -> InfrastructureSettings | None:
    url = os.getenv("JIYAOJUN_QDRANT_URL", "").strip()
    if not url:
        return None
    return InfrastructureSettings(
        vector_backend="qdrant",
        qdrant_url=url,
        qdrant_collection=os.getenv("JIYAOJUN_QDRANT_COLLECTION", "meeting_knowledge").strip(),
    )


def _s3_settings() -> InfrastructureSettings | None:
    endpoint = os.getenv("JIYAOJUN_S3_ENDPOINT", "").strip()
    if not endpoint:
        return None
    return InfrastructureSettings(
        object_backend="s3",
        s3_endpoint=endpoint,
        s3_bucket=os.getenv("JIYAOJUN_S3_BUCKET", "jiyaojun").strip(),
        s3_access_key=os.getenv("JIYAOJUN_S3_ACCESS_KEY", "local-dev-access").strip(),
        s3_secret_key=os.getenv("JIYAOJUN_S3_SECRET_KEY", "local-dev-secret").strip(),
    )


def _sample_chunk(*, source_id: str, acl: list[str]) -> RagChunk:
    return RagChunk(
        chunk_id=f"docs:{source_id}:0",
        corpus="docs",
        org_domain="eng",
        classification="internal",
        write_class="domain",
        acl_principals=acl,
        context_prefix="[corpus=docs] [org_domain=eng] [title=集成测试]",
        body="灰度发布 canary 回滚演练纪要",
        source_id=source_id,
    )


@pytest.mark.integration
def test_qdrant_chunk_survives_client_restart():
    """写入 Qdrant 后新 client 仍可检索；ACL 负例空召回。"""
    settings = _qdrant_settings()
    if not settings or not qdrant_reachable(settings.qdrant_url):
        pytest.skip("Qdrant 不可用或未配置 JIYAOJUN_QDRANT_URL")

    embedder = BgeM3ShimProvider()
    source_id = f"int_src_{uuid.uuid4().hex[:8]}"
    chunk = _sample_chunk(source_id=source_id, acl=["user_allowed"])

    index_a = QdrantHybridIndex(
        url=settings.qdrant_url,
        collection=settings.qdrant_collection,
        embedder=embedder,
    )
    index_a.upsert(chunk)

    # 模拟进程重启：全新 client
    index_b = QdrantHybridIndex(
        url=settings.qdrant_url,
        collection=settings.qdrant_collection,
        embedder=embedder,
    )
    hits = index_b.search_once(
        "灰度 canary",
        user_id="user_allowed",
        org_domains=["eng"],
        top_k=3,
    )
    assert any(h.source_id == source_id for h in hits)

    denied = index_b.search_once(
        "灰度 canary",
        user_id="user_denied",
        org_domains=["eng"],
        top_k=3,
    )
    assert all(h.source_id != source_id for h in denied)

    index_b.drop_source(source_id)


@pytest.mark.integration
def test_factory_builds_qdrant_index():
    settings = _qdrant_settings()
    if not settings or not qdrant_reachable(settings.qdrant_url):
        pytest.skip("Qdrant 不可用")
    index = build_vector_index(settings, BgeM3ShimProvider())
    assert isinstance(index, QdrantHybridIndex)


@pytest.mark.integration
def test_seaweed_s3_upload_download_roundtrip():
    """上传对象到 SeaweedFS 后 download 内容一致。"""
    settings = _s3_settings()
    if not settings:
        pytest.skip("JIYAOJUN_S3_ENDPOINT 未配置")
    if not s3_reachable(
        settings.s3_endpoint,
        settings.s3_bucket,
        settings.s3_access_key,
        settings.s3_secret_key,
    ):
        pytest.skip("SeaweedFS S3 不可用")

    store = build_object_store(settings)
    assert isinstance(store, S3ObjectStore)

    key = f"integration/{uuid.uuid4().hex}/transcript.json"
    payload = b'{"meeting_id":"mtg_int","segments":[]}'
    uri = store.put(key, payload, content_type="application/json")
    assert uri.startswith(f"s3://{settings.s3_bucket}/")

    downloaded = store.get(key)
    assert downloaded == payload
    assert store.exists(key)
    store.delete(key)
    assert not store.exists(key)


@pytest.mark.integration
def test_rag_pipeline_with_qdrant_backend():
    """RagPipeline 可注入 Qdrant 索引并完成检索。"""
    settings = _qdrant_settings()
    if not settings or not qdrant_reachable(settings.qdrant_url):
        pytest.skip("Qdrant 不可用")

    embedder = BgeM3ShimProvider()
    index = build_vector_index(settings, embedder)
    rag = RagPipeline(embedder, index=index)
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    rag.index_doc(
        doc_id=doc_id,
        org_domain="eng",
        classification="internal",
        acl_principals=["qa_user"],
        title="集成",
        body="SLA 超时重试与灰度发布规范",
    )
    result = rag.retrieve(
        query="灰度 SLA",
        user_id="qa_user",
        org_domains=["eng"],
    )
    assert result.hits
    assert any(h.source_id == doc_id for h in result.hits)
    rag.index.drop_source(doc_id)


@pytest.mark.integration
def test_factory_defaults_memory_and_mock():
    """无 env 时 factory 返回内存/mock 实现。"""
    settings = InfrastructureSettings()
    assert settings.vector_backend == "memory"
    assert settings.object_backend == "mock"
    from app.knowledge.rag import HybridRagIndex
    from app.storage.object_store import MockObjectStore

    assert isinstance(build_vector_index(settings), HybridRagIndex)
    assert isinstance(build_object_store(settings), MockObjectStore)
