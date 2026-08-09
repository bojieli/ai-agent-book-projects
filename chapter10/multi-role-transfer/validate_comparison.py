#!/usr/bin/env python3
"""Independently verify the retained Experiment 10-1 comparison package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run_dir", type=Path, nargs="?",
                   default=ROOT / "validation" / "comparison" / "runs" / "exp10-1-qwen35flash-20260809-v2")
    return p.parse_args()


def main() -> int:
    run_dir = args.run_dir.resolve()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    acceptance = json.loads((run_dir / "acceptance.json").read_text(encoding="utf-8"))
    campaign = json.loads((run_dir / "campaign.json").read_text(encoding="utf-8"))
    judge = json.loads((run_dir / "judge.json").read_text(encoding="utf-8"))
    assert manifest["acceptance"]["evidence_status"] == "pass"
    assert acceptance["evidence_status"] == "pass"
    assert acceptance["passed_gates"] == acceptance["total_gates"]
    assert all(acceptance["gates"].values())
    for name, expected in manifest["artifact_sha256"].items():
        assert sha256(run_dir / name) == expected, name
    for name, expected in manifest["runtime_source_sha256"].items():
        assert sha256(ROOT / name) == expected, name
    runs = campaign["runs"]
    assert campaign["paired_samples"] == 30
    assert len(runs) == 60
    assert len(campaign["boundary_runs"]) == 12
    assert all(run.get("provider_receipts") for run in runs)
    assert all(run.get("loaded_skills") for run in runs if run["path"] == "skill")
    assert sum(run["outcome"]["pass"] for run in runs if run["path"] == "skill") == 15
    assert sum(run["outcome"]["pass"] for run in runs if run["path"] == "transfer") == 2
    assert judge["paired_n"] == 30
    assert judge["judge_receipt_count"] == 60
    assert judge["unique_response_ids"] == 60
    assert judge["parse_complete"] is True
    assert all(pair["parse_complete"] for pair in judge["pairs"])
    blob = b"\n".join(path.read_bytes() for path in run_dir.iterdir() if path.is_file())
    assert not re.search(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}', blob)
    assert not re.search(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|\s*")[^"]+"', blob)
    print(f"validated {manifest['run_id']}: {acceptance['passed_gates']}/{acceptance['total_gates']} gates")
    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(main())
