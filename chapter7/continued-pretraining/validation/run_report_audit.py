#!/usr/bin/env python3
"""Build the canonical, checkpoint-free evidence package for Experiment 7-5.

The historical RTX 4090 run is retained as a raw terminal transcript in
``model_eval_results.md``.  This tool does not pretend to rerun that GPU job.
It extracts the fifteen saved generations, submits five stage-blind comparison
tasks to an independent judge, and binds the report, current reproduction
sources, frozen upstream revisions, receipts, findings, and limitations into a
content-hashed manifest.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
REPORT_PATH = EXPERIMENT_DIR / "model_eval_results.md"
RUNS_DIR = HERE / "runs"
LATEST_PATH = HERE / "latest.json"

DEFAULT_RUN_ID = "exp7-5-training-report-20260731-v1"
DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEFAULT_MODEL = "doubao-seed-1-6-250615"
BLIND_SEED = 750731
ENGLISH_RETENTION_TOLERANCE = 1.0

BASE_REVISION = "9ea1b83f5ced5663c5fa89c300fe59f9bdcd2b10"
WIKIPEDIA_REVISION = "b04c8d1ceb2f5cd4588862100d08de323dccfbaa"
ALPACA_REVISION = "f38ae19cf673363d74fab6217de46c1b9c3150d4"

TEST_RE = re.compile(r"^Test ([1-5]):\s*(.+)$")
BOX_RE = re.compile(r"^┌─ (BASELINE|PRETRAINED|FINETUNED) MODEL\b")
CLOSE_RE = re.compile(r"^└─+")
STAGES = ("baseline", "pretrained", "finetuned")
LABELS = ("A", "B", "C")

PROMPTS = {
    1: {
        "language": "korean",
        "task": "Write the opening of a Korean Wikipedia article about artificial intelligence.",
    },
    2: {
        "language": "english",
        "task": "Write the opening of an English Wikipedia article about artificial intelligence.",
    },
    3: {
        "language": "korean",
        "task": "한국의 전통 음식인 김치에 대해 설명하세요.",
    },
    4: {
        "language": "korean",
        "task": "대한민국의 수도인 서울에 대해 간단히 소개해주세요.",
    },
    5: {
        "language": "english",
        "task": "Explain Thanksgiving turkey, a traditional American food.",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_retained_outputs(report_path: Path = REPORT_PATH) -> dict[str, Any]:
    """Extract the five-by-three raw comparison matrix from the saved report."""

    lines = report_path.read_text(encoding="utf-8").splitlines()
    tests: dict[int, dict[str, Any]] = {}
    current_test: int | None = None
    current_stage: str | None = None
    body: list[str] = []

    for line in lines:
        test_match = TEST_RE.match(line)
        if test_match:
            current_test = int(test_match.group(1))
            if current_test in tests:
                raise ValueError(f"duplicate raw Test {current_test}")
            tests[current_test] = {
                "test_id": current_test,
                "name": test_match.group(2).strip(),
                "language": PROMPTS[current_test]["language"],
                "task": PROMPTS[current_test]["task"],
                "outputs": {},
            }
            continue

        box_match = BOX_RE.match(line)
        if box_match:
            if current_test is None:
                raise ValueError("model output box appeared before a raw Test heading")
            if current_stage is not None:
                raise ValueError("nested model output boxes")
            current_stage = box_match.group(1).lower()
            body = []
            continue

        if current_stage is None:
            continue

        if CLOSE_RE.match(line):
            output = "\n".join(body).strip()
            if not output:
                raise ValueError(f"empty {current_stage} output in Test {current_test}")
            outputs = tests[current_test]["outputs"]
            if current_stage in outputs:
                raise ValueError(f"duplicate {current_stage} output in Test {current_test}")
            outputs[current_stage] = output
            current_stage = None
            body = []
            continue

        if line == "│":
            body.append("")
        elif line.startswith("│ "):
            body.append(line[2:])
        elif line.startswith("│"):
            body.append(line[1:].lstrip())
        else:
            # The historical terminal capture wrapped a few long lines without
            # repeating the box prefix. Preserve those bytes as output text.
            body.append(line)

    if current_stage is not None:
        raise ValueError("unterminated model output box")
    if set(tests) != set(PROMPTS):
        raise ValueError(f"expected Tests 1-5, found {sorted(tests)}")

    for test_id, test in tests.items():
        if set(test["outputs"]) != set(STAGES):
            raise ValueError(
                f"Test {test_id} expected stages {STAGES}, found {sorted(test['outputs'])}"
            )

    ordered = [tests[test_id] for test_id in sorted(tests)]
    return {
        "schema_version": "exp7-5-retained-outputs-v1",
        "source_report": str(REPORT_PATH.relative_to(REPO_ROOT)),
        "source_report_sha256": sha256_file(report_path),
        "test_count": len(ordered),
        "output_count": sum(len(test["outputs"]) for test in ordered),
        "tests": ordered,
    }


def blind_mapping(test_id: int) -> dict[str, str]:
    stages = list(STAGES)
    random.Random(BLIND_SEED + test_id).shuffle(stages)
    return dict(zip(LABELS, stages, strict=True))


def judge_payload(test: dict[str, Any], mapping: dict[str, str], model: str) -> dict[str, Any]:
    candidates = {
        label: test["outputs"][stage]
        for label, stage in mapping.items()
    }
    rubric = {
        "language_fluency": "0 unreadable; 3 understandable with defects; 5 native-quality and coherent",
        "instruction_following": "0 ignores the task; 3 partly satisfies it; 5 directly and fully satisfies it",
        "factuality": "0 dominated by falsehoods; 3 mixed/minor errors; 5 accurate with no material error",
    }
    expected_shape = {
        "test_id": test["test_id"],
        "language": test["language"],
        "candidates": {
            label: {
                "language_fluency": "number 0-5",
                "instruction_following": "number 0-5",
                "factuality": "number 0-5",
                "factual_errors": ["specific error, empty only if none"],
                "rationale": "short evidence-based explanation",
            }
            for label in LABELS
        },
        "ranking": ["best label", "middle label", "worst label"],
    }
    user_content = {
        "test_id": test["test_id"],
        "language": test["language"],
        "task": test["task"],
        "rubric": rubric,
        "candidates": candidates,
        "required_json_shape": expected_shape,
    }
    return {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an independent bilingual Korean/English evaluator. "
                    "The candidates are deliberately anonymous; do not infer model identity or training stage. "
                    "Score only the supplied text. Identify concrete factual errors, especially invented food "
                    "ingredients or preparation claims. Return one JSON object only, with every requested field."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(user_content, ensure_ascii=False, sort_keys=True),
            },
        ],
    }


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("judge content must decode to an object")
    return parsed


def validate_judgment(judgment: dict[str, Any], test: dict[str, Any]) -> None:
    if judgment.get("test_id") != test["test_id"]:
        raise ValueError("judge returned the wrong test_id")
    if judgment.get("language") != test["language"]:
        raise ValueError("judge returned the wrong language")
    candidates = judgment.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != set(LABELS):
        raise ValueError("judge must score exactly candidates A, B, and C")
    for label in LABELS:
        row = candidates[label]
        if not isinstance(row, dict):
            raise ValueError(f"candidate {label} score must be an object")
        for metric in ("language_fluency", "instruction_following", "factuality"):
            score = row.get(metric)
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 5:
                raise ValueError(f"candidate {label} has invalid {metric}: {score!r}")
        errors = row.get("factual_errors")
        if not isinstance(errors, list) or not all(isinstance(item, str) for item in errors):
            raise ValueError(f"candidate {label} factual_errors must be a list of strings")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            raise ValueError(f"candidate {label} rationale is missing")
    ranking = judgment.get("ranking")
    if not isinstance(ranking, list) or set(ranking) != set(LABELS) or len(ranking) != 3:
        raise ValueError("judge ranking must contain A, B, and C exactly once")


def call_judge(
    test: dict[str, Any],
    *,
    endpoint: str,
    model: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    mapping = blind_mapping(test["test_id"])
    payload = judge_payload(test, mapping, model)
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read()
            http_status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"judge HTTP {exc.code}: {body[:500]}") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    raw_response = json.loads(response_body)
    try:
        content = raw_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("judge response has no choices[0].message.content") from exc
    judgment = extract_json_object(content)
    validate_judgment(judgment, test)

    response_id = raw_response.get("id")
    usage = raw_response.get("usage")
    if not isinstance(response_id, str) or not response_id:
        raise ValueError("judge response has no response ID")
    if not isinstance(usage, dict) or not isinstance(usage.get("total_tokens"), int):
        raise ValueError("judge response has no complete usage object")

    return {
        "test_id": test["test_id"],
        "provider": "ark",
        "endpoint": endpoint,
        "credential_env": "ARK_API_KEY",
        "blind_seed": BLIND_SEED,
        "blind_map": mapping,
        "request": payload,
        "http_status": http_status,
        "response": raw_response,
        "response_id": response_id,
        "usage": usage,
        "latency_ms": latency_ms,
        "judgment": judgment,
    }


def reproduction_contract() -> dict[str, Any]:
    pin_note = (
        "This immutable revision is the frozen reproduction contract selected on 2026-07-31. "
        "The historical run did not retain its resolved upstream commit, so this is not claimed "
        "to be the exact historical revision."
    )
    return {
        "schema_version": "exp7-5-reproduction-contract-v1",
        "experiment": "7-5",
        "historical_evidence_boundary": {
            "historical_training_executed": True,
            "raw_three_stage_evaluation_retained": True,
            "historical_upstream_revisions_retained": False,
            "historical_checkpoint_hashes_retained": False,
            "claim": (
                "The retained terminal report proves a three-stage evaluation ran on the reported RTX 4090 "
                "software stack. It does not prove the byte identity of the historical adapters or upstream data."
            ),
        },
        "upstream_revisions": {
            "base_model": {
                "repository": "unsloth/mistral-7b-v0.3",
                "revision": BASE_REVISION,
                "note": pin_note,
            },
            "continued_pretraining_dataset": {
                "repository": "wikimedia/wikipedia",
                "configuration": "20231101.ko",
                "revision": WIKIPEDIA_REVISION,
                "note": pin_note,
            },
            "instruction_dataset": {
                "repository": "FreedomIntelligence/alpaca-gpt4-korean",
                "revision": ALPACA_REVISION,
                "note": pin_note,
            },
        },
        "training": {
            "model_loading": {"max_sequence_length": 2048, "load_in_4bit": True},
            "lora": {
                "rank": 128,
                "alpha": 32,
                "dropout": 0,
                "bias": "none",
                "use_rslora": True,
                "random_state": 3407,
                "gradient_checkpointing": "unsloth",
                "target_modules": [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                    "embed_tokens",
                    "lm_head",
                ],
            },
            "continued_pretraining": {
                "dataset_fraction": 0.05,
                "epochs": 1,
                "max_steps": -1,
                "batch_size": 2,
                "gradient_accumulation_steps": 8,
                "learning_rate": 5e-5,
                "embedding_learning_rate": 1e-5,
                "warmup_steps": 10,
                "warmup_ratio": 0.1,
                "optimizer": "adamw_8bit",
                "weight_decay": 0.01,
                "scheduler": "linear",
                "trainer_seed": 42,
                "dataset_split_seed": "not explicitly recorded by the historical script",
            },
            "instruction_sft": {
                "epochs": 2,
                "max_steps": -1,
                "batch_size": 2,
                "gradient_accumulation_steps": 8,
                "learning_rate": 5e-5,
                "embedding_learning_rate": 1e-5,
                "warmup_steps": 10,
                "warmup_ratio": 0.1,
                "optimizer": "adamw_8bit",
                "weight_decay": 0.0,
                "scheduler": "linear",
                "trainer_seed": 42,
            },
        },
        "evaluation": {
            "stages": list(STAGES),
            "test_count": 5,
            "output_count": 15,
            "max_new_tokens": 150,
            "temperature": 0.3,
            "do_sample": True,
            "historical_generation_seed": "not retained",
        },
        "historical_environment_from_report": {
            "gpu": "NVIDIA GeForce RTX 4090",
            "gpu_memory_gb": 23.647,
            "platform": "Linux",
            "torch": "2.8.0+cu128",
            "cuda_compute_capability": "8.9",
            "cuda_toolkit": "12.8",
            "unsloth": "2025.10.4",
            "transformers": "4.56.2",
            "triton": "3.4.0",
            "xformers": "0.0.32.post2",
        },
        "checkpoint_policy": {
            "distributed_with_book": False,
            "acceptance_artifact": False,
            "required_artifact": "reproducible evidence-backed training report",
            "reason": "Training adapters are intentionally local and are not distributed to readers.",
        },
    }


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4)


def summarize(
    retained: dict[str, Any], receipts: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    by_test = {test["test_id"]: test for test in retained["tests"]}
    stage_rows: dict[int, dict[str, dict[str, Any]]] = {}
    for receipt in receipts:
        reverse = {label: stage for label, stage in receipt["blind_map"].items()}
        stage_rows[receipt["test_id"]] = {
            reverse[label]: score
            for label, score in receipt["judgment"]["candidates"].items()
        }

    metrics = ("language_fluency", "instruction_following", "factuality")
    stage_averages: dict[str, dict[str, Any]] = {}
    for stage in STAGES:
        korean_rows = [
            stage_rows[test_id][stage]
            for test_id in (1, 3, 4)
        ]
        english_rows = [
            stage_rows[test_id][stage]
            for test_id in (2, 5)
        ]
        stage_averages[stage] = {
            "korean": {
                metric: mean([float(row[metric]) for row in korean_rows])
                for metric in metrics
            },
            "english": {
                metric: mean([float(row[metric]) for row in english_rows])
                for metric in metrics
            },
        }
        stage_averages[stage]["korean"]["overall"] = mean(
            [float(row[metric]) for row in korean_rows for metric in metrics]
        )
        stage_averages[stage]["english"]["overall"] = mean(
            [float(row[metric]) for row in english_rows for metric in metrics]
        )

    baseline_korean = stage_averages["baseline"]["korean"]["overall"]
    final_korean = stage_averages["finetuned"]["korean"]["overall"]
    baseline_english = stage_averages["baseline"]["english"]["overall"]
    final_english = stage_averages["finetuned"]["english"]["overall"]
    english_drop = round(baseline_english - final_english, 4)
    kimchi_errors = stage_rows[3]["finetuned"]["factual_errors"]

    findings = {
        "korean_gain_observed": final_korean > baseline_korean,
        "korean_gain": round(final_korean - baseline_korean, 4),
        "english_retention_tolerance": ENGLISH_RETENTION_TOLERANCE,
        "english_drop": english_drop,
        "english_retention_within_tolerance": english_drop <= ENGLISH_RETENTION_TOLERANCE,
        "kimchi_factual_failure_observed": bool(kimchi_errors),
        "kimchi_finetuned_factual_errors": kimchi_errors,
    }
    execution_gates = {
        "raw_report_hashed": bool(retained["source_report_sha256"]),
        "exactly_five_tests": retained["test_count"] == 5,
        "exactly_fifteen_outputs": retained["output_count"] == 15,
        "all_three_stages_retained": all(
            set(test["outputs"]) == set(STAGES) for test in retained["tests"]
        ),
        "five_independent_blind_judgments": len(receipts) == 5,
        "judge_response_ids_usage_and_latency_retained": all(
            receipt["response_id"]
            and receipt["usage"].get("total_tokens", 0) > 0
            and receipt["latency_ms"] > 0
            for receipt in receipts
        ),
        "training_and_evaluation_sources_declared": True,
        "immutable_future_reproduction_revisions_frozen": all(
            contract["upstream_revisions"][key]["revision"]
            for key in (
                "base_model",
                "continued_pretraining_dataset",
                "instruction_dataset",
            )
        ),
        "historical_revision_boundary_explicit": (
            contract["historical_evidence_boundary"]["historical_upstream_revisions_retained"]
            is False
        ),
        "checkpoints_not_an_acceptance_artifact": (
            contract["checkpoint_policy"]["acceptance_artifact"] is False
        ),
        # Scientific outcomes are reported, not promoted into evidence-completeness
        # gates. A real negative result still completes the prescribed comparison.
        "korean_gain_comparison_completed": isinstance(findings["korean_gain"], float),
        "english_retention_comparison_completed": isinstance(findings["english_drop"], float),
        "kimchi_failure_explicitly_reported": findings["kimchi_factual_failure_observed"],
    }
    passed = all(execution_gates.values())
    return {
        "schema_version": "exp7-5-summary-v1",
        "experiment": "7-5",
        "status": "passed" if passed else "failed",
        "judge": {
            "provider": "ark",
            "model": receipts[0]["request"]["model"],
            "calls": len(receipts),
            "response_ids": [receipt["response_id"] for receipt in receipts],
            "total_tokens": sum(receipt["usage"]["total_tokens"] for receipt in receipts),
            "total_latency_ms": round(sum(receipt["latency_ms"] for receipt in receipts), 3),
            "blind_seed": BLIND_SEED,
        },
        "stage_averages": stage_averages,
        "per_test_stage_scores": stage_rows,
        "scientific_findings": findings,
        "acceptance": {**execution_gates, "passed": passed},
        "limitations": [
            "The historical adapters/checkpoints are intentionally not distributed and were not re-created.",
            "The exact historical upstream revisions and generation RNG seed were not retained.",
            "The frozen upstream revisions are a future reproduction contract, not historical provenance.",
            "The retained evaluation has five prompts and one sampled generation per stage/prompt.",
        ],
        "test_names": {str(test_id): by_test[test_id]["name"] for test_id in sorted(by_test)},
    }


def render_report(summary: dict[str, Any]) -> str:
    averages = summary["stage_averages"]
    findings = summary["scientific_findings"]
    rows = []
    for stage in STAGES:
        rows.append(
            f"| {stage} | {averages[stage]['korean']['overall']:.4f} | "
            f"{averages[stage]['english']['overall']:.4f} |"
        )
    kimchi = "; ".join(findings["kimchi_finetuned_factual_errors"])
    return "\n".join(
        [
            "# Experiment 7-5 retained-training-report audit",
            "",
            "## Result",
            "",
            f"Status: **{summary['status']}**. The historical RTX 4090 report contains all five "
            "prompts across the baseline, continued-pretrained, and instruction-tuned stages. "
            "An independent stage-blind ARK judge scored the exact 15 retained outputs.",
            "",
            "| Stage | Korean mean (0-5) | English mean (0-5) |",
            "| --- | ---: | ---: |",
            *rows,
            "",
            f"Observed Korean gain, final minus baseline: **{findings['korean_gain']:+.4f}**.",
            f"Observed English drop, baseline minus final: **{findings['english_drop']:+.4f}** "
            f"(declared tolerance: {findings['english_retention_tolerance']:.1f}).",
            (
                "The final English score is within the declared tolerance."
                if findings["english_retention_within_tolerance"]
                else "The final English score is outside the declared tolerance; the historical retention "
                "claim is not supported by this blind audit."
            ),
            "",
            "## Material negative result",
            "",
            "The final model's Korean is more fluent, but the kimchi answer remains factually unsafe. "
            f"The blind judge identified: {kimchi}",
            "",
            "## Provenance boundary",
            "",
            "The raw terminal report records the historical GPU/software identity and generated text, "
            "but not adapter hashes, the exact resolved upstream commits, or the sampling seed. The "
            "immutable Hugging Face revisions in `reproduction_contract.json` were selected on "
            "2026-07-31 for future reproduction and are not represented as the historical revisions.",
            "",
            "Checkpoints are intentionally local and are not an acceptance artifact. The accepted "
            "book artifact is this reproducible, evidence-backed training report.",
            "",
        ]
    )


def input_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def artifact_record(path: Path, run_dir: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(run_dir)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_manifest(run_id: str, run_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    inputs = [
        input_record(REPORT_PATH),
        input_record(EXPERIMENT_DIR / "continued-pretrain.py"),
        input_record(EXPERIMENT_DIR / "compare_models.py"),
        input_record(EXPERIMENT_DIR / "evaluate_model.py"),
        input_record(HERE / "run_report_audit.py"),
        input_record(HERE / "validate_evidence.py"),
    ]
    artifact_paths = [
        run_dir / "retained_outputs.json",
        run_dir / "reproduction_contract.json",
        run_dir / "judge_receipts.json",
        run_dir / "summary.json",
        run_dir / "report.md",
    ]
    return {
        "schema_version": "exp7-5-manifest-v1",
        "experiment": "7-5",
        "run_id": run_id,
        "created_at": utc_now(),
        "status": summary["status"],
        "run_dir": str(run_dir.relative_to(EXPERIMENT_DIR)),
        "inputs": inputs,
        "artifacts": [artifact_record(path, run_dir) for path in artifact_paths],
        "acceptance": summary["acceptance"],
        "checkpoint_policy": "not distributed; not an acceptance artifact",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--endpoint", default=os.getenv("ARK_BASE_URL", DEFAULT_ENDPOINT))
    parser.add_argument("--model", default=os.getenv("ARK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-key-env", default="ARK_API_KEY")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument(
        "--refresh-manifest",
        action="store_true",
        help="Rehash an existing run after pre-commit source-only corrections; makes no provider call.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        raise SystemExit("run ID may contain only letters, digits, dot, underscore, and hyphen")

    run_dir = RUNS_DIR / args.run_id
    if args.refresh_manifest:
        if not run_dir.is_dir():
            raise SystemExit(f"cannot refresh missing run: {run_dir}")
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        manifest = build_manifest(args.run_id, run_dir, summary)
        write_json(run_dir / "manifest.json", manifest)
        latest = {
            "schema_version": "exp7-5-latest-v1",
            "experiment": "7-5",
            "run_id": args.run_id,
            "status": summary["status"],
            "run_dir": str(run_dir.relative_to(EXPERIMENT_DIR)),
            "manifest_sha256": sha256_file(run_dir / "manifest.json"),
        }
        write_json(LATEST_PATH, latest)
        print(json.dumps(latest, indent=2, sort_keys=True))
        return 0
    if run_dir.exists():
        raise SystemExit(f"refusing to overwrite existing run: {run_dir}")
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"{args.api_key_env} is required for the independent judge")

    retained = parse_retained_outputs()
    if not 1 <= args.concurrency <= 5:
        raise SystemExit("concurrency must be between 1 and 5")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        receipts = list(
            executor.map(
                lambda test: call_judge(
                    test,
                    endpoint=args.endpoint,
                    model=args.model,
                    api_key=api_key,
                    timeout=args.timeout,
                ),
                retained["tests"],
            )
        )
    contract = reproduction_contract()
    summary = summarize(retained, receipts, contract)
    if summary["status"] != "passed":
        failed = [key for key, value in summary["acceptance"].items() if value is False]
        raise SystemExit(f"acceptance failed; no canonical run written: {failed}")

    run_dir.mkdir(parents=True)
    write_json(run_dir / "retained_outputs.json", retained)
    write_json(run_dir / "reproduction_contract.json", contract)
    write_json(
        run_dir / "judge_receipts.json",
        {
            "schema_version": "exp7-5-judge-receipts-v1",
            "experiment": "7-5",
            "credential_headers_retained": False,
            "calls": receipts,
        },
    )
    write_json(run_dir / "summary.json", summary)
    (run_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    manifest = build_manifest(args.run_id, run_dir, summary)
    write_json(run_dir / "manifest.json", manifest)
    latest = {
        "schema_version": "exp7-5-latest-v1",
        "experiment": "7-5",
        "run_id": args.run_id,
        "status": summary["status"],
        "run_dir": str(run_dir.relative_to(EXPERIMENT_DIR)),
        "manifest_sha256": sha256_file(run_dir / "manifest.json"),
    }
    write_json(LATEST_PATH, latest)
    print(json.dumps(latest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
