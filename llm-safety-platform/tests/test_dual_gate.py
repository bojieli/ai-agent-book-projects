"""Dual-gate: attack efficacy + false-positive budget must both pass."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.eval.dual_gates import run_dual_gates


def test_dual_gate_ci_passes() -> None:
    report = run_dual_gates("ci")
    assert report["passed"], report.get("failed")
    assert report["attack"]["passed"]
    assert report["fp"]["passed"]
    assert report["fp"]["rate"] == 0.0
    assert report["attack"]["rate"] == 0.0
    assert report["attack"]["case_count"] == 120
    assert report["fp"]["case_count"] == 310


def test_dual_gate_release_fp_count() -> None:
    report = run_dual_gates("release")
    assert report["passed"], report.get("failed")
    assert report["fp"]["case_count"] == 410
    assert report["attack"]["case_count"] == 600


def test_dual_gate_full_attack_count() -> None:
    report = run_dual_gates("full")
    assert report["passed"], report.get("failed")
    assert report["attack"]["case_count"] == 2400
    assert report["fp"]["case_count"] == 410
