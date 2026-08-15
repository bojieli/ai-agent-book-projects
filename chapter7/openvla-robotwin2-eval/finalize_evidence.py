#!/usr/bin/env python3
"""Finalize and verify the retained Experiment 6-12 evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import experiment


HERE = Path(__file__).resolve().parent
DEFAULT_RUN = HERE / "validation" / "runs" / "exp6-12-localgpu-20260803-v1"
PACKAGE_FILES = (
    "chunk_1/episodes.jsonl",
    "chunk_1/process.json",
    "chunk_25/episodes.jsonl",
    "chunk_25/process.json",
    "failure_annotations.json",
    "launch_manifest.json",
    "preflight.json",
    "report.json",
    "report.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path, label: str) -> dict[str, Any]:
    return {"path": label, "bytes": path.stat().st_size, "sha256": sha256(path)}


def canonical_videos(run_dir: Path) -> list[dict[str, Any]]:
    launch = experiment.load_json(run_dir / "launch_manifest.json")
    records: list[dict[str, Any]] = []
    for arm in ("chunk_1", "chunk_25"):
        process = experiment.load_json(run_dir / arm / "process.json")
        index = experiment.video_index(
            Path(launch["arms"][arm]["rollout_directory"]),
            started_at_utc=process["started_at_utc"],
            ended_at_utc=process["ended_at_utc"],
        )
        for (task_key, success), candidates in sorted(index.items()):
            if len(candidates) != 1:
                raise RuntimeError(
                    f"{arm}/{task_key}/{success}: expected one in-window video, "
                    f"found {len(candidates)}"
                )
            path = Path(candidates[0])
            records.append(
                {
                    "arm": arm,
                    "task_key": task_key,
                    "success": success,
                    "filename": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return records


def build_manifest(run_dir: Path) -> dict[str, Any]:
    report = experiment.load_json(run_dir / "report.json")
    annotations = experiment.load_json(run_dir / "failure_annotations.json")
    videos = canonical_videos(run_dir)
    package = [artifact(run_dir / name, name) for name in PACKAGE_FILES]
    sources = []
    for name in (
        "README.md",
        "annotate_timeouts.py",
        "config.json",
        "experiment.py",
        "finalize_evidence.py",
        "instrument_upstream.py",
        "task_config_exp6_12_three_view.yml",
        "test_experiment.py",
    ):
        sources.append(artifact(HERE / name, f"chapter6/openvla-robotwin2-eval/{name}"))
    checks = {
        "strict_analysis_complete": report["strict_completion"]["complete"] is True,
        "two_256_episode_arms": all(
            report["arms"][arm]["episodes"] == 256 for arm in ("chunk_1", "chunk_25")
        ),
        "all_512_rollout_videos_hashed": len(videos) == 512,
        "all_486_failures_annotated": len(annotations) == 486,
        "all_processes_succeeded": all(
            experiment.load_json(run_dir / arm / "process.json")["exit_code"] == 0
            for arm in ("chunk_1", "chunk_25")
        ),
        "preflight_passed": experiment.load_json(run_dir / "preflight.json")[
            "ready_for_real_validation"
        ]
        is True,
    }
    return {
        "schema_version": 1,
        "experiment": "6-12",
        "generated_at_utc": experiment.utc_now(),
        "status": "complete" if all(checks.values()) else "incomplete",
        "checks": checks,
        "results": {
            "chunk_1_successes": report["arms"]["chunk_1"]["successes"],
            "chunk_25_successes": report["arms"]["chunk_25"]["successes"],
            "paired_success_delta": report["controlled_action_chunk_comparison"][
                "mean_paired_success_delta"
            ],
            "classified_failures": len(annotations),
        },
        "retained_package": package,
        "runtime_sources": sources,
        "external_rollout_videos": videos,
        "claim_boundary": (
            "The retained JSON/Markdown package and source hashes are reviewable in a clean "
            "clone. The 512 rollout MP4s and 15 GB checkpoint remain external local artifacts; "
            "their identities were hashed during finalization and are not vendored."
        ),
    }


def verify(run_dir: Path) -> None:
    manifest = experiment.load_json(run_dir / "manifest.json")
    failures: list[str] = []
    sidecar_path = run_dir / "manifest.json.sha256"
    expected_sidecar = f"{sha256(run_dir / 'manifest.json')}  manifest.json\n"
    if not sidecar_path.is_file():
        failures.append("missing manifest.json.sha256")
    elif sidecar_path.read_text(encoding="utf-8") != expected_sidecar:
        failures.append("manifest.json.sha256 does not match manifest.json")
    for section, base in (("retained_package", run_dir), ("runtime_sources", HERE.parent.parent)):
        for item in manifest[section]:
            path = base / item["path"]
            if not path.is_file():
                failures.append(f"missing {item['path']}")
            elif path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                failures.append(f"hash mismatch {item['path']}")
    if manifest["status"] != "complete" or not all(manifest["checks"].values()):
        failures.append("manifest acceptance checks are not complete")
    if len(manifest["external_rollout_videos"]) != 512:
        failures.append("manifest does not retain 512 rollout-video identities")
    if failures:
        raise RuntimeError("; ".join(failures))
    print("Experiment 6-12 retained evidence verification passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("finalize", "verify"))
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    if args.command == "finalize":
        manifest = build_manifest(run_dir)
        experiment.dump_json(run_dir / "manifest.json", manifest)
        (run_dir / "manifest.json.sha256").write_text(
            f"{sha256(run_dir / 'manifest.json')}  manifest.json\n", encoding="utf-8"
        )
        print(f"Wrote complete manifest with {len(manifest['external_rollout_videos'])} videos")
    else:
        verify(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
