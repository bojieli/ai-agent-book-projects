"""Embedding report honesty."""

from __future__ import annotations

from app.knowledge.embedding import BgeM3ShimProvider, embedding_report


def test_embedding_report_shim():
    rep = embedding_report(BgeM3ShimProvider())
    assert rep["provider_kind"] == "shim"
    assert rep["ci_default"] == "true"
    assert "bge-m3-shim" in rep["model_id"]
