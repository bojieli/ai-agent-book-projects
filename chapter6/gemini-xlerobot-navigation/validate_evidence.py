#!/usr/bin/env python3
"""Validate the local GPU desktop-planning evidence for Experiment 9-9."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_TOOL_NAMES = ["observe_scene", "pick", "place", "verify_state", "stop"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(data: dict[str, Any], evidence_dir: Path | None = None) -> list[str]:
    errors: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    expect(data.get("schema_version") == "3.0", "schema_version must be 3.0")
    expect(data.get("experiment_id") == "9-9", "experiment_id must be 9-9")
    expect(data.get("kind") == "desktop_manipulation_planning", "wrong evidence kind")
    expect(data.get("status") == "complete", "local evidence must be complete")
    metrics = data.get("metrics", {})
    expect(metrics.get("device", {}).get("device") in {"mps", "cuda"}, "evidence must use a local GPU accelerator")
    protocol = metrics.get("protocol", {})
    expect(len(protocol.get("seeds", [])) >= 3, "at least three planner seeds are required")
    expect(set(protocol.get("failure_probabilities", [])) >= {0.0, 0.25, 0.5}, "zero, moderate and high failure conditions are required")
    expect(protocol.get("total_episodes", 0) >= 2000, "at least 2000 planner episodes are required")
    models = metrics.get("models", [])
    expect(len(models) == len(protocol.get("seeds", [])), "one world-model report is required per seed")
    expect(max((item.get("test_mse", 1.0) for item in models), default=1.0) < 0.03, "world-model test MSE is too high")
    cells = metrics.get("cells", [])
    expect(len(cells) == len(protocol.get("seeds", [])) * len(protocol.get("failure_probabilities", [])) * 3, "one result cell is required per seed/failure/mode condition")
    high_failure = [item for item in cells if item.get("failure_probability") == 0.5]
    expect(high_failure and all(item.get("mode") in {"closed_loop", "predictive"} and item.get("success_rate") == 1.0 for item in high_failure if item.get("mode") != "open_loop"), "closed-loop and predictive planners must recover high-failure trials")
    open_loop_high = [item for item in high_failure if item.get("mode") == "open_loop"]
    expect(open_loop_high and max(item.get("success_rate", 1.0) for item in open_loop_high) < 1.0, "open-loop baseline must expose injected failures")
    expect(metrics.get("deterministic_replay") is True, "repeating a fixed planner seed must reproduce the same episode")
    contract = data.get("tool_contract", [])
    expect(contract == EXPECTED_TOOL_NAMES, "工具契约不是桌面操作实验规定的五个工具")
    artifacts = data.get("artifacts", [])
    expect(len(artifacts) == 3, "metrics, events and scene artifacts are required")
    if evidence_dir is not None:
        for index, artifact in enumerate(artifacts):
            path = evidence_dir / str(artifact.get("path", ""))
            expect(path.is_file(), f"artifact[{index}] does not exist")
            if path.is_file():
                expect(file_sha256(path) == artifact.get("sha256"), f"artifact[{index}] hash mismatch")
                if artifact.get("kind") == "events":
                    try:
                        event_log = json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError) as exc:
                        errors.append(f"event log cannot be read: {exc}")
                    else:
                        expect(event_log.get("tools") == EXPECTED_TOOL_NAMES, "event log tool list does not match the contract")
                        episodes = event_log.get("episodes", [])
                        expect(len(episodes) == protocol.get("total_episodes", 0), "one auditable event trace is required per episode")
                        expect(all(isinstance(item.get("events"), list) for item in episodes), "every episode must contain a tool event list")
    extension = data.get("xlerobot_robocrew_extension", {})
    expect(extension.get("actuation_attempted") is False, "local run must not claim hardware actuation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    errors = validate(data, args.evidence.resolve().parent)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID: experiment 9-9 local GPU evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
