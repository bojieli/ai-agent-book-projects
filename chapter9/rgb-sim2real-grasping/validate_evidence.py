#!/usr/bin/env python3
"""Strict five-stage completion/blocker gate for Experiment 9-10 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMIT = "87d6c1d969f6e0ca4dc5697940804e231118a63a"
GUIDE_BLOB = "844d113a726d7c3c8494700496591a2604f742e0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STAGES = {
    1: ("environment_alignment", True),
    2: ("background_replacement", False),
    3: ("domain_randomization", False),
    4: ("ppo_training", False),
    5: ("real_world_deployment", True),
}
REQUIRED_RANDOMIZATION = {"robot_color", "object_texture", "lighting", "camera_fov", "physical_parameters"}


def valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


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
    expect(data.get("experiment_id") == "9-10", "experiment_id must be 9-10")
    status = data.get("status")
    expect(status in {"complete", "blocked"}, "status must be complete or blocked")
    upstream = data.get("upstream", {})
    expect(upstream.get("repository") == "https://github.com/StoneT2000/lerobot-sim2real.git", "wrong upstream repository")
    expect(upstream.get("commit") == COMMIT, "wrong pinned upstream commit")
    expect(upstream.get("guide_path") == "docs/zero_shot_rgb_sim2real.md", "wrong guide path")
    expect(upstream.get("guide_blob") == GUIDE_BLOB, "wrong guide blob")

    stages = data.get("stages", [])
    expect(isinstance(stages, list), "stages must be a list")
    by_number = {item.get("stage"): item for item in stages if isinstance(item, dict)}
    expect(set(by_number) == set(STAGES) and len(stages) == 5, "evidence must contain exactly stages 1 through 5")
    for number, (name, hardware) in STAGES.items():
        stage = by_number.get(number, {})
        expect(stage.get("name") == name, f"stage {number}: expected name {name}")
        expect(stage.get("robot_actuation_required") is hardware, f"stage {number}: wrong hardware boundary")
        expect(stage.get("status") in {"complete", "blocked", "not_run"}, f"stage {number}: invalid status")

    blockers = data.get("blockers")
    expect(isinstance(blockers, list), "blockers must be a list")
    if status == "blocked":
        expect(bool(blockers), "blocked evidence must state at least one blocker")
        return errors

    expect(not blockers, "complete evidence cannot contain blockers")
    expect(all(by_number.get(number, {}).get("status") == "complete" for number in STAGES), "overall complete requires all five stages complete")
    run = data.get("run", {})
    expect(run.get("robot_actuation_authorized") is True, "stage 5 completion requires explicit robot-actuation authorization")
    expect(bool(run.get("operator")), "complete requires an identified operator")
    expect(bool(run.get("started_at")) and bool(run.get("ended_at")), "complete requires start and end timestamps")
    expect(bool(run.get("gpu")), "complete requires the GPU used for simulation/training")

    stage1 = by_number.get(1, {})
    for field in ("simulation_config_sha256", "real_frame_sha256", "overlay_sha256"):
        expect(valid_sha(stage1.get(field)), f"stage 1: {field} is required")
    expect(isinstance(stage1.get("alignment_error_px"), (int, float)), "stage 1: measured alignment_error_px is required")

    stage2 = by_number.get(2, {})
    for field in ("background_sha256", "config_sha256", "composite_sha256"):
        expect(valid_sha(stage2.get(field)), f"stage 2: {field} is required")

    stage3 = by_number.get(3, {})
    expect(REQUIRED_RANDOMIZATION.issubset(set(stage3.get("parameters", []))), "stage 3: robot color, object texture, lighting, camera FOV, and physical parameters are required")
    expect(valid_sha(stage3.get("real_measurements_sha256")), "stage 3: real-world calibration measurements are required")
    expect(valid_sha(stage3.get("reset_distribution_sha256")), "stage 3: randomized reset-distribution evidence is required")

    stage4 = by_number.get(4, {})
    expect(stage4.get("algorithm") == "PPO", "stage 4: algorithm must be PPO")
    expect(stage4.get("rgb_only") is True, "stage 4: observations must be RGB-only")
    expect(isinstance(stage4.get("timesteps"), int) and stage4["timesteps"] > 0, "stage 4: positive training timesteps required")
    expect(isinstance(stage4.get("evaluation_episodes"), int) and stage4["evaluation_episodes"] > 0, "stage 4: evaluation episodes required")
    rate = stage4.get("simulation_success_rate")
    expect(isinstance(rate, (int, float)) and rate > 0.9, "stage 4: measured simulation success rate must be greater than 0.90")
    expect(valid_sha(stage4.get("checkpoint_sha256")) and valid_sha(stage4.get("metrics_sha256")), "stage 4: hashed checkpoint and metrics are required")

    stage5 = by_number.get(5, {})
    expect(stage5.get("executed") is True, "stage 5: real deployment was not executed")
    expect(stage5.get("zero_shot") is True and stage5.get("fine_tuning_steps") == 0, "stage 5: deployment must be zero-shot with no real-world fine-tuning")
    expect(stage5.get("step_confirmation_enabled") is True, "stage 5: first acceptance must preserve --no-continuous-eval")
    expect(stage5.get("control_frequency_hz") == 15, "stage 5: acceptance run must use the upstream-recommended 15 Hz")
    trials, successes = stage5.get("trials"), stage5.get("successes")
    expect(isinstance(trials, int) and trials > 0, "stage 5: at least one real trial is required")
    expect(isinstance(successes, int) and isinstance(trials, int) and 0 < successes <= trials, "stage 5: at least one successful grasp is required")
    expect(valid_sha(stage5.get("video_sha256")), "stage 5: hashed real-run video is required")
    safety = stage5.get("safety", {})
    for field in ("robot_calibrated", "clear_workspace", "emergency_stop_ready", "human_observer_present"):
        expect(safety.get(field) is True, f"stage 5: safety.{field} must be true")

    artifacts = data.get("artifacts", [])
    artifact_stages = {item.get("stage") for item in artifacts if isinstance(item, dict)}
    expect(set(STAGES).issubset(artifact_stages), "complete requires at least one hashed artifact from every stage")
    for index, item in enumerate(artifacts if isinstance(artifacts, list) else []):
        expect(bool(item.get("path")), f"artifact[{index}] requires a path")
        expect(valid_sha(item.get("sha256")), f"artifact[{index}] requires a SHA-256")
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
    print(f"VALID: experiment 9-10 evidence is an honest {data['status']} record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
