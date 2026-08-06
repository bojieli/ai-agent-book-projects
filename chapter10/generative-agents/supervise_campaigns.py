#!/usr/bin/env python3
"""Supervise and automatically resume all long-running Experiment 10-7 arms."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
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


def live_receipt_has_error(
    output: Path, arm: str, target_steps: int, chunk_steps: int
) -> bool:
    """Detect a failed provider call before an expensive chunk finishes."""

    status_path = output / "status" / f"{arm}.json"
    completed = 0
    if status_path.exists():
        completed = int(json.loads(status_path.read_text()).get("completed_steps", 0))
    if completed >= target_steps:
        return False
    end = min(completed + chunk_steps, target_steps)
    receipt = (
        output
        / "receipts"
        / arm
        / f"steps_{completed:05d}_{end:05d}.jsonl"
    )
    if not receipt.exists():
        return False
    with receipt.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("success") is not True:
                return True
    return False


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
    status_path = output / "supervisor_status.json"
    launch_path = output / "launch.json"
    launch = json.loads(launch_path.read_text()) if launch_path.exists() else {"launches": []}
    pids = {
        row["arm"]: row.get("pid")
        for row in launch.get("launches", [])
        if row.get("arm") in ARMS
    }
    attempts = {arm: 0 for arm in ARMS}
    error_aborts = {arm: 0 for arm in ARMS}
    if status_path.exists():
        previous = json.loads(status_path.read_text())
        for arm, pid in previous.get("pids", {}).items():
            if (
                arm in ARMS
                and pid
                and process_alive(pid)
                and not process_alive(pids.get(arm))
            ):
                pids[arm] = pid
        for arm, count in previous.get("attempts", {}).items():
            if arm in ARMS:
                attempts[arm] = int(count)
        for arm, count in previous.get("provider_error_aborts", {}).items():
            if arm in ARMS:
                error_aborts[arm] = int(count)
    children: dict[str, subprocess.Popen] = {}
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
                    "provider_error_aborts": error_aborts,
                    "pids": pids,
                },
            )
            return 0
        for arm in ARMS:
            child = children.get(arm)
            if child is not None and child.poll() is not None:
                children.pop(arm)
                pids[arm] = None
            if (
                not complete[arm]
                and process_alive(pids.get(arm))
                and live_receipt_has_error(
                    output, arm, args.target_steps, args.chunk_steps
                )
            ):
                os.kill(pids[arm], signal.SIGTERM)
                pids[arm] = None
                error_aborts[arm] += 1
                continue
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
                "provider_error_aborts": error_aborts,
                "pids": pids,
            },
        )
        time.sleep(max(5, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
