"""Offline demonstration of Experiment 8-2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experience_documents import build_documents, evaluate_retrieval_baselines, write_documents


ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Experiment 8-2 experience-document extraction")
    parser.add_argument("--extractor", choices=("fixture", "llm"), default="fixture")
    parser.add_argument("--model", help="real LLM model; defaults to LLM_MODEL or gpt-5.6")
    args = parser.parse_args()
    dataset = json.loads((ROOT / "sample_trajectories.json").read_text(encoding="utf-8"))
    records = dataset["learning_trajectories"]
    if args.extractor == "llm":
        from llm_extractor import OpenAIExperienceExtractor
        records = OpenAIExperienceExtractor(args.model).extract_all(records)
    documents = build_documents(records, validated_on="2026-07-24")
    output_paths = write_documents(documents, ROOT / "output" / "experience_documents")
    report = evaluate_retrieval_baselines(records, documents, dataset["transfer_cases"])

    print(f"Experiment 8-2: evaluated trajectories -> Markdown experience documents (extractor={args.extractor})\n")
    for document, path in zip(documents, output_paths):
        print(f"{document.task_family:<18} sources={len(document.sources)} "
              f"recommendations={len(document.recommended_strategies)} -> {path.relative_to(ROOT)}")
    print("\nThree-baseline transfer report:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
