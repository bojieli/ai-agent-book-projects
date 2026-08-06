#!/usr/bin/env python3
"""Create a compact, complete, reviewable Experiment 10-7 evidence package."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ARMS = ("baseline", "custom_goal", "no_reflection")
SOURCE_COMMIT = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_json(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def export_state(sim: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    meta = load_json(sim / "reverie" / "meta.json")
    copy_json(sim / "reverie" / "meta.json", destination / "meta.json")
    copy_json(
        sim / "environment" / f"{meta['step']}.json",
        destination / "final_environment.json",
    )
    scratch = {}
    memory_path = destination / "memory_nodes.jsonl.gz"
    with gzip.open(memory_path, "wt", encoding="utf-8", compresslevel=9) as memory:
        for persona in sorted(meta["persona_names"]):
            root = sim / "personas" / persona / "bootstrap_memory"
            scratch[persona] = load_json(root / "scratch.json")
            nodes = load_json(root / "associative_memory" / "nodes.json")
            for node_id, node in nodes.items():
                memory.write(
                    json.dumps(
                        {"persona": persona, "node_id": node_id, "node": node},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
    (destination / "scratch.json").write_text(
        json.dumps(scratch, indent=2, ensure_ascii=False) + "\n"
    )
    movements_path = destination / "movements.jsonl.gz"
    with gzip.open(movements_path, "wt", encoding="utf-8", compresslevel=9) as output:
        for step in range(int(meta["step"])):
            movement = load_json(sim / "movement" / f"{step}.json")
            output.write(
                json.dumps(
                    {"step": step, "movement": movement},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    destination = args.destination.resolve()
    if destination.exists():
        raise SystemExit(f"destination already exists: {destination}")
    statuses = {
        arm: load_json(output / "status" / f"{arm}.json") for arm in ARMS
    }
    if not all(status.get("complete") for status in statuses.values()):
        raise SystemExit("all three arms must be complete before packaging")
    for required in (
        output / "analysis" / "deterministic_analysis.json",
        output / "analysis" / "plausibility_judgments.jsonl",
        output / "analysis" / "plausibility_summary.json",
    ):
        if not required.exists():
            raise SystemExit(f"missing analysis artifact: {required}")
    destination.mkdir(parents=True)
    experiment_root = Path(__file__).resolve().parent
    copy_json(experiment_root / "experiment_protocol.json", destination / "protocol.json")
    copy_json(output / "seed_status.json", destination / "seed_status.json")
    for arm in ARMS:
        copy_json(output / "status" / f"{arm}.json", destination / "status" / f"{arm}.json")
        sim = output / "storage" / statuses[arm]["current_sim"]
        export_state(sim, destination / "states" / arm)
    shutil.copytree(output / "receipts", destination / "receipts")
    compatibility = output / "compatibility"
    if not compatibility.is_dir():
        raise SystemExit("missing action-arena compatibility receipts")
    shutil.copytree(compatibility, destination / "compatibility")
    shutil.copytree(output / "analysis", destination / "analysis")
    upstream_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.upstream, text=True
    ).strip()
    upstream_status = subprocess.check_output(
        ["git", "status", "--short"], cwd=args.upstream, text=True
    ).splitlines()
    environment = {
        "schema_version": 1,
        "experiment": "10-7",
        "source_commit": upstream_commit,
        "source_clean": not upstream_status,
        "source_status": upstream_status,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "chat_model": os.environ.get("GA_CHAT_MODEL", "qwen3.7-flash"),
        "embedding_model": os.environ.get("GA_EMBEDDING_MODEL", "text-embedding-v4"),
        "credential_environment_variables": ["DASHSCOPE_API_KEY", "ANTHROPIC_API_KEY"],
    }
    (destination / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n"
    )
    if upstream_commit != SOURCE_COMMIT:
        raise SystemExit("upstream commit changed during the campaign")
    files = []
    for path in sorted(item for item in destination.rglob("*") if item.is_file()):
        if path.name in {"acceptance.json", "manifest.json"}:
            continue
        files.append(
            {
                "path": str(path.relative_to(destination)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "schema_version": 1,
        "experiment": "10-7",
        "run_id": destination.name,
        "files": files,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps({"destination": str(destination), "files": len(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
