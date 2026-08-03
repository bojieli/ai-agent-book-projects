#!/usr/bin/env python3
"""Report durable Experiment 10-7 progress without reading credentials."""

from __future__ import annotations

import argparse
import gzip
import json
import os
from pathlib import Path


ARMS = ("baseline", "custom_goal", "no_reflection")


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def receipt_rows(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    launch_path = output / "launch.json"
    launch_by_arm = {}
    if launch_path.exists():
        launch = json.loads(launch_path.read_text())
        launch_by_arm = {row["arm"]: row for row in launch.get("launches", [])}
    supervisor_path = output / "supervisor_status.json"
    if supervisor_path.exists():
        supervisor = json.loads(supervisor_path.read_text())
        for arm, pid in supervisor.get("pids", {}).items():
            launch_by_arm.setdefault(arm, {})["pid"] = pid
    result = {"seed": None, "arms": {}}
    seed_path = output / "seed_status.json"
    if seed_path.exists():
        result["seed"] = json.loads(seed_path.read_text())
    else:
        live = output / "receipts" / "seed_history.jsonl"
        result["seed"] = {
            "complete": False,
            "live_receipt_calls": receipt_rows(live) if live.exists() else 0,
        }
    for arm in ARMS:
        status_path = output / "status" / f"{arm}.json"
        status = json.loads(status_path.read_text()) if status_path.exists() else {
            "completed_steps": 0,
            "target_steps": 17_280,
            "complete": False,
            "checkpoints": [],
        }
        launch = launch_by_arm.get(arm, {})
        status["pid"] = launch.get("pid")
        status["process_alive"] = process_alive(launch.get("pid"))
        receipt_dir = output / "receipts" / arm
        live = (
            sorted(
                path
                for path in receipt_dir.glob("*.jsonl")
                if ".failed-" not in path.name
            )
            if receipt_dir.exists()
            else []
        )
        status["live_receipt_calls"] = sum(receipt_rows(path) for path in live)
        result["arms"][arm] = status
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
