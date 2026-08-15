#!/usr/bin/env python3
"""Experiment 9-9: desktop manipulation planning with a local GPU backend.

The local run keeps the RoboCrew-style tool contract and the XLeRobot adapter
boundary, but executes against a deterministic tabletop simulator.  This
makes planner, postcondition, retry and short-horizon world-model behavior
fully reproducible without claiming that a real robot moved.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from robotics_lab_common import device_info, relative_or_absolute, select_device, seed_everything, sha256, write_json

OBJECTS = ("red_cup", "yellow_paper")
TARGETS = ("tray", "bin")
ACTIONS = ("pick_red_cup", "place_red_cup", "pick_yellow_paper", "place_yellow_paper")
TOOL_NAMES = ("observe_scene", "pick", "place", "verify_state", "stop")


@dataclass
class DesktopState:
    status: list[int]  # 0=on table, 1=held, 2=placed
    target_available: list[bool]

    def copy(self) -> "DesktopState":
        return DesktopState(self.status[:], self.target_available[:])

    def done(self) -> bool:
        return self.status == [2, 2]


class DesktopToolAdapter:
    """RoboCrew-compatible semantic tool boundary for local validation."""

    def __init__(self, seed: int, failure_probability: float = 0.25):
        self.rng = random.Random(seed)
        self.state = DesktopState([0, 0], [True, True])
        self.failure_probability = failure_probability
        self.injected_failure = False
        self.events: list[dict[str, Any]] = []

    def observe_scene(self) -> dict[str, Any]:
        observation = {"objects": dict(zip(OBJECTS, self.state.status)), "targets_available": dict(zip(TARGETS, self.state.target_available))}
        self.events.append({"tool": "observe_scene", "ok": True, "observation": observation})
        return observation

    def _maybe_fail(self, action: str) -> bool:
        if action == "pick_yellow_paper" and not self.injected_failure and self.rng.random() < self.failure_probability:
            self.injected_failure = True
            return True
        return False

    def pick(self, object_id: str) -> dict[str, Any]:
        if object_id not in OBJECTS:
            result = {"ok": False, "reason": "unknown_object"}
        else:
            index = OBJECTS.index(object_id)
            action = f"pick_{object_id}"
            if self._maybe_fail(action):
                result = {"ok": False, "reason": "injected_transient_grasp_failure"}
            elif self.state.status[index] != 0:
                result = {"ok": False, "reason": "object_not_on_table"}
            else:
                self.state.status[index] = 1
                result = {"ok": True, "postcondition": f"{object_id}=held"}
        self.events.append({"tool": "pick", "object_id": object_id, **result})
        return result

    def place(self, object_id: str, target_id: str) -> dict[str, Any]:
        if object_id not in OBJECTS or target_id not in TARGETS:
            result = {"ok": False, "reason": "unknown_object_or_target"}
        else:
            oi, ti = OBJECTS.index(object_id), TARGETS.index(target_id)
            if self.state.status[oi] != 1:
                result = {"ok": False, "reason": "object_not_held"}
            elif not self.state.target_available[ti]:
                result = {"ok": False, "reason": "target_unavailable"}
            else:
                self.state.status[oi] = 2
                self.state.target_available[ti] = False
                result = {"ok": True, "postcondition": f"{object_id}=in_{target_id}"}
        self.events.append({"tool": "place", "object_id": object_id, "target_id": target_id, **result})
        return result

    def verify_state(self) -> dict[str, Any]:
        result = {"ok": self.state.done(), "state": self.observe_scene()}
        self.events.append({"tool": "verify_state", **result})
        return result

    def stop(self) -> dict[str, Any]:
        result = {"ok": True, "stopped": True}
        self.events.append({"tool": "stop", **result})
        return result


def encode_state(state: DesktopState) -> list[float]:
    return [state.status[0] / 2.0, state.status[1] / 2.0, float(state.target_available[0]), float(state.target_available[1])]


def transition(state: DesktopState, action: int) -> DesktopState:
    next_state = state.copy()
    if action == 0 and next_state.status[0] == 0:
        next_state.status[0] = 1
    elif action == 1 and next_state.status[0] == 1 and next_state.target_available[0]:
        next_state.status[0], next_state.target_available[0] = 2, False
    elif action == 2 and next_state.status[1] == 0:
        next_state.status[1] = 1
    elif action == 3 and next_state.status[1] == 1 and next_state.target_available[1]:
        next_state.status[1], next_state.target_available[1] = 2, False
    return next_state


class WorldModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(8, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 4))

    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([state, action], dim=-1))


def train_world_model(device: torch.device, seed: int, epochs: int = 160) -> tuple[WorldModel, float, float]:
    rng = random.Random(seed)
    states, actions, targets = [], [], []
    for _ in range(12000):
        state = DesktopState([rng.randrange(3), rng.randrange(3)], [bool(rng.randrange(2)), bool(rng.randrange(2))])
        action_index = rng.randrange(len(ACTIONS))
        nxt = transition(state, action_index)
        states.append(encode_state(state))
        one_hot = [1.0 if index == action_index else 0.0 for index in range(len(ACTIONS))]
        actions.append(one_hot)
        targets.append(encode_state(nxt))
    x_state = torch.tensor(states, dtype=torch.float32, device=device)
    x_action = torch.tensor(actions, dtype=torch.float32, device=device)
    y = torch.tensor(targets, dtype=torch.float32, device=device)
    split = int(len(y) * 0.8)
    model = WorldModel().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3)
    loss_fn = nn.MSELoss()
    for _ in range(epochs):
        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(model(x_state[:split], x_action[:split]), y[:split])
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        train_loss = float(loss_fn(model(x_state[:split], x_action[:split]), y[:split]).item())
        test_loss = float(loss_fn(model(x_state[split:], x_action[split:]), y[split:]).item())
    return model, train_loss, test_loss


def action_from_index(index: int) -> tuple[str, str | None, str | None]:
    mapping = [("pick", "red_cup", None), ("place", "red_cup", "tray"), ("pick", "yellow_paper", None), ("place", "yellow_paper", "bin")]
    return mapping[index]


def execute(adapter: DesktopToolAdapter, index: int) -> dict[str, Any]:
    kind, object_id, target_id = action_from_index(index)
    if kind == "pick":
        return adapter.pick(object_id or "")
    return adapter.place(object_id or "", target_id or "")


def render_scene(path: Path, state: DesktopState) -> None:
    image = Image.new("RGB", (480, 300), (235, 232, 220))
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 440, 260), outline=(60, 60, 60), width=3)
    locations = [(150, 130), (250, 130)]
    colors = [(210, 60, 60), (220, 190, 40)]
    for idx, (x, y) in enumerate(locations):
        if state.status[idx] != 2:
            draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=colors[idx], outline=(20, 20, 20))
        draw.text((x - 35, y + 30), OBJECTS[idx], fill=(20, 20, 20))
    draw.rectangle((320, 80, 390, 145), outline=(40, 100, 210), width=3)
    draw.rectangle((320, 170, 390, 235), outline=(40, 130, 60), width=3)
    draw.text((325, 95), "tray", fill=(20, 20, 20))
    draw.text((325, 185), "bin", fill=(20, 20, 20))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def run_episode(mode: str, seed: int, model: WorldModel | None, device: torch.device, failure_probability: float) -> dict[str, Any]:
    adapter = DesktopToolAdapter(seed, failure_probability=failure_probability)
    if mode == "open_loop":
        plan = [0, 1, 2, 3]
        for action in plan:
            execute(adapter, action)
    else:
        for _ in range(12):
            if adapter.state.done():
                break
            if mode == "predictive" and model is not None:
                state_tensor = torch.tensor([encode_state(adapter.state)], dtype=torch.float32, device=device)
                candidates = [index for index in range(4) if (index in (0, 2) and adapter.state.status[index // 2] == 0) or (index in (1, 3) and adapter.state.status[index // 2] == 1)]
                if not candidates:
                    break
                action_vectors = torch.eye(4, device=device)[candidates]
                with torch.no_grad():
                    predicted = model(state_tensor.repeat(len(candidates), 1), action_vectors)
                score = predicted[:, 0] + predicted[:, 1] + (predicted[:, 0] > 0.95).float() + (predicted[:, 1] > 0.95).float()
                action = candidates[int(torch.argmax(score).item())]
            else:
                action = next((index for index in (0, 1, 2, 3) if (index in (0, 2) and adapter.state.status[index // 2] == 0) or (index in (1, 3) and adapter.state.status[index // 2] == 1)), 0)
            result = execute(adapter, action)
            if not result.get("ok"):
                adapter.observe_scene()
        adapter.verify_state()
    return {"success": adapter.state.done(), "tool_calls": len(adapter.events), "recoveries": sum(1 for event in adapter.events if event.get("reason") == "injected_transient_grasp_failure"), "events": adapter.events}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=128, help="episodes per seed/failure/mode cell")
    parser.add_argument("--seeds", default="20260808,20260809,20260810")
    parser.add_argument("--failure-probabilities", default="0.0,0.25,0.5")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "validation" / "runs" / "local-gpu")
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args()
    try:
        seeds = [int(value) for value in args.seeds.split(",")]
        failure_probabilities = [float(value) for value in args.failure_probabilities.split(",")]
    except ValueError:
        parser.error("--seeds and --failure-probabilities must be comma-separated values")
    if args.episodes < 64 or len(seeds) < 3 or not failure_probabilities or any(value < 0 or value > 1 for value in failure_probabilities):
        parser.error("use at least three seeds, 64 episodes per cell, and probabilities in [0,1]")
    seed_everything(seeds[0])
    try:
        device = select_device(not args.allow_cpu)
    except RuntimeError as exc:
        parser.error(str(exc))
    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    model_reports: list[dict[str, Any]] = []
    event_log_rows: list[dict[str, Any]] = []
    for model_seed in seeds:
        model, train_loss, test_loss = train_world_model(device, model_seed)
        model_reports.append({"seed": model_seed, "train_mse": train_loss, "test_mse": test_loss})
        for failure_probability in failure_probabilities:
            for mode in ("open_loop", "closed_loop", "predictive"):
                episodes = [run_episode(mode, model_seed + index, model if mode == "predictive" else None, device, failure_probability) for index in range(args.episodes)]
                results.append({"seed": model_seed, "failure_probability": failure_probability, "mode": mode, "episodes": args.episodes, "success_rate": sum(item["success"] for item in episodes) / args.episodes, "mean_tool_calls": sum(item["tool_calls"] for item in episodes) / args.episodes, "recoveries": sum(item["recoveries"] for item in episodes)})
                for episode_index, episode in enumerate(episodes):
                    event_log_rows.append({
                        "seed": model_seed,
                        "failure_probability": failure_probability,
                        "mode": mode,
                        "episode": episode_index,
                        "success": episode["success"],
                        "events": episode["events"],
                    })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene_path = args.output_dir / "scene_initial.png"
    render_scene(scene_path, DesktopState([0, 0], [True, True]))
    events_path = args.output_dir / "predictive_episode_events.json"
    write_json(events_path, {"tools": TOOL_NAMES, "episodes": event_log_rows})
    replay_model, _, _ = train_world_model(device, seeds[0])
    replay_a = run_episode("predictive", seeds[0], replay_model, device, failure_probabilities[-1])
    replay_b = run_episode("predictive", seeds[0], replay_model, device, failure_probabilities[-1])
    metrics = {"device": device_info(device), "protocol": {"seeds": seeds, "failure_probabilities": failure_probabilities, "episodes_per_cell": args.episodes, "total_episodes": len(results) * args.episodes}, "models": model_reports, "cells": results, "deterministic_replay": replay_a == replay_b, "wall_time_ms": round((time.perf_counter() - started) * 1000, 3)}
    metrics_path = args.output_dir / "metrics.json"
    write_json(metrics_path, metrics)
    evidence = {"schema_version": "3.0", "experiment_id": "9-9", "status": "complete", "kind": "desktop_manipulation_planning", "seed": seeds[0], "tool_contract": list(TOOL_NAMES), "metrics": metrics, "artifacts": [{"kind": "metrics", "path": relative_or_absolute(metrics_path, args.output_dir), "sha256": sha256(metrics_path)}, {"kind": "events", "path": relative_or_absolute(events_path, args.output_dir), "sha256": sha256(events_path)}, {"kind": "scene", "path": relative_or_absolute(scene_path, args.output_dir), "sha256": sha256(scene_path)}], "xlerobot_robocrew_extension": {"status": "gated", "tool_adapter_required": True, "actuation_attempted": False}, "blockers": [] if not args.allow_cpu else ["CPU debug mode is not a GPU acceptance run"]}
    evidence_path = args.output_dir / "evidence.json"
    write_json(evidence_path, evidence)
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
