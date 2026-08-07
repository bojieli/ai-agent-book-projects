#!/usr/bin/env python3
"""实验 8-8 验收入口：确定性生成器与真实 Coding Agent 经过同一组发布门槛。

默认（完整模式）调用真实 LLM；--quick 为离线模式，只跑确定性候选与
故意过宽的反例，不调用 API、不写 validation/ 证据目录。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from evolution import (
    CHECK_NAMES,
    diagnose,
    generate_candidate,
    generate_rejected_control,
    release_manifest,
    sha256_text,
    validate_candidate,
    write_candidate,
)


ROOT = Path(__file__).resolve().parent


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_fields_complete(manifest: dict[str, Any]) -> bool:
    required = {
        "failure_cluster", "source_trajectories", "inferred_root_cause",
        "target_component", "target_file", "code_diff", "integration_diff",
        "impact_prediction", "expected_fix", "potential_regressions",
        "checks", "candidate_version", "rollback_version", "provenance", "decision",
    }
    return required.issubset(manifest) and all(manifest.get(key) is not None for key in required)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default="ark")
    parser.add_argument("--model", default="doubao-seed-1-6-250615")
    parser.add_argument("--seed", type=int, default=8801)
    parser.add_argument("--quick", action="store_true",
                        help="离线模式：跳过真实 LLM，只验证确定性候选与反例")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    stable_path = ROOT / "stable" / "tool_dispatcher.py"
    data_paths = {
        "failure_trajectories.json": ROOT / "failure_trajectories.json",
        "boundary_cases.json": ROOT / "boundary_cases.json",
        "retention_cases.json": ROOT / "retention_cases.json",
    }
    trusted_paths = {"evolution.py": ROOT / "evolution.py"}
    stable_source = stable_path.read_text(encoding="utf-8")
    trajectories = json.loads(data_paths["failure_trajectories.json"].read_text(encoding="utf-8"))
    boundary_cases = json.loads(data_paths["boundary_cases.json"].read_text(encoding="utf-8"))
    retention_cases = json.loads(data_paths["retention_cases.json"].read_text(encoding="utf-8"))

    def snapshot() -> dict[str, str]:
        return {
            "stable/tool_dispatcher.py": _sha_file(stable_path),
            **{name: _sha_file(path) for name, path in data_paths.items()},
            **{name: _sha_file(path) for name, path in trusted_paths.items()},
        }

    immutable_before = snapshot()
    diagnosis = diagnose(trajectories)

    # 先评估一个"门禁存在但放行一切"的反例，把具体失败原因作为
    # 有界历史上下文提供给真实 Coding Agent。
    rejected = generate_rejected_control(stable_source, diagnosis)
    rejected_checks = validate_candidate(rejected["source"], boundary_cases, retention_cases)
    rejected_manifest = release_manifest(stable_source, rejected, diagnosis, rejected_checks)
    rejected_history = [{
        "candidate_sha256": rejected["source_sha256"],
        "failed_checks": rejected_manifest["failed_checks"],
        "rejection_reason": rejected_manifest["rejection_reason"],
        "failure": "gate suspended nothing; high-risk calls still executed unconfirmed",
    }]

    deterministic = generate_candidate(stable_source, diagnosis)
    candidates = {"deterministic": deterministic, "rejected_control": rejected}
    llm_receipt = None
    if not args.quick:
        from llm_generator import generate_with_openai
        llm = generate_with_openai(
            stable_source,
            diagnosis,
            args.model,
            provider=args.provider,
            seed=args.seed,
            rejected_history=rejected_history,
        )
        candidates["real_llm"] = llm
        llm_receipt = llm["generator_metadata"]["receipt"]

    protected_unchanged = immutable_before == snapshot()

    manifests = {}
    for name, candidate in candidates.items():
        checks = validate_candidate(candidate["source"], boundary_cases, retention_cases)
        checks["protected_surfaces_unchanged"] = protected_unchanged
        manifests[name] = release_manifest(
            stable_source,
            candidate,
            diagnosis,
            checks,
            provenance=candidate.get("generator_metadata", {}),
        )

    gates = {
        "cross_trajectory_support_met": all(
            pattern["cross_trajectory_support"] >= 2 for pattern in diagnosis["patterns"]
        ) and bool(diagnosis["patterns"]),
        "root_cause_targets_dispatch_layer": diagnosis["target"] == "stable/tool_dispatcher.py",
        "signals_include_user_feedback_and_audit": {
            "user_correction", "user_thumbs_down", "post_hoc_audit"
        } <= {s for p in diagnosis["patterns"] for s in p["signals"]},
        "all_candidates_isolated": stable_path.read_text(encoding="utf-8") == stable_source,
        "trusted_surfaces_unchanged": protected_unchanged,
        "same_release_gate_for_all_candidates": (
            len({tuple(manifest["checks"]) for manifest in manifests.values()}) == 1
        ),
        "deterministic_candidate_release_to_canary": manifests["deterministic"]["decision"] == "release_to_canary",
        "known_bad_candidate_rejected_and_retained": (
            manifests["rejected_control"]["decision"] == "reject_candidate"
            and "boundary_replay" in manifests["rejected_control"]["failed_checks"]
        ),
        "canary_only_not_production": all(
            manifest["decision"] in {"release_to_canary", "reject_candidate"}
            for manifest in manifests.values()
        ),
        "rollback_hash_pinned_to_stable": all(
            manifest["rollback_sha256"] == sha256_text(stable_source)
            for manifest in manifests.values()
        ),
        "release_manifest_fields_complete": all(
            _manifest_fields_complete(item) for item in manifests.values()
        ),
    }
    if not args.quick:
        gates["real_coding_model_called"] = (
            candidates["real_llm"]["generator_metadata"].get("api_calls") == 1
            and bool(llm_receipt["response"].get("id"))
        )
        real_checks = manifests["real_llm"]["checks"]
        real_checks_pass = all(real_checks.get(name, False) for name in CHECK_NAMES)
        gates["real_llm_decision_matches_checks"] = (
            manifests["real_llm"]["decision"]
            == ("release_to_canary" if real_checks_pass else "reject_candidate")
        )

    report = {
        "experiment": "8-8",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": (
            "offline_deterministic_gate_only" if args.quick
            else "real_api_coding_agent_plus_model_external_release_harness"
        ),
        "provider": None if args.quick else args.provider,
        "model": None if args.quick else args.model,
        "seed": args.seed,
        "input_artifacts": immutable_before,
        "validation_boundary": {
            "sandbox": "none (candidate is a new isolated module, not an overwrite of stable code)",
            "static_checks": ["compile", "ast_import_whitelist", "forbidden_builtins"],
            "replay": "in-memory simulated dispatch; executor injected by the validator",
            "boundary_cases": len(boundary_cases),
            "retention_cases": len(retention_cases),
        },
        "diagnosis": diagnosis,
        "rejected_history_given_to_coding_agent": rejected_history,
        "comparison": {
            name: {
                "decision": manifests[name]["decision"],
                "checks": manifests[name]["checks"],
                "patch_size": candidate["patch_size"],
            }
            for name, candidate in candidates.items()
        },
        "manifests": manifests,
        "raw_api_receipts": [llm_receipt] if llm_receipt else [],
        "gates": gates,
        "accepted": all(gates.values()),
    }

    if args.quick:
        (ROOT / "output").mkdir(exist_ok=True)
        for name, candidate in candidates.items():
            write_candidate(candidate["source"], ROOT / "output" / "candidate" / name / "confirmation_gate.py")
            (ROOT / "output" / f"{name}_manifest.json").write_text(
                json.dumps(manifests[name], ensure_ascii=False, indent=2), encoding="utf-8"
            )
        print(json.dumps({
            "mode": "quick_offline",
            "accepted": report["accepted"],
            "decisions": {name: item["decision"] for name, item in manifests.items()},
            "gates": gates,
        }, ensure_ascii=False, indent=2))
        return 0 if report["accepted"] else 1

    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or ROOT / "validation" / stamp
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, candidate in candidates.items():
        write_candidate(candidate["source"], output_dir / "candidates" / name / "confirmation_gate.py")
        (output_dir / f"{name}_manifest.json").write_text(
            json.dumps(manifests[name], ensure_ascii=False, indent=2), encoding="utf-8"
        )
    evidence_path = output_dir / "evidence.json"
    evidence_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    evidence_sha = _sha_file(evidence_path)
    (output_dir / "evidence.sha256").write_text(
        evidence_sha + "  evidence.json\n", encoding="utf-8"
    )

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
    print(json.dumps({
        "evidence": str(evidence_path.relative_to(ROOT)),
        "evidence_sha256": evidence_sha,
        "accepted": report["accepted"],
        "decisions": {name: item["decision"] for name, item in manifests.items()},
        "cost": llm_receipt["usage"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
