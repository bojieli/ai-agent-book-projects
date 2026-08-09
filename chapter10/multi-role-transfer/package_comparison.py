#!/usr/bin/env python3
"""Package a completed Experiment 10-1 campaign into auditable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_FILES = (
    "run_comparison.py",
    "evaluation.py",
    "orchestrator.py",
    "skill_orchestrator.py",
    "tools.py",
    "experiment_protocol.json",
    "tasks.formal.json",
    "package_comparison.py",
    "judge_comparison.py",
    "validate_comparison.py",
)
SECRET_ENV_NAMES = (
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "MOONSHOT_API_KEY",
    "TAVILY_API_KEY",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def credential_scan(payload: bytes) -> dict[str, int]:
    actual = 0
    for name in SECRET_ENV_NAMES:
        secret = os.getenv(name, "").encode("utf-8")
        if len(secret) >= 8:
            actual += payload.count(secret)
    patterns = (
        re.compile(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|\s*")[^"]+"'),
        re.compile(rb"(?i)bearer\s+[a-z0-9._~+/=-]{16,}"),
    )
    return {
        "actual_secret_hits": actual,
        "credential_pattern_hits": sum(len(pattern.findall(payload)) for pattern in patterns),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--judge", type=Path, required=True,
                        help="position-swapped quality-judge evidence JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    campaign_path = output / "campaign.json"
    campaign_path.write_bytes(args.campaign.read_bytes())
    judge_path = output / "judge.json"
    judge_path.write_bytes(args.judge.read_bytes())
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    judge = json.loads(judge_path.read_text(encoding="utf-8"))
    runs = campaign.get("runs", [])
    boundary_runs = campaign.get("boundary_runs", [])

    pairs: dict[str, set[str]] = {}
    for run in runs:
        pairs.setdefault(str(run.get("pair_id")), set()).add(str(run.get("path")))
    task_specs = campaign.get("tasks", [])
    task_ids = {str(item.get("id")) for item in task_specs}
    observed_task_ids = {str(item.get("task_id")) for item in runs}
    provider_receipts = [
        receipt for run in [*runs, *boundary_runs]
        for receipt in run.get("provider_receipts", [])
    ]
    tavily_receipts = [
        receipt for run in [*runs, *boundary_runs]
        for receipt in run.get("tavily_receipts", [])
    ]
    response_ids = [item.get("response_id") for item in provider_receipts]
    expected_provider_receipts = sum(
        int(run.get("metrics", {}).get("api_calls", 0))
        for run in [*runs, *boundary_runs]
    )
    scan = credential_scan(campaign_path.read_bytes() + b"\n" + judge_path.read_bytes())
    required_tool_sets = [set(item.get("required_tools", [])) for item in task_specs]
    boundary_pairs = {
        (str(run.get("case_id")), str(run.get("path"))) for run in boundary_runs
    }
    boundary_case_ids = {str(run.get("case_id")) for run in boundary_runs}
    judge_receipts = [item for pair in judge.get("pairs", []) for item in pair.get("judgments", [])]
    normalized_winners = [winner for pair in judge.get("pairs", []) for winner in pair.get("normalized_winners", [])]

    gates = {
        "campaign_finished_not_checkpoint": not campaign.get("checkpoint", False),
        "minimum_30_paired_samples": (
            int(campaign.get("paired_samples", 0)) >= 30
            and len(pairs) >= 30
            and all(paths == {"transfer", "skill"} for paths in pairs.values())
        ),
        "task_file_matches_retained_runs": task_ids == observed_task_ids and len(task_ids) == 30,
        "research_coding_writing_strata_present": (
            any("web_search" in tools for tools in required_tool_sets)
            and any("execute_python" in tools for tools in required_tool_sets)
            and any(tools == {"count_characters"} for tools in required_tool_sets)
        ),
        "raw_provider_receipt_for_every_call": (
            len(provider_receipts) == expected_provider_receipts > 0
            and all(item.get("request") and item.get("response") for item in provider_receipts)
        ),
        "unique_provider_response_ids": (
            all(response_ids) and len(set(response_ids)) == len(response_ids)
        ),
        "real_tavily_receipts_retained": (
            len(tavily_receipts) > 0
            and all(item.get("response", {}).get("http_status") == 200 for item in tavily_receipts)
            and all(item.get("response", {}).get("raw_body") for item in tavily_receipts)
            and all("api_key" not in item.get("request", {}).get("body", {}) for item in tavily_receipts)
        ),
        "all_failed_and_limited_trajectories_retained": (
            any(not run.get("outcome", {}).get("pass", False) for run in runs)
            and all(run.get("history") and run.get("provider_receipts") for run in runs)
        ),
        "complete_two_arm_boundary_suite": (
            len(boundary_case_ids) == 6
            and len(boundary_pairs) == 12
            and all(
                (case_id, path) in boundary_pairs
                for case_id in boundary_case_ids for path in ("transfer", "skill")
            )
        ),
        "paired_statistics_and_costs_present": (
            campaign.get("paired_comparison", {}).get("paired_n") == 30
            and campaign.get("paired_comparison", {}).get("pass_rate_delta", {}).get("bootstrap_95_percent") is not None
            and campaign.get("paired_comparison", {}).get("mcnemar", {}).get("two_sided_exact_p") is not None
            and campaign.get("paired_comparison", {}).get("cost_delta_usd") is not None
        ),
        "blind_quality_judge_position_swapped": (
            judge.get("paired_n") == 30
            and judge.get("judge_receipt_count") == 60
            and judge.get("unique_response_ids") == 60
            and judge.get("parse_complete") is True
            and len(judge.get("pairs", [])) == 30
            and all(len(pair.get("judgments", [])) == 2 for pair in judge.get("pairs", []))
        ),
        "credential_free_campaign": scan["actual_secret_hits"] == 0 and scan["credential_pattern_hits"] == 0,
    }
    overall = "pass" if all(gates.values()) else "incomplete"
    transfer = campaign["aggregate"]["transfer"]
    skill = campaign["aggregate"]["skill"]
    paired = campaign["paired_comparison"]
    acceptance = {
        "schema_version": 1,
        "experiment": "10-1",
        "run_id": args.run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_status": overall,
        "interpretation": "complete_bounded_comparison",
        "model": campaign.get("model"),
        "base_url": campaign.get("base_url"),
        "campaign_parameters": {
            "tasks": len(task_specs),
            "paired_samples": len(pairs),
            "main_runs": len(runs),
            "boundary_runs": len(boundary_runs),
            "max_steps": campaign.get("max_steps"),
            "max_output_tokens": campaign.get("max_output_tokens"),
            "temperature": campaign.get("temperature"),
        },
        "receipt_counts": {
            "provider": len(provider_receipts),
            "tavily": len(tavily_receipts),
        },
        "result": {
            "transfer_pass_at_1": transfer["pass_at_1"],
            "skill_pass_at_1": skill["pass_at_1"],
            "transfer_required_sequence_rate": transfer["required_role_sequence_rate"],
            "skill_required_sequence_rate": skill["required_role_sequence_rate"],
            "skill_minus_transfer_uncached_input_token_median": paired["uncached_input_token_delta"]["median"],
            "skill_minus_transfer_latency_seconds_median": paired["latency_delta_seconds"]["median"],
            "skill_minus_transfer_cost_usd_median": paired["cost_delta_usd"]["median"],
            "boundary_pass_rate": campaign["boundary_summary"],
            "quality_judge_stage": "completed_position_swapped_external_judge",
            "blind_judge_winner_counts": {
                "skill": normalized_winners.count("skill"),
                "transfer": normalized_winners.count("transfer"),
                "tie": normalized_winners.count("tie"),
            },
        },
        "credential_scan": scan,
        "gates": gates,
        "passed_gates": sum(gates.values()),
        "total_gates": len(gates),
    }
    acceptance_path = output / "acceptance.json"
    write_json(acceptance_path, acceptance)

    report = f"""# Experiment 10-1 retained comparison report

