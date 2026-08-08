#!/usr/bin/env python3
"""Validate local GPU RGB domain-transfer evidence for Experiment 9-10."""

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
    expect(data.get("experiment_id") == "9-10", "experiment_id must be 9-10")
    expect(data.get("kind") == "local_gpu_rgb_domain_transfer", "wrong evidence kind")
    expect(data.get("status") == "complete", "local evidence must be complete")
    metrics = data.get("metrics", {})
    expect(metrics.get("device", {}).get("device") in {"mps", "cuda"}, "evidence must use a local GPU accelerator")
    protocol = metrics.get("protocol", {})
    expect(len(protocol.get("seeds", [])) >= 3, "at least three training seeds are required")
    expect(set(protocol.get("variants", [])) == {"source_clean", "source_background", "source_appearance", "source_full"}, "all four randomization conditions are required")
    expect(len(protocol.get("target_domains", [])) >= 2, "at least two target visual domains are required")
    expect(protocol.get("total_training_examples", 0) >= 20000, "at least 20000 training examples are required")
    summary = metrics.get("summary", {})
    expect(summary.get("source_clean", {}).get("source", {}).get("mean", 0) > 0.85, "clean source accuracy must exceed 0.85")
    for domain in protocol.get("target_domains", []):
        clean = summary.get("source_clean", {}).get(domain, {}).get("mean", 0)
        full = summary.get("source_full", {}).get(domain, {}).get("mean", 0)
        expect(full > 0.65, f"full randomization target accuracy is too low for {domain}")
        expect(full > clean, f"full randomization must improve target accuracy for {domain}")
    expect(metrics.get("dataset_replay_match") is True, "repeating a fixed dataset seed must reproduce the exact data")
    artifacts = data.get("artifacts", [])
    expect(len(artifacts) == 5, "checkpoint, metrics, matrix and two preview artifacts are required")
    if evidence_dir is not None:
        for index, artifact in enumerate(artifacts):
            path = evidence_dir / str(artifact.get("path", ""))
            expect(path.is_file(), f"artifact[{index}] does not exist")
            if path.is_file():
                expect(file_sha256(path) == artifact.get("sha256"), f"artifact[{index}] hash mismatch")
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
    print("VALID: experiment 9-10 local GPU evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
