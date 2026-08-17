#!/usr/bin/env python3
"""Re-judge only incomplete saved 7-3 rubric records without mutating 7-4.

The source campaign remains immutable.  Each supplemental judgment records the
source record identity and answer hash so the full 7-3 validator can join it
without confusing it with a newly executed memory-system trajectory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
EVAL_DIR = HERE.parents[1] / "chapter3" / "user-memory-evaluation"
sys.path.insert(0, str(EVAL_DIR))

from evaluator import LLMEvaluator  # noqa: E402
from framework import UserMemoryEvaluationFramework  # noqa: E402


REQUIRED_DIMENSIONS = {"precision", "recall", "reasoning", "proactivity"}


def answer_hash(answer: str) -> str:
    return hashlib.sha256(answer.encode("utf-8")).hexdigest()


def complete_rubric(row: dict) -> bool:
    dimensions = row.get("rubric_details") or {}
    hallucination = row.get("hallucination_detail")
    return (
        set(dimensions) == REQUIRED_DIMENSIONS
        and isinstance(hallucination, dict)
        and "detected" in hallucination
        and all(
            isinstance(detail, dict)
            and bool(detail.get("reasoning"))
            and bool(detail.get("evidence") or detail.get("boundary_case"))
            for detail in dimensions.values()
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=HERE / "results" / "full_7_4_60_cases_costed.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE / "results" / "full_7_3_missing_rubric_supplement.json",
    )
    parser.add_argument("--evaluator", default="kimi", choices=["kimi", "openai"])
    parser.add_argument("--model", default="kimi-k2.5")
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    missing = [row for row in source.get("records", []) if not complete_rubric(row)]
    framework = UserMemoryEvaluationFramework(str(EVAL_DIR / "test_cases"))
    judge = LLMEvaluator(args.evaluator, model=args.model)
    supplements = []
    for row in missing:
        test_case = framework.get_test_case(row["test_id"])
        result = judge.evaluate(test_case, row["answer"])
        supplements.append({
            "test_id": row["test_id"],
            "system": row["system"],
            "layer": row["layer"],
            "answer_sha256": answer_hash(row["answer"]),
            "provider": args.evaluator,
            "model": args.model,
            "evaluation": result.model_dump(mode="json"),
        })
        print(f"Re-judged {row['test_id']} / {row['system']}")

    complete = all(
        set(item["evaluation"].get("dimensions", {})) == REQUIRED_DIMENSIONS
        and item["evaluation"].get("hallucination") is not None
        and all(
            detail.get("reasoning") and (detail.get("evidence") or detail.get("boundary_case"))
            for detail in item["evaluation"]["dimensions"].values()
        )
        for item in supplements
    )
    report = {
        "schema_version": "1.0",
        "experiment": "7-3",
        "purpose": "supplement incomplete rubric evidence only; source trajectories are unchanged",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(args.source),
        "missing_records_detected": len(missing),
        "supplements": supplements,
        "status": "complete" if complete else "incomplete",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "supplements": len(supplements),
        "output": str(args.output),
    }))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
