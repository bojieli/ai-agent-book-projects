#!/usr/bin/env python3
"""Run a fresh, read-only Hermes acceptance review of the candidate patch."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
MODEL = "openai/gpt-5.6-luna"
SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--round", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is required", file=sys.stderr)
        return 2

    source = ROOT / "worktree" / "hermes-agent"
    output = ROOT / "validation" / args.run_id / "raw" / (
        f"hermes-acceptance-review-{args.round}.txt"
    )
    reviewer_home = ROOT / ".hermes-home" / (
        f"{args.run_id}-acceptance-{args.round}"
    )
    env = os.environ.copy()
    env.update(
        {
            "HERMES_HOME": str(reviewer_home),
            "HERMES_YOLO_MODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )
    prompt = (ROOT / "acceptance_review.md").read_text(encoding="utf-8")
    before = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=source,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    result = subprocess.run(
        [
            "uv", "run", "hermes", "chat",
            "--provider", "openrouter", "--model", args.model,
            "--toolsets", "terminal", "-q", prompt,
        ],
        cwd=source,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    text = result.stdout or ""
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        raise RuntimeError("credential-shaped value detected in review transcript")
    after = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=source,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    if after != before:
        raise RuntimeError("acceptance reviewer modified the candidate checkout")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text)
    if result.returncode != 0:
        return result.returncode
    if "VERDICT: ACCEPT" in text and "VERDICT: REJECT" not in text:
        return 0
    if "VERDICT: REJECT" in text:
        return 3
    print("Reviewer did not emit a valid terminal verdict", file=sys.stderr)
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
