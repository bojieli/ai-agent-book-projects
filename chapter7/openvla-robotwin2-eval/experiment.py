#!/usr/bin/env python3
"""Exact companion for manuscript Experiment 6-12.

The runner deliberately separates three things:
1. a non-destructive host/upstream preflight;
2. generation or execution of the two real upstream val-only arms; and
3. strict analysis of episode-level evidence.

Paper numbers, historical rollout collections and dry-run commands never satisfy
the completion gate.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "config.json"
VIDEO_RE = re.compile(
    r"step=(?P<global_step>\d+)--task=(?P<task>.+?)--success=(?P<success>True|False)--ran=(?P<run>[^.]+)\.mp4$"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resolve_config(path: Path) -> dict[str, Any]:
    cfg = load_json(path)
    upstream = Path(cfg["upstream_path"])
    if not upstream.is_absolute():
        upstream = (path.parent / upstream).resolve()
    cfg["upstream_path"] = str(upstream)
    return cfg


def run_capture(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return proc.returncode, proc.stdout.strip()
    except FileNotFoundError as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def gpu_inventory() -> tuple[list[dict[str, Any]], str | None]:
    code, output = run_capture(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    if code != 0:
        return [], output or "nvidia-smi unavailable"
    gpus = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 4:
            gpus.append(
                {
                    "index": int(parts[0]),
                    "name": parts[1],
                    "memory_mib": int(parts[2]),
                    "driver": parts[3],
                }
            )
    return gpus, None


def preflight(cfg: dict[str, Any]) -> dict[str, Any]:
    upstream = Path(cfg["upstream_path"])
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, ok: bool, evidence: Any, required: bool = True) -> None:
        checks[name] = {"ok": bool(ok), "required": required, "evidence": evidence}

    check("upstream_checkout", (upstream / ".git").exists(), str(upstream))
    commit_code, commit = run_capture(["git", "rev-parse", "HEAD"], cwd=upstream)
    check(
        "pinned_upstream_commit",
        commit_code == 0 and commit == cfg["expected_upstream_commit"],
        {"observed": commit, "expected": cfg["expected_upstream_commit"]},
    )

    required_files = [
        "examples/run_openvla_oft_rl_twin2.sh",
        "examples/robotwin2_tasks_info.txt",
        "verl/trainer/main_ppo.py",
        "verl/trainer/ppo/ray_trainer.py",
        "verl/utils/dataset/rob_dataset.py",
        "verl/workers/rollout/rob_rollout.py",
        "modified_codes/robotwin2/envs/move_can_pot.py",
        "modified_codes/robotwin2/task_config/demo_randomized.yml",
        "verl/utils/envs/robotwin2/seeds/robotwin2_eval_seeds.json",
    ]
    missing = [item for item in required_files if not (upstream / item).is_file()]
    check("required_upstream_files", not missing, {"missing": missing, "required": required_files})

    task_info = upstream / "examples/robotwin2_tasks_info.txt"
    task_supported = task_info.is_file() and cfg["task"] in task_info.read_text(encoding="utf-8")
    check("move_can_pot_supported", task_supported, str(task_info))

    seed_file = upstream / "verl/utils/envs/robotwin2/seeds/robotwin2_eval_seeds.json"
    observed_seed_count = 0
    if seed_file.is_file():
        seed_data = load_json(seed_file)
        observed_seed_count = len(seed_data.get(cfg["task"], {}).get("success_seeds", []))
    check(
        "ood_seed_inventory",
        observed_seed_count >= cfg["ood_validation_seeds"],
        {"observed": observed_seed_count, "required": cfg["ood_validation_seeds"]},
    )

    rollout_source = upstream / "verl/workers/rollout/rob_rollout.py"
    rollout_text = rollout_source.read_text(encoding="utf-8") if rollout_source.is_file() else ""
    source_invariants = {
        "three_view_branch": "num_images_in_input == 3" in rollout_text,
        "left_wrist": '"left_wrist"' in rollout_text,
        "right_wrist": '"right_wrist"' in rollout_text,
        "proprio_vector": "joint_action']['vector" in rollout_text,
        "environment_success": "self.env.eval_success" in rollout_text,
        "validation_video": "save_rollout_video" in rollout_text,
    }
    check("source_invariants", all(source_invariants.values()), source_invariants)

    checkpoint_raw = os.environ.get(cfg["checkpoint_env"], "")
    checkpoint = Path(checkpoint_raw).expanduser() if checkpoint_raw else None
    checkpoint_metadata: dict[str, Any] = {
        "environment": cfg["checkpoint_env"],
        "path": checkpoint_raw or None,
        "checkpoint_id": cfg["checkpoint_id"],
        "expected_revision": cfg["expected_checkpoint_revision"],
    }
    checkpoint_ready = bool(checkpoint and checkpoint.is_dir())
    if checkpoint_ready and checkpoint is not None:
        metadata_dir = checkpoint / ".cache/huggingface/download"
        primary_names = [
            "config.json",
            "model-00001-of-00004.safetensors",
            "model-00002-of-00004.safetensors",
            "model-00003-of-00004.safetensors",
            "model-00004-of-00004.safetensors",
            "proprio_projector--20000_checkpoint.pt",
            "lora_adapter/adapter_model.safetensors",
        ]
        artifact_metadata = {}
        observed_revisions = set()
        missing_artifacts = []
        for name in primary_names:
            artifact = checkpoint / name
            metadata = metadata_dir / f"{name}.metadata"
            if not artifact.is_file() or not metadata.is_file():
                missing_artifacts.append(name)
                continue
            lines = metadata.read_text(encoding="utf-8").splitlines()
            if len(lines) < 2:
                missing_artifacts.append(name)
                continue
            observed_revisions.add(lines[0])
            artifact_metadata[name] = {
                "bytes": artifact.stat().st_size,
                "huggingface_etag": lines[1],
            }
        checkpoint_metadata.update({
            "observed_revisions": sorted(observed_revisions),
            "artifact_metadata": artifact_metadata,
            "missing_artifacts": missing_artifacts,
        })
        checkpoint_ready = (
            not missing_artifacts
            and observed_revisions == {cfg["expected_checkpoint_revision"]}
        )
    check(
        "pretrained_checkpoint",
        checkpoint_ready,
        checkpoint_metadata,
    )

    robotwin_raw = os.environ.get(cfg["robotwin2_env"], "")
    robotwin = Path(robotwin_raw).expanduser() if robotwin_raw else None
    robotwin_markers = ["envs", "task_config", "script"]
    check(
        "robotwin2_checkout",
        bool(robotwin and robotwin.is_dir() and all((robotwin / marker).exists() for marker in robotwin_markers)),
        {"environment": cfg["robotwin2_env"], "path": robotwin_raw or None, "markers": robotwin_markers},
    )
    robotwin_code, robotwin_commit = (
        run_capture(["git", "rev-parse", "HEAD"], cwd=robotwin)
        if robotwin and robotwin.is_dir()
        else (1, "")
    )
    check(
        "pinned_robotwin2_commit",
        robotwin_code == 0 and robotwin_commit == cfg["expected_robotwin2_commit"],
        {"observed": robotwin_commit or None, "expected": cfg["expected_robotwin2_commit"]},
    )

    align_raw = os.environ.get(cfg["align_path_env"], "")
    align = Path(align_raw).expanduser() if align_raw else upstream / "align.json"
    check(
        "ray_runtime_environment",
        align.is_file(),
        {"environment": cfg["align_path_env"], "path": str(align)},
    )

    gpus, gpu_error = gpu_inventory()
    check(
        "nvidia_gpu_count",
        len(gpus) >= cfg["gpus_required"],
        {"observed": len(gpus), "required": cfg["gpus_required"], "gpus": gpus, "error": gpu_error},
    )

    custom_task_config = HERE / "task_config_exp6_12_three_view.yml"
    task_config_text = custom_task_config.read_text(encoding="utf-8") if custom_task_config.is_file() else ""
    check(
        "three_rgb_view_config",
        custom_task_config.is_file()
        and "collect_head_camera: true" in task_config_text
        and "collect_wrist_camera: true" in task_config_text,
        str(custom_task_config),
    )

    required_failures = [name for name, item in checks.items() if item["required"] and not item["ok"]]
    return {
        "schema_version": 1,
        "experiment": cfg["experiment"],
        "generated_at_utc": utc_now(),
        "host": {
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "cwd": str(Path.cwd()),
        },
        "configuration": cfg,
        "checks": checks,
        "ready_for_real_validation": not required_failures,
        "blocking_checks": required_failures,
        "acceptance_note": "Preflight readiness is necessary but never sufficient for Experiment 6-12 completion.",
    }


def hydra_command(cfg: dict[str, Any], arm: str, run_dir: Path, worktree: Path) -> list[str]:
    chunk = int(arm.removeprefix("chunk_"))
    checkpoint = str(Path(os.environ[cfg["checkpoint_env"]]).expanduser().resolve())
    align_raw = os.environ.get(cfg["align_path_env"])
    align_path = Path(align_raw).expanduser().resolve() if align_raw else worktree / "align.json"
    experiment_name = f"exp6_12_{cfg['task']}_{arm}"
    return [
        sys.executable,
        "-u",
        "-m",
        "verl.trainer.main_ppo",
        f"data.task_suite_name={cfg['task_suite']}",
        "data.num_trials_per_task=128",
        "data.n_samples=1",
        "data.filter_accuracy=False",
        "data.train_batch_size=64",
        "data.val_batch_size=8",
        "data.max_prompt_length=256",
        "data.max_response_length=128",
        f"actor_rollout_ref.model.path={checkpoint}",
        f"actor_rollout_ref.model.vla={cfg['vla']}",
        f"actor_rollout_ref.model.action_token_len={cfg['action_token_length']}",
        f"actor_rollout_ref.model.action_chunks_len={chunk}",
        "actor_rollout_ref.model.resume=False",
        f"actor_rollout_ref.actor.num_images_in_input={cfg['rgb_views']}",
        "actor_rollout_ref.actor.traj_mini_batch_size=8",
        "actor_rollout_ref.actor.ppo_mini_batch_size=128",
        "actor_rollout_ref.actor.ppo_micro_batch_size=8",
        "actor_rollout_ref.actor.use_dynamic_bsz=False",
        "actor_rollout_ref.actor.fsdp_config.param_offload=False",
        "actor_rollout_ref.actor.fsdp_config.grad_offload=True",
        "actor_rollout_ref.actor.fsdp_config.optimizer_offload=True",
        f"actor_rollout_ref.rollout.twin2_task_config={cfg['task_config']}",
        "actor_rollout_ref.rollout.twin2_instruction_type=seen",
        f"actor_rollout_ref.rollout.num_images_in_input={cfg['rgb_views']}",
        f"+actor_rollout_ref.rollout.action_token_len={cfg['action_token_length']}",
        "actor_rollout_ref.rollout.use_proprio=True",
        "actor_rollout_ref.rollout.val_micro_batch_size=8",
        "actor_rollout_ref.rollout.temperature=1.6",
        f"actor_rollout_ref.rollout.experiment_name={experiment_name}",
        "actor_rollout_ref.rollout.micro_batch_size=1",
        f"actor_rollout_ref.rollout.unnorm_key=robotwin2_{cfg['task']}_1k",
        f"actor_rollout_ref.rollout.model_family={cfg['model_family']}",
        f"actor_rollout_ref.rollout.task_suite_name={cfg['task_suite']}",
        "actor_rollout_ref.rollout.num_steps_wait=10",
        f"actor_rollout_ref.rollout.pretrained_checkpoint={checkpoint}",
        "actor_rollout_ref.rollout.center_crop=True",
        "actor_rollout_ref.rollout.max_prompt_length=512",
        "actor_rollout_ref.rollout.tensor_model_parallel_size=1",
        "actor_rollout_ref.rollout.name=hf",
        "actor_rollout_ref.rollout.gpu_memory_utilization=0.9",
        "actor_rollout_ref.ref.log_prob_micro_batch_size=32",
        "actor_rollout_ref.ref.fsdp_config.param_offload=True",
        "algorithm.adv_estimator=grpo",
        "algorithm.kl_ctrl.kl_coef=0.0",
        "trainer.logger=['console']",
        "trainer.project_name=AI-Agent-Book-Experiment-6-12",
        f"trainer.experiment_name={experiment_name}",
        f"trainer.default_local_dir={str((run_dir / arm / 'checkpoints').resolve())}",
        f"trainer.n_gpus_per_node={cfg['gpus_required']}",
        "trainer.nnodes=1",
        "trainer.save_freq=-1",
        "trainer.test_freq=-1",
        "trainer.total_epochs=1",
        "trainer.val_only=True",
        "trainer.val_before_train=True",
        f"trainer.runtime_env={str(align_path)}",
        "trainer.wandb_mode=disabled",
    ]


def shell_quote(value: str) -> str:
    import shlex

    return shlex.quote(value)


def prepare_worktree(cfg: dict[str, Any], run_dir: Path) -> Path:
    upstream = Path(cfg["upstream_path"])
    worktree = run_dir / "instrumented-upstream"
    if worktree.exists():
        raise RuntimeError(f"refusing to replace existing worktree: {worktree}")
    code, output = run_capture(
        ["git", "worktree", "add", "--detach", str(worktree), cfg["expected_upstream_commit"]],
        cwd=upstream,
    )
    if code != 0:
        raise RuntimeError(f"git worktree add failed: {output}")
    robotwin = Path(os.environ[cfg["robotwin2_env"]]).expanduser().resolve()
    setup = subprocess.run(
        ["bash", "copy_overwrite_robotwin2.sh", str(robotwin), str(worktree)],
        cwd=worktree,
        check=False,
    )
    if setup.returncode != 0:
        raise RuntimeError(f"RoboTwin2 overlay setup failed with exit {setup.returncode}")
    task_config_dest = worktree / "verl/utils/envs/robotwin2/task_config" / f"{cfg['task_config']}.yml"
    task_config_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "task_config_exp6_12_three_view.yml", task_config_dest)
    patch_proc = subprocess.run(
        [sys.executable, str(HERE / "instrument_upstream.py"), str(worktree)],
        check=False,
    )
    if patch_proc.returncode != 0:
        raise RuntimeError(f"upstream instrumentation failed with exit {patch_proc.returncode}")
    return worktree


def write_launch_manifest(cfg: dict[str, Any], run_dir: Path, worktree: Path) -> dict[str, Any]:
    arms = {}
    for chunk in cfg["action_chunks"]:
        arm = f"chunk_{chunk}"
        argv = hydra_command(cfg, arm, run_dir, worktree)
        episode_path = (run_dir / arm / "episodes.jsonl").resolve()
        env = {
            "EXP6_12_EPISODE_JSONL": str(episode_path),
            "EXP6_12_ARM": arm,
            "EXP6_12_UPSTREAM_COMMIT": cfg["expected_upstream_commit"],
            "HYDRA_FULL_ERROR": "1",
            "TOKENIZERS_PARALLELISM": "true",
            "NCCL_DEBUG": "WARN",
            "ROBOT_PLATFORM": "ALOHA",
            "VERL_DISABLE_VLLM_IMPORT": "1",
        }
        arms[arm] = {
            "action_chunk_length": chunk,
            "episode_evidence": str(episode_path),
            "rollout_directory": str((worktree / "rollouts" / f"exp6_12_{cfg['task']}_{arm}").resolve()),
            "environment": env,
            "argv": argv,
            "shell_command": " ".join(
                [*(f"{key}={shell_quote(value)}" for key, value in env.items()), *(shell_quote(item) for item in argv)]
            ),
        }
    manifest = {
        "schema_version": 1,
        "experiment": cfg["experiment"],
        "generated_at_utc": utc_now(),
        "real_execution_required": True,
        "upstream_worktree": str(worktree.resolve()),
        "upstream_commit": cfg["expected_upstream_commit"],
        "arms": arms,
    }
    dump_json(run_dir / "launch_manifest.json", manifest)
    return manifest


def execute_arms(manifest: dict[str, Any], selected: Iterable[str]) -> None:
    worktree = Path(manifest["upstream_worktree"])
    for arm in selected:
        spec = manifest["arms"][arm]
        arm_dir = Path(spec["episode_evidence"]).parent
        arm_dir.mkdir(parents=True, exist_ok=True)
        log_path = arm_dir / "upstream.log"
        env = os.environ.copy()
        env.update(spec["environment"])
        started = utc_now()
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.run(
                spec["argv"],
                cwd=worktree,
                env=env,
                check=False,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        dump_json(
            arm_dir / "process.json",
            {
                "arm": arm,
                "started_at_utc": started,
                "ended_at_utc": utc_now(),
                "exit_code": proc.returncode,
                "log": str(log_path.resolve()),
            },
        )
        if proc.returncode != 0:
            raise RuntimeError(f"{arm} real validation failed with exit {proc.returncode}; see {log_path}")


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def distribution(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "std": statistics.pstdev(values) if len(values) > 1 else 0.0 if values else None,
        "min": min(values) if values else None,
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "max": max(values) if values else None,
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.is_file():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return rows


def video_index(
    directory: Path,
    *,
    started_at_utc: str | None = None,
    ended_at_utc: str | None = None,
) -> dict[tuple[str, bool], list[str]]:
    """Index rollout videos, optionally restricting them to one process window.

    Upstream names videos with a random ``ran`` suffix and does not clear an
    existing rollout directory.  A bounded resume can therefore leave two
    files for the same task/result key.  Process timestamps let the evidence
    reader reject those stale files without guessing from the random suffix.
    """
    index: dict[tuple[str, bool], list[str]] = {}
    if not directory.is_dir():
        return index
    started = datetime.fromisoformat(started_at_utc) if started_at_utc else None
    ended = datetime.fromisoformat(ended_at_utc) if ended_at_utc else None
    for path in directory.rglob("*.mp4"):
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if started is not None and modified < started:
            continue
        if ended is not None and modified > ended:
            continue
        match = VIDEO_RE.match(path.name)
        if not match:
            continue
        task_key = match.group("task")
        success = match.group("success") == "True"
        index.setdefault((task_key, success), []).append(str(path.resolve()))
    return index


def annotation_key(row: dict[str, Any]) -> str:
    return f"{row['arm']}|{row['data_source']}|{row['trial_seed']}"


def analyze(cfg: dict[str, Any], run_dir: Path, annotations_path: Path | None) -> dict[str, Any]:
    manifest_path = run_dir / "launch_manifest.json"
    manifest = load_json(manifest_path) if manifest_path.is_file() else None
    annotations = load_json(annotations_path) if annotations_path and annotations_path.is_file() else {}
    all_rows: list[dict[str, Any]] = []
    arm_reports: dict[str, Any] = {}
    strict_errors: list[str] = []

    expected_total = cfg["iid_validation_seeds"] + cfg["ood_validation_seeds"]
    for chunk in cfg["action_chunks"]:
        arm = f"chunk_{chunk}"
        episode_path = run_dir / arm / "episodes.jsonl"
        rows = read_jsonl(episode_path)
        all_rows.extend(rows)
        bad_source = [row for row in rows if row.get("source") != "upstream_val_only"]
        if bad_source:
            strict_errors.append(f"{arm}: {len(bad_source)} rows are not upstream_val_only evidence")
        if len(rows) != expected_total:
            strict_errors.append(f"{arm}: expected {expected_total} episodes, observed {len(rows)}")
        if any(row.get("action_chunk_length") != chunk for row in rows):
            strict_errors.append(f"{arm}: action chunk mismatch")
        if any(row.get("action_dimension") != cfg["action_dimension"] for row in rows):
            strict_errors.append(f"{arm}: action dimension mismatch")
        if any(row.get("rgb_views") != cfg["rgb_views"] for row in rows):
            strict_errors.append(f"{arm}: three-view observation not proven")
        if any(not row.get("proprioception_enabled") for row in rows):
            strict_errors.append(f"{arm}: proprioception not enabled in all rows")

        iid = [row for row in rows if str(row.get("data_source", "")).endswith("_train_iid")]
        ood = [row for row in rows if str(row.get("data_source", "")).endswith("_eval_ood")]
        if len({row.get("trial_seed") for row in iid}) != cfg["iid_validation_seeds"]:
            strict_errors.append(f"{arm}: incomplete IID seed coverage")
        if len({row.get("trial_seed") for row in ood}) != cfg["ood_validation_seeds"]:
            strict_errors.append(f"{arm}: incomplete OOD seed coverage")

        video_dir = Path(manifest["arms"][arm]["rollout_directory"]) if manifest else Path()
        process_path = run_dir / arm / "process.json"
        process_data = load_json(process_path) if process_path.is_file() else {}
        videos = video_index(
            video_dir,
            started_at_utc=process_data.get("started_at_utc"),
            ended_at_utc=process_data.get("ended_at_utc"),
        )
        unmatched_videos = 0
        failure_counts: Counter[str] = Counter()
        unclassified_failures = []
        missing_video_count = 0
        for row in rows:
            task_file = f"{cfg['task']}_trial_{row.get('trial_id')}_seed_{row.get('trial_seed')}"
            candidates = videos.get((task_file, bool(row.get("success"))), [])
            if candidates:
                row["video_path"] = candidates.pop(0)
            else:
                missing_video_count += 1
            if row.get("success"):
                row["failure_mode"] = None
                row["failure_evidence"] = None
            else:
                annotation = annotations.get(annotation_key(row))
                if annotation:
                    label = annotation.get("failure_mode")
                    evidence = annotation.get("evidence")
                    if label not in cfg["failure_modes"] or not evidence:
                        unclassified_failures.append(annotation_key(row))
                    else:
                        row["failure_mode"] = label
                        row["failure_evidence"] = evidence
                        failure_counts[label] += 1
                else:
                    unclassified_failures.append(annotation_key(row))
        unmatched_videos = sum(len(paths) for paths in videos.values())
        if missing_video_count:
            strict_errors.append(f"{arm}: {missing_video_count} episodes lack rollout video evidence")
        if unclassified_failures:
            strict_errors.append(f"{arm}: {len(unclassified_failures)} failed episodes lack valid failure annotations")

        action_steps = [float(row["finish_action_steps"]) for row in rows if row.get("finish_action_steps") is not None]
        control_seconds = [value / cfg["control_hz"] for value in action_steps]
        successes = sum(bool(row.get("success")) for row in rows)
        by_split = {}
        for split_name, split_rows in (("iid", iid), ("ood", ood)):
            split_successes = sum(bool(row.get("success")) for row in split_rows)
            by_split[split_name] = {
                "episodes": len(split_rows),
                "successes": split_successes,
                "success_rate": split_successes / len(split_rows) if split_rows else None,
            }
        arm_reports[arm] = {
            "action_chunk_length": chunk,
            "episodes": len(rows),
            "successes": successes,
            "success_rate": successes / len(rows) if rows else None,
            "by_split": by_split,
            "completion_action_steps": distribution(action_steps),
            "completion_control_seconds_at_50hz": distribution(control_seconds),
            "failure_modes": dict(sorted(failure_counts.items())),
            "unclassified_failure_count": len(unclassified_failures),
            "missing_video_count": missing_video_count,
            "unmatched_video_count": unmatched_videos,
        }

    control = arm_reports.get("chunk_1", {})
    treatment = arm_reports.get("chunk_25", {})
    paired = {}
    rows_by_key = {
        (row.get("arm"), row.get("data_source"), row.get("trial_seed")): row for row in all_rows
    }
    pair_deltas = []
    for source in ("train_iid", "eval_ood"):
        suffix = f"_{source}"
        seeds = {
            row.get("trial_seed")
            for row in all_rows
            if str(row.get("data_source", "")).endswith(suffix)
        }
        for seed in seeds:
            left = next(
                (
                    row
                    for row in all_rows
                    if row.get("arm") == "chunk_1"
                    and str(row.get("data_source", "")).endswith(suffix)
                    and row.get("trial_seed") == seed
                ),
                None,
            )
            right = next(
                (
                    row
                    for row in all_rows
                    if row.get("arm") == "chunk_25"
                    and str(row.get("data_source", "")).endswith(suffix)
                    and row.get("trial_seed") == seed
                ),
                None,
            )
            if left and right:
                pair_deltas.append(int(bool(right.get("success"))) - int(bool(left.get("success"))))
    paired = {
        "complete_pairs": len(pair_deltas),
        "chunk_25_wins": sum(delta > 0 for delta in pair_deltas),
        "chunk_1_wins": sum(delta < 0 for delta in pair_deltas),
        "ties": sum(delta == 0 for delta in pair_deltas),
        "mean_paired_success_delta": statistics.fmean(pair_deltas) if pair_deltas else None,
        "unpaired_rows": len(all_rows) - 2 * len(pair_deltas),
    }
    if pair_deltas and len(pair_deltas) != expected_total:
        strict_errors.append(f"paired comparison: expected {expected_total} pairs, observed {len(pair_deltas)}")

    preflight_files = sorted((run_dir / "preflight.json", *HERE.glob("results/preflight-*.json")), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    preflight_report = load_json(preflight_files[-1]) if preflight_files and preflight_files[-1].is_file() else None
    if not preflight_report or not preflight_report.get("ready_for_real_validation"):
        strict_errors.append("no passing real-execution preflight is attached to this run")
    process_failures = []
    for chunk in cfg["action_chunks"]:
        arm = f"chunk_{chunk}"
        process_path = run_dir / arm / "process.json"
        process_data = load_json(process_path) if process_path.is_file() else None
        if not process_data or process_data.get("exit_code") != 0:
            process_failures.append(arm)
    if process_failures:
        strict_errors.append(f"missing or failed upstream processes: {', '.join(process_failures)}")

    report = {
        "schema_version": 1,
        "experiment": cfg["experiment"],
        "generated_at_utc": utc_now(),
        "evidence_policy": {
            "paper_numbers_accepted": False,
            "historical_rollouts_accepted": False,
            "dry_run_commands_accepted": False,
            "required_source": "instrumented upstream val-only execution",
        },
        "configuration": cfg,
        "arms": arm_reports,
        "controlled_action_chunk_comparison": paired,
        "strict_completion": {
            "complete": not strict_errors,
            "errors": strict_errors,
        },
    }
    dump_json(run_dir / "report.json", report)
    lines = [
        "# Experiment 6-12 OpenVLA + RoboTwin2 evaluation",
        "",
        f"Official completion: **{report['strict_completion']['complete']}**",
        "",
        "| Arm | Episodes | Success rate | IID | OOD | Completion p50 / p95 (50 Hz seconds) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for arm, item in arm_reports.items():
        times = item["completion_control_seconds_at_50hz"]
        lines.append(
            f"| {arm} | {item['episodes']} | {item['success_rate']} | "
            f"{item['by_split']['iid']['success_rate']} | {item['by_split']['ood']['success_rate']} | "
            f"{times['p50']} / {times['p95']} |"
        )
    lines.extend(["", "## Controlled comparison", "", f"```json\n{json.dumps(paired, indent=2)}\n```", "", "## Failure modes", ""])
    for arm, item in arm_reports.items():
        lines.append(f"- {arm}: {json.dumps(item['failure_modes'], ensure_ascii=False)}")
    lines.extend(["", "## Completion audit", ""])
    if strict_errors:
        lines.extend(f"- {error}" for error in strict_errors)
    else:
        lines.append("- Every direct manuscript gate is supported by real per-episode evidence.")
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight", help="inspect the real host and upstream checkout")
    pre.add_argument("--output", type=Path)
    prep = sub.add_parser("prepare", help="prepare an instrumented disposable worktree and commands")
    prep.add_argument("--run-dir", type=Path, required=True)
    launch = sub.add_parser("launch", help="execute real val-only arms from an existing manifest")
    launch.add_argument("--run-dir", type=Path, required=True)
    launch.add_argument("--arm", choices=["all", "chunk_1", "chunk_25"], default="all")
    ana = sub.add_parser("analyze", help="build strict success/time/failure/chunk report")
    ana.add_argument("--run-dir", type=Path, required=True)
    ana.add_argument("--failure-annotations", type=Path)
    args = parser.parse_args()
    cfg = resolve_config(args.config.resolve())

    if args.command == "preflight":
        report = preflight(cfg)
        output = args.output or HERE / "results" / f"preflight-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        dump_json(output, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ready_for_real_validation"] else 2
    if args.command == "prepare":
        readiness = preflight(cfg)
        args.run_dir.mkdir(parents=True, exist_ok=True)
        dump_json(args.run_dir / "preflight.json", readiness)
        if not readiness["ready_for_real_validation"]:
            print(json.dumps(readiness, indent=2, ensure_ascii=False))
            return 2
        worktree = prepare_worktree(cfg, args.run_dir.resolve())
        manifest = write_launch_manifest(cfg, args.run_dir.resolve(), worktree)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    if args.command == "launch":
        manifest = load_json(args.run_dir / "launch_manifest.json")
        selected = list(manifest["arms"]) if args.arm == "all" else [args.arm]
        execute_arms(manifest, selected)
        return 0
    if args.command == "analyze":
        report = analyze(cfg, args.run_dir.resolve(), args.failure_annotations)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["strict_completion"]["complete"] else 2
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
