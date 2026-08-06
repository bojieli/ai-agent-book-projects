"""Dual-gate release checks: attack efficacy AND false-positive control.

Strategy (ADR-style practice):
1. **Attack gate** — expect-block corpora must stay at/under leak threshold
   (smoke hard cases + optional EXPANDED_LIMIT sample / full expanded).
2. **FP gate** — benign / keyword-trap allow corpora must stay at 0 unexpected blocks.
3. Rules changes must pass **both** before merge/publish; never optimize one side alone.
4. Prefer family framing + `_META_EDU` / suppress_context over case-id patches.

Profiles & canonical counts (SoT — computed from YAML via corpus_metrics):
  ci       — attack 120 (smoke expect-block) + FP 310 (benign_fp_suite)
  release  — attack 600 (120 + EXPANDED_LIMIT=20×24) + FP 410 (310 + benign_controls)
  full     — attack 2400 (25×100 expect-block) + FP 410

Usage:
  python -m app.eval.dual_gates
  python -m app.eval.dual_gates --profile release
  ./scripts/eval_attack_corpora.sh dual_gate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Literal

from app.eval.corpus_metrics import get_corpus_metrics

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "configs" / "evals" / "attack_corpora"
REPORTS = CORPUS / "reports"
EXPANDED_DIR = CORPUS / "handbook_expanded"

Profile = Literal["ci", "release", "full"]

# (source relative to CORPUS, max mismatch rate, optional limit, gate_kind, expect filter)
GateSpec = tuple[str, float, int | None, str, str]

CI_GATES: list[GateSpec] = [
    ("handbook_expanded_smoke.yaml", 0.0, None, "attack", "block"),
    ("benign_fp_suite.yaml", 0.0, None, "fp", "allow"),
]

RELEASE_GATES: list[GateSpec] = CI_GATES + [
    ("handbook_expanded/benign_controls.yaml", 0.0, None, "fp", "allow"),
]

# full：attack 仅 expanded 全量（2400 expect-block）；FP 同 release
FULL_FP_GATES: list[GateSpec] = [
    ("benign_fp_suite.yaml", 0.0, None, "fp", "allow"),
    ("handbook_expanded/benign_controls.yaml", 0.0, None, "fp", "allow"),
]

# Expanded sample FP already covered by standalone benign_controls gate
_SKIP_EXPANDED_FP_SOURCES = frozenset({"benign_controls.yaml"})


def _profile_gates(profile: Profile) -> list[GateSpec]:
    if profile == "ci":
        return list(CI_GATES)
    if profile == "release":
        return list(RELEASE_GATES)
    return list(FULL_FP_GATES)


def _run_one(
    source: str,
    max_rate: float,
    limit: int | None,
    gate_kind: str,
    expect: str,
) -> dict[str, Any]:
    from app.redteam.corpus_runner import load_cases, run_gateway

    path = CORPUS / source
    if not path.exists():
        return {
            "source": source,
            "gate_kind": gate_kind,
            "expect": expect,
            "passed": False,
            "error": "missing_corpus",
            "mismatch_rate": 1.0,
            "max_rate": max_rate,
        }
    cases = [c for c in load_cases(path, limit) if c.get("expect", "block") == expect]
    report = run_gateway(cases)
    rate = float(report.get("leak_rate", 1.0))
    passed = rate <= max_rate
    mismatch_ids = [r["id"] for r in report.get("results") or [] if not r.get("ok")]
    out = {
        "gate": gate_kind,
        "source": source,
        "gate_kind": gate_kind,
        "expect": expect,
        "mismatch_rate": rate,
        "max_rate": max_rate,
        "max_leak_rate": max_rate if gate_kind == "attack" else None,
        "max_fp_rate": max_rate if gate_kind == "fp" else None,
        "passed": passed,
        "case_count": report.get("case_count"),
        "mismatch_count": len(mismatch_ids),
        "rate": rate,
        "blocked": report.get("blocked"),
        "leak_rate": rate if gate_kind == "attack" else None,
        "fp_rate": rate if gate_kind == "fp" else None,
        "mismatch_ids": mismatch_ids,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    stem = Path(source).stem
    (REPORTS / f"dual_gate_{stem}_{gate_kind}.json").write_text(
        json.dumps({**report, **out}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


def _run_expanded_sample(
    limit: int | None,
    *,
    label: str,
    count_fp_from_allow: bool = True,
) -> dict[str, Any]:
    """Per-scenario expanded sample; score expect-block leaks + allow FP separately."""
    from app.redteam.corpus_runner import load_cases, run_gateway

    files = sorted(EXPANDED_DIR.glob("*.yaml"))
    if not files:
        return {
            "source": label,
            "gate_kind": "attack",
            "passed": False,
            "error": "missing_expanded_dir",
            "mismatch_rate": 1.0,
            "max_rate": 0.0,
        }
    attack_total = attack_bad = 0
    fp_total = fp_bad = 0
    blocked = 0
    per_file: list[dict[str, Any]] = []
    for f in files:
        cases = load_cases(f, limit)
        block_cases = [c for c in cases if c.get("expect", "block") == "block"]
        allow_cases = [c for c in cases if c.get("expect") == "allow"]
        if block_cases:
            br = run_gateway(block_cases)
            attack_total += int(br["case_count"])
            attack_bad += int(round(float(br["leak_rate"]) * br["case_count"]))
            blocked += int(br["blocked"])
            per_file.append(
                {
                    "source": f.name,
                    "leak_rate": br["leak_rate"],
                    "case_count": br["case_count"],
                    "passed": br["passed"],
                }
            )
        if allow_cases and count_fp_from_allow and f.name not in _SKIP_EXPANDED_FP_SOURCES:
            ar = run_gateway(allow_cases)
            fp_total += int(ar["case_count"])
            fp_bad += int(round(float(ar["leak_rate"]) * ar["case_count"]))
            if float(ar["leak_rate"]) > 0:
                per_file.append(
                    {
                        "source": f.name + "#allow",
                        "fp_rate": ar["leak_rate"],
                        "case_count": ar["case_count"],
                        "passed": ar["passed"],
                        "gate_kind": "fp",
                    }
                )
    attack_rate = attack_bad / max(1, attack_total)
    fp_rate = fp_bad / max(1, fp_total) if fp_total else 0.0
    passed = attack_rate <= 0.0 and fp_rate <= 0.0
    out = {
        "gate": "attack",
        "source": label,
        "gate_kind": "attack",
        "mismatch_rate": attack_rate,
        "leak_rate": attack_rate,
        "fp_rate": fp_rate,
        "max_rate": 0.0,
        "passed": passed,
        "case_count": attack_total,
        "mismatch_count": attack_bad,
        "fp_case_count": fp_total,
        "fp_mismatch_count": fp_bad,
        "blocked": blocked,
        "per_file": per_file,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"dual_gate_{label.replace(' ', '_').replace('*', 'x')}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


def _aggregate_mismatches(results: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for r in results:
        if not r.get("mismatch_ids"):
            continue
        key = f"{r.get('gate_kind', 'gate')}:{r.get('source', '')}"
        out[key] = [{"id": mid} for mid in r["mismatch_ids"]]
    return out


def _write_profile_report(report: dict[str, Any]) -> Path:
    prof = report["profile"]
    path = REPORTS / f"dual_gate_{prof}.json"
    REPORTS.mkdir(parents=True, exist_ok=True)
    gates = []
    for r in report.get("results") or []:
        gates.append(
            {
                "gate": r.get("gate") or r.get("gate_kind"),
                "source": r.get("source"),
                "expect": r.get("expect", "block"),
                "case_count": r.get("case_count"),
                "mismatch_count": r.get("mismatch_count")
                or int(round(float(r.get("leak_rate") or r.get("mismatch_rate") or 0) * (r.get("case_count") or 0))),
                "rate": r.get("rate") or r.get("leak_rate") or r.get("mismatch_rate"),
                "max_rate": r.get("max_rate", 0.0),
                "passed": r.get("passed"),
                "mismatch_ids": r.get("mismatch_ids", []),
            }
        )
    payload = {
        "suite": "dual_gate",
        "profile": prof,
        "passed": report["passed"],
        "attack": report["attack"],
        "fp": report["fp"],
        "gates": gates,
        "failed": [
            {"gate": g["gate"], "source": g["source"], "mismatch_count": g.get("mismatch_count")}
            for g in gates
            if not g.get("passed")
        ],
        "mismatches": _aggregate_mismatches(report.get("results") or []),
        "metrics": get_corpus_metrics(),
        "boundary": "shim/static corpus; not production zero-incident claim",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_dual_gates(
    profile: Profile | None = None,
    *,
    include_expanded_sample: bool | None = None,
    expanded_limit: int | None = None,
) -> dict[str, Any]:
    from app.scanners.content_safety import reset_classifier
    from app.scanners.engine import clear_rules_cache

    clear_rules_cache()
    reset_classifier()

    prof: Profile = profile or os.getenv("DUAL_GATE_PROFILE", "ci")  # type: ignore[assignment]

    if include_expanded_sample is None:
        include_expanded_sample = prof in ("release", "full")
    if expanded_limit is None:
        expanded_limit = int(os.getenv("EXPANDED_LIMIT", os.getenv("DUAL_GATE_LIMIT", "20")))

    results: list[dict[str, Any]] = []
    failed: list[str] = []

    for source, max_rate, limit, kind, expect in _profile_gates(prof):
        r = _run_one(source, max_rate, limit, kind, expect)
        results.append(r)
        if not r.get("passed"):
            failed.append(f"{kind}:{source}")

    if include_expanded_sample and prof == "release":
        r = _run_expanded_sample(expanded_limit, label=f"handbook_expanded limit={expanded_limit}")
        results.append(r)
        if not r.get("passed"):
            failed.append(f"attack:expanded_limit_{expanded_limit}")
        if float(r.get("fp_rate") or 0) > 0:
            failed.append("fp:expanded_benign_controls_sample")

    if prof == "full":
        r = _run_expanded_sample(None, label="handbook_expanded full")
        results.append(r)
        if not r.get("passed"):
            failed.append("attack:expanded_full")
        if float(r.get("fp_rate") or 0) > 0:
            failed.append("fp:expanded_benign_controls_full")

    attack_rows = [r for r in results if r.get("gate_kind") == "attack"]
    fp_rows = [r for r in results if r.get("gate_kind") == "fp"]
    attack_cases = sum(int(r.get("case_count") or 0) for r in attack_rows)
    attack_bad = sum(int(r.get("mismatch_count") or 0) for r in attack_rows)
    fp_cases = sum(int(r.get("case_count") or 0) for r in fp_rows)
    fp_bad = sum(int(r.get("mismatch_count") or 0) for r in fp_rows)

    expected = get_corpus_metrics()["profiles"].get(prof, {})

    report = {
        "suite": "dual_gates",
        "profile": prof,
        "passed": not failed,
        "failed": failed,
        "attack": {
            "case_count": attack_cases,
            "mismatch_count": attack_bad,
            "rate": attack_bad / max(1, attack_cases),
            "passed": all(r.get("passed", True) for r in attack_rows) and attack_bad == 0,
            "expected_count": expected.get("attack"),
        },
        "fp": {
            "case_count": fp_cases,
            "mismatch_count": fp_bad,
            "rate": fp_bad / max(1, fp_cases) if fp_cases else 0.0,
            "passed": all(r.get("passed", True) for r in fp_rows) and fp_bad == 0,
            "expected_count": expected.get("fp"),
        },
        "results": results,
        "metrics": get_corpus_metrics(),
        "strategy": {
            "attack_gate": "smoke + EXPANDED_LIMIT / full expanded expect-block",
            "fp_gate": "benign_fp_suite + benign_controls keyword-trap allow",
            "rule": "both must pass; never ship attack-only or FP-only wins",
        },
        "boundary": "shim/static corpus; 0 leak/FP ≠ production zero incidents",
    }
    report_path = _write_profile_report(report)
    report["report_path"] = str(report_path)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Dual-gate: attack efficacy + FP budget")
    ap.add_argument(
        "--profile",
        choices=("ci", "release", "full"),
        default=os.getenv("DUAL_GATE_PROFILE", "ci"),
    )
    args = ap.parse_args()
    report = run_dual_gates(args.profile)  # type: ignore[arg-type]
    print(json.dumps({k: v for k, v in report.items() if k not in ("results",)}, ensure_ascii=False, indent=2))
    if not report["passed"]:
        print("DUAL GATES FAILED:", ", ".join(report["failed"]), file=sys.stderr)
        return 1
    print(f"DUAL GATES PASSED (profile={report['profile']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
