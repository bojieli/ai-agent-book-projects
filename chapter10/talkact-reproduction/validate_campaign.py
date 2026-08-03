#!/usr/bin/env python3
"""Validate a retained 16-episode Experiment 10-4 campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


TASKS = (
    "forms-insurance",
    "booking-flight",
    "webmail-report",
    "meeting-helper",
)
CONDITIONS = ("duplex", "strawman")
SEEDS = (0, 1)
SOURCE_COMMIT = "7d70007f72d45ddfc1a14e8e229b6d444e4919a2"
SLOW_MODEL = "claude-opus-4-8"
FAST_MODEL = "claude-haiku-4-5"
USER_MODEL = "anthropic:claude-sonnet-4-5-20250929"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def positive_usage(usage: dict | None) -> bool:
    return bool(usage) and sum(v for v in usage.values() if isinstance(v, int)) > 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    protocol = json.loads((run_dir / "protocol.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    aggregate = json.loads((run_dir / "aggregate.json").read_text())

    expected_names = {
        f"{task}__{condition}__s{seed}.json"
        for task in TASKS
        for condition in CONDITIONS
        for seed in SEEDS
    }
    episode_paths = sorted((run_dir / "episodes").glob("*.json"))
    actual_names = {path.name for path in episode_paths}
    episodes = [json.loads(path.read_text()) for path in episode_paths]

    episode_pairs = Counter((ep.get("task"), ep.get("condition")) for ep in episodes)
    event_kinds = Counter(
        event.get("kind") for episode in episodes for event in episode.get("events", [])
    )
    duplex_events = [
        event
        for episode in episodes
        if episode.get("condition") == "duplex"
        for event in episode.get("events", [])
    ]
    fast_to_slow = sum(
        len(event.get("to_slow", []))
        for event in duplex_events
        if event.get("kind") == "fast_turn"
    )
    slow_to_fast = sum(
        1
        for event in duplex_events
        if event.get("kind") in {"slow_ask_user", "slow_tell_user"}
    )
    latency_samples = sum(
        1
        for episode in episodes
        for event in episode.get("events", [])
        if event.get("kind") == "voice_latency"
    )
    provider_errors = [
        event
        for episode in episodes
        for event in episode.get("events", [])
        if event.get("kind")
        in {"episode_error", "slow_task_error", "episode_crashed"}
    ]

    gates = {
        "source_commit": protocol.get("source_commit") == SOURCE_COMMIT,
        "exact_campaign_shape": actual_names == expected_names and len(episodes) == 16,
        "two_seeds_per_task_condition": all(
            episode_pairs[(task, condition)] == 2
            for task in TASKS
            for condition in CONDITIONS
        ),
        "summary_has_16_fresh_rows": len(summary) == 16
        and Counter((row.get("task"), row.get("condition")) for row in summary)
        == episode_pairs,
        "all_episode_records_complete": all(
            ep.get("error") is None
            and isinstance(ep.get("env_state"), dict)
            and isinstance(ep.get("events"), list)
            and isinstance(ep.get("transcript"), list)
            for ep in episodes
        ),
        "anthropic_slow_model": all(ep.get("slow_model") == SLOW_MODEL for ep in episodes),
        "anthropic_fast_model": all(
            (ep.get("fast_model") == FAST_MODEL if ep.get("condition") == "duplex" else ep.get("fast_model") is None)
            for ep in episodes
        ),
        "explicit_anthropic_caller_override": all(
            ep.get("user_model") == USER_MODEL for ep in episodes
        )
        and protocol.get("caller_deviation", {}).get("model")
        == "claude-sonnet-4-5-20250929",
        "provider_usage_retained": all(
            positive_usage(ep.get("slow_usage"))
            and (
                positive_usage(ep.get("fast_usage"))
                if ep.get("condition") == "duplex"
                else ep.get("fast_usage") is None
            )
            for ep in episodes
        ),
        "no_runtime_provider_errors": not provider_errors,
        "real_concurrent_duplex_events": event_kinds["fast_turn"] > 0
        and event_kinds["slow_step"] > 0,
        "bidirectional_bridge_observed": fast_to_slow > 0 and slow_to_fast > 0,
        "voice_latency_samples": latency_samples > 0
        and all(
            any(event.get("kind") == "voice_latency" for event in ep.get("events", []))
            for ep in episodes
        ),
        "deterministic_checks_retained": all(
            "success" in row and "partial" in row and "details" in row
            for row in summary
        ),
        "judge_results_retained": all(
            "judge_error" not in row for row in summary
        ),
        "duplex_strawman_aggregate": {
            row.get("condition"): row.get("n_episodes") for row in aggregate
        }
        == {"duplex": 8, "strawman": 8},
        "no_credential_material": not any(
            re.search(rb"sk-ant-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}", path.read_bytes())
            for path in run_dir.rglob("*")
            if path.is_file()
        ),
    }

    files = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        if path.name in {"acceptance.json", "manifest.json"}:
            continue
        files.append(
            {
                "path": str(path.relative_to(run_dir)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    acceptance = {
        "schema_version": 1,
        "experiment": "10-4",
        "run_dir": run_dir.name,
        "passed": all(gates.values()),
        "gates": gates,
        "counts": {
            "episodes": len(episodes),
            "duplex": sum(ep.get("condition") == "duplex" for ep in episodes),
            "strawman": sum(ep.get("condition") == "strawman" for ep in episodes),
            "fast_to_slow_relays": fast_to_slow,
            "slow_to_fast_events": slow_to_fast,
            "voice_latency_samples": latency_samples,
            "files_hashed": len(files),
        },
        "comparison": aggregate,
    }
    manifest = {
        "schema_version": 1,
        "experiment": "10-4",
        "run_dir": run_dir.name,
        "files": files,
    }
    (run_dir / "acceptance.json").write_text(json.dumps(acceptance, indent=2) + "\n")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(acceptance, indent=2))
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
