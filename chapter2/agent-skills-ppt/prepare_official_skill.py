#!/usr/bin/env python3
"""Fetch and verify the pinned official Anthropic PPTX Skill (no reimplementation)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROTOCOL = json.loads((ROOT / "experiment_protocol.json").read_text(encoding="utf-8"))


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(destination: Path) -> dict:
    destination = destination.resolve()
    repository = PROTOCOL["runtime"]["official_skill_repository"]
    revision = PROTOCOL["runtime"]["official_skill_revision"]
    if not (destination / ".git").exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--filter=blob:none", "--no-checkout", repository, str(destination)])
    run(["git", "fetch", "origin", revision], cwd=destination)
    run(["git", "checkout", "--detach", revision], cwd=destination)
    head = run(["git", "rev-parse", "HEAD"], cwd=destination)
    if head != revision:
        raise RuntimeError(f"official Skill revision mismatch: {head} != {revision}")
    required = [
        destination / "skills/pptx/SKILL.md",
        destination / "skills/pptx/html2pptx.md",
        destination / "skills/pptx/scripts/html2pptx.js",
        destination / "skills/pptx/scripts/thumbnail.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("pinned official Skill is missing required files: " + ", ".join(missing))
    return {
        "repository": repository,
        "revision": head,
        "skill_path": str((destination / "skills/pptx").resolve()),
        "required_file_hashes": {
            str(path.relative_to(destination)): sha256(path) for path in required
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=ROOT / "external" / "anthropics-skills",
    )
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = prepare(args.destination)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
