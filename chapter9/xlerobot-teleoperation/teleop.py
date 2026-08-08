#!/usr/bin/env python3
"""Experiment 9-8: local GPU expert-control upper-bound benchmark.

This is the reproducible, non-actuating companion for the chapter.  It uses a
small batched tabletop simulator to measure what a perfect teleoperator-like
controller can do.  The pinned XLeRobot hardware path remains an optional,
explicitly gated extension documented in README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from robotics_lab_common import device_info, relative_or_absolute, select_device, seed_everything, sha256, write_json


def run_upper_bound(episodes: int, objects: int, seed: int, device: torch.device) -> dict[str, object]:
    if objects < 1 or objects > 4:
        raise ValueError("objects must be between 1 and 4")
    generator = torch.Generator(device=device).manual_seed(seed)
    object_xy = torch.rand((episodes, objects, 2), generator=generator, device=device) * 0.60 + 0.20
    target_xy = torch.rand((episodes, objects, 2), generator=generator, device=device) * 0.60 + 0.20
    ee = torch.full((episodes, 2), 0.50, dtype=torch.float32, device=device)
    current = torch.zeros(episodes, dtype=torch.long, device=device)
    phase = torch.zeros(episodes, dtype=torch.long, device=device)  # 0=approach, 1=carry, 2=advance
    finished = torch.zeros(episodes, dtype=torch.bool, device=device)
    path = torch.zeros(episodes, dtype=torch.float32, device=device)
    steps = torch.zeros(episodes, dtype=torch.long, device=device)
    max_steps = 900
    speed = 0.018
    tolerance = 0.025

    for _ in range(max_steps):
        active = ~finished
        if not bool(active.any().item()):
            break
        idx = current.clamp(max=objects - 1)
        obj = object_xy[torch.arange(episodes, device=device), idx]
        target = target_xy[torch.arange(episodes, device=device), idx]
        destination = torch.where((phase == 1).unsqueeze(1), target, obj)
        delta = destination - ee
        distance = torch.linalg.vector_norm(delta, dim=1)
        step = delta / distance.clamp_min(1e-6).unsqueeze(1) * speed
        step = torch.where((distance < speed).unsqueeze(1), delta, step)
        step = torch.where(active.unsqueeze(1), step, torch.zeros_like(step))
        ee = ee + step
        path += torch.linalg.vector_norm(step, dim=1)
        steps += active.to(torch.long)
        arrived = distance <= tolerance
        phase = torch.where(active & (phase == 0) & arrived, torch.ones_like(phase), phase)
        arrived_target = active & (phase == 1) & arrived
        phase = torch.where(arrived_target, torch.full_like(phase, 2), phase)
        current = torch.where(arrived_target, current + 1, current)
        phase = torch.where((phase == 2) & (current < objects), torch.zeros_like(phase), phase)
        finished = current >= objects
        phase = torch.where(finished, torch.full_like(phase, 3), phase)

    success = finished
    return {
        "seed": seed,
        "episodes": episodes,
        "objects_per_episode": objects,
        "max_steps": max_steps,
        "control_hz": 20,
        "successes": int(success.sum().item()),
        "success_rate": float(success.float().mean().item()),
        "mean_steps": float(steps.float().mean().item()),
        "p95_steps": float(torch.quantile(steps.float(), 0.95).item()),
        "mean_path_length_m": float(path.mean().item()),
        "device": device_info(device),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=512, help="episodes per seed/object-count cell")
    parser.add_argument("--object-counts", default="1,2,3,4")
    parser.add_argument("--seeds", default="20260808,20260809,20260810,20260811,20260812")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "validation" / "runs" / "local-gpu")
    parser.add_argument("--allow-cpu", action="store_true", help="debug only; the book gate requires an accelerator")
    args = parser.parse_args()
    if args.episodes < 128:
        parser.error("--episodes must be at least 128 for the benchmark protocol")
    try:
        object_counts = [int(value) for value in args.object_counts.split(",")]
        seeds = [int(value) for value in args.seeds.split(",")]
    except ValueError:
        parser.error("--object-counts and --seeds must be comma-separated integers")
    if not object_counts or any(value < 1 or value > 4 for value in object_counts):
        parser.error("object counts must be in 1..4")
    if len(seeds) < 3:
        parser.error("at least three independent seeds are required")
    if args.episodes < 1:
        parser.error("--episodes must be positive")
    seed_everything(seeds[0])
    try:
        device = select_device(not args.allow_cpu)
    except RuntimeError as exc:
        parser.error(str(exc))
    started = time.perf_counter()
    cells = [run_upper_bound(args.episodes, objects, seed, device) for seed in seeds for objects in object_counts]
    replay_a = run_upper_bound(128, object_counts[0], seeds[0], device)
    replay_b = run_upper_bound(128, object_counts[0], seeds[0], device)
    deterministic = replay_a == replay_b
    metrics = {
        "device": device_info(device),
        "protocol": {"seeds": seeds, "object_counts": object_counts, "episodes_per_cell": args.episodes, "total_episodes": len(cells) * args.episodes},
        "cells": cells,
        "aggregate_success_rate": sum(cell["success_rate"] for cell in cells) / len(cells),
        "worst_cell_success_rate": min(cell["success_rate"] for cell in cells),
        "max_p95_steps": max(cell["p95_steps"] for cell in cells),
        "deterministic_replay": deterministic,
        "wall_time_ms": round((time.perf_counter() - started) * 1000, 3),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "metrics.json"
    cells_path = args.output_dir / "cells.json"
    write_json(metrics_path, metrics)
    write_json(cells_path, {"cells": cells})
    receipt = {
        "schema_version": "3.0",
        "experiment_id": "9-8",
        "status": "complete",
        "kind": "local_gpu_expert_upper_bound",
        "seed": seeds[0],
        "run": {"accelerator_required": not args.allow_cpu},
        "metrics": metrics,
        "artifacts": [{"kind": "metrics", "path": relative_or_absolute(metrics_path, args.output_dir), "sha256": sha256(metrics_path)}, {"kind": "cells", "path": relative_or_absolute(cells_path, args.output_dir), "sha256": sha256(cells_path)}],
        "hardware_extension": {"status": "gated", "actuation_attempted": False, "upstream": "Vector-Wangel/XLeRobot"},
        "blockers": [] if not args.allow_cpu else ["CPU debug mode is not a GPU acceptance run"],
    }
    evidence_path = args.output_dir / "evidence.json"
    write_json(evidence_path, receipt)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
