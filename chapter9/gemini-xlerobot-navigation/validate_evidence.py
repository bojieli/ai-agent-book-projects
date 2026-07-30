#!/usr/bin/env python3
"""Strict completion/blocker gate for Experiment 9-9 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMIT = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"
GUIDE_BLOB = "d336a9e35838267614d31cdb98b9b50d66427f03"
MODEL = "gemini-robotics-er-1.5-preview"
TOOLS = {"move_forward", "turn_left", "turn_right"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


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

    expect(data.get("schema_version") == "1.0", "schema_version must be 1.0")
    expect(data.get("experiment_id") == "9-9", "experiment_id must be 9-9")
    status = data.get("status")
    expect(status in {"complete", "blocked"}, "status must be complete or blocked")
    upstream = data.get("upstream", {})
    expect(upstream.get("repository") == "https://github.com/Vector-Wangel/XLeRobot.git", "wrong upstream repository")
    expect(upstream.get("commit") == COMMIT, "wrong pinned XLeRobot commit")
    expect(upstream.get("guide_path") == "docs/en/source/software/getting_started/LLM_agent.md", "wrong guide path")
    expect(upstream.get("guide_blob") == GUIDE_BLOB, "wrong guide blob")
    expect(upstream.get("robocrew_version") == "0.3.1", "RoboCrew must be pinned to 0.3.1")
    blockers = data.get("blockers")
    expect(isinstance(blockers, list), "blockers must be a list")
    if status == "blocked":
        expect(bool(blockers), "blocked evidence must state at least one blocker")
        return errors

    expect(not blockers, "complete evidence cannot contain blockers")
    run = data.get("run", {})
    expect(run.get("actuation_authorized") is True, "complete requires explicit actuation authorization")
    expect(bool(run.get("operator")), "complete requires an identified operator")
    expect(bool(run.get("started_at")) and bool(run.get("ended_at")), "complete requires start and end timestamps")
    receipt_path, receipt_sha = run.get("receipt_path"), run.get("receipt_sha256")
    expect(bool(receipt_path) and bool(SHA256.fullmatch(str(receipt_sha or ""))), "complete requires a hashed navigation-run receipt")
    if evidence_dir is not None and receipt_path:
        receipt_file = evidence_dir / str(receipt_path)
        expect(receipt_file.is_file(), f"navigation receipt does not exist: {receipt_file}")
        if receipt_file.is_file():
            expect(file_sha256(receipt_file) == receipt_sha, "navigation receipt SHA-256 mismatch")
            try:
                receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                receipt = {}
                expect(False, "navigation receipt is not valid JSON")
            expect(receipt.get("kind") == "direct_execution_receipt", "wrong navigation receipt kind")
            expect(receipt.get("model") == "google_genai:" + MODEL and receipt.get("task") == "find the kitchen and go there", "navigation receipt model/task mismatch")
            expect(receipt.get("agent_go_returned") is True and receipt.get("error") is None, "navigation receipt does not show a completed agent loop")
            receipt_safety = receipt.get("safety", {})
            expect(all(receipt_safety.get(key) is True for key in ("robot_calibrated", "clear_route", "emergency_stop_ready", "human_observer_present")), "navigation receipt safety gate failed")
    safety = data.get("safety", {})
    for field in ("robot_calibrated", "clear_route", "emergency_stop_ready", "human_observer_present"):
        expect(safety.get(field) is True, f"complete requires safety.{field}=true")

    planner = data.get("planner", {})
    expect(planner.get("provider") == "google_genai", "planner provider must be google_genai")
    expect(planner.get("model") == MODEL, f"planner model must be {MODEL}; generic Gemini is not equivalent")
    expect(planner.get("api_call_succeeded") is True, "complete requires a real successful model call")
    expect(planner.get("robocrew") is True, "complete requires RoboCrew execution")
    expect(planner.get("angular_overlay") is True, "complete requires angular-scale camera annotation")
    frequency = planner.get("decision_frequency_hz")
    expect(isinstance(frequency, (int, float)) and 0.5 <= frequency <= 1.0, "measured decision frequency must be 0.5..1.0 Hz")
    expect(set(planner.get("tools", [])) == TOOLS and len(planner.get("tools", [])) == 3, "navigation tool set must be exactly move_forward, turn_left, turn_right")

    navigation = data.get("navigation", {})
    expect(navigation.get("task") == "find the kitchen and go there", "task must match the manuscript")
    expect(navigation.get("executed") is True, "complete requires a real navigation run")
    expect(navigation.get("success") is True, "complete requires reaching the kitchen under the declared success rule")
    cues = navigation.get("semantic_cues", [])
    expect(isinstance(cues, list) and len(cues) >= 2, "record at least two visual semantic cues")
    expect(any(any(word in cue.lower() for word in ("fridge", "refrigerator", "kitchen")) for cue in cues), "semantic cues need kitchen-specific evidence")
    steps = navigation.get("steps", [])
    expect(isinstance(steps, list) and len(steps) >= 3, "complete requires at least three timestamped planning steps")
    for index, step in enumerate(steps if isinstance(steps, list) else []):
        expect(step.get("tool") in TOOLS, f"step[{index}] used an undeclared tool")
        expect(bool(step.get("observation")) and bool(step.get("reasoning_summary")), f"step[{index}] lacks observation/reasoning evidence")
        expect(bool(SHA256.fullmatch(str(step.get("image_sha256", "")))), f"step[{index}] lacks an image SHA-256")

    artifacts = data.get("artifacts", [])
    kinds = {item.get("kind") for item in artifacts if isinstance(item, dict)}
    expect({"video", "planner_log", "timing"}.issubset(kinds), "complete requires video, planner_log, and timing artifacts")
    for index, item in enumerate(artifacts if isinstance(artifacts, list) else []):
        expect(bool(item.get("path")), f"artifact[{index}] requires a path")
        expect(bool(SHA256.fullmatch(str(item.get("sha256", "")))), f"artifact[{index}] requires a SHA-256")
        if evidence_dir is not None and item.get("path"):
            artifact_path = evidence_dir / str(item["path"])
            expect(artifact_path.is_file(), f"artifact[{index}] does not exist: {artifact_path}")
            if artifact_path.is_file():
                expect(file_sha256(artifact_path) == item.get("sha256"), f"artifact[{index}] SHA-256 mismatch")
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
    print(f"VALID: experiment 9-9 evidence is an honest {data['status']} record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
