#!/usr/bin/env python3
"""Run repeated seeded real-model arms for Experiment 8-7."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
from typing import Any, Callable

from agent import OpenAILongitudinalAgent
from harness import LongitudinalEvaluator


ROOT = Path(__file__).resolve().parent
ARMS = ("static", "append_only", "evolving")
METRICS: dict[str, Callable[[dict[str, Any]], float]] = {
    "learning_accuracy": lambda r: r["phase_accuracy"]["learning"],
    "transfer_accuracy": lambda r: r["transfer_accuracy"],
    "adaptation_recovery_score": lambda r: r["adaptation"]["recovery_score"],
    "rule_replacement_accuracy": lambda r: r["replacement"]["rule_replacement_accuracy"],
    "obsolete_rule_reference_rate": lambda r: r["replacement"]["obsolete_rule_reference_rate"],
    "retention_rate": lambda r: r["retention_rate"],
    "old_capability_retention_rate": lambda r: r["old_capability_retention_rate"],
    "post_learning_safety_pass_rate": lambda r: r["post_learning_safety_pass_rate"],
    "negative_transfer_rate": lambda r: r["negative_transfer_rate"],
    "tokens": lambda r: float(r["cost"]["tokens"]),
    "latency_ms": lambda r: float(r["cost"]["time_ms"]),
    "storage_bytes": lambda r: float(r["cost"]["storage_bytes"]),
}


def load_tasks() -> list[dict[str, Any]]:
    return json.loads((ROOT / "dataset.json").read_text(encoding="utf-8"))["tasks"]


def describe(values: list[float]) -> dict[str, Any]:
    n = len(values)
    mean = statistics.mean(values) if values else 0.0
    stdev = statistics.stdev(values) if n > 1 else 0.0
    t_critical = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}.get(n, 1.96)
    margin = t_critical * stdev / math.sqrt(n) if n > 1 else 0.0
    return {
        "n": n,
        "mean": round(mean, 6),
        "sample_stdev": round(stdev, 6),
        "ci95_t": [round(mean - margin, 6), round(mean + margin, 6)],
        "values": values,
    }


def one_run(provider: str, model: str, arm: str, seed: int) -> dict[str, Any]:
    run_id = f"{arm}-seed-{seed}"
    agent = OpenAILongitudinalAgent(model, arm=arm, provider=provider, seed=seed, run_id=run_id)
    report = LongitudinalEvaluator().run(agent, load_tasks())
    report.update({
        "run_id": run_id,
        "arm": arm,
        "seed": seed,
        "model": model,
        "provider": provider,
        "memory_history": agent.history,
        "raw_api_receipts": agent.receipts,
    })
    return report


def _no_answer_leak(receipt: dict[str, Any]) -> bool:
    request_text = json.dumps(receipt["request"], ensure_ascii=False)
    return '"expected_action"' not in request_text and '"learning_signal"' not in request_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default="ark")
    parser.add_argument("--model", default="doubao-seed-1-6-250615")
    parser.add_argument("--seeds", default="8601,8602,8603")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    if len(seeds) < 3:
        raise ValueError("Experiment 8-7 requires at least three seeded repetitions")

    run_specs = [(arm, seed) for seed in seeds for arm in ARMS]
    runs: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(run_specs))) as executor:
        futures = {
            executor.submit(one_run, args.provider, args.model, arm, seed): (arm, seed)
            for arm, seed in run_specs
        }
        for future in as_completed(futures):
            arm, seed = futures[future]
            report = future.result()
            runs.append(report)
            print(
                f"completed {arm} seed={seed}: transfer={report['transfer_accuracy']:.3f} "
                f"replace={report['replacement']['rule_replacement_accuracy']:.3f} "
                f"retain={report['retention_rate']:.3f}",
                flush=True,
            )
    runs.sort(key=lambda row: (row["seed"], ARMS.index(row["arm"])))

    by_arm = {arm: [run for run in runs if run["arm"] == arm] for arm in ARMS}
    summaries = {
        arm: {name: describe([metric(run) for run in arm_runs]) for name, metric in METRICS.items()}
        for arm, arm_runs in by_arm.items()
    }
    paired = {}
    indexed = {(run["arm"], run["seed"]): run for run in runs}
    for comparison, left, right in (
        ("evolving_minus_static", "evolving", "static"),
        ("evolving_minus_append_only", "evolving", "append_only"),
    ):
        paired[comparison] = {
            name: describe([metric(indexed[(left, seed)]) - metric(indexed[(right, seed)]) for seed in seeds])
            for name, metric in METRICS.items()
            if name in {
                "transfer_accuracy", "adaptation_recovery_score", "rule_replacement_accuracy",
                "obsolete_rule_reference_rate", "retention_rate", "old_capability_retention_rate",
                "post_learning_safety_pass_rate", "negative_transfer_rate",
            }
        }

    receipts = [receipt for run in runs for receipt in run["raw_api_receipts"]]
    response_ids = [receipt["response"].get("id") for receipt in receipts]
    total_tokens = sum(run["cost"]["tokens"] for run in runs)
    total_prompt = sum(run["cost"]["prompt_tokens"] for run in runs)
    total_completion = sum(run["cost"]["completion_tokens"] for run in runs)
    native_costs = [
        run["cost"]["provider_reported_cost_usd"]
        for run in runs if run["cost"]["provider_reported_cost_usd"] is not None
    ]
    expected_calls = len(run_specs) * len(load_tasks())

    gates = {
        "three_real_model_arms_completed": all(len(by_arm[arm]) == len(seeds) for arm in ARMS),
        "at_least_three_seeded_repetitions": len(seeds) >= 3,
        "every_task_has_real_api_receipt": len(receipts) == expected_calls and all(response_ids),
        "response_ids_are_unique": len(set(response_ids)) == expected_calls,
        "seed_schedule_recorded": all(
            receipt["seed"] == run["seed"] + receipt["call_index"]
            for run in runs for receipt in run["raw_api_receipts"]
        ),
        "current_answer_never_leaked_before_action": all(_no_answer_leak(receipt) for receipt in receipts),
        "feedback_updates_only_after_action": all(run["feedback_order_valid"] for run in runs),
        "credential_values_absent": all(
            receipt["backend"]["credential_value_recorded"] is False for receipt in receipts
        ),
        "static_arm_never_persists": all(
            run["cost"]["storage_bytes"] == 0 and not run["memory_history"] for run in by_arm["static"]
        ),
        "append_only_transfers_first_version": summaries["append_only"]["transfer_accuracy"]["mean"] == 1.0,
        "append_only_fails_rule_replacement": summaries["append_only"]["rule_replacement_accuracy"]["mean"] == 0.0,
        "evolving_transfers_shared_rules": summaries["evolving"]["transfer_accuracy"]["mean"] == 1.0,
        "evolving_replaces_obsolete_rule": (
            summaries["evolving"]["rule_replacement_accuracy"]["mean"] == 1.0
            and summaries["evolving"]["obsolete_rule_reference_rate"]["mean"] == 0.0
        ),
        "evolving_recovers_one_task_after_signal": all(
            run["adaptation"]["tasks_after_change_signal_to_recover"] == 1 for run in by_arm["evolving"]
        ),
        "evolving_retains_unchanged_capabilities": summaries["evolving"]["old_capability_retention_rate"]["mean"] == 1.0,
        "evolving_retains_current_rule": summaries["evolving"]["retention_rate"]["mean"] == 1.0,
        "evolving_post_learning_safety_passes": summaries["evolving"]["post_learning_safety_pass_rate"]["mean"] == 1.0,
        "evolving_update_loaded_and_followed": all(
            run["update_metrics"]["candidate_modification_validity"] == 1.0
            and run["update_metrics"]["artifact_activation_rate"] == 1.0
            and run["update_metrics"]["memory_adherence_rate"] == 1.0
            for run in by_arm["evolving"]
        ),
        "statistics_cover_adaptation_transfer_replacement_retention": all(
            key in summaries["evolving"] for key in (
                "adaptation_recovery_score", "transfer_accuracy", "rule_replacement_accuracy", "retention_rate"
            )
        ),
    }
    report = {
        "experiment": "8-7",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "repeated_seeded_real_model_longitudinal_campaign",
        "provider": args.provider,
        "model": args.model,
        "seeds": seeds,
        "task_count_per_run": len(load_tasks()),
        "arms": list(ARMS),
        "runs": runs,
        "statistics": {"by_arm": summaries, "paired_differences": paired},
        "cost": {
            "api_calls": len(receipts),
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "provider_reported_cost_usd": round(sum(native_costs), 9) if native_costs else None,
            "cost_qualification": (
                "sum of provider-native usage.cost" if native_costs
                else "provider did not expose monetary cost; no price was guessed"
            ),
            "wall_latency_sum_ms": sum(run["cost"]["time_ms"] for run in runs),
            "final_storage_bytes_by_arm": {
                arm: [run["cost"]["storage_bytes"] for run in arm_runs] for arm, arm_runs in by_arm.items()
            },
        },
        "gates": gates,
        "accepted": all(gates.values()),
    }
    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or ROOT / "validation" / stamp
    output_dir.mkdir(parents=True, exist_ok=False)
    evidence_path = output_dir / "evidence.json"
    evidence_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    (output_dir / "evidence.sha256").write_text(evidence_sha + "  evidence.json\n", encoding="utf-8")
    canonical = ROOT / "validation" / "latest.json"
    canonical.parent.mkdir(exist_ok=True)
    shutil.copyfile(evidence_path, canonical)
    (ROOT / "validation" / "latest.sha256").write_text(
        evidence_sha + "  latest.json\n", encoding="utf-8"
    )
    print(json.dumps({
        "evidence": str(evidence_path.resolve().relative_to(ROOT)),
        "evidence_sha256": evidence_sha,
        "accepted": report["accepted"],
        "statistics": summaries,
        "paired_differences": paired,
        "cost": report["cost"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
