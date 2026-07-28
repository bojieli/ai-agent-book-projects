"""Run the deterministic reference agent or evaluate external structured predictions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent import DeterministicReportingAgent
from evaluator import evaluate, expected_by_task, load_json
from reporting_tools import ReportingEnvironment


ROOT = Path(__file__).parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions",
        help="Evaluate an external agent's JSON predictions instead of the reference agent.",
    )
    parser.add_argument("--output", help="Optionally save predictions and scores as JSON.")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=float(os.getenv("PUBLIC_HEALTH_EVAL_TOLERANCE", "0.01")),
        help="Absolute tolerance for numeric answers (default: 0.01).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    expected = expected_by_task(ROOT / "expected_answers.json")

    if args.predictions:
        predictions = load_json(args.predictions)
    else:
        tasks = load_json(ROOT / "tasks.json")
        environment = ReportingEnvironment(ROOT / "data" / "synthetic_reports.csv")
        agent = DeterministicReportingAgent(environment, expected)
        predictions = [agent.run(task) for task in tasks]

    report = evaluate(predictions, expected, tolerance=args.tolerance)
    for task in report["tasks"]:
        print(f"{task['task_id']:<30} {task['score']}/{task['max_score']}")
    print("-" * 36)
    print(f"TOTAL{'':<25} {report['score']}/{report['max_score']}")

    if args.output:
        payload = {"predictions": predictions, "evaluation": report}
        Path(args.output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
