#!/usr/bin/env python3
"""Independently validate a retained Experiment 10-7 evidence package."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ARMS = ("baseline", "custom_goal", "no_reflection")
SOURCE_COMMIT = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"
SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"AIza[A-Za-z0-9_-]{20,}"),
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl_rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def contains_secret(path: Path) -> bool:
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                if any(pattern.search(chunk) for pattern in SECRET_PATTERNS):
                    return True
    except (OSError, EOFError):
        return True
    return False


def positive_provider_usage(row: dict) -> bool:
    """Accept provider usage objects even when they contain nested details."""

    usage = (row.get("response") or {}).get("usage") or {}
    total = usage.get("total_tokens")
    if isinstance(total, (int, float)) and not isinstance(total, bool):
        return total > 0
    return any(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
        for value in usage.values()
    )


def compatibility_correction_valid(row: dict) -> bool:
    allowed = row.get("accessible_arenas")
    return (
        row.get("kind") == "action_arena_compatibility_correction"
        and isinstance(allowed, list)
        and bool(allowed)
        and row.get("normalized_output") in allowed
        and row.get("raw_output") != row.get("normalized_output")
        and isinstance(row.get("fallback"), bool)
        and row.get("reason")
        in {
            "stripped_response_wrappers",
            "case_insensitive_exact_match",
            "invalid_output_current_arena_fallback",
            "invalid_output_first_accessible_fallback",
        }
    )


def canonical_provider_receipt(path: Path) -> bool:
    return path.name.endswith(".jsonl.gz") and ".failed-" not in path.name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    protocol = load_json(run_dir / "protocol.json")
    seed = load_json(run_dir / "seed_status.json")
    environment = load_json(run_dir / "environment.json")
    analysis = load_json(run_dir / "analysis" / "deterministic_analysis.json")
    judge_summary = load_json(run_dir / "analysis" / "plausibility_summary.json")
    statuses = {
        arm: load_json(run_dir / "status" / f"{arm}.json") for arm in ARMS
    }
    metas = {arm: load_json(run_dir / "states" / arm / "meta.json") for arm in ARMS}
    scratch = {
        arm: load_json(run_dir / "states" / arm / "scratch.json") for arm in ARMS
    }
    movement_counts = {
        arm: sum(1 for _ in jsonl_rows(run_dir / "states" / arm / "movements.jsonl.gz"))
        for arm in ARMS
    }
    memory_rows = {
        arm: list(jsonl_rows(run_dir / "states" / arm / "memory_nodes.jsonl.gz"))
        for arm in ARMS
    }
    provider_rows = []
    for path in sorted((run_dir / "receipts").rglob("*.jsonl.gz")):
        if not canonical_provider_receipt(path):
            continue
        provider_rows.extend(jsonl_rows(path))
    provider_ids = [
        row.get("response", {}).get("id")
        for row in provider_rows
        if row.get("success") and row.get("response")
    ]
    provider_models = Counter(
        row.get("response", {}).get("model")
        for row in provider_rows
        if row.get("success") and row.get("response")
    )
    compatibility_rows = []
    compatibility_receipts_valid = True
    for arm, status in statuses.items():
        for checkpoint in status.get("checkpoints", []):
            relative = checkpoint.get("compatibility_receipt")
            expected = checkpoint.get("compatibility_corrections")
            if not isinstance(expected, int) or expected < 0:
                compatibility_receipts_valid = False
                continue
            if expected == 0 and relative is None:
                continue
            if not isinstance(relative, str):
                compatibility_receipts_valid = False
                continue
            relative_path = Path(relative)
            if (
                not relative_path.parts
                or relative_path.parts[0] != "compatibility"
                or ".." in relative_path.parts
            ):
                compatibility_receipts_valid = False
                continue
            path = run_dir / relative_path
            if not path.is_file():
                compatibility_receipts_valid = False
                continue
            rows = list(jsonl_rows(path))
            if len(rows) != expected:
                compatibility_receipts_valid = False
            compatibility_rows.extend(rows)
    judge_rows = list(jsonl_rows(run_dir / "analysis" / "plausibility_judgments.jsonl"))
    judge_ids = [row.get("response", {}).get("id") for row in judge_rows if row.get("success")]
    no_reflection_memory = analysis["arms"]["no_reflection"]["memory"]
    manifest = load_json(run_dir / "manifest.json")
    manifest_paths = {row["path"] for row in manifest["files"]}
    actual_paths = {
        str(path.relative_to(run_dir))
        for path in run_dir.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "acceptance.json"}
    }
    hash_valid = all(
        (run_dir / row["path"]).is_file()
        and (run_dir / row["path"]).stat().st_size == row["bytes"]
        and sha256(run_dir / row["path"]) == row["sha256"]
        for row in manifest["files"]
    )
    gates = {
        "pinned_clean_source": protocol["upstream"]["commit"] == SOURCE_COMMIT
        and environment["source_commit"] == SOURCE_COMMIT
        and environment["source_clean"],
        "shared_history_seed": seed.get("complete") is True
        and seed.get("personas") == 25
        and seed.get("step") == 0
        and seed.get("history", {}).get("whispers") == 248
        and seed.get("history", {}).get("thought_nodes") == 248,
        "exact_three_arm_shape": set(statuses) == set(ARMS)
        and all(status.get("complete") for status in statuses.values())
        and all(status.get("target_steps") == 17_280 for status in statuses.values())
        and all(len(status.get("checkpoints", [])) == 48 for status in statuses.values()),
        "exact_two_virtual_days": all(meta.get("step") == 17_280 for meta in metas.values())
        and all(meta.get("curr_time") == "February 15, 2023, 00:00:00" for meta in metas.values())
        and all(meta.get("sec_per_step") == 10 for meta in metas.values())
        and all(len(meta.get("persona_names", [])) == 25 for meta in metas.values()),
        "complete_movement_streams": all(count == 17_280 for count in movement_counts.values()),
        "complete_memory_streams": all(
            len({row["persona"] for row in rows}) == 25 and len(rows) > 248
            for rows in memory_rows.values()
        ),
        "custom_goal_applied": "climate-resilience workshop"
        in scratch["custom_goal"]["Isabella Rodriguez"]["currently"]
        and "Valentine's Day party"
        in scratch["baseline"]["Isabella Rodriguez"]["currently"],
        "reflection_ablation_effective": no_reflection_memory.get("new_thoughts_with_evidence") == 0,
        "provider_receipts_real_and_complete": len(provider_rows) > 0
        and not any(not row.get("success") for row in provider_rows)
        and len(provider_ids) == len(set(provider_ids))
        and all(provider_ids)
        and provider_models["qwen3.7-flash"] > 0
        and provider_models["text-embedding-v4"] > 0
        and all(positive_provider_usage(row) for row in provider_rows),
        "action_arena_compatibility_bounded": compatibility_receipts_valid
        and len(compatibility_rows) > 0
        and all(compatibility_correction_valid(row) for row in compatibility_rows),
        "deterministic_analysis_complete": set(analysis.get("arms", {})) == set(ARMS)
        and all(
            analysis["arms"][arm]["simulation"]["steps"] == 17_280 for arm in ARMS
        ),
        "blind_plausibility_judgments": judge_summary.get("judgments") == 25
        and len(judge_rows) == 25
        and all(row.get("success") for row in judge_rows)
        and len(judge_ids) == len(set(judge_ids)) == 25
        and all(judge_ids),
        "manifest_complete_and_valid": manifest_paths == actual_paths and hash_valid,
        "credential_scan_clean": not any(
            contains_secret(path)
            for path in run_dir.rglob("*")
            if path.is_file()
        ),
    }
    acceptance = {
        "schema_version": 1,
        "experiment": "10-7",
        "run_id": run_dir.name,
        "passed": all(gates.values()),
        "gates": gates,
        "counts": {
            "arms": len(ARMS),
            "personas_per_arm": 25,
            "steps_per_arm": 17_280,
            "provider_receipts": len(provider_rows),
            "provider_response_ids": len(provider_ids),
            "action_arena_compatibility_corrections": len(compatibility_rows),
            "judge_response_ids": len(judge_ids),
            "movement_rows": movement_counts,
            "memory_rows": {arm: len(rows) for arm, rows in memory_rows.items()},
            "manifest_files": len(manifest["files"]),
        },
        "results": {
            "baseline_event_diffusion": analysis["arms"]["baseline"]["seeded_event_diffusion"],
            "custom_event_diffusion": analysis["arms"]["custom_goal"]["seeded_event_diffusion"],
            "election_diffusion": {
                arm: analysis["arms"][arm]["election_diffusion"] for arm in ARMS
            },
            "plausibility": judge_summary,
        },
    }
    (run_dir / "acceptance.json").write_text(
        json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(acceptance, indent=2, ensure_ascii=False))
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
