#!/usr/bin/env python3
"""Read-only, stage-aware preflight for Experiment 6-13."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

COMMIT = "87d6c1d969f6e0ca4dc5697940804e231118a63a"
PINNED_BLOBS = {
    "docs/zero_shot_rgb_sim2real.md": "844d113a726d7c3c8494700496591a2604f742e0",
    "env_config.json": "e32727956fc9dbf64336b53b77bc1a6044e2f5ef",
    "lerobot_sim2real/config/real_robot.py": "f522e6d1dab0ef4ff4a0204497c1616995346ad7",
    "lerobot_sim2real/scripts/record_reset_distribution.py": "ff20e1c3ea34b6d75f646c325f6fe49e1d83903c",
    "lerobot_sim2real/scripts/camera_alignment.py": "5d7a323075e43ba5c0a24bd2ce6c910f89e4a9c6",
    "lerobot_sim2real/scripts/capture_background_image.py": "f30d97cd7ead0cdfe9b38ea6c9523a5f38b404aa",
    "lerobot_sim2real/scripts/train_ppo_rgb.py": "af900d1e247349b61b707b4a63d30e0d297c9ea9",
    "lerobot_sim2real/scripts/eval_ppo_rgb.py": "506a4c190eb99b7cd2691562edb78f6f0dd748e3",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--real-frame", type=Path, help="existing real-camera frame; file is not opened")
    parser.add_argument("--greenscreen", type=Path, help="existing background image; file is not opened")
    parser.add_argument("--checkpoint", type=Path, help="existing trained checkpoint; file is not opened")
    parser.add_argument("--camera", type=Path, help="camera device; path is checked only")
    parser.add_argument("--robot-port", type=Path, help="robot device; path is checked only")
    parser.add_argument("--hardware-run-authorized", action="store_true")
    parser.add_argument("--safety-checklist-complete", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks: list[dict[str, object]] = []

    def add(check_id: str, passed: bool, detail: str, stages: list[int]) -> None:
        checks.append({"id": check_id, "passed": passed, "stages": stages, "detail": detail})

    head = git(args.upstream, "rev-parse", "HEAD")
    add("pinned_commit", head == COMMIT, f"expected {COMMIT}; found {head or 'not a git checkout'}", [1, 2, 3, 4, 5])
    for path, blob in PINNED_BLOBS.items():
        found = git(args.upstream, "rev-parse", f"HEAD:{path}")
        add(f"blob:{path}", found == blob, f"expected {blob}; found {found or 'missing'}", [1, 2, 3, 4, 5])
    for module in ("torch", "mani_skill"):
        found = importlib.util.find_spec(module) is not None
        add(f"python_module:{module}", found, "installed" if found else "not importable", [1, 2, 3, 4])
    nvidia_smi = shutil.which("nvidia-smi")
    add("nvidia_gpu", bool(nvidia_smi), nvidia_smi or "nvidia-smi not found", [3, 4])
    add("offline_real_frame", bool(args.real_frame and args.real_frame.is_file()), str(args.real_frame or "not supplied; optional and not equivalent to the live upstream script"), [])
    add("camera_path", bool(args.camera and args.camera.exists()), str(args.camera or "not supplied"), [1, 2])
    add("greenscreen", bool(args.greenscreen and args.greenscreen.is_file()), str(args.greenscreen or "not supplied"), [3, 4])
    add("checkpoint", bool(args.checkpoint and args.checkpoint.is_file()), str(args.checkpoint or "not supplied"), [5])
    add("robot_port", bool(args.robot_port and args.robot_port.exists()), str(args.robot_port or "not supplied"), [1, 2, 5])
    add("hardware_authorization", args.hardware_run_authorized, "explicit" if args.hardware_run_authorized else "not granted", [1, 2, 5])
    add("safety_checklist", args.safety_checklist_complete, "attested" if args.safety_checklist_complete else "not attested", [1, 2, 5])

    readiness = {}
    for stage in range(1, 6):
        failed = [str(item["id"]) for item in checks if stage in item["stages"] and not item["passed"]]
        readiness[str(stage)] = {"preflight": "ready" if not failed else "blocked", "blockers": failed}
    report = {
        "schema_version": "1.0",
        "experiment_id": "6-13",
        "kind": "non_actuating_preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node() or "unknown",
        "upstream_path": str(args.upstream.resolve()),
        "stage_readiness": readiness,
        "status": "ready" if all(item["preflight"] == "ready" for item in readiness.values()) else "blocked",
        "checks": checks,
        "hardware_boundary": "Pinned stage 1 can actuate during real_env.reset; stage 2 connects hardware and disables torque; stages 3-4 are GPU-only; stage 5 actuates the policy.",
        "actuation_attempted": False
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
