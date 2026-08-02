#!/usr/bin/env python3
"""Run the real Coding-Agent self-modification campaign for Experiment 8-5."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from candidate_sandbox import sandbox_image
from evolution import (
    behavior_metrics,
    diagnose,
    generate_candidate,
    generate_rejected_control,
    release_manifest,
    sha256_text,
    validate_candidate,
    write_candidate,
)
from llm_generator import generate_with_openai


ROOT = Path(__file__).resolve().parent


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_fields_complete(manifest: dict[str, Any]) -> bool:
    required = {
        "failure_cluster", "source_trajectories", "inferred_root_cause",
        "target_component", "target_file", "code_diff", "impact_prediction",
        "expected_fix", "potential_regressions", "checks", "candidate_version",
        "rollback_version", "provenance", "decision",
    }
    return required.issubset(manifest) and all(manifest.get(key) is not None for key in required)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default="ark")
    parser.add_argument("--model", default="doubao-seed-1-6-250615")
    parser.add_argument("--seed", type=int, default=8501)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    stable_path = ROOT / "stable" / "retry_policy.py"
    trajectories_path = ROOT / "failure_trajectories.json"
    trusted_paths = {
        "evolution.py": ROOT / "evolution.py",
        "candidate_sandbox.py": ROOT / "candidate_sandbox.py",
        "sandbox_runner.py": ROOT / "sandbox_runner.py",
        "Dockerfile.sandbox": ROOT / "Dockerfile.sandbox",
    }
    stable_source = stable_path.read_text(encoding="utf-8")
    trajectories = json.loads(trajectories_path.read_text(encoding="utf-8"))
    immutable_before = {
        "stable/retry_policy.py": _sha_file(stable_path),
        "failure_trajectories.json": _sha_file(trajectories_path),
        **{name: _sha_file(path) for name, path in trusted_paths.items()},
    }
    diagnosis = diagnose(trajectories)

    # The rejected control is evaluated first so its concrete failure can be
    # supplied to the real Coding Agent as bounded historical context.
    rejected = generate_rejected_control(stable_source, diagnosis)
    rejected_checks = validate_candidate(rejected["source"], trajectories, stable_source)
    rejected_manifest = release_manifest(stable_source, rejected, diagnosis, rejected_checks)
    rejected_history = [{
        "candidate_sha256": rejected["source_sha256"],
        "failed_checks": rejected_manifest["failed_checks"],
        "rejection_reason": rejected_manifest["rejection_reason"],
        "failure": "disabled temporary-timeout retries",
    }]

    deterministic = generate_candidate(stable_source, diagnosis)
    llm = generate_with_openai(
        stable_source,
        diagnosis,
        args.model,
        provider=args.provider,
        seed=args.seed,
        rejected_history=rejected_history,
    )

    immutable_after_generation = {
        "stable/retry_policy.py": _sha_file(stable_path),
        "failure_trajectories.json": _sha_file(trajectories_path),
        **{name: _sha_file(path) for name, path in trusted_paths.items()},
    }
    protected_unchanged = immutable_before == immutable_after_generation
    candidates = {
        "deterministic": deterministic,
        "real_llm": llm,
        "rejected_control": rejected,
    }
    manifests = {}
    metrics = {"stable_buggy_baseline": behavior_metrics(stable_source, trajectories)}
    for name, candidate in candidates.items():
        checks = validate_candidate(candidate["source"], trajectories, stable_source)
        checks["protected_surfaces_unchanged"] = protected_unchanged
        manifests[name] = release_manifest(
            stable_source,
            candidate,
            diagnosis,
            checks,
            provenance=candidate.get("generator_metadata", {}),
        )
        metrics[name] = behavior_metrics(candidate["source"], trajectories)

    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or ROOT / "validation" / stamp
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, candidate in candidates.items():
        write_candidate(candidate["source"], output_dir / "candidates" / name / "retry_policy.py")
        (output_dir / f"{name}_manifest.json").write_text(
            json.dumps(manifests[name], ensure_ascii=False, indent=2), encoding="utf-8"
        )

    decisions = [manifest["decision"] for manifest in manifests.values()]
    accepted_count = decisions.count("release_to_canary")
    comparison = {
        name: {
            "decision": manifests[name]["decision"],
            "checks": manifests[name]["checks"],
            "patch_size": candidate["patch_size"],
            "behavior": metrics[name],
        }
        for name, candidate in candidates.items()
    }
    llm_receipt = llm["generator_metadata"]["receipt"]
    gates = {
        "cross_trajectory_support_met": diagnosis["patterns"][0]["cross_trajectory_support"] >= 2,
        "root_cause_targets_control_code": diagnosis["target"] == "stable/retry_policy.py",
        "real_coding_model_called": (
            llm["generator_metadata"].get("api_calls") == 1
            and bool(llm_receipt["response"].get("id"))
        ),
        "impact_prediction_precedes_validation": bool(llm.get("impact_prediction")),
        "all_candidates_isolated": stable_path.read_text(encoding="utf-8") == stable_source,
        "trusted_surfaces_unchanged": protected_unchanged,
        "same_release_gate_for_both_generators": (
            set(manifests["deterministic"]["checks"]) == set(manifests["real_llm"]["checks"])
        ),
        "deterministic_candidate_release_to_canary": manifests["deterministic"]["decision"] == "release_to_canary",
        "real_llm_candidate_release_to_canary": manifests["real_llm"]["decision"] == "release_to_canary",
        "known_bad_candidate_rejected_and_retained": (
            manifests["rejected_control"]["decision"] == "reject_candidate"
            and bool(manifests["rejected_control"]["rejection_reason"])
        ),
        "failure_replay_reduces_calls": (
            metrics["real_llm"]["mean_nonretryable_calls"] == 1.0
            and metrics["stable_buggy_baseline"]["mean_nonretryable_calls"] > 1.0
        ),
        "temporary_recovery_preserved": metrics["real_llm"]["temporary_error_recovery_rate"] == 1.0,
        "old_task_regression_zero": metrics["real_llm"]["old_task_regressions"] == 0,
        "canary_only_not_production": all(
            manifest["decision"] in {"release_to_canary", "reject_candidate"} for manifest in manifests.values()
        ),
        "rollback_hash_pinned_to_stable": all(
            manifest["rollback_sha256"] == sha256_text(stable_source) for manifest in manifests.values()
        ),
        "release_manifest_fields_complete": all(_manifest_fields_complete(item) for item in manifests.values()),
    }
    report = {
        "experiment": "8-5",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "real_api_coding_agent_plus_model_external_release_harness",
        "provider": args.provider,
        "model": args.model,
        "seed": args.seed,
        "input_artifacts": {
            "stable_sha256": immutable_before["stable/retry_policy.py"],
            "trajectory_sha256": immutable_before["failure_trajectories.json"],
            "validator_sha256_before_generation": immutable_before["evolution.py"],
            "validator_sha256_after_generation": immutable_after_generation["evolution.py"],
            "trusted_surface_sha256_before": {
                name: immutable_before[name] for name in trusted_paths
            },
            "trusted_surface_sha256_after": {
                name: immutable_after_generation[name] for name in trusted_paths
            },
        },
        "candidate_sandbox": {
            "image": sandbox_image(),
            "network": "none",
            "root_filesystem": "read_only",
            "user": "65534:65534",
            "memory": "64m",
            "cpus": 0.5,
            "wall_clock_timeout_seconds": 8.0,
        },
        "diagnosis": diagnosis,
        "rejected_history_given_to_coding_agent": rejected_history,
        "behavior_metrics": metrics,
        "comparison": comparison,
        "manifests": manifests,
        "raw_api_receipts": [llm_receipt],
        "cost": llm_receipt["usage"],
        "candidate_acceptance_rate": accepted_count / len(candidates),
        "gates": gates,
        "accepted": all(gates.values()),
    }
    evidence_path = output_dir / "evidence.json"
    evidence_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    evidence_sha = _sha_file(evidence_path)
    (output_dir / "evidence.sha256").write_text(
        evidence_sha + "  evidence.json\n", encoding="utf-8"
    )
    (output_dir / "artifact_hashes.json").write_text(json.dumps({
        str(path.relative_to(output_dir)): _sha_file(path)
        for path in sorted(output_dir.rglob("*.py"))
    }, indent=2), encoding="utf-8")

    # Canonical, credential-free evidence and the manuscript-required manifest.
    canonical = ROOT / "validation" / "latest.json"
    canonical.parent.mkdir(exist_ok=True)
    shutil.copyfile(evidence_path, canonical)
    (ROOT / "validation" / "latest.sha256").write_text(
        evidence_sha + "  latest.json\n", encoding="utf-8"
    )
    (ROOT / "output").mkdir(exist_ok=True)
    (ROOT / "output" / "release_manifest.json").write_text(
        json.dumps(manifests["real_llm"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "output" / "rejected_manifest.json").write_text(
        json.dumps(manifests["rejected_control"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "evidence": str(evidence_path.relative_to(ROOT)),
        "evidence_sha256": evidence_sha,
        "accepted": report["accepted"],
        "decisions": {name: item["decision"] for name, item in manifests.items()},
        "metrics": metrics,
        "cost": report["cost"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
