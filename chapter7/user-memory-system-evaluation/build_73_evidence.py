#!/usr/bin/env python3
"""Derive canonical Experiment 7-3 evidence from the completed 7-4 campaign.

The completed 7-4 report ran the Experiment 7-3 judge on every one of its
60 cases and three memory systems.  This validator creates a small, auditable
index without changing, adding, or re-judging any paid API trajectory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_DIMENSIONS = {"precision", "recall", "reasoning", "proactivity"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).with_name("results") / "full_7_4_60_cases_costed.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("results") / "full_7_3_structured_rubric_evidence.json",
    )
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    records = source.get("records", [])
    valid = []
    errors = []
    by_layer_system = defaultdict(lambda: Counter(records=0, passed=0, vetoes=0))
    for index, row in enumerate(records):
        dimensions = row.get("rubric_details") or {}
        numeric = row.get("rubric_dimensions") or {}
        hallucination = row.get("hallucination_detail")
        problems = []
        if row.get("status") != "ok":
            problems.append(f"status={row.get('status')!r}")
        if set(dimensions) != REQUIRED_DIMENSIONS:
            problems.append(f"rubric_details={sorted(dimensions)}")
        if set(numeric) != REQUIRED_DIMENSIONS:
            problems.append(f"rubric_dimensions={sorted(numeric)}")
        if any(not 1 <= int(value) <= 4 for value in numeric.values()):
            problems.append("rubric score outside 1..4")
        if not isinstance(hallucination, dict) or "detected" not in hallucination:
            problems.append("missing hallucination verdict")
        for name, detail in dimensions.items():
            # A concise direct answer can legitimately have no affirmative
            # proactivity evidence.  In that boundary case the judge must name
            # the applied boundary explicitly instead of inventing evidence.
            if (
                not isinstance(detail, dict)
                or not detail.get("reasoning")
                or not (detail.get("evidence") or detail.get("boundary_case"))
            ):
                problems.append(f"{name} lacks reasoning and evidence/boundary")
        if problems:
            errors.append({
                "record_index": index,
                "test_id": row.get("test_id"),
                "system": row.get("system"),
                "problems": problems,
            })
            continue
        valid.append(row)
        bucket = by_layer_system[(row["layer"], row["system"])]
        bucket["records"] += 1
        bucket["passed"] += int(bool(row.get("success")))
        bucket["vetoes"] += int(bool(row.get("hallucination_veto")))

    distinct_cases = sorted({row.get("test_id") for row in valid})
    systems = sorted({row.get("system") for row in valid})
    layers = sorted({row.get("layer") for row in valid})
    complete = (
        not errors
        and len(records) == 180
        and len(valid) == 180
        and len(distinct_cases) == 60
        and len(systems) == 3
        and layers == ["layer1", "layer2", "layer3"]
        and all(counter["records"] == 20 for counter in by_layer_system.values())
        and len(by_layer_system) == 9
    )
    report = {
        "schema_version": "1.0",
        "experiment": "7-3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_lineage": {
            "source_file": str(args.source),
            "source_sha256": sha256(args.source),
            "source_experiment": source.get("experiment"),
            "source_generated_at_utc": source.get("generated_at_utc"),
            "transformation": (
                "Validation/index only: no API records, answers, scores, or verdicts were added, "
                "removed, or changed."
            ),
        },
        "rubric_contract": {
            "dimensions": sorted(REQUIRED_DIMENSIONS),
            "scale": "1..4 with concrete reasoning and cited evidence",
            "hallucination": "independent hard veto",
        },
        "run_scope": {
            "distinct_test_cases": len(distinct_cases),
            "layers": layers,
            "systems": systems,
            "records_expected": 180,
            "records_validated": len(valid),
            "all_60_cases_covered": len(distinct_cases) == 60,
            "validation_scope": "full" if complete else "incomplete",
        },
        "summary": [
            {"layer": layer, "system": system, **dict(counter)}
            for (layer, system), counter in sorted(by_layer_system.items())
        ],
        "errors": errors,
        "status": "complete" if complete else "incomplete",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "records_validated": len(valid),
        "distinct_cases": len(distinct_cases),
        "errors": len(errors),
        "output": str(args.output),
    }, ensure_ascii=False))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
