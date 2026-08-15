#!/usr/bin/env python3
"""Create a credential-free integrity manifest for a Chapter 6 run directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, base: Path) -> dict:
    return {
        "path": str(path.resolve().relative_to(base.resolve())),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--status", required=True, choices=("complete", "incomplete", "blocked", "failed"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--reason", action="append", default=[])
    parser.add_argument("--input", action="append", type=Path, default=[])
    parser.add_argument("--provider-receipts", type=int, default=0)
    parser.add_argument("--command", default=None, help="Sanitized command; never include credentials")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    run_dir = args.run_dir.resolve()
    manifest_path = run_dir / "manifest.json"
    artifacts = [
        file_record(path, root)
        for path in sorted(run_dir.rglob("*"))
        if path.is_file() and path != manifest_path
    ]
    inputs = [file_record(path.resolve(), root) for path in args.input]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None

    payload = {
        "schema_version": 1,
        "experiment": args.experiment,
        "status": args.status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir.relative_to(root)),
        "git_commit": commit,
        "command": args.command,
        "provider_receipt_count": args.provider_receipts,
        "status_reasons": args.reason,
        "inputs": inputs,
        "artifacts": artifacts,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(manifest_path)


if __name__ == "__main__":
    main()
