#!/usr/bin/env python3
"""Run and retain the exact real Experiment 8-2 comparison.

The manuscript compares 10,000 deterministic Q-learning episodes with Kimi K3's
first attempt in the same treasure-hunt environment. A failed manuscript
hypothesis is still a completed experiment; acceptance therefore verifies the
protocol and evidence provenance separately from the observed outcome.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from experiment import ExperimentRunner


ROOT = Path(__file__).resolve().parent


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _write_json(path: Path, payload: Any) -> None:
    def json_default(value: Any) -> Any:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, Path):
            return str(value)
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    path.write_text(
        json.dumps(
            payload, ensure_ascii=False, indent=2, default=json_default
        ) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real, evidence-retaining Chapter 7 Experiment 8-2 campaign"
    )
    parser.add_argument("--model", default="kimi-k3")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rl-episodes", type=int, default=10_000)
    parser.add_argument("--rl-eval-episodes", type=int, default=100)
    parser.add_argument(
        "--llm-eval-episodes",
        type=int,
        default=0,
        help="The manuscript's core observation is the first attempt; optional later evaluations are separate.",
    )
    parser.add_argument("--output-root", default=str(ROOT / "validation"))
    args = parser.parse_args()

    if args.rl_episodes != 10_000 or args.rl_eval_episodes != 100:
        parser.error("canonical Experiment 8-2 requires 10,000 RL training and 100 RL evaluation episodes")
    if args.llm_eval_episodes < 0:
        parser.error("--llm-eval-episodes must be non-negative")
    if not os.getenv("MOONSHOT_API_KEY"):
        parser.error(
            "MOONSHOT_API_KEY is required: an OpenRouter substitute is not exact Kimi K3 evidence"
        )

    random.seed(args.seed)
    np.random.seed(args.seed)

    output_root = Path(args.output_root).expanduser().resolve()
    runner = ExperimentRunner(results_dir=str(output_root))
    started_at = datetime.now(timezone.utc)

    rl_results = runner.run_rl_experiment(
        num_training_episodes=args.rl_episodes,
        num_eval_episodes=args.rl_eval_episodes,
        verbose=False,
        stochastic=False,
        checkpoint_interval=1000,
        learning_rate=0.2,
        discount_factor=0.99,
        epsilon_decay=0.9995,
        epsilon_min=0.1,
    )
    llm_results = runner.run_llm_experiment(
        num_training_episodes=1,
        num_eval_episodes=args.llm_eval_episodes,
        verbose=False,
        stochastic=False,
        model=args.model,
    )
    runner.results = {"rl": rl_results, "llm": llm_results}
    _write_json(runner.experiment_dir / "experiment_results.json", runner.results)

    raw_path = runner.experiment_dir / "llm_experiences.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    training = [
        episode
        for episode in raw.get("episode_trajectories", [])
        if episode.get("phase") == "training"
    ]
    first_attempt = training[0] if training else None
    api_records = raw.get("api_records", [])
    response_ids_present = all(
        bool((record.get("response") or {}).get("id")) for record in api_records
    )
    response_contents_present = all(
        bool((record.get("response") or {}).get("content")) for record in api_records
    )
    no_api_errors = all(not record.get("error") for record in api_records)
    no_fallbacks = all(not record.get("fallback_used") for record in api_records)
    direct_exact_kimi = (
        raw.get("backend", {}).get("provider") == "moonshot"
        and raw.get("backend", {}).get("model") == "kimi-k3"
        and raw.get("backend", {}).get("using_openrouter") is False
    )
    response_models = sorted(
        {
            (record.get("response") or {}).get("model")
            for record in api_records
            if (record.get("response") or {}).get("model")
        }
    )

    protocol_gates = {
        "same_deterministic_environment": True,
        "q_learning_10000_training_episodes": rl_results["training_episodes"] == 10_000,
        "q_learning_100_evaluation_episodes": args.rl_eval_episodes == 100,
        "q_learning_reached_full_evaluation_success": rl_results["eval_victory_rate"] == 1.0,
        "one_kimi_first_attempt_recorded": len(training) == 1,
        "direct_official_moonshot_kimi_k3": direct_exact_kimi,
        "one_real_response_per_first_attempt_action": bool(first_attempt)
        and len(api_records) == first_attempt["steps"],
        "provider_response_ids_retained": bool(api_records) and response_ids_present,
        "provider_response_content_retained": bool(api_records) and response_contents_present,
        "zero_api_errors": no_api_errors,
        "zero_fallback_actions": no_fallbacks,
    }
    acceptance_complete = all(protocol_gates.values())
    first_attempt_victory = bool(first_attempt and first_attempt["victory"])
    first_attempt_steps = first_attempt["steps"] if first_attempt else None

    evidence = {
        "schema_version": 1,
        "experiment_id": "8-2",
        "title": "Traditional RL versus Kimi K3 in the same treasure-hunt environment",
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "git_revision": _git_revision(),
        "command": {
            "argv": sys.argv,
            "seed": args.seed,
            "deterministic": True,
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
        },
        "backend": raw.get("backend"),
        "provider_response_models": response_models,
        "usage": {
            "successful_api_calls": raw.get("statistics", {}).get("api_calls"),
            "api_attempts": len(api_records),
            "total_tokens": raw.get("statistics", {}).get("total_tokens"),
            "provider_cost": None,
            "provider_cost_note": "The response exposed token usage but no authoritative billed cost; unknown is not zero.",
        },
        "q_learning": {
            "training_episodes": rl_results["training_episodes"],
            "training_time_seconds": rl_results["training_time"],
            "training_victory_rate": rl_results["training_victory_rate"],
            "evaluation_victory_rate": rl_results["eval_victory_rate"],
            "evaluation_average_steps": rl_results["eval_avg_steps"],
            "q_table_states": rl_results["q_table_size"],
            "learning_curve": rl_results["learning_curve"],
        },
        "k3_first_attempt": {
            "victory": first_attempt_victory,
            "steps": first_attempt_steps,
            "reward": first_attempt.get("total_reward") if first_attempt else None,
            "api_calls": len(api_records),
        },
        "protocol_gates": protocol_gates,
        "acceptance_complete": acceptance_complete,
        "manuscript_observation_matches": {
            "first_attempt_victory": first_attempt_victory,
            "exactly_18_steps": first_attempt_steps == 18,
            "q_learning_11_step_greedy_solution": rl_results["eval_avg_steps"] == 11.0,
        },
        "interpretation": (
            "The protocol is accepted independently of whether stochastic model behavior reproduces the manuscript's exact 18-step observation."
        ),
        "artifacts": {
            "experiment_results": "experiment_results.json",
            "raw_llm_calls_and_trajectories": "llm_experiences.json",
            "q_learning_checkpoint": "rl_agent.pkl",
        },
        "source_sha256": {
            name: _sha256(ROOT / name)
            for name in (
                "game_environment.py",
                "rl_agent.py",
                "llm_agent.py",
                "experiment.py",
                "run_experiment_8_2.py",
            )
        },
    }
    _write_json(runner.experiment_dir / "evidence.json", evidence)
    _write_json(output_root / "latest.json", {
        "experiment_id": "8-2",
        "artifact": str((runner.experiment_dir / "evidence.json").relative_to(output_root)),
        "acceptance_complete": acceptance_complete,
        "finished_at": evidence["finished_at"],
    })

    print(json.dumps({
        "evidence": str(runner.experiment_dir / "evidence.json"),
        "acceptance_complete": acceptance_complete,
        "first_attempt_victory": first_attempt_victory,
        "first_attempt_steps": first_attempt_steps,
    }, indent=2))
    return 0 if acceptance_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
