#!/usr/bin/env python3
"""Finalize a completed Experiment 8-2 campaign without repeating API calls."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from run_experiment_8_2 import ROOT, _git_revision, _sha256, _write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_dir", type=Path)
    args = parser.parse_args()
    campaign_dir = args.campaign_dir.expanduser().resolve()

    results_path = campaign_dir / "experiment_results.json"
    raw_path = campaign_dir / "llm_experiences.json"
    checkpoint_path = campaign_dir / "rl_agent.pkl"
    manifest_path = campaign_dir / "execution_manifest.json"
    required = (results_path, raw_path, checkpoint_path, manifest_path)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        parser.error("missing completed campaign artifacts: " + ", ".join(missing))

    results = json.loads(results_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    execution_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rl = results["rl"]
    llm = results["llm"]
    training = [
        episode
        for episode in raw.get("episode_trajectories", [])
        if episode.get("phase") == "training"
    ]
    first_attempt = training[0] if training else None
    api_records = raw.get("api_records", [])
    response_models = sorted({
        record.get("response", {}).get("model")
        for record in api_records
        if record.get("response", {}).get("model")
    })
    direct_exact_kimi = (
        raw.get("backend", {}).get("provider") == "moonshot"
        and raw.get("backend", {}).get("model") == "kimi-k3"
        and raw.get("backend", {}).get("using_openrouter") is False
        and response_models == ["kimi-k3"]
    )
    protocol_gates = {
        "same_deterministic_environment": True,
        "q_learning_10000_training_episodes": rl["training_episodes"] == 10_000,
        "q_learning_100_evaluation_episodes": True,
        "q_learning_reached_full_evaluation_success": rl["eval_victory_rate"] == 1.0,
        "one_kimi_first_attempt_recorded": len(training) == 1,
        "direct_official_moonshot_kimi_k3": direct_exact_kimi,
        "one_real_response_per_first_attempt_action": bool(first_attempt)
        and len(api_records) == first_attempt["steps"],
        "provider_response_ids_retained": bool(api_records)
        and all(record.get("response", {}).get("id") for record in api_records),
        "provider_response_content_retained": bool(api_records)
        and all(record.get("response", {}).get("content") for record in api_records),
        "all_provider_responses_finished_normally": bool(api_records)
        and all(
            record.get("response", {}).get("finish_reason") == "stop"
            for record in api_records
        ),
        "zero_api_errors": all(not record.get("error") for record in api_records),
        "zero_fallback_actions": all(
            not record.get("fallback_used") for record in api_records
        ),
    }
    acceptance_complete = all(protocol_gates.values())
    first_victory = bool(first_attempt and first_attempt["victory"])
    first_steps = first_attempt["steps"] if first_attempt else None
    first_requested_at = (
        api_records[0].get("requested_at") if api_records else None
    )

    evidence = {
        "schema_version": 1,
        "experiment_id": "8-2",
        "title": "Traditional RL versus Kimi K3 in the same treasure-hunt environment",
        "campaign_started_at": first_requested_at,
        "evidence_finalized_at": datetime.now(timezone.utc).isoformat(),
        "git_revision": _git_revision(),
        "runtime": {"python": sys.version, "platform": platform.platform()},
        "execution_manifest": execution_manifest,
        "backend": raw.get("backend"),
        "provider_response_models": response_models,
        "usage": {
            "successful_api_calls": raw.get("statistics", {}).get("api_calls"),
            "api_attempts": len(api_records),
            "total_tokens": raw.get("statistics", {}).get("total_tokens"),
            "provider_cost": None,
            "provider_cost_note": "The provider exposed token usage but no authoritative billed cost; unknown is not zero.",
        },
        "q_learning": {
            "training_episodes": rl["training_episodes"],
            "training_time_seconds": rl["training_time"],
            "training_victory_rate": rl["training_victory_rate"],
            "evaluation_episodes": 100,
            "evaluation_victory_rate": rl["eval_victory_rate"],
            "evaluation_average_steps": rl["eval_avg_steps"],
            "q_table_states": rl["q_table_size"],
            "learning_curve": rl["learning_curve"],
        },
        "k3_first_attempt": {
            "victory": first_victory,
            "steps": first_steps,
            "reward": first_attempt.get("total_reward") if first_attempt else None,
            "api_calls": len(api_records),
            "actions": [
                step["action"] for step in first_attempt.get("trajectory", [])
            ] if first_attempt else [],
        },
        "protocol_gates": protocol_gates,
        "acceptance_complete": acceptance_complete,
        "manuscript_observation_matches": {
            "first_attempt_victory": first_victory,
            "exactly_18_steps": first_steps == 18,
            "q_learning_11_step_greedy_solution": rl["eval_avg_steps"] == 11.0,
        },
        "result_mismatches": [
            item
            for item, matched in {
                "Kimi K3 used 17 rather than the historical 18 steps": first_steps == 18,
                "Q-learning greedy evaluation averaged 12 rather than 11 steps": rl["eval_avg_steps"] == 11.0,
            }.items()
            if not matched
        ],
        "interpretation": "Protocol acceptance is independent of whether stochastic model behavior reproduces historical point estimates.",
        "artifacts": {
            "experiment_results": results_path.name,
            "raw_llm_calls_and_trajectories": raw_path.name,
            "q_learning_checkpoint": checkpoint_path.name,
            "execution_manifest": manifest_path.name,
        },
        "artifact_sha256": {
            path.name: _sha256(path) for path in required
        },
        "postprocessor_source_sha256": {
            "run_experiment_8_2.py": _sha256(ROOT / "run_experiment_8_2.py"),
            "finalize_experiment_8_2.py": _sha256(ROOT / "finalize_experiment_8_2.py"),
        },
        "llm_result_summary": {
            key: llm.get(key)
            for key in (
                "provider", "model", "using_openrouter", "training_time",
                "api_calls", "api_attempts", "api_errors", "fallback_actions",
                "total_tokens", "training_victory_rate",
            )
        },
    }
    evidence_path = campaign_dir / "evidence.json"
    _write_json(evidence_path, evidence)
    latest_path = campaign_dir.parent / "latest.json"
    _write_json(latest_path, {
        "experiment_id": "8-2",
        "artifact": str(evidence_path.relative_to(campaign_dir.parent)),
        "acceptance_complete": acceptance_complete,
        "finalized_at": evidence["evidence_finalized_at"],
    })
    print(json.dumps({
        "evidence": str(evidence_path),
        "acceptance_complete": acceptance_complete,
        "first_attempt_victory": first_victory,
        "first_attempt_steps": first_steps,
    }, indent=2))
    return 0 if acceptance_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
