#!/usr/bin/env python3
"""Validate the honest local GPU evidence for Experiment 9-8."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(data: dict[str, Any], evidence_dir: Path | None = None) -> list[str]:
    errors: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    expect(data.get("schema_version") == "3.0", "schema_version must be 3.0")
    expect(data.get("experiment_id") == "9-8", "experiment_id must be 9-8")
    expect(data.get("kind") == "local_gpu_expert_upper_bound", "wrong evidence kind")
    expect(data.get("status") == "complete", "local evidence must be complete")
    metrics = data.get("metrics", {})
    expect(metrics.get("device", {}).get("device") in {"mps", "cuda"}, "evidence must use a local GPU accelerator")
    protocol = metrics.get("protocol", {})
    expect(len(protocol.get("seeds", [])) >= 3, "at least three seeds are required")
    expect(len(protocol.get("object_counts", [])) >= 3, "at least three object-count conditions are required")
    expect(protocol.get("total_episodes", 0) >= 2000, "at least 2000 benchmark episodes are required")
    cells = metrics.get("cells", [])
    expect(len(cells) == len(protocol.get("seeds", [])) * len(protocol.get("object_counts", [])), "one result cell is required per seed/object-count pair")
    expect(metrics.get("worst_cell_success_rate") == 1.0, "expert upper bound must solve every benchmark cell")
    expect(metrics.get("deterministic_replay") is True, "repeating a fixed seed must reproduce the same metrics")
    artifacts = data.get("artifacts", [])
    expect(len(artifacts) == 2, "metrics and episode-cell artifacts are required")
    if evidence_dir is not None:
        for artifact in artifacts:
            path = evidence_dir / str(artifact.get("path", ""))
            expect(path.is_file(), f"artifact does not exist: {path}")
            if path.is_file():
                expect(file_sha256(path) == artifact.get("sha256"), f"artifact hash mismatch: {path.name}")
    extension = data.get("hardware_extension", {})
    expect(extension.get("actuation_attempted") is False, "local run must not claim hardware actuation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    errors = validate(data, args.evidence.resolve().parent)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID: experiment 9-8 local GPU evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
