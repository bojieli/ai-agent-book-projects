"""Explicit publish evaluation profile — loaded from configs/evals/publish_profile.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.eval.corpus_metrics import get_corpus_metrics

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "configs" / "evals" / "publish_profile.yaml"


def load_publish_profile(path: Path | None = None) -> dict[str, Any]:
    p = path or PROFILE_PATH
    if not p.exists():
        return {
            "version": 1,
            "profile": "publish",
            "corpus_shim": {"enabled": True, "blocking": True},
            "fp_gates": {"enabled": True, "blocking": True},
            "dual_gate": {"enabled": True, "profile": "ci", "blocking": True},
            "remote_judge_compare": {
                "enabled": False,
                "blocking": False,
                "skip_without_classifier_url": True,
            },
        }
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def publish_profile_audit() -> dict[str, Any]:
    """Machine-readable profile metadata for publish API / reports."""
    prof = load_publish_profile()
    dg = prof.get("dual_gate") or {}
    rjc = prof.get("remote_judge_compare") or {}
    cs = prof.get("corpus_shim") or {}
    fp = prof.get("fp_gates") or {}
    return {
        "profile": prof.get("profile", "publish"),
        "version": prof.get("version", 1),
        "config_path": str(PROFILE_PATH.relative_to(ROOT)),
        "corpus_shim_enabled": bool(cs.get("enabled", True)),
        "corpus_shim_blocking": bool(cs.get("blocking", True)),
        "fp_gates_enabled": bool(fp.get("enabled", True)),
        "fp_gates_blocking": bool(fp.get("blocking", True)),
        "dual_gate_profile": dg.get("profile", "ci"),
        "dual_gate_enabled": bool(dg.get("enabled", True)),
        "dual_gate_blocking": bool(dg.get("blocking", True)),
        "remote_judge_compare_enabled": bool(rjc.get("enabled", False)),
        "remote_judge_compare_blocking": bool(rjc.get("blocking", False)),
        "metrics": get_corpus_metrics(),
        "boundary": (
            "shim/static corpus only; 0 leak/FP here does not imply production zero incidents"
        ),
        "chain_writer_mode": "single_writer_desensitized_rebuild",
    }


def _gate_result(
    name: str,
    *,
    enabled: bool,
    blocking: bool,
    passed: bool,
    detail: dict[str, Any],
    status: str = "ran",
) -> dict[str, Any]:
    return {
        "gate": name,
        "enabled": enabled,
        "blocking": blocking,
        "status": status,
        "passed": passed if enabled else True,
        "blocks_publish": enabled and blocking and not passed,
        **detail,
    }


def run_publish_gates() -> dict[str, Any]:
    """Execute publish-time gates per publish_profile.yaml with per-gate audit."""
    from app.eval.corpus_gates import run_corpus_gates
    from app.eval.remote_judge_compare import run_remote_judge_compare

    prof = load_publish_profile()
    audit = publish_profile_audit()
    cs_cfg = prof.get("corpus_shim") or {}
    fp_cfg = prof.get("fp_gates") or {}
    dg_cfg = prof.get("dual_gate") or {}
    rjc_cfg = prof.get("remote_judge_compare") or {}

    cs_enabled = bool(cs_cfg.get("enabled", True))
    fp_enabled = bool(fp_cfg.get("enabled", True))
    dg_enabled = bool(dg_cfg.get("enabled", True))
    dg_profile = dg_cfg.get("profile", "ci")
    rjc_enabled = bool(rjc_cfg.get("enabled", False))

    gates_audit: list[dict[str, Any]] = []
    blocking_failed: list[str] = []
    results: list[dict[str, Any]] = []

    gates = run_corpus_gates(
        include_shim=cs_enabled,
        include_fp=fp_enabled,
        include_dual_gate=dg_enabled,
        dual_gate_profile=dg_profile,
    )
    results.extend(gates.get("results") or [])

    if cs_enabled:
        shim_rows = [r for r in results if r.get("gate") == "attack" and "dual_gate" not in str(r.get("source", ""))]
        shim_passed = all(r.get("passed", True) for r in shim_rows) and bool(shim_rows or not cs_enabled)
        cs_blocking = bool(cs_cfg.get("blocking", True))
        gates_audit.append(
            _gate_result(
                "corpus_shim",
                enabled=True,
                blocking=cs_blocking,
                passed=shim_passed,
                detail={"results": shim_rows, "failed": [r["source"] for r in shim_rows if not r.get("passed")]},
            )
        )
        if cs_blocking and not shim_passed:
            blocking_failed.append("corpus_shim")
    else:
        gates_audit.append(
            _gate_result("corpus_shim", enabled=False, blocking=False, passed=True, detail={}, status="skipped")
        )

    if fp_enabled:
        fp_rows = [r for r in results if r.get("gate") == "fp"]
        fp_passed = all(r.get("passed", True) for r in fp_rows)
        fp_blocking = bool(fp_cfg.get("blocking", True))
        gates_audit.append(
            _gate_result(
                "fp_gates",
                enabled=True,
                blocking=fp_blocking,
                passed=fp_passed,
                detail={"results": fp_rows},
            )
        )
        if fp_blocking and not fp_passed:
            blocking_failed.append("fp_gates")
    else:
        gates_audit.append(
            _gate_result("fp_gates", enabled=False, blocking=False, passed=True, detail={}, status="skipped")
        )

    if dg_enabled:
        dual = gates.get("dual_gate") or {}
        dg_blocking = bool(dg_cfg.get("blocking", True))
        dg_passed = bool(dual.get("passed", False))
        gates_audit.append(
            _gate_result(
                f"dual_gate:{dg_profile}",
                enabled=True,
                blocking=dg_blocking,
                passed=dg_passed,
                detail={"dual_gate": dual},
            )
        )
        if dg_blocking and not dg_passed:
            blocking_failed.append(f"dual_gate:{dg_profile}")
    else:
        gates_audit.append(
            _gate_result("dual_gate", enabled=False, blocking=False, passed=True, detail={}, status="skipped")
        )

    rjc_report: dict[str, Any] | None = None
    if rjc_enabled:
        rjc_report = run_remote_judge_compare(
            enabled=True,
            blocking=bool(rjc_cfg.get("blocking", False)),
            skip_without_url=bool(rjc_cfg.get("skip_without_classifier_url", True)),
            thresholds={
                "max_attack_fn_rate": float(rjc_cfg.get("max_attack_fn_rate", 0.0)),
                "max_benign_fp_rate": float(rjc_cfg.get("max_benign_fp_rate", 0.0)),
                "max_decision_drift_rate": float(rjc_cfg.get("max_decision_drift_rate", 0.05)),
            },
            sample_limit=int(rjc_cfg.get("sample_limit", 30)),
        )
        rjc_blocking = bool(rjc_cfg.get("blocking", False))
        rjc_passed = bool(rjc_report.get("passed", True))
        rjc_status = rjc_report.get("status", "ran")
        gates_audit.append(
            _gate_result(
                "remote_judge_compare",
                enabled=True,
                blocking=rjc_blocking,
                passed=rjc_passed,
                status=rjc_status,
                detail={"report": rjc_report},
            )
        )
        if rjc_blocking and rjc_status != "skipped" and not rjc_passed:
            blocking_failed.append("remote_judge_compare")
    else:
        gates_audit.append(
            _gate_result(
                "remote_judge_compare",
                enabled=False,
                blocking=False,
                passed=True,
                detail={},
                status="skipped",
            )
        )

    passed = not blocking_failed
    out = {
        "suite": "publish_gates",
        "passed": passed,
        "failed": blocking_failed,
        "results": results,
        "gates_audit": gates_audit,
        "dual_gate": gates.get("dual_gate"),
        "remote_judge_compare": rjc_report,
        "publish_profile": audit,
        "publish_dual_gate_profile": dg_profile if dg_enabled else None,
    }
    return out
