#!/usr/bin/env python3
"""Create auditable timeout annotations from complete Experiment 6-12 evidence.

This helper only labels an episode when the upstream recorder says it failed at
the configured action horizon and an exact failure-video match can be probed.
It refuses early failures, missing videos, duplicate videos, and malformed MP4s
instead of guessing a visual failure mechanism.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

import experiment


def video_metadata(path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames,duration,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr.strip()}")
    streams = json.loads(proc.stdout).get("streams", [])
    if len(streams) != 1:
        raise RuntimeError(f"expected one video stream in {path}, found {len(streams)}")
    stream = streams[0]
    required = {"nb_frames", "duration", "width", "height"}
    if not required.issubset(stream):
        raise RuntimeError(f"incomplete ffprobe metadata for {path}: {stream}")
    return stream


def build_annotations(
    config: dict[str, Any],
    run_dir: Path,
    timeout_action_steps: int,
) -> dict[str, dict[str, str]]:
    manifest = experiment.load_json(run_dir / "launch_manifest.json")
    annotations: dict[str, dict[str, str]] = {}
    expected_episodes = (
        int(config["iid_validation_seeds"])
        + int(config["ood_validation_seeds"])
    )
    for chunk in config["action_chunks"]:
        arm = f"chunk_{chunk}"
        rows = experiment.read_jsonl(run_dir / arm / "episodes.jsonl")
        if len(rows) != expected_episodes:
            raise RuntimeError(
                f"{arm} is incomplete: expected {expected_episodes} episodes, found {len(rows)}"
            )
        videos = experiment.video_index(
            Path(manifest["arms"][arm]["rollout_directory"]),
            started_at_utc=experiment.load_json(run_dir / arm / "process.json")[
                "started_at_utc"
            ],
            ended_at_utc=experiment.load_json(run_dir / arm / "process.json")[
                "ended_at_utc"
            ],
        )
        for candidates in videos.values():
            candidates.sort()
        for row in rows:
            if row.get("success"):
                continue
            observed_steps = int(row.get("finish_action_steps", -1))
            if observed_steps != timeout_action_steps:
                raise RuntimeError(
                    f"refusing to infer timeout for {experiment.annotation_key(row)}: "
                    f"observed {observed_steps} action steps"
                )
            task_file = (
                f"{config['task']}_trial_{row['trial_id']}_seed_{row['trial_seed']}"
            )
            matches = videos.get((task_file, False), [])
            if len(matches) != 1:
                raise RuntimeError(
                    f"expected one exact failure video for {experiment.annotation_key(row)}, "
                    f"found {len(matches)}"
                )
            video_path = Path(matches[0])
            metadata = video_metadata(video_path)
            control_seconds = timeout_action_steps / float(config["control_hz"])
            annotations[experiment.annotation_key(row)] = {
                "failure_mode": "timeout",
                "evidence": (
                    f"Exact rollout {video_path.name} is a "
                    f"{metadata['width']}x{metadata['height']} MP4 with "
                    f"{metadata['nb_frames']} frames over {float(metadata['duration']):.3f}s. "
                    f"The paired upstream episode recorder reports failure after "
                    f"{observed_steps}/{timeout_action_steps} action steps "
                    f"({control_seconds:.3f}s at {config['control_hz']} Hz) without eval_success."
                ),
            }
    return annotations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=experiment.DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--timeout-action-steps", type=int, default=200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.timeout_action_steps <= 0:
        parser.error("--timeout-action-steps must be positive")
    config = experiment.resolve_config(args.config.resolve())
    run_dir = args.run_dir.resolve()
    output = args.output.resolve() if args.output else run_dir / "failure_annotations.json"
    annotations = build_annotations(config, run_dir, args.timeout_action_steps)
    experiment.dump_json(output, annotations)
    print(f"Wrote {len(annotations)} timeout annotations to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
