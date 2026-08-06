"""Tests: audit chain graph verify, publish profile flags, critical re-eval, metrics SoT."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SAFETY_DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'test_audit_chain.db'}")
os.environ.setdefault("SAFETY_SCANNER_MODE", "shim")
os.environ.setdefault("SAFETY_OIDC_DISABLED", "1")


def test_corpus_metrics_computed_from_yaml():
    from app.eval.corpus_metrics import assert_profile_metrics, get_corpus_metrics

    m = get_corpus_metrics()
    assert m["total_corpus"] == 2500
    assert m["expect_block"] == 2400
    assert m["profiles"]["ci"]["fp"] == 310
    assert m["profiles"]["release"]["fp"] == 410
    assert m["profiles"]["release"]["attack"] == 600
    assert m["profiles"]["full"]["attack"] == 2400
    assert_profile_metrics("ci", attack=120, fp=310)
    assert_profile_metrics("release", attack=600, fp=410)
    assert_profile_metrics("full", attack=2400, fp=410)


def test_publish_profile_config():
    from app.eval.publish_profile import load_publish_profile, publish_profile_audit

    prof = load_publish_profile()
    assert prof.get("profile") == "publish"
    assert (prof.get("corpus_shim") or {}).get("blocking") is True
    audit = publish_profile_audit()
    assert audit["dual_gate_profile"] == "ci"
    assert audit["metrics"]["total_corpus"] == 2500


def test_dual_gate_metric_counts():
    from app.eval.dual_gates import run_dual_gates

    ci = run_dual_gates("ci")
    assert ci["passed"]
    assert ci["attack"]["case_count"] == 120
    assert ci["fp"]["case_count"] == 310

    rel = run_dual_gates("release")
    assert rel["passed"]
    assert rel["attack"]["case_count"] == 600
    assert rel["fp"]["case_count"] == 410

    full = run_dual_gates("full")
    assert full["passed"]
    assert full["attack"]["case_count"] == 2400
    assert full["fp"]["case_count"] == 410


def _make_row(request_id: str, env: dict, *, prev: str) -> object:
    from types import SimpleNamespace

    return SimpleNamespace(
        request_id=request_id,
        body_json=json.dumps(env, ensure_ascii=False),
        chain_hash=env["chain_hash"],
        prev_chain_hash=env.get("prev_chain_hash", prev),
        decision=env.get("decision", "allow"),
        content_hash=env.get("content_hash", ""),
    )


def _chain_env(i: int, prev: str) -> dict:
    from app.gateway.envelope import build_decision
    from app.observability.siem import HashChainLedger

    env = build_decision(
        request_id=f"req_{i}",
        tenant_id="t_demo",
        app_id="customer_bot",
        policy_binding_id="pb_test",
        policy_version=1,
        risk_tier="medium",
        layer="L1",
        decision="allow",
        reason_codes=[],
        scanner_results=[],
        source_text=f"hello {i}",
        retention="hash_only",
        latency_ms=1.0,
    )
    led = HashChainLedger()
    led._prev = prev  # noqa: SLF001
    led.write(env)
    return env


def test_chain_out_of_order_db_order_still_valid():
    from app.observability.chain_verify import rebuild_chain_from_rows, verify_audit_rows

    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    rows = [
        _make_row("req_1", e1, prev=e0["chain_hash"]),
        _make_row("req_0", e0, prev="GENESIS"),
    ]
    ordered, result = rebuild_chain_from_rows(rows)
    assert result["ok"] is True
    assert len(ordered) == 2
    assert verify_audit_rows(rows)["ok"] is True


def test_chain_fork_detected():
    from app.observability.chain_verify import verify_audit_rows

    e0 = _chain_env(0, "GENESIS")
    e1a = _chain_env(1, e0["chain_hash"])
    e1b = _chain_env(2, e0["chain_hash"])
    rows = [
        _make_row("req_0", e0, prev="GENESIS"),
        _make_row("req_1a", e1a, prev=e0["chain_hash"]),
        _make_row("req_1b", e1b, prev=e0["chain_hash"]),
    ]
    result = verify_audit_rows(rows)
    assert result["ok"] is False
    assert result["error"] == "fork"


def test_hydrate_fail_closed_on_broken_chain():
    from app.observability.chain_verify import ChainIntegrityError, hydrate_ledger_from_rows
    from app.observability.siem import HashChainLedger

    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    e1_bad = dict(e1)
    e1_bad["chain_hash"] = "deadbeef"
    rows = [_make_row("req_0", e0, prev="GENESIS"), _make_row("req_1", e1_bad, prev=e0["chain_hash"])]
    ledger = HashChainLedger()
    with pytest.raises(ChainIntegrityError):
        hydrate_ledger_from_rows(ledger, rows)
    assert ledger.chain == []


def test_chain_verify_cross_restart(monkeypatch, tmp_path):
    import app.bootstrap as bootstrap
    import app.config
    import app.db.models as models
    from app.db import get_session, init_db
    from app.db.models import AuditDecisionRow
    from app.observability.chain_verify import verify_audit_rows

    db_path = tmp_path / "test_chain_cross.db"
    monkeypatch.setenv("SAFETY_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr(models, "settings", app.config.Settings.from_env())
    bootstrap._STATE = None
    models._engine = None
    models.SessionLocal = None
    init_db()

    prev = "GENESIS"
    for i in range(3):
        env = _chain_env(i, prev)
        prev = env["chain_hash"]
        db = get_session()
        try:
            db.add(
                AuditDecisionRow(
                    request_id=env["request_id"],
                    tenant_id="t_demo",
                    app_id="customer_bot",
                    decision=env["decision"],
                    body_json=json.dumps(env, ensure_ascii=False),
                    content_hash=env["content_hash"],
                    chain_hash=env["chain_hash"],
                    prev_chain_hash=env["prev_chain_hash"],
                )
            )
            db.commit()
        finally:
            db.close()

    db = get_session()
    try:
        rows = db.query(AuditDecisionRow).all()
        result = verify_audit_rows(rows)
        assert result["ok"] is True
        assert result["length"] == 3
    finally:
        db.close()

    bootstrap._STATE = None
    from app.bootstrap import AppState

    st = AppState()
    assert st.chain_ok is True
    assert len(st.ledger.chain) == 3


def test_bootstrap_fail_closed_on_corrupt_chain(monkeypatch, tmp_path):
    import app.bootstrap as bootstrap
    import app.config
    import app.db.models as models
    from app.db import get_session, init_db
    from app.db.models import AuditDecisionRow

    db_path = tmp_path / "test_chain_corrupt.db"
    monkeypatch.setenv("SAFETY_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr(models, "settings", app.config.Settings.from_env())
    bootstrap._STATE = None
    models._engine = None
    models.SessionLocal = None
    init_db()

    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    db = get_session()
    db.add(
        AuditDecisionRow(
            request_id="req_0",
            tenant_id="t",
            app_id="a",
            decision="allow",
            body_json=json.dumps(e0),
            content_hash=e0["content_hash"],
            chain_hash=e0["chain_hash"],
            prev_chain_hash="GENESIS",
        )
    )
    db.add(
        AuditDecisionRow(
            request_id="req_1",
            tenant_id="t",
            app_id="a",
            decision="allow",
            body_json=json.dumps(e1),
            content_hash=e1["content_hash"],
            chain_hash="tampered",
            prev_chain_hash=e0["chain_hash"],
        )
    )
    db.commit()
    db.close()

    bootstrap._STATE = None
    from app.bootstrap import AppState

    st = AppState()
    assert st.chain_ok is False
    assert st.chain_error is not None
    assert len(st.ledger.chain) == 0


def test_legacy_schema_migration_adds_chain_columns(tmp_path, monkeypatch):
    import sqlalchemy as sa
    import app.config
    import app.db.models as models
    from app.db.migrate import upgrade_audit_chain_columns

    db_path = tmp_path / "legacy.db"
    monkeypatch.setenv("SAFETY_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr(models, "settings", app.config.Settings.from_env())
    models._engine = None
    models.SessionLocal = None

    eng = sa.create_engine(f"sqlite:///{db_path}")
    with eng.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE audit_decisions ("
                "id INTEGER PRIMARY KEY, request_id VARCHAR(64), "
                "tenant_id VARCHAR(64), app_id VARCHAR(64), decision VARCHAR(32), "
                "body_json TEXT, content_hash VARCHAR(128))"
            )
        )
    applied = upgrade_audit_chain_columns(eng)
    assert "audit_decisions.chain_hash" in applied
    assert "audit_decisions.prev_chain_hash" in applied
    applied2 = upgrade_audit_chain_columns(eng)
    assert applied2 == []


def test_backfill_chain_from_body_json_and_compute(tmp_path, monkeypatch):
    import sqlalchemy as sa
    import app.config
    import app.db.models as models
    from app.db.migrate import backfill_audit_chain_hashes, upgrade_audit_chain_columns
    from app.observability.chain_verify import verify_audit_rows

    db_path = tmp_path / "backfill.db"
    monkeypatch.setenv("SAFETY_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr(models, "settings", app.config.Settings.from_env())
    models._engine = None
    models.SessionLocal = None

    eng = sa.create_engine(f"sqlite:///{db_path}")
    with eng.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE audit_decisions ("
                "id INTEGER PRIMARY KEY, request_id VARCHAR(64), "
                "tenant_id VARCHAR(64), app_id VARCHAR(64), decision VARCHAR(32), "
                "body_json TEXT, content_hash VARCHAR(128), "
                "chain_hash VARCHAR(128) DEFAULT '', prev_chain_hash VARCHAR(128) DEFAULT '')"
            )
        )

    upgrade_audit_chain_columns(eng)

    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    body_only_e1 = {k: v for k, v in e1.items() if k not in ("chain_hash", "prev_chain_hash")}

    with eng.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO audit_decisions "
                "(request_id, tenant_id, app_id, decision, body_json, content_hash, chain_hash, prev_chain_hash) "
                "VALUES (:rid, 't', 'a', 'allow', :body, :ch, '', '')"
            ),
            {"rid": "req_body", "body": json.dumps(e0, ensure_ascii=False), "ch": e0["content_hash"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO audit_decisions "
                "(request_id, tenant_id, app_id, decision, body_json, content_hash, chain_hash, prev_chain_hash) "
                "VALUES (:rid, 't', 'a', 'allow', :body, :ch, '', '')"
            ),
            {
                "rid": "req_compute",
                "body": json.dumps(body_only_e1, ensure_ascii=False),
                "ch": body_only_e1["content_hash"],
            },
        )

    stats1 = backfill_audit_chain_hashes(eng)
    assert stats1["copied_from_body"] == 1
    assert stats1["computed"] == 1

    stats2 = backfill_audit_chain_hashes(eng)
    assert stats2["skipped"] == 2
    assert stats2["computed"] == 0

    with eng.connect() as conn:
        rows = conn.execute(sa.text("SELECT * FROM audit_decisions ORDER BY id")).fetchall()

    class _Row:
        def __init__(self, r) -> None:
            self.request_id = r[1]
            self.body_json = r[5]
            self.chain_hash = r[7]
            self.prev_chain_hash = r[8]

    result = verify_audit_rows([_Row(r) for r in rows])
    assert result["ok"] is True


def test_chain_duplicate_hash_detected():
    from app.observability.chain_verify import verify_audit_rows

    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    dup = dict(e1)
    rows = [
        _make_row("req_0", e0, prev="GENESIS"),
        _make_row("req_1", e1, prev=e0["chain_hash"]),
        _make_row("req_dup", dup, prev=e0["chain_hash"]),
    ]
    result = verify_audit_rows(rows)
    assert result["ok"] is False
    assert result["error"] == "duplicate_chain_hash"


def test_chain_orphan_detected():
    from app.observability.chain_verify import verify_audit_rows

    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    e2 = _chain_env(2, e1["chain_hash"])
    # break link: e2 points to wrong prev (orphan branch)
    orphan = dict(e2)
    orphan["prev_chain_hash"] = "deadbeef"
    orphan["chain_hash"] = _chain_env(99, "deadbeef")["chain_hash"]
    rows = [
        _make_row("req_0", e0, prev="GENESIS"),
        _make_row("req_1", e1, prev=e0["chain_hash"]),
        _make_row("req_orphan", orphan, prev="deadbeef"),
    ]
    result = verify_audit_rows(rows)
    assert result["ok"] is False
    assert result["error"] in ("orphan", "missing_link")


def test_chain_cycle_detected():
    """cycle 由遍历主链时重复访问同一 hash 触发（防御性检测）。"""
    from types import SimpleNamespace

    from app.observability.chain_verify import rebuild_chain_from_rows

    # 两条互指：A.prev=GENESIS→ha, B.prev=ha→hb；再插 C.prev=hb 且 hash=ha（与 A 同 hash，先 duplicate）
    # 直接构造 visited 冲突：主链 GENESIS→H1→H2，第三条 prev=H2 但 hash 已在 visited
    e0 = _chain_env(0, "GENESIS")
    e1 = _chain_env(1, e0["chain_hash"])
    # 篡改 e1 的 stored hash 使其与 e0 相同（绕过 duplicate 前的不同 request_id）
    tampered = SimpleNamespace(
        request_id="req_t",
        body_json=json.dumps(e1, ensure_ascii=False),
        chain_hash=e0["chain_hash"],
        prev_chain_hash=e0["chain_hash"],
        decision="allow",
        content_hash=e1["content_hash"],
    )
    rows = [
        _make_row("req_0", e0, prev="GENESIS"),
        _make_row("req_1", e1, prev=e0["chain_hash"]),
        tampered,
    ]
    _, result = rebuild_chain_from_rows(rows)
    assert result["ok"] is False
    assert result["error"] in ("duplicate_chain_hash", "cycle", "hash_mismatch")


def test_publish_gates_respect_disabled_flags(monkeypatch):
    from app.eval import publish_profile as pp

    def _fake_load():
        return {
            "corpus_shim": {"enabled": False, "blocking": True},
            "fp_gates": {"enabled": False, "blocking": True},
            "dual_gate": {"enabled": False, "blocking": True},
            "remote_judge_compare": {"enabled": False, "blocking": False},
        }

    monkeypatch.setattr(pp, "load_publish_profile", _fake_load)
    report = pp.run_publish_gates()
    assert report["passed"] is True
    names = {g["gate"] for g in report["gates_audit"]}
    assert "corpus_shim" in names
    skipped = [g for g in report["gates_audit"] if g["status"] == "skipped"]
    assert len(skipped) >= 3


def test_siem_chain_metadata():
    from app.observability.siem import FileSIEMBackend, HashChainLedger, SIEMSink

    path = ROOT / "data" / "_test_siem_chain.jsonl"
    if path.exists():
        path.unlink()
    sink = SIEMSink(backend=FileSIEMBackend(str(path)))
    ledger = HashChainLedger()
    d = {"request_id": "r_siem", "decision": "block"}
    ledger.write(d)
    sink.emit(
        {
            "event_type": "safety.decision",
            "request_id": "r_siem",
            "decision": "block",
            "chain_hash": d["chain_hash"],
            "prev_chain_hash": d["prev_chain_hash"],
        }
    )
    row = json.loads(path.read_text(encoding="utf-8").strip())
    assert row["chain_hash"] == d["chain_hash"]
    assert row["prev_chain_hash"] == d["prev_chain_hash"]


def test_remote_judge_skip_without_url(monkeypatch):
    monkeypatch.delenv("SAFETY_CLASSIFIER_URL", raising=False)
    monkeypatch.delenv("SAFETY_REMOTE_JUDGE_URL", raising=False)
    monkeypatch.delenv("MODERATION_MOCK", raising=False)
    from app.eval.remote_judge_compare import run_remote_judge_compare, sanitize_classifier_url

    report = run_remote_judge_compare(enabled=True, skip_without_url=True)
    assert report["status"] == "skipped"
    assert report["reason"] == "no_classifier_url_or_credentials"
    assert sanitize_classifier_url("http://user:secret@host:8091/v1/classify?token=abc") == "http://host:8091/v1/classify"


def test_remote_judge_url_sanitized_in_report(monkeypatch):
    monkeypatch.setenv("SAFETY_CLASSIFIER_URL", "https://api:key@judge.example/v1/classify?sig=xyz")
    from app.eval.remote_judge_compare import sanitize_classifier_url

    assert sanitize_classifier_url(os.environ["SAFETY_CLASSIFIER_URL"]) == "https://judge.example/v1/classify"
