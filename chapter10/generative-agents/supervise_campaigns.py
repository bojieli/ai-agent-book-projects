#!/usr/bin/env python3
"""Supervise and automatically resume all long-running Experiment 10-7 arms."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path


ARMS = ("baseline", "custom_goal", "no_reflection")


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(temporary, path)


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def arm_complete(output: Path, arm: str) -> bool:
    path = output / "status" / f"{arm}.json"
    return path.exists() and json.loads(path.read_text()).get("complete") is True


def command_for(args: argparse.Namespace, arm: str) -> list[str]:
    return [
        str(args.python.expanduser().absolute()),
        str(Path(__file__).resolve().with_name("run_campaign.py")),
        "--upstream",
        str(args.upstream.resolve()),
        "--output",
        str(args.output.resolve()),
        "--mode",
        "arm",
        "--arm",
        arm,
        "--target-steps",
        str(args.target_steps),
        "--chunk-steps",
        str(args.chunk_steps),
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--target-steps", type=int, default=17_280)
    parser.add_argument("--chunk-steps", type=int, default=360)
    parser.add_argument("--poll-seconds", type=int, default=30)
    args = parser.parse_args()
    output = args.output.resolve()
    launch_path = output / "launch.json"
    launch = json.loads(launch_path.read_text()) if launch_path.exists() else {"launches": []}
    pids = {
        row["arm"]: row.get("pid")
        for row in launch.get("launches", [])
        if row.get("arm") in ARMS
    }
    attempts = {arm: 0 for arm in ARMS}
    children: dict[str, subprocess.Popen] = {}
    status_path = output / "supervisor_status.json"
    while True:
        complete = {arm: arm_complete(output, arm) for arm in ARMS}
        if all(complete.values()):
            atomic_json(
                status_path,
                {
                    "schema_version": 1,
                    "experiment": "10-7",
                    "complete": True,
                    "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "attempts": attempts,
                    "pids": pids,
                },
            )
            return 0
        for arm in ARMS:
            child = children.get(arm)
            if child is not None and child.poll() is not None:
                children.pop(arm)
                pids[arm] = None
            if complete[arm] or process_alive(pids.get(arm)):
                continue
            command = command_for(args, arm)
            log_path = output / "logs" / f"{arm}.log"
            with log_path.open("ab", buffering=0) as handle:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    cwd=Path(__file__).resolve().parents[2],
                    env=os.environ.copy(),
                    start_new_session=True,
                )
            children[arm] = process
            pids[arm] = process.pid
            attempts[arm] += 1
        atomic_json(
            status_path,
            {
                "schema_version": 1,
                "experiment": "10-7",
                "complete": False,
                "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "arms_complete": complete,
                "attempts": attempts,
                "pids": pids,
            },
        )
        time.sleep(max(5, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())

