#!/usr/bin/env python3
"""Add complete 6-3 rubric evidence to saved 6-4/6-11 case checkpoints."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict

from experiment import EVAL_DIR, UserMemoryEvaluationFramework
from evaluator import LLMEvaluator


REQUIRED_DIMENSIONS = {"precision", "recall", "reasoning", "proactivity"}


def enrich_case(path: Path, evaluator_type: str, model: str, test_cases_dir: Path) -> Dict[str, Any]:
    framework = UserMemoryEvaluationFramework(str(test_cases_dir))
    evaluator = LLMEvaluator(evaluator_type, model=model)
    payload = json.loads(path.read_text(encoding="utf-8"))
    updated = 0
    errors = []
    for row in payload.get("records", []):
        if row.get("status") != "ok":
            continue
        if set(row.get("rubric_details", {})) == REQUIRED_DIMENSIONS and row.get("hallucination_detail"):
            continue
        test_case = framework.get_test_case(row["test_id"])
        result = evaluator.evaluate(test_case, row["answer"])
        if set(result.dimensions) != REQUIRED_DIMENSIONS or result.hallucination is None:
            errors.append({"system": row["system"], "reason": result.reasoning})
            continue
        row["reward"] = result.reward
        row["success"] = bool(result.passed)
        row["rubric_dimensions"] = {name: value.score for name, value in result.dimensions.items()}
        row["rubric_details"] = {
            name: value.model_dump(mode="json") for name, value in result.dimensions.items()
        }
        row["hallucination_veto"] = result.veto_applied
        row["hallucination_detail"] = result.hallucination.model_dump(mode="json")
        row["evaluation_reasoning"] = result.reasoning
        row["evaluation_suggestions"] = result.suggestions
        updated += 1
    if not errors:
        payload["rubric_enrichment"] = {
            "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evaluator": evaluator_type,
            "model": model,
            "records_updated": updated,
            "all_ok_records_have_full_rubric": all(
                row.get("status") != "ok"
                or (
                    set(row.get("rubric_details", {})) == REQUIRED_DIMENSIONS
                    and row.get("hallucination_detail") is not None
                )
                for row in payload.get("records", [])
            ),
        }
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    return {"path": str(path), "updated": updated, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint_dir", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--evaluator", default="kimi")
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.checkpoint_dir.glob("*.json"))
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(enrich_case, path, args.evaluator, args.model, EVAL_DIR / "test_cases"): path
            for path in paths
        }
        for index, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            print(f"[{index}/{len(paths)}] {Path(result['path']).stem}: +{result['updated']} rubric records, errors={len(result['errors'])}")
    report = {
        "schema_version": "1.0",
        "experiment": "6-3 rubric enrichment",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoint_dir": str(args.checkpoint_dir),
        "checkpoint_count": len(paths),
        "records_updated": sum(row["updated"] for row in results),
        "errors": [error for row in results for error in row["errors"]],
        "complete": not any(row["errors"] for row in results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote enrichment audit to {args.output}; complete={report['complete']}")
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
