"""Run the complete offline self-modification release flow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evolution import diagnose, generate_candidate, release_manifest, validate_candidate, write_candidate


ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 8-5 self-modification pipeline")
    parser.add_argument("--generator", choices=("deterministic", "llm"), default="deterministic")
    parser.add_argument("--model", help="real LLM model; defaults to LLM_MODEL or gpt-5.6")
    args = parser.parse_args()
    trajectories = json.loads((ROOT / "failure_trajectories.json").read_text(encoding="utf-8"))
    stable_path = ROOT / "stable" / "retry_policy.py"
    stable_source = stable_path.read_text(encoding="utf-8")

    diagnosis = diagnose(trajectories)
    if args.generator == "llm":
        from llm_generator import generate_with_openai
        candidate = generate_with_openai(stable_source, diagnosis, args.model)
    else:
        candidate = generate_candidate(stable_source, diagnosis)
    checks = validate_candidate(candidate["source"], trajectories)
    manifest = release_manifest(stable_source, candidate, diagnosis, checks)

    write_candidate(candidate["source"], ROOT / "output" / "candidate" / "retry_policy.py")
    (ROOT / "output" / "release_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Experiment 8-5: trajectory-triggered self-modification (generator={args.generator})\n")
    print("diagnosed target:", diagnosis["target"])
    print("source cases:", ", ".join(diagnosis["source_case_ids"]))
    print("\nCandidate diff:\n")
    print(candidate["diff"])
    print("checks:", checks)
    print("decision:", manifest["decision"])
    print("stable file unchanged:", stable_path.read_text(encoding="utf-8") == stable_source)
    print("rollback version:", manifest["rollback_version"])


if __name__ == "__main__":
    main()
