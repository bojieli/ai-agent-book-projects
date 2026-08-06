#!/usr/bin/env python3
"""Bounded analysis executable used by the Experiment 4-6 task manager."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path


def analyze(path: Path, job: str) -> dict:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    headings = [line for line in lines if re.match(r"^#{1,6}\s", line)]
    return {
        "job": job,
        "input_path": str(path),
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "lines": len(lines),
        "heading_count": len(headings),
        "experiment_mentions": text.lower().count("实验"),
        "async_mentions": len(re.findall(r"异步|async", text, flags=re.IGNORECASE)),
        "error_keyword_count": len(re.findall(r"错误|error", text, flags=re.IGNORECASE)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True,
                        choices=["fast", "mid", "slow", "logs", "recovery"])
    parser.add_argument("--rate", required=True, type=float)
    parser.add_argument("--tick-real", required=True, type=float)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    if args.rate <= 0 or args.tick_real <= 0:
        raise SystemExit("rate and tick-real must be positive")
    if not args.input.is_file():
        raise SystemExit(f"input does not exist: {args.input}")
    progress = 0.0
    while progress < 100.0:
        time.sleep(args.tick_real)
        progress = min(100.0, progress + args.rate)
        print(f"PROGRESS {progress:.3f}", flush=True)
    print("RESULT " + json.dumps(analyze(args.input.resolve(), args.job),
                                 ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
