#!/usr/bin/env python3
"""Run and persist a live Experiment 6-3 structured-rubric validation."""

import argparse
import json
import time
from pathlib import Path

from evaluator import LLMEvaluator
from framework import UserMemoryEvaluationFramework


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-id", default="layer1_01_bank_account")
    parser.add_argument("--answer", required=True)
    parser.add_argument("--evaluator", default="kimi", choices=["kimi", "openai"])
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    framework = UserMemoryEvaluationFramework()
    test_case = framework.get_test_case(args.test_id)
    if test_case is None:
        parser.error(f"unknown test id: {args.test_id}")
    result = LLMEvaluator(args.evaluator, args.model).evaluate(test_case, args.answer)
    evidence = {
        "schema_version": "1.0",
        "experiment": "6-3",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "command": (
            f"python validate_rubric.py --test-id {args.test_id} --answer <redacted> "
            f"--evaluator {args.evaluator} --model {args.model} --output {args.output}"
        ),
        "run_scope": {
            "suite_case_count": len(framework.list_test_cases()),
            "requested_case_count": 1,
            "requested_test_ids": [args.test_id],
            "full_60_case_suite_completed": False,
            "validation_scope": "smoke",
        },
        "provider": args.evaluator,
        "model": args.model,
        "test_id": args.test_id,
        "agent_answer": args.answer,
        "evaluation": result.model_dump(mode="json"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote structured rubric evidence to {args.output}")
    return 0 if result.dimensions and result.hallucination is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
