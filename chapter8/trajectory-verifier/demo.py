"""Run Experiment 8-1 without an API key."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from calibration import calibration_report
from verifier import TrajectoryVerifier, diagnostic_utility, scalar_baseline


ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 8-1 trajectory verifier")
    parser.add_argument("--judge", choices=("heuristic", "llm"), default="heuristic")
    parser.add_argument("--model", help="real LLM model; defaults to LLM_MODEL or gpt-5.6")
    args = parser.parse_args()
    trajectories = json.loads((ROOT / "sample_trajectories.json").read_text(encoding="utf-8"))
    if args.judge == "llm":
        from llm_judge import OpenAIQualityJudge
        verifier = TrajectoryVerifier(quality_judge=OpenAIQualityJudge(args.model))
    else:
        verifier = TrajectoryVerifier()
    reports = [verifier.evaluate(item) for item in trajectories]

    print(f"Experiment 8-1: three-layer customer-service trajectory verifier (judge={args.judge})\n")
    for report in reports:
        failed = [
            item["dimension"] for item in report["dimensions"] if item["verdict"] == "fail"
        ]
        print(f"{report['trajectory_id']:<24} score={report['overall_score']:.3f} "
              f"decision={report['release_recommendation']:<16} failures={failed or ['none']}")

    scalar = scalar_baseline(reports[1])
    print("\nScalar baseline:", scalar)
    print("Multidimensional diagnostic utility:", diagnostic_utility(reports[1]))
    print("\nCalibration:")
    print(json.dumps(calibration_report(trajectories, reports), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
