#!/usr/bin/env python3
"""Experiment 9-10: RGB domain-transfer benchmark on the local GPU.

The benchmark is intentionally self-contained.  It trains a small RGB policy
on a source visual domain and evaluates it on a shifted target domain, with
and without domain randomization.  It is a production-grade local proxy for
the sim-to-real argument; SO-100 deployment remains a separately gated
extension and is never implied by this run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from robotics_lab_common import device_info, relative_or_absolute, select_device, seed_everything, sha256, write_json

IMAGE_SIZE = 32
CLASSES = ("left", "right", "up", "down", "grasp")


def label_for(object_xy: tuple[float, float], target_xy: tuple[float, float]) -> int:
    dx, dy = target_xy[0] - object_xy[0], target_xy[1] - object_xy[1]
    if abs(dx) < 0.10 and abs(dy) < 0.10:
        return 4
    if abs(dx) >= abs(dy):
        return 1 if dx > 0 else 0
    return 3 if dy > 0 else 2


def render_sample(rng: np.random.Generator, domain: str) -> tuple[np.ndarray, int]:
    object_xy = tuple(rng.uniform(0.18, 0.82, size=2))
    target_xy = tuple(rng.uniform(0.18, 0.82, size=2))
    label = label_for(object_xy, target_xy)
    if domain == "source_clean":
        background = np.full((IMAGE_SIZE, IMAGE_SIZE, 3), [220, 220, 220], dtype=np.float32)
        object_color, target_color = (214, 60, 60), (45, 130, 65)
        noise = 0.0
    elif domain in {"source_background", "source_full"}:
        if domain == "source_background":
            base = rng.uniform(45, 225, size=(1, 1, 3)).astype(np.float32)
            background = np.broadcast_to(base, (IMAGE_SIZE, IMAGE_SIZE, 3)).copy()
            background += rng.normal(0, 9, size=background.shape)
            object_color, target_color = (214, 60, 60), (45, 130, 65)
        else:
            base = rng.uniform(45, 225, size=(1, 1, 3)).astype(np.float32)
            background = np.broadcast_to(base, (IMAGE_SIZE, IMAGE_SIZE, 3)).copy()
            background += rng.normal(0, 9, size=background.shape)
            object_color = (int(rng.uniform(180, 245)), int(rng.uniform(45, 105)), int(rng.uniform(35, 100)))
            target_color = (int(rng.uniform(35, 100)), int(rng.uniform(125, 205)), int(rng.uniform(75, 170)))
        noise = 3.0
    elif domain == "source_appearance":
        background = np.full((IMAGE_SIZE, IMAGE_SIZE, 3), rng.uniform(150, 235), dtype=np.float32)
        object_color = (int(rng.uniform(170, 245)), int(rng.uniform(45, 110)), int(rng.uniform(35, 100)))
        target_color = (int(rng.uniform(35, 100)), int(rng.uniform(120, 210)), int(rng.uniform(75, 175)))
        noise = 2.0
    elif domain in {"target_realistic", "target_bright"}:
        base = rng.uniform(45, 175, size=(IMAGE_SIZE, IMAGE_SIZE, 1))
        stripes = (np.sin(np.arange(IMAGE_SIZE)[None, :, None] / 3.0) * 18.0).astype(np.float32)
        background = np.repeat(base, 3, axis=2) + stripes
        if domain == "target_bright":
            background = np.clip(background + 55, 0, 255)
        object_color, target_color = (235, 185, 55), (70, 160, 205)
        noise = 14.0
    else:
        raise ValueError(f"unknown domain: {domain}")
    image = Image.fromarray(np.uint8(np.clip(background, 0, 255)), mode="RGB")
    draw = ImageDraw.Draw(image)
    ox, oy = int(object_xy[0] * IMAGE_SIZE), int(object_xy[1] * IMAGE_SIZE)
    tx, ty = int(target_xy[0] * IMAGE_SIZE), int(target_xy[1] * IMAGE_SIZE)
    draw.rectangle((tx - 4, ty - 4, tx + 4, ty + 4), outline=target_color, width=2)
    draw.ellipse((ox - 3, oy - 3, ox + 3, oy + 3), fill=object_color, outline=(20, 20, 20))
    array = np.asarray(image, dtype=np.float32)
    if noise:
        array += rng.normal(0, noise, size=array.shape)
    array = np.clip(array / 255.0, 0.0, 1.0).transpose(2, 0, 1)
    return array.astype(np.float32), label


def make_dataset(size: int, domain: str, seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    rng = np.random.default_rng(seed)
    images, labels = zip(*(render_sample(rng, domain) for _ in range(size)))
    return torch.from_numpy(np.stack(images)), torch.tensor(labels, dtype=torch.long)


class RGBPolicy(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 48, 3, padding=1), nn.ReLU(),
        )
        self.head = nn.Sequential(nn.Flatten(), nn.Linear(48 * 8 * 8, 128), nn.ReLU(), nn.Linear(128, len(CLASSES)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.net(x))


def train_policy(images: torch.Tensor, labels: torch.Tensor, device: torch.device, seed: int, epochs: int) -> tuple[RGBPolicy, list[float]]:
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(TensorDataset(images, labels), batch_size=128, shuffle=True, generator=generator)
    model = RGBPolicy().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3)
    criterion = nn.CrossEntropyLoss()
    losses: list[float] = []
    for _ in range(epochs):
        total, count = 0.0, 0
        for batch_images, batch_labels in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(batch_images.to(device)), batch_labels.to(device))
            loss.backward()
            optimizer.step()
            total += float(loss.item()) * len(batch_labels)
            count += len(batch_labels)
        losses.append(total / count)
    return model, losses


def accuracy(model: RGBPolicy, images: torch.Tensor, labels: torch.Tensor, device: torch.device) -> float:
    with torch.no_grad():
        prediction = model(images.to(device)).argmax(dim=1).cpu()
    return float((prediction == labels).float().mean().item())


def save_preview(path: Path, images: torch.Tensor, labels: torch.Tensor) -> None:
    tile = (images[:16].permute(0, 2, 3, 1).numpy() * 255).astype(np.uint8)
    canvas = Image.new("RGB", (IMAGE_SIZE * 4, IMAGE_SIZE * 4), "white")
    for index, array in enumerate(tile):
        canvas.paste(Image.fromarray(array), ((index % 4) * IMAGE_SIZE, (index // 4) * IMAGE_SIZE))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-size", type=int, default=4096, help="examples per seed and training variant")
    parser.add_argument("--test-size", type=int, default=1024, help="examples per seed and target domain")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--seeds", default="20260808,20260809,20260810")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "validation" / "runs" / "local-gpu")
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args()
    try:
        seeds = [int(value) for value in args.seeds.split(",")]
    except ValueError:
        parser.error("--seeds must be comma-separated integers")
    if args.train_size < 2048 or args.test_size < 512 or args.epochs < 8 or len(seeds) < 3:
        parser.error("the benchmark requires at least 2048 train examples, 512 test examples, 8 epochs and 3 seeds")
    seed_everything(seeds[0])
    try:
        device = select_device(not args.allow_cpu)
    except RuntimeError as exc:
        parser.error(str(exc))
    started = time.perf_counter()
    variants = ("source_clean", "source_background", "source_appearance", "source_full")
    target_domains = ("target_realistic", "target_bright")
    rows: list[dict[str, Any]] = []
    checkpoint_model: RGBPolicy | None = None
    for seed in seeds:
        source_test_x, source_test_y = make_dataset(args.test_size, "source_clean", seed + 100)
        target_tests = {domain: make_dataset(args.test_size, domain, seed + 200 + index) for index, domain in enumerate(target_domains)}
        for variant_index, variant in enumerate(variants):
            train_x, train_y = make_dataset(args.train_size, variant, seed + variant_index)
            model, losses = train_policy(train_x, train_y, device, seed + 50 + variant_index, args.epochs)
            if seed == seeds[0] and variant == "source_full":
                checkpoint_model = model
            rows.append({"seed": seed, "variant": variant, "source_accuracy": accuracy(model, source_test_x, source_test_y, device), "target_accuracy": {domain: accuracy(model, images, labels, device) for domain, (images, labels) in target_tests.items()}, "final_loss": losses[-1]})
    grouped: dict[str, dict[str, Any]] = {}
    for variant in variants:
        grouped[variant] = {}
        for domain in target_domains:
            values = [row["target_accuracy"][domain] for row in rows if row["variant"] == variant]
            grouped[variant][domain] = {"mean": float(np.mean(values)), "std": float(np.std(values)), "values": values}
        source_values = [row["source_accuracy"] for row in rows if row["variant"] == variant]
        grouped[variant]["source"] = {"mean": float(np.mean(source_values)), "std": float(np.std(source_values)), "values": source_values}
    replay_a = make_dataset(256, "source_full", seeds[0])
    replay_b = make_dataset(256, "source_full", seeds[0])
    metrics = {"device": device_info(device), "protocol": {"seeds": seeds, "variants": list(variants), "target_domains": list(target_domains), "train_size_per_variant": args.train_size, "test_size_per_domain": args.test_size, "epochs": args.epochs, "total_training_examples": len(seeds) * len(variants) * args.train_size}, "rows": rows, "summary": grouped, "dataset_replay_match": bool(torch.equal(replay_a[0], replay_b[0]) and torch.equal(replay_a[1], replay_b[1])), "wall_time_ms": round((time.perf_counter() - started) * 1000, 3)}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    preview_source = args.output_dir / "source_preview.png"
    preview_target = args.output_dir / "target_preview.png"
    source_preview_x, source_preview_y = make_dataset(64, "source_clean", seeds[0] + 1000)
    target_preview_x, target_preview_y = make_dataset(64, "target_realistic", seeds[0] + 1001)
    save_preview(preview_source, source_preview_x, source_preview_y)
    save_preview(preview_target, target_preview_x, target_preview_y)
    checkpoint_path = args.output_dir / "randomized_policy.pt"
    if checkpoint_model is None:
        raise RuntimeError("source_full checkpoint was not produced")
    torch.save({"model": {key: value.detach().cpu() for key, value in checkpoint_model.state_dict().items()}, "seed": seeds[0], "classes": CLASSES}, checkpoint_path)
    matrix_path = args.output_dir / "matrix.json"
    write_json(matrix_path, {"rows": rows, "summary": grouped})
    metrics_path = args.output_dir / "metrics.json"
    write_json(metrics_path, metrics)
    evidence = {"schema_version": "3.0", "experiment_id": "9-10", "status": "complete", "kind": "local_gpu_rgb_domain_transfer", "seed": seeds[0], "metrics": metrics, "artifacts": [{"kind": "checkpoint", "path": relative_or_absolute(checkpoint_path, args.output_dir), "sha256": sha256(checkpoint_path)}, {"kind": "metrics", "path": relative_or_absolute(metrics_path, args.output_dir), "sha256": sha256(metrics_path)}, {"kind": "matrix", "path": relative_or_absolute(matrix_path, args.output_dir), "sha256": sha256(matrix_path)}, {"kind": "source_preview", "path": relative_or_absolute(preview_source, args.output_dir), "sha256": sha256(preview_source)}, {"kind": "target_preview", "path": relative_or_absolute(preview_target, args.output_dir), "sha256": sha256(preview_target)}], "hardware_extension": {"status": "gated", "actuation_attempted": False, "upstream": "StoneT2000/lerobot-sim2real"}, "blockers": [] if not args.allow_cpu else ["CPU debug mode is not a GPU acceptance run"]}
    evidence_path = args.output_dir / "evidence.json"
    write_json(evidence_path, evidence)
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
