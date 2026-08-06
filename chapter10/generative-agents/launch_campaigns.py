#!/usr/bin/env python3
"""Launch or resume all Experiment 10-7 arms as detached local processes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


ARMS = ("baseline", "custom_goal", "no_reflection")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--target-steps", type=int, default=17_280)
    parser.add_argument("--chunk-steps", type=int, default=360)
    args = parser.parse_args()
    output = args.output.resolve()
    if not (output / "seed_status.json").exists():
        raise SystemExit("prepare the shared history seed before launching arms")
    logs = output / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    launches = []
    for arm in ARMS:
        status_path = output / "status" / f"{arm}.json"
        if status_path.exists() and json.loads(status_path.read_text()).get("complete"):
            launches.append({"arm": arm, "skipped": "already complete"})
            continue
        command = [
            str(args.python.expanduser().absolute()),
            str(Path(__file__).resolve().with_name("run_campaign.py")),
            "--upstream",
            str(args.upstream.resolve()),
            "--output",
            str(output),
            "--mode",
            "arm",
            "--arm",
            arm,
            "--target-steps",
            str(args.target_steps),
            "--chunk-steps",
            str(args.chunk_steps),
        ]
        log_path = logs / f"{arm}.log"
        handle = log_path.open("ab", buffering=0)
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).resolve().parents[2],
            env=os.environ.copy(),
            start_new_session=True,
        )
        handle.close()
        launches.append(
            {
                "arm": arm,
                "pid": process.pid,
                "log": str(log_path.relative_to(output)),
                "command": command,
            }
        )
    record = {
        "schema_version": 1,
        "experiment": "10-7",
        "launched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "launches": launches,
    }
    launch_path = output / "launch.json"
    launch_path.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
