#!/usr/bin/env python3
"""Start the Experiment 10-7 supervisor in a detached process session."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    output = args.output.resolve()
    command = [
        str(args.python.expanduser().absolute()),
        str(Path(__file__).resolve().with_name("supervise_campaigns.py")),
        "--upstream",
        str(args.upstream.resolve()),
        "--output",
        str(output),
        "--python",
        str(args.python.expanduser().absolute()),
    ]
    log_path = output / "logs" / "supervisor.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
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
    record = {
        "schema_version": 1,
        "experiment": "10-7",
        "launched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pid": process.pid,
        "command": command,
        "log": str(log_path.relative_to(output)),
    }
    (output / "supervisor_launch.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

