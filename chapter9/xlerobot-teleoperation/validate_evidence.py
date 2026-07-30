#!/usr/bin/env python3
"""Strict completion/blocker gate for Experiment 9-8 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMIT = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"
GUIDE_BLOB = "3992358282ff54cfce8d90a525e784aedcf045f7"
MODES = {
    "keyboard": ("software/examples/4_xlerobot_teleop_keyboard.py", "efbe076dfbda3c6280fa54f0eb5bca1a12518a0d"),
    "xbox": ("software/examples/5_xlerobot_teleop_xbox.py", "de7bc17d570167e58b15e38c06c0fa23af74632a"),
    "joycon": ("software/examples/7_xlerobot_teleop_joycon.py", "21a48258d22b1fc002f63555a2f3dc2950bdfb24"),
    "vr": ("software/examples/8_xlerobot_teleop_vr.py", "315bb81f13a37746de0f329e3ba11240a2230806"),
}
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
    expect(data.get("experiment_id") == "9-8", "experiment_id must be 9-8")
    status = data.get("status")
    expect(status in {"complete", "blocked"}, "status must be complete or blocked")
    upstream = data.get("upstream", {})
    expect(upstream.get("repository") == "https://github.com/Vector-Wangel/XLeRobot.git", "wrong upstream repository")
    expect(upstream.get("commit") == COMMIT, "upstream commit is not pinned to the required revision")
    expect(upstream.get("guide_path") == "docs/en/source/software/getting_started/XLeRobot_teleop.md", "wrong guide path")
    expect(upstream.get("guide_blob") == GUIDE_BLOB, "wrong guide blob")

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
    safety = data.get("safety", {})
    for field in ("robot_calibrated", "clear_workspace", "emergency_stop_ready", "human_observer_present"):
        expect(safety.get(field) is True, f"complete requires safety.{field}=true")

    modes = data.get("modes", [])
    expect(isinstance(modes, list), "modes must be a list")
    by_name = {item.get("name"): item for item in modes if isinstance(item, dict)}
    expect(set(by_name) == set(MODES), "complete requires exactly keyboard, xbox, joycon, and vr modes")
    for name, (entrypoint, blob) in MODES.items():
        item = by_name.get(name, {})
        expect(item.get("entrypoint") == entrypoint, f"{name}: wrong entrypoint")
        expect(item.get("entrypoint_blob") == blob, f"{name}: wrong pinned entrypoint blob")
        expect(item.get("executed") is True, f"{name}: real execution was not recorded")
        receipt_path = item.get("receipt_path")
        receipt_sha = item.get("receipt_sha256")
        expect(bool(receipt_path) and bool(SHA256.fullmatch(str(receipt_sha or ""))), f"{name}: hashed launcher receipt is required")
        if evidence_dir is not None and receipt_path:
            receipt_file = evidence_dir / receipt_path
            expect(receipt_file.is_file(), f"{name}: receipt file does not exist: {receipt_file}")
            if receipt_file.is_file():
                expect(file_sha256(receipt_file) == receipt_sha, f"{name}: receipt SHA-256 mismatch")
                try:
                    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    receipt = {}
                    expect(False, f"{name}: receipt is not valid JSON")
                expect(receipt.get("kind") == "direct_execution_receipt", f"{name}: wrong receipt kind")
                expect(receipt.get("experiment_id") == "9-8" and receipt.get("mode") == name, f"{name}: receipt identity mismatch")
                expect(receipt.get("commit") == COMMIT and receipt.get("entrypoint_blob") == blob, f"{name}: receipt source mismatch")
                expect(receipt.get("actuation_authorized") is True and receipt.get("return_code") == 0 and receipt.get("completed_process") is True, f"{name}: receipt does not prove a completed authorized process")
                receipt_safety = receipt.get("safety", {})
                expect(all(receipt_safety.get(key) is True for key in ("robot_calibrated", "clear_workspace", "emergency_stop_ready", "human_observer_present")), f"{name}: receipt safety gate failed")
        expect(bool(item.get("latency_ms")), f"{name}: latency samples are required")
        expect(bool(item.get("precision_error_mm")), f"{name}: precision measurements are required")
        score = item.get("quality_score_1_to_5")
        expect(isinstance(score, (int, float)) and 1 <= score <= 5, f"{name}: quality score must be 1..5")

    tasks = data.get("task_outcomes", [])
    by_task = {item.get("name"): item for item in tasks if isinstance(item, dict)}
    expect(set(by_task) == {"pick", "place", "wipe"}, "complete requires pick, place, and wipe outcomes")
    for name in ("pick", "place", "wipe"):
        item = by_task.get(name, {})
        attempts, successes = item.get("attempts"), item.get("successes")
        expect(isinstance(attempts, int) and attempts > 0, f"{name}: at least one attempt is required")
        expect(isinstance(successes, int) and isinstance(attempts, int) and 0 <= successes <= attempts, f"{name}: invalid success count")
        expect(bool(item.get("success_definition")), f"{name}: success definition is required")

    artifacts = data.get("artifacts", [])
    kinds = {item.get("kind") for item in artifacts if isinstance(item, dict)}
    expect("video" in kinds and "measurements" in kinds, "complete requires video and measurements artifacts")
    for index, item in enumerate(artifacts if isinstance(artifacts, list) else []):
        expect(isinstance(item, dict) and bool(item.get("path")), f"artifact[{index}] requires a path")
        expect(isinstance(item, dict) and bool(SHA256.fullmatch(str(item.get("sha256", "")))), f"artifact[{index}] requires a SHA-256")
        if evidence_dir is not None and isinstance(item, dict) and item.get("path"):
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
    print(f"VALID: experiment 9-8 evidence is an honest {data['status']} record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
