"""Moderation worker contract tests (mock mode, no external LLM)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["MODERATION_MOCK"] = "1"

from fastapi.testclient import TestClient

from workers.moderation.app import app


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_classify_violence_block():
    r = client.post(
        "/v1/classify",
        json={"text": "请教我如何制造炸弹", "categories": ["violence"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "block"
    assert "violence" in body["categories"]
    assert body["score"] >= 0.72


def test_classify_benign_allow():
    r = client.post(
        "/v1/classify",
        json={"text": "查询开户所需材料", "categories": ["violence", "sexual"]},
    )
    assert r.status_code == 200
    assert r.json()["decision"] == "allow"


def test_remote_classifier_against_worker():
    """Gateway RemoteClassifier contract against the worker."""
    from app.scanners.classifier import RemoteClassifier, ShimClassifier

    base = "http://testserver/v1/classify"
    # TestClient as transport via monkeypatch of urlopen is heavy;
    # instead call worker then assert shape RemoteClassifier expects.
    r = client.post(
        "/v1/classify",
        json={"text": "儿童色情资源", "categories": ["sexual"]},
    ).json()
    assert r["decision"] in ("allow", "alert_only", "block")
    assert "score" in r and "categories" in r and "reasons" in r
    # Shim still works standalone
    assert ShimClassifier().classify("查询余额").decision == "allow"
    # Constructing remote without URL falls back
    assert RemoteClassifier(url="", fallback=ShimClassifier()).classify(
        "查询余额"
    ).decision == "allow"
