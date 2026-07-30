#!/usr/bin/env python3
"""Audit safe pinned inputs and preserve direct host blockers; not an acceptance run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

COMMIT = "87d6c1d969f6e0ca4dc5697940804e231118a63a"
FILES = {
    "docs/zero_shot_rgb_sim2real.md": "844d113a726d7c3c8494700496591a2604f742e0",
    "docs/assets/camera_alignment_step_1.2.png": "688f0089c4a99bb2f608a805cbbb9fd96fb80830",
    "docs/assets/camera_alignment_step_1.3.png": "20943d0a0eff5b64afaafb04dab3522791e3bcf2",
    "docs/assets/eval_return_success_curves.png": "7185d982e165081ec0ad5ded4eb21dc9f172bac9",
    "docs/assets/tutorial_result_video.mp4": "d15f57adfd8b889ed8bb4d44d073f0cf7ba96c4a",
    "env_config.json": "e32727956fc9dbf64336b53b77bc1a6044e2f5ef",
    "system_id_so100.npy": "047b0110496f15f3a78a41b59c9f041cbbbbfd91",
    "lerobot_sim2real/scripts/record_reset_distribution.py": "ff20e1c3ea34b6d75f646c325f6fe49e1d83903c",
    "lerobot_sim2real/scripts/camera_alignment.py": "5d7a323075e43ba5c0a24bd2ce6c910f89e4a9c6",
    "lerobot_sim2real/scripts/capture_background_image.py": "f30d97cd7ead0cdfe9b38ea6c9523a5f38b404aa",
    "lerobot_sim2real/scripts/train_ppo_rgb.py": "af900d1e247349b61b707b4a63d30e0d297c9ea9",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def source_integrity(repo: Path) -> dict[str, Any]:
    head = git(repo, "rev-parse", "HEAD")
    files = []
    for path, expected in FILES.items():
        found = git(repo, "rev-parse", f"HEAD:{path}")
        files.append({"path": path, "expected_blob": expected, "found_blob": found or None, "passed": found == expected})
    return {"head": head, "expected_head": COMMIT, "passed": head == COMMIT and all(item["passed"] for item in files), "files": files}


def inspect_image(repo: Path, relative: str) -> dict[str, Any]:
    path = repo / relative
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
        return {
            "path": relative,
            "sha256": sha256(path),
            "width": image.width,
            "height": image.height,
            "channels": 3,
            "mean_rgb": [round(float(value), 4) for value in rgb.mean(axis=(0, 1))],
            "pixel_stddev": round(float(rgb.std()), 4),
        }


def measure_dynamics(repo: Path) -> dict[str, Any]:
    path = repo / "system_id_so100.npy"
    expected_sha = "4ca6cc4cd5c26540685d54e2cd2babde2204d0d3f369a63b5e817b1e7cf381db"
    actual_sha = sha256(path)
    if actual_sha != expected_sha or git(repo, "rev-parse", "HEAD:system_id_so100.npy") != FILES["system_id_so100.npy"]:
        raise RuntimeError("refusing to unpickle system_id_so100.npy because its pinned hashes do not match")
    # The trusted, commit-pinned upstream artifact is a scalar object array containing two numeric arrays.
    payload = np.load(path, allow_pickle=True).item()
    qpos = np.asarray(payload["qpos"], dtype=np.float64)
    target = np.asarray(payload["target_qpos"], dtype=np.float64)
    if qpos.shape != target.shape or qpos.ndim != 2:
        raise RuntimeError("unexpected system-identification array shape")
    errors = target - qpos
    lag_samples = []
    for joint in range(qpos.shape[1]):
        candidates = []
        for lag in range(0, min(21, qpos.shape[0] // 4)):
            observed = qpos[lag:, joint]
            commanded = target[: len(observed), joint]
            candidates.append(float(np.mean(np.square(observed - commanded))))
        lag_samples.append(int(np.argmin(candidates)))
    return {
        "path": "system_id_so100.npy",
        "sha256": actual_sha,
        "source": "real SO-100 system-identification capture committed by the pinned upstream",
        "samples": int(qpos.shape[0]),
        "joints": int(qpos.shape[1]),
        "qpos_dtype": str(payload["qpos"].dtype),
        "target_qpos_dtype": str(payload["target_qpos"].dtype),
        "mean_absolute_tracking_error_by_joint": [round(float(value), 8) for value in np.mean(np.abs(errors), axis=0)],
        "max_absolute_tracking_error_by_joint": [round(float(value), 8) for value in np.max(np.abs(errors), axis=0)],
        "best_tracking_lag_samples_by_joint": lag_samples,
        "sample_period_seconds": None,
        "note": "The upstream artifact contains no timestamps, so lag is reported in samples and is not converted to milliseconds."
    }


def invoke(repo: Path, relative: str) -> dict[str, Any]:
    command = [sys.executable, str(repo / relative), "--help"]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(repo), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    try:
        result = subprocess.run(command, cwd=repo, env=env, capture_output=True, text=True, timeout=30, check=False)
        output = (result.stdout + result.stderr)[-12000:]
        return {"command": command, "return_code": result.returncode, "timed_out": False, "output": output}
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or b"") + (exc.stderr or b"")) if isinstance(exc.stdout, bytes) else str(exc.stdout or "") + str(exc.stderr or "")
        return {"command": command, "return_code": None, "timed_out": True, "output": str(output)[-12000:]}


def build_report(repo: Path) -> dict[str, Any]:
    integrity = source_integrity(repo)
    if not integrity["passed"]:
        raise RuntimeError("pinned source-integrity gate failed")
    alignment = inspect_image(repo, "docs/assets/camera_alignment_step_1.2.png")
    composited = inspect_image(repo, "docs/assets/camera_alignment_step_1.3.png")
    dynamics = measure_dynamics(repo)
    probes = {
        "stage_1_alignment": invoke(repo, "lerobot_sim2real/scripts/camera_alignment.py"),
        "stage_2_background_capture": invoke(repo, "lerobot_sim2real/scripts/capture_background_image.py"),
        "stage_3_randomized_resets": invoke(repo, "lerobot_sim2real/scripts/record_reset_distribution.py"),
        "stage_4_rgb_ppo": invoke(repo, "lerobot_sim2real/scripts/train_ppo_rgb.py"),
    }
    mani_skill = shutil.which("python") is not None and __import__("importlib").util.find_spec("mani_skill") is not None
    nvidia = shutil.which("nvidia-smi")
    return {
        "schema_version": "1.0",
        "experiment_id": "9-10",
        "kind": "reference_and_blocker_audit_not_acceptance",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {"node": platform.node() or "unknown", "platform": platform.platform(), "machine": platform.machine()},
        "source_integrity": integrity,
        "runtime": {
            "python": sys.version.split()[0],
            "mani_skill_importable": mani_skill,
            "nvidia_smi": nvidia,
            "apple_mps_available": bool(getattr(getattr(__import__("torch").backends, "mps", None), "is_available", lambda: False)()),
            "upstream_training_backend": "CUDA (the pinned PPO implementation sets device cuda when available and the documented setup requires NVIDIA >=8GB)"
        },
        "stages": {
            "1": {
                "name": "environment_alignment",
                "robot_actuation_required": True,
                "reference_asset_verified": alignment,
                "local_upstream_invocation": probes["stage_1_alignment"],
                "complete": False,
                "blocker": "No authorized/calibrated SO-100 camera run or ManiSkill runtime. The pinned script connects the robot and calls real_env.reset(), so only --help was probed; the verified image is upstream reference evidence, not this host's alignment."
            },
            "2": {
                "name": "background_replacement",
                "robot_actuation_required": False,
                "reference_asset_verified": composited,
                "local_upstream_invocation": probes["stage_2_background_capture"],
                "complete": False,
                "blocker": "No local empty-scene background capture or ManiSkill runtime; the verified composite is upstream reference evidence, not a local composite."
            },
            "3": {
                "name": "domain_randomization_and_real_dynamics_calibration",
                "robot_actuation_required": False,
                "real_dynamics_measurement": dynamics,
                "local_upstream_invocation": probes["stage_3_randomized_resets"],
                "complete": False,
                "blocker": "Pinned real dynamics were measured, but randomized ManiSkill resets could not execute without ManiSkill/NVIDIA and the required visual/physical ranges were not locally evaluated."
            },
            "4": {
                "name": "rgb_only_ppo_training_and_evaluation",
                "robot_actuation_required": False,
                "local_upstream_invocation": probes["stage_4_rgb_ppo"],
                "complete": False,
                "simulation_success_rate": None,
                "blocker": "No importable ManiSkill or NVIDIA CUDA runtime; no PPO checkpoint or >90% direct evaluation exists on this host. Apple MPS is not a proven substitute for this pinned CUDA path."
            },
            "5": {
                "name": "zero_shot_real_world_deployment",
                "robot_actuation_required": True,
                "complete": False,
                "blocker": "No SO-100, authorized operator, calibrated workspace, E-stop, observer, or stage-4 checkpoint; no actuation was attempted."
            }
        },
        "actuation_attempted": False
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.upstream)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output} sha256={sha256(args.output)}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
