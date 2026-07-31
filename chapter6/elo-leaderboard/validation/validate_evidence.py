"""Fail-closed verifier for a saved Experiment 6-6 run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--input", type=Path, help="Optionally re-hash the 2 GB Arena input")
    args = parser.parse_args()

    manifest_path = args.run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    if manifest.get("experiment") != "6-6":
        failures.append("wrong experiment id")
    if manifest.get("status") != "passed" or manifest.get("official_complete") is not True:
        failures.append("run is not officially complete")
    false_gates = sorted(name for name, passed in manifest.get("gates", {}).items() if passed is not True)
    if false_gates:
        failures.append(f"false gates: {false_gates}")

    for name, expected in manifest.get("artifacts", {}).items():
        path = args.run_dir / name
        if not path.is_file():
            failures.append(f"missing artifact: {name}")
            continue
        if path.stat().st_size != expected.get("bytes"):
            failures.append(f"size mismatch: {name}")
        if sha256_file(path) != expected.get("sha256"):
            failures.append(f"sha256 mismatch: {name}")

    project = Path(__file__).resolve().parents[1]
    for name, expected_hash in manifest.get("sources", {}).items():
        path = project / name
        if not path.is_file() or sha256_file(path) != expected_hash:
            failures.append(f"source mismatch: {name}")

    if args.input:
        expected = manifest["input"]
        if args.input.stat().st_size != expected["bytes"]:
            failures.append("input size mismatch")
        if sha256_file(args.input) != expected["sha256"]:
            failures.append("input sha256 mismatch")

    result = {"valid": not failures, "failures": failures}
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
