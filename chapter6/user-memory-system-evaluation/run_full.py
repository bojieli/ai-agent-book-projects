#!/usr/bin/env python3
"""Restart-safe bounded-parallel runner for the full 60-case experiments."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from experiment import (
    EVAL_DIR,
    HERE,
    RunRecord,
    UserMemoryEvaluationFramework,
    execution_config_fingerprint,
    load_config,
    reprice_legacy_64_records,
    save_report,
    validate_readiness,
)


REQUIRED_RUBRIC_DIMENSIONS = {"precision", "recall", "reasoning", "proactivity"}


Cell = Tuple[str, ...]


def valid_checkpoint(
    path: Path,
    test_id: str,
    experiment: str,
    expected_records: int,
    required_ok_cells: Optional[Set[Cell]] = None,
    expected_cells: Optional[Set[Cell]] = None,
    expected_config_fingerprint: Optional[str] = None,
) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    scope = data.get("run_scope", {})
    records = data.get("records", [])
    if not (
        data.get("experiment") == experiment
        and scope.get("requested_test_ids") == [test_id]
        and len(records) == expected_records
    ):
        return False
    if expected_config_fingerprint is not None:
        try:
            observed_fingerprint = execution_config_fingerprint(
                data["configuration"], experiment
            )
        except (KeyError, TypeError, ValueError):
            return False
        if observed_fingerprint != expected_config_fingerprint:
            return False
    observed_cells: List[Cell] = []
    for row in records:
        if row.get("test_id") != test_id or row.get("experiment") != experiment:
            return False
        if row.get("status") == "ok":
            if set(row.get("rubric_details", {})) != REQUIRED_RUBRIC_DIMENSIONS:
                return False
            if row.get("hallucination_detail") is None:
                return False
        elif row.get("status") == "error":
            identity = (row.get("embedding"), row.get("reranker"), row.get("main_model"))
            if (
                experiment == "6-4"
                or not row.get("error")
                or required_ok_cells is None
                or identity in required_ok_cells
            ):
                return False
        else:
            return False
        if experiment == "6-11":
            observed_cells.append((row.get("embedding"), row.get("reranker"), row.get("main_model")))
        else:
            observed_cells.append((row.get("system"),))
    if expected_cells is not None and (
        len(observed_cells) != len(set(observed_cells)) or set(observed_cells) != expected_cells
    ):
        return False
    return True


def required_611_cells(config: Dict[str, Any], readiness: Optional[Dict[str, Any]]) -> Set[Cell]:
    """Return matrix cells whose backends passed preflight and must complete live."""
    matrix = config["experiment_6_11"]
    blocked = {
        (row["component"], row["name"])
        for row in (readiness or {}).get("probes", [])
        if row.get("status") == "error"
    }
    return {
        (embedding, reranker, main_model)
        for embedding in matrix["embeddings"]
        for reranker in matrix["rerankers"]
        for main_model in matrix["main_models"]
        if ("embedding", embedding) not in blocked
        and ("reranker", reranker) not in blocked
        and ("chat", main_model) not in blocked
    }


def run_case(
    experiment: str,
    config_path: Path,
    test_id: str,
    output: Path,
    readiness: Path | None = None,
) -> Dict[str, Any]:
    command = [
        sys.executable,
        str(HERE / "experiment.py"),
        experiment,
        "--config",
        str(config_path),
        "--test-id",
        test_id,
        "--output",
        str(output),
    ]
    if readiness:
        command.extend(["--readiness", str(readiness)])
    started = time.perf_counter()
    process = subprocess.run(command, cwd=HERE, capture_output=True, text=True)
    return {
        "test_id": test_id,
        "returncode": process.returncode,
        "elapsed_seconds": time.perf_counter() - started,
        "stdout": process.stdout[-2000:],
        "stderr": process.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", choices=["6-4", "6-11"])
    parser.add_argument("--config", type=Path, default=HERE / "default_config.yaml")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--readiness", type=Path)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    config_path = args.config.resolve()
    config = load_config(config_path)
    readiness_data = (
        json.loads(args.readiness.resolve().read_text(encoding="utf-8"))
        if args.readiness else None
    )
    if args.experiment == "6-11":
        if readiness_data is None:
            parser.error("exact Experiment 6-11 requires --readiness from probe_backends.py")
        readiness_errors = validate_readiness(config, readiness_data)
        if readiness_errors:
            parser.error("invalid readiness evidence: " + "; ".join(readiness_errors))
        config["execution_readiness"] = {
            "source_file": str(args.readiness.resolve()),
            "generated_at_utc": readiness_data.get("generated_at_utc"),
            "execution_config_fingerprint": readiness_data.get("execution_config_fingerprint"),
            "all_required_backends_ready": readiness_data.get("summary", {}).get("all_required_backends_ready"),
            "validated": True,
        }
        if not readiness_data.get("summary", {}).get("all_required_backends_ready"):
            parser.error(
                "exact Experiment 6-11 campaign is blocked: every required real backend "
                "must pass probe_backends.py before launch"
            )
    framework = UserMemoryEvaluationFramework(str(EVAL_DIR / "test_cases"))
    test_ids = [case.test_id for case in framework.list_test_cases()]
    if len(test_ids) != 60:
        parser.error(f"full run requires exactly 60 loaded cases, found {len(test_ids)}")

    if args.experiment == "6-4":
        expected_records = 3
        required_ok_cells = None
        all_matrix_cells = {
            ("advanced_json_cards",),
            ("rag",),
            ("hybrid",),
        }
    else:
        matrix = config["experiment_6_11"]
        shape = (len(matrix["embeddings"]), len(matrix["rerankers"]), len(matrix["main_models"]))
        if shape != (4, 3, 2):
            parser.error(f"exact Experiment 6-11 requires a 4x3x2 matrix, found {shape}")
        expected_records = len(matrix["embeddings"]) * len(matrix["rerankers"]) * len(matrix["main_models"])
        required_ok_cells = required_611_cells(config, readiness_data)
        all_matrix_cells = {
            (embedding, reranker, main_model)
            for embedding in matrix["embeddings"]
            for reranker in matrix["rerankers"]
            for main_model in matrix["main_models"]
        }
    checkpoint_dir = args.checkpoint_dir or (
        HERE / "results" / "checkpoints" / args.experiment.replace("-", "_") / config_path.stem
    )
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    expected_fingerprint = execution_config_fingerprint(config, args.experiment)

    pending = []
    for test_id in test_ids:
        path = checkpoint_dir / f"{test_id}.json"
        if not valid_checkpoint(
            path,
            test_id,
            args.experiment,
            expected_records,
            required_ok_cells,
            all_matrix_cells,
            expected_fingerprint,
        ):
            pending.append((test_id, path))
    print(f"Full {args.experiment}: {60 - len(pending)}/60 checkpoints reusable; {len(pending)} pending")

    failures: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                run_case,
                args.experiment,
                config_path,
                test_id,
                path,
                args.readiness.resolve() if args.readiness else None,
            ): test_id
            for test_id, path in pending
        }
        done = 60 - len(pending)
        for future in as_completed(futures):
            result = future.result()
            done += 1
            if result["returncode"]:
                failures.append(result)
                print(f"[{done}/60] ERROR {result['test_id']} ({result['elapsed_seconds']:.1f}s)")
            else:
                print(f"[{done}/60] OK {result['test_id']} ({result['elapsed_seconds']:.1f}s)")

    records: List[RunRecord] = []
    valid_case_ids = []
    for test_id in test_ids:
        path = checkpoint_dir / f"{test_id}.json"
        if not valid_checkpoint(
            path,
            test_id,
            args.experiment,
            expected_records,
            required_ok_cells,
            all_matrix_cells,
            expected_fingerprint,
        ):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        records.extend(RunRecord(**row) for row in data["records"])
        valid_case_ids.append(test_id)

    repricing = None
    if args.experiment == "6-4":
        repricing = reprice_legacy_64_records(records, config)
    save_report(args.output, args.experiment, records, config)
    merged = json.loads(args.output.read_text(encoding="utf-8"))
    merged["full_run_orchestration"] = {
        "workers": args.workers,
        "checkpoint_dir": str(checkpoint_dir),
        "expected_case_count": 60,
        "expected_records_per_case": expected_records,
        "valid_checkpoint_case_count": len(valid_case_ids),
        "missing_case_ids": sorted(set(test_ids) - set(valid_case_ids)),
        "subprocess_failures": failures,
        "execution_config_fingerprint": expected_fingerprint,
        "legacy_6_4_repricing": repricing,
    }
    # A complete experiment requires exact case/cell coverage, real successful
    # trajectories, explicit readiness (6-11), and zero unpriced usage.
    complete = bool(merged["completion"]["evidence_complete"]) and not failures
    if failures:
        merged["completion"]["evidence_complete"] = False
        merged["completion"]["trajectory_matrix_complete"] = False
        merged["completion"]["status"] = "incomplete"
        merged["completion"]["blockers"].append({
            "code": "subprocess_failures",
            "message": f"{len(failures)} case subprocesses failed",
        })
        merged["status"] = "incomplete"
    merged["run_scope"]["full_60_case_suite_completed"] = complete
    merged["run_scope"]["validation_scope"] = (
        "full" if complete else "incomplete-full-suite"
    )
    args.output.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Merged {len(records)} records from {len(valid_case_ids)}/60 cases into {args.output}; "
        f"full completion={complete}"
    )
    if complete:
        return 0
    return 2 if merged["completion"]["status"] == "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
