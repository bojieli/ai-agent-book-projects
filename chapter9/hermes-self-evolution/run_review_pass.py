#!/usr/bin/env python3
"""Continue the canonical Hermes session with independent review feedback."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import argparse


ROOT = Path(__file__).resolve().parent
RUN_ID = "exp8-6-hermes-gpt56luna-20260802-v1"
MODEL = "openai/gpt-5.6-luna"
SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--task", default="review_task.md")
    parser.add_argument("--output", default="hermes-review-transcript.txt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is required", file=sys.stderr)
        return 2
    source = ROOT / "worktree" / "hermes-agent"
    output = ROOT / "validation" / args.run_id / "raw" / args.output
    env = os.environ.copy()
    env.update(
        {
            "HERMES_HOME": str(ROOT / ".hermes-home" / args.run_id),
            "HERMES_YOLO_MODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )
    prompt = (ROOT / args.task).read_text(encoding="utf-8")
    result = subprocess.run(
        [
            "uv", "run", "hermes", "chat", "--continue",
            "--provider", "openrouter", "--model", args.model,
            "--toolsets", "terminal,skills", "-q", prompt,
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
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
