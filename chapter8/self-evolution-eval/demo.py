"""Run Experiment 8-6 with a reference or real LLM-backed agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent import OpenAILongitudinalAgent, ReferenceAgent
from harness import LongitudinalEvaluator


ROOT = Path(__file__).parent


def load_tasks():
    return json.loads((ROOT / "dataset.json").read_text(encoding="utf-8"))["tasks"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 8-6: longitudinal continual-evolution evaluation")
    parser.add_argument("--profile", choices=("evolving", "append_only", "static", "llm", "all"), default="all")
    parser.add_argument("--model", help="model for --profile llm; defaults to LLM_MODEL or gpt-5.6")
    parser.add_argument("--output", help="optional JSON report path")
    args = parser.parse_args()

    profiles = ("evolving", "append_only", "static") if args.profile == "all" else (args.profile,)
    reports = []
    for profile in profiles:
        agent = OpenAILongitudinalAgent(args.model) if profile == "llm" else ReferenceAgent(profile)
        reports.append(LongitudinalEvaluator().run(agent, load_tasks()))

    print("Experiment 8-6: does the Agent keep evolving?\n")
    print(f"{'profile':<14} {'learn':>7} {'transfer':>9} {'change':>8} {'retain':>8} "
          f"{'safety':>8} {'neg-xfer':>9} {'tokens':>8} {'storage':>9}")
    for report in reports:
        phases = report["phase_accuracy"]
        print(
            f"{report['profile']:<14} {phases['learning']:>7.3f} {phases['transfer']:>9.3f} "
            f"{phases['change']:>8.3f} {report['retention_rate']:>8.3f} "
            f"{report['safety_rubric_pass_rate']:>8.3f} {report['negative_transfer_rate']:>9.3f} "
            f"{report['cost']['tokens']:>8} {report['cost']['storage_bytes']:>9}"
        )
    evolving = next((item for item in reports if item["profile"] == "evolving"), None)
    if evolving:
        print("\nEvolving-agent learning curve:")
        print(" -> ".join(
            f"{point['task_id']}:{point['cumulative_accuracy']:.2f}"
            for point in evolving["learning_curve"]
        ))
        print("tasks after change signal to recover:", evolving["adaptation"]["tasks_after_change_signal_to_recover"])

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
