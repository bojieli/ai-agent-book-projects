"""M5：审计链双副本分叉可检测。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.observability.audit_lock import audit_chain_lock, simulate_dual_writer_fork


def test_dual_writer_fork_is_detected():
    out = simulate_dual_writer_fork()
    assert out["ok"] is True
    assert out["verify"]["error"] == "fork"
    assert "recovery" in out


def test_audit_chain_lock_context():
    with audit_chain_lock(None):
        assert True
