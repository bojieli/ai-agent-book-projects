"""M6 质量门禁规模与负例。"""

from __future__ import annotations

from app.eval.m6_quality_gates import run_m6_quality_gates
from app.eval.negative_runners import run_negative_catalog


def test_m6_quality_gates_pass():
    report = run_m6_quality_gates()
    assert report["ok"] is True
    assert report["counts"]["rag_cases"] >= 60
    assert report["counts"]["agent_stories"] >= 30
    assert report["counts"]["negatives"] >= 20


def test_negative_catalog_all_pass():
    results = run_negative_catalog()
    assert len(results) >= 20
    failed = [r for r in results if not r[1]]
    assert failed == []