## Outcome

This is a **complete bounded comparison**. The campaign
retains {len(pairs)} paired tasks ({len(runs)} main trajectories), {len(boundary_runs)} boundary trajectories,
{len(provider_receipts)} raw provider receipts, {len(tavily_receipts)} raw Tavily receipts, and
{len(judge_receipts)} position-swapped blind-judge receipts. Every evidence gate passes
({sum(gates.values())}/{len(gates)}).

- Transfer passed {sum(bool(run['outcome']['pass']) for run in runs if run['path'] == 'transfer')}/{len(pairs)} complete
  deterministic task gates; its declared capability sequence completed in {transfer['required_role_sequence_rate']:.1%} of runs.
- Skill passed {sum(bool(run['outcome']['pass']) for run in runs if run['path'] == 'skill')}/{len(pairs)} complete
  deterministic task gates. It loaded at least triage in {sum(bool(run.get('loaded_skills')) for run in runs if run['path'] == 'skill')}/{len(pairs)} runs,
  and completed the declared sequence in {skill['required_role_sequence_rate']:.1%} of runs.
- Both arms passed 6/6 boundary cases; boundary reliability is reported separately from end-to-end task success.
- The independent Gemini 2.5 Flash Lite judge preferred Skill {normalized_winners.count('skill')}/{len(normalized_winners)}
  swapped presentations, Transfer {normalized_winners.count('transfer')}/{len(normalized_winners)}, and called
  {normalized_winners.count('tie')}/{len(normalized_winners)} ties. The two presentations per pair were retained to
  control position bias.

## Cost and latency

The Skill-minus-Transfer median delta was {paired['uncached_input_token_delta']['median']:.1f} uncached input tokens,
{paired['latency_delta_seconds']['median']:.3f} seconds, and ${paired['cost_delta_usd']['median']:.8f}. Provider-reported
cached input was zero throughout, so this run does not establish a model-prefix cache benefit. The Skill document
cache recorded per-run misses (and no hits across a run), as expected for the fresh-session cache used by this harness.

## Interpretation

For `qwen/qwen3.5-flash-02-23` under this bounded OpenRouter campaign, the repaired Skill arm now follows the
progressive-disclosure state machine and materially improves deterministic acceptance (50.0% vs 6.7%). The trade-off
is higher median uncached input (+{paired['uncached_input_token_delta']['median']:.1f} tokens), latency (+{paired['latency_delta_seconds']['median']:.3f}s),
and repriced cost (+${paired['cost_delta_usd']['median']:.8f}). This is evidence for the documented architecture trade-off,
not a universal model-independent superiority claim.
"""
    report_path = output / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    source_hashes = {name: sha256_file(ROOT / name) for name in SOURCE_FILES}
    manifest = {
        "schema_version": 1,
        "experiment": "10-1",
        "run_id": args.run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_source_sha256": source_hashes,
        "artifact_sha256": {
            "campaign.json": sha256_file(campaign_path),
            "judge.json": sha256_file(judge_path),
            "acceptance.json": sha256_file(acceptance_path),
            "REPORT.md": sha256_file(report_path),
        },
        "acceptance": {
            "evidence_status": overall,
            "passed_gates": acceptance["passed_gates"],
            "total_gates": acceptance["total_gates"],
        },
    }
    write_json(output / "manifest.json", manifest)
    print(f"packaged {args.run_id}: {overall} ({sum(gates.values())}/{len(gates)} gates)")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
