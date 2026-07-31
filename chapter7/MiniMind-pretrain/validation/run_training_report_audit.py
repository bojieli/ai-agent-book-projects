#!/usr/bin/env python3
"""Build checkpoint-free retained training evidence for Experiment 7-3.

The book already contains the author's historical six-cell evaluation report:
original versus QK-Norm + Muon at pretrain, SFT, and DPO.  This program does
not pretend to rerun the GPU training job.  It extracts every saved generation,
submits a preregistered stage-balanced subset to an arm-blind external judge,
and binds the raw report, judge receipts, immutable future-reproduction source
and dataset revisions, environment lock, findings, and limitations into a
content-hashed evidence package.  Checkpoints are intentionally not published
and are not an acceptance artifact for book training experiments.
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
REPORT_PATH = EXPERIMENT_DIR / "README.md"
RUNS_DIR = HERE / "runs"
LATEST_PATH = HERE / "latest.json"

DEFAULT_RUN_ID = "exp7-3-training-report-20260731-v1"
DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEFAULT_MODEL = "doubao-seed-1-6-250615"
BLIND_SEED = 730731

SOURCE_REVISION = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"
DATASET_REVISION = "84983ed4dec7836d240577760c1d6be5d4cabcf9"
SOURCE_FILES = {
    "model/model_minimind.py": "2d33988711c704be6a22c4c61489b23106a2340a7cb8b97ebe3e40f30819cbb0",
    "model/tokenizer.json": "e489029175fb3f94b8211a120a72a2ee41a664db65b828d077c7bde989c845a9",
    "model/tokenizer_config.json": "190cc4738bac3b6f6b563376019c581b320fdb0260a03b9d5ab806296c8c6bb8",
    "dataset/lm_dataset.py": "213726b1781289548784220b2b2db48fe97d84f3b67ac0cd70186cbbcb7b5d2c",
    "trainer/muon.py": "00c2c6a225edeb55433df0724c3c74f6ff98ac4b2cc73c4aafcff686824f6267",
    "trainer/train_pretrain.py": "ddd122645a9f1043bc8dac69a81ac51d2df95df8745d25faed7963d38fedc328",
    "trainer/train_pretrain_muon.py": "fc83d07754ec3a8c156b6b8bfc0fd4326edecb72efabc5e08ae4ff5e3a7029bc",
    "trainer/train_full_sft.py": "a57422f1df80bf2867f31f3b4a646a92ac7f66729e98a3b32cd1ec4d6780cb8b",
    "trainer/train_full_sft_muon.py": "acd0b7db5b1d8b25d3c3103f92d68a7d381f9322a1b33bbec34be3d005930bad",
    "trainer/train_dpo.py": "97f2c31cc8bc21a777e2efcb5e2fa35a49e4e9e3698db120148f8a0b2f678449",
    "eval_model.py": "43930a4b55048a4a3ffa17eb78ae67d59582d639aa9365f0bbf41ba149128af8",
    "requirements.txt": "23f4cea09281765eec7cf03e28231425638e8e42580f418781fed166b75af968",
}
DATASET_FILES = {
    "pretrain_hq.jsonl": {
        "lfs_sha256": "9801b0d2210c61c2e4bc130f6dc4b3c870698a88d04af8f103c23dd5f0ce2440",
        "bytes": 1_669_750_047,
    },
    "sft_512.jsonl": {
        "lfs_sha256": "053b7d09574e48a86232e929211434ff9e5016c6ed13312e63687dd52edcbebf",
        "bytes": 7_531_517_862,
    },
    "dpo.jsonl": {
        "lfs_sha256": "ee934a8a455ccc99d1334d63e1254dd1d64f497fd067cfcbb71e3043f5b46768",
        "bytes": 53_653_322,
    },
}

ARMS = ("original", "qk_norm_muon")
STAGES = ("pretrain", "sft", "dpo")
EXPECTED_COUNTS = {
    ("original", "pretrain"): 7,
    ("original", "sft"): 8,
    ("original", "dpo"): 9,
    ("qk_norm_muon", "pretrain"): 7,
    ("qk_norm_muon", "sft"): 9,
    ("qk_norm_muon", "dpo"): 9,
}
SELECTED_CASES = (
    {"case_id": 1, "stage": "pretrain", "keyword": "highest mountain", "task": "Continue the prompt by identifying the highest mountain in the world accurately."},
    {"case_id": 2, "stage": "pretrain", "keyword": "carbon dioxide", "task": "Continue the prompt with an accurate statement about carbon dioxide in air."},
    {"case_id": 3, "stage": "sft", "keyword": "speed of light", "task": "Explain the physical concept of the speed of light in detail."},
    {"case_id": 4, "stage": "sft", "keyword": "how to understand chatgpt", "task": "Explain what ChatGPT is and how it works."},
    {"case_id": 5, "stage": "sft", "keyword": "history of the united states", "task": "Introduce the history of the United States."},
    {"case_id": 6, "stage": "dpo", "keyword": "speed of light", "task": "Explain the physical concept of the speed of light in detail."},
    {"case_id": 7, "stage": "dpo", "keyword": "how to understand chatgpt", "task": "Explain what ChatGPT is and how it works."},
    {"case_id": 8, "stage": "dpo", "keyword": "history of the united states", "task": "Introduce the history of the United States."},
)


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


def _terminal_transcript(section: str) -> tuple[str, str]:
    """Return the terminal header and prompt/output transcript from one cell.

    The historical Markdown has one stray closing fence immediately before the
    improved-SFT Lu Xun answer.  Treat fences as presentation markup rather
    than semantic delimiters so that the retained answer is not silently lost.
    """

    prompt_position = section.find("👶:")
    if prompt_position < 0:
        raise ValueError("model section has no user prompt marker")
    header = section[:prompt_position].replace("```", "").strip()
    transcript = section[prompt_position:]
    analysis = re.search(r"(?m)^\*\*[^\n]*Analysis[^\n]*\*\*:?\s*$", transcript)
    if analysis:
        transcript = transcript[: analysis.start()]
    transcript = re.sub(r"(?m)^```\s*$", "", transcript).strip()
    return header, transcript


def _parse_pairs(transcript: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"^👶:\s*(.*?)\n🤖️:\s*(.*?)(?=\n(?:\s*\n)*👶:|\Z)",
        flags=re.DOTALL | re.MULTILINE,
    )
    pairs = []
    for match in pattern.finditer(transcript):
        prompt = match.group(1).strip()
        output = match.group(2).strip()
        if not prompt or not output:
            raise ValueError("empty prompt or output in historical transcript")
        pairs.append({"prompt": prompt, "output": output})
    return pairs


def parse_retained_outputs(report_path: Path = REPORT_PATH) -> dict[str, Any]:
    """Extract all six historical LLM evaluation cells from the bilingual report."""

    text = report_path.read_text(encoding="utf-8")
    start = text.index("## Language Model Training Results Analysis")
    end = text.index("# Analysis of Vision-Language Model Training Results", start)
    llm_text = text[start:end]
    arm_markers = {
        "original": "## Without Muon Optimizer (Original Architecture)",
        "qk_norm_muon": "## With Muon Optimizer and QK Norm (Improved Architecture)",
    }
    cells: list[dict[str, Any]] = []
    for arm_index, arm in enumerate(ARMS):
        arm_start = llm_text.index(arm_markers[arm])
        arm_end = (
            llm_text.index(arm_markers[ARMS[arm_index + 1]], arm_start)
            if arm_index + 1 < len(ARMS)
            else len(llm_text)
        )
        arm_text = llm_text[arm_start:arm_end]
        for stage_index, stage in enumerate(STAGES):
            heading = {"pretrain": "### Pretrain Model", "sft": "### SFT Model", "dpo": "### DPO Model"}[stage]
            cell_start = arm_text.index(heading)
            next_positions = [
                arm_text.find(next_heading, cell_start + len(heading))
                for next_heading in ("### Pretrain Model", "### SFT Model", "### DPO Model")
            ]
            next_positions = [position for position in next_positions if position >= 0]
            cell_end = min(next_positions) if next_positions else len(arm_text)
            header, transcript = _terminal_transcript(arm_text[cell_start:cell_end])
            pairs = _parse_pairs(transcript)
            expected = EXPECTED_COUNTS[(arm, stage)]
            if len(pairs) != expected:
                raise ValueError(f"{arm}/{stage}: expected {expected} pairs, found {len(pairs)}")
            cells.append(
                {
                    "arm": arm,
                    "stage": stage,
                    "terminal_header": header,
                    "pair_count": len(pairs),
                    "pairs": pairs,
                }
            )

    return {
        "schema_version": "exp7-3-retained-outputs-v1",
        "experiment": "7-3",
        "source_report": str(report_path.relative_to(REPO_ROOT)),
        "source_report_sha256": sha256_file(report_path),
        "arms": list(ARMS),
        "stages": list(STAGES),
        "cell_count": len(cells),
        "output_count": sum(cell["pair_count"] for cell in cells),
        "cells": cells,
    }


def _find_pair(retained: dict[str, Any], arm: str, stage: str, keyword: str) -> dict[str, str]:
    cell = next(cell for cell in retained["cells"] if cell["arm"] == arm and cell["stage"] == stage)
    matches = [pair for pair in cell["pairs"] if keyword in pair["prompt"].lower()]
    if len(matches) != 1:
        raise ValueError(f"{arm}/{stage}/{keyword}: expected one prompt, found {len(matches)}")
    return matches[0]


def selected_comparisons(retained: dict[str, Any]) -> list[dict[str, Any]]:
    comparisons = []
    for case in SELECTED_CASES:
        rows = {
            arm: _find_pair(retained, arm, case["stage"], case["keyword"])
            for arm in ARMS
        }
        comparisons.append({**case, "arms": rows})
    return comparisons


def blind_mapping(case_id: int) -> dict[str, str]:
    arms = list(ARMS)
    random.Random(BLIND_SEED + case_id).shuffle(arms)
    return dict(zip(("A", "B"), arms, strict=True))


def judge_payload(comparison: dict[str, Any], mapping: dict[str, str], model: str) -> dict[str, Any]:
    candidates = {
        label: {
            "historical_prompt": comparison["arms"][arm]["prompt"],
            "historical_output": comparison["arms"][arm]["output"],
        }
        for label, arm in mapping.items()
    }
    required = {
        "case_id": comparison["case_id"],
        "candidates": {
            label: {
                "language_fluency": "number 0-5",
                "instruction_following": "number 0-5",
                "factuality": "number 0-5",
                "factual_errors": ["specific material errors; empty only if none"],
                "rationale": "brief evidence-based explanation",
            }
            for label in ("A", "B")
        },
        "winner": "A, B, or tie",
    }
    return {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an independent evaluator of two anonymous small-language-model outputs. "
                    "Do not infer model identity, architecture, optimizer, or training stage. Score only "
                    "the supplied text. Penalize hallucinations, unsafe medical specificity, repetition, "
                    "and non-answers. Return one JSON object with exactly the requested fields."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "case_id": comparison["case_id"],
                        "task": comparison["task"],
                        "rubric": {
                            "language_fluency": "0 unreadable; 3 understandable with defects; 5 coherent and natural",
                            "instruction_following": "0 non-answer; 3 partial; 5 directly and fully answers",
                            "factuality": "0 dominated by falsehoods; 3 mixed/minor errors; 5 no material error",
                        },
                        "candidates": candidates,
                        "required_json_shape": required,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
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


def validate_judgment(judgment: dict[str, Any], case_id: int) -> None:
    if str(judgment.get("case_id")) != str(case_id):
        raise ValueError(
            f"judge returned the wrong case_id: expected {case_id}, got {judgment.get('case_id')!r}"
        )
    candidates = judgment.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != {"A", "B"}:
        raise ValueError("judge must score A and B exactly")
    for label in ("A", "B"):
        row = candidates[label]
        if not isinstance(row, dict):
            raise ValueError(f"candidate {label} score must be an object")
        for metric in ("language_fluency", "instruction_following", "factuality"):
            score = row.get(metric)
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 5:
                raise ValueError(f"candidate {label} has invalid {metric}: {score!r}")
        if not isinstance(row.get("factual_errors"), list):
            raise ValueError(f"candidate {label} factual_errors must be a list")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            raise ValueError(f"candidate {label} rationale is missing")
    if judgment.get("winner") not in {"A", "B", "tie"}:
        raise ValueError("judge winner must be A, B, or tie")


def call_judge(
    comparison: dict[str, Any], *, endpoint: str, model: str, api_key: str, timeout: float
) -> dict[str, Any]:
    mapping = blind_mapping(comparison["case_id"])
    payload = judge_payload(comparison, mapping, model)
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read()
            http_status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"judge HTTP {exc.code}: {body[:500]}") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    raw_response = json.loads(raw_body)
    content = raw_response["choices"][0]["message"]["content"]
    judgment = extract_json_object(content)
    validate_judgment(judgment, comparison["case_id"])
    response_id = raw_response.get("id")
    usage = raw_response.get("usage")
    if not isinstance(response_id, str) or not response_id:
        raise ValueError("judge response has no response ID")
    if not isinstance(usage, dict) or not isinstance(usage.get("total_tokens"), int):
        raise ValueError("judge response has no complete usage object")
    return {
        "case_id": comparison["case_id"],
        "stage": comparison["stage"],
        "keyword": comparison["keyword"],
        "task": comparison["task"],
        "provider": "ark",
        "endpoint": endpoint,
        "credential_env": "ARK_API_KEY",
        "credential_headers_retained": False,
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
    return {
        "schema_version": "exp7-3-reproduction-contract-v1",
        "experiment": "7-3",
        "historical_evidence_boundary": {
            "historical_training_executed": True,
            "six_historical_evaluation_transcripts_retained": True,
            "historical_source_revision_retained": False,
            "historical_dataset_hashes_retained": False,
            "historical_checkpoint_hashes_retained": False,
            "historical_stepwise_training_logs_retained": False,
            "claim": (
                "The author's retained report supports that original and QK-Norm+Muon 104.03M models "
                "were evaluated after pretrain, SFT, and DPO. It does not establish byte identity of the "
                "historical checkpoints, datasets, source checkout, or every loss point."
            ),
        },
        "future_reproduction": {
            "source": {
                "repository": "bojieli/minimind",
                "revision": SOURCE_REVISION,
                "selected_at": "2026-07-31",
                "not_claimed_as_historical_revision": True,
                "file_sha256": SOURCE_FILES,
            },
            "dataset": {
                "repository": "jingyaogong/minimind_dataset",
                "revision": DATASET_REVISION,
                "selected_at": "2026-07-31",
                "not_claimed_as_historical_revision": True,
                "files": DATASET_FILES,
            },
            "commands": {
                "original_pretrain": "torchrun --nproc_per_node=8 trainer/train_pretrain.py --epochs 10 --hidden_size 768 --num_hidden_layers 16 --data_path dataset/pretrain_hq.jsonl --use_wandb",
                "improved_pretrain": "torchrun --nproc_per_node=8 trainer/train_pretrain_muon.py --epochs 10 --hidden_size 768 --num_hidden_layers 16 --data_path dataset/pretrain_hq.jsonl --use_wandb",
                "original_sft": "torchrun --nproc_per_node=8 trainer/train_full_sft.py --epochs 2 --hidden_size 768 --num_hidden_layers 16 --data_path dataset/sft_512.jsonl --use_wandb",
                "improved_sft": "torchrun --nproc_per_node=8 trainer/train_full_sft_muon.py --epochs 2 --hidden_size 768 --num_hidden_layers 16 --data_path dataset/sft_512.jsonl --use_wandb",
                "original_dpo": "torchrun --nproc_per_node=8 trainer/train_dpo.py --epochs 2 --hidden_size 768 --num_hidden_layers 16 --init_from out/full_sft_768.pth --data_path dataset/dpo.jsonl --use_wandb",
                "improved_dpo": "torchrun --nproc_per_node=8 trainer/train_dpo.py --epochs 2 --hidden_size 768 --num_hidden_layers 16 --init_from out/full_sft_muon_768.pth --data_path dataset/dpo.jsonl --use_wandb",
            },
            "environment": {
                "book_pyproject": "pyproject.toml",
                "book_lock": "uv.lock",
                "install": "uv sync --locked --python 3.12 --extra ch7 --extra dev",
                "boundary": (
                    "The book lock freezes a future software environment. The pinned upstream requirements "
                    "file itself is unversioned, and the future GPU/CUDA stack has not been exercised here."
                ),
            },
        },
        "model_and_training": {
            "reported_parameter_count_millions": 104.03,
            "architecture": {"hidden_size": 768, "layers": 16, "sequence_length": 512},
            "stages": list(STAGES),
            "arms": list(ARMS),
            "source_verified_mechanisms": {
                "qk_norm_before_rope": True,
                "muon_for_two_dimensional_non_embedding_weights": True,
                "adamw_for_embeddings_norms_and_lm_head": True,
                "dpo_uses_adamw_from_arm_specific_sft_checkpoint": True,
            },
            "reported_scalars_without_stepwise_logs": {
                "steps_to_loss_3_original": 36,
                "steps_to_loss_3_qk_norm_muon": 12,
                "final_loss_original": 2.0,
                "final_loss_qk_norm_muon": 1.7,
                "eight_rtx_4090_pretrain_hours": 6,
                "eight_rtx_4090_sft_hours": 8,
            },
        },
        "checkpoint_policy": {
            "distributed_with_book": False,
            "acceptance_artifact": False,
            "required_artifact": "reproducible evidence-backed training report",
            "reason": "Training checkpoints are intentionally not distributed to readers.",
        },
    }


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4)


def summarize(retained: dict[str, Any], receipts: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    metrics = ("language_fluency", "instruction_following", "factuality")
    rows: dict[int, dict[str, dict[str, Any]]] = {}
    wins = {"original": 0, "qk_norm_muon": 0, "tie": 0}
    for receipt in receipts:
        reverse = receipt["blind_map"]
        rows[receipt["case_id"]] = {
            reverse[label]: score for label, score in receipt["judgment"]["candidates"].items()
        }
        winner = receipt["judgment"]["winner"]
        wins["tie" if winner == "tie" else reverse[winner]] += 1

    arm_averages = {}
    stage_averages = {}
    for arm in ARMS:
        arm_scores = [rows[case["case_id"]][arm] for case in SELECTED_CASES]
        arm_averages[arm] = {
            metric: mean([float(row[metric]) for row in arm_scores]) for metric in metrics
        }
        arm_averages[arm]["overall"] = mean(
            [float(row[metric]) for row in arm_scores for metric in metrics]
        )
        stage_averages[arm] = {}
        for stage in STAGES:
            stage_scores = [
                rows[case["case_id"]][arm] for case in SELECTED_CASES if case["stage"] == stage
            ]
            stage_averages[arm][stage] = {
                metric: mean([float(row[metric]) for row in stage_scores]) for metric in metrics
            }
            stage_averages[arm][stage]["overall"] = mean(
                [float(row[metric]) for row in stage_scores for metric in metrics]
            )

    findings = {
        "blind_judge_overall_delta_qk_norm_muon_minus_original": round(
            arm_averages["qk_norm_muon"]["overall"] - arm_averages["original"]["overall"], 4
        ),
        "blind_judge_prefers_qk_norm_muon_overall": (
            arm_averages["qk_norm_muon"]["overall"] > arm_averages["original"]["overall"]
        ),
        "wins": wins,
        "reported_loss_comparison_retained_but_not_independently_recomputed": True,
    }
    acceptance = {
        "raw_historical_report_hashed": bool(retained["source_report_sha256"]),
        "all_six_arm_stage_cells_retained": retained["cell_count"] == 6,
        "all_expected_outputs_retained": retained["output_count"] == sum(EXPECTED_COUNTS.values()),
        "pretrain_sft_and_dpo_compared": set(retained["stages"]) == set(STAGES),
        "original_and_qk_norm_muon_compared": set(retained["arms"]) == set(ARMS),
        "eight_stage_balanced_blind_judgments": len(receipts) == len(SELECTED_CASES),
        "raw_judge_requests_responses_ids_usage_latency_retained": all(
            receipt["response_id"]
            and receipt["usage"].get("total_tokens", 0) > 0
            and receipt["latency_ms"] > 0
            for receipt in receipts
        ),
        "immutable_source_revision_and_file_hashes_frozen": bool(SOURCE_REVISION and SOURCE_FILES),
        "immutable_dataset_revision_lfs_hashes_and_sizes_frozen": bool(DATASET_REVISION and DATASET_FILES),
        "future_reproduction_commands_declared": len(contract["future_reproduction"]["commands"]) == 6,
        "historical_provenance_limitations_explicit": (
            contract["historical_evidence_boundary"]["historical_checkpoint_hashes_retained"] is False
            and contract["historical_evidence_boundary"]["historical_stepwise_training_logs_retained"] is False
        ),
        "reported_loss_claims_qualified": findings[
            "reported_loss_comparison_retained_but_not_independently_recomputed"
        ],
        "checkpoints_not_an_acceptance_artifact": (
            contract["checkpoint_policy"]["acceptance_artifact"] is False
        ),
    }
    passed = all(acceptance.values())
    return {
        "schema_version": "exp7-3-summary-v1",
        "experiment": "7-3",
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
        "retained": {
            "cells": retained["cell_count"],
            "outputs": retained["output_count"],
            "selected_comparisons": len(receipts),
        },
        "arm_averages": arm_averages,
        "stage_averages": stage_averages,
        "per_case_arm_scores": rows,
        "scientific_findings": findings,
        "acceptance": {**acceptance, "passed": passed},
        "limitations": [
            "Historical checkpoints are intentionally not distributed and were not recreated in this audit.",
            "The historical source revision, dataset byte identities, RNG state, and stepwise loss logs were not retained.",
            "Frozen source/data revisions and the book lock define a future reproduction contract, not historical provenance.",
            "The independent judge covers eight preregistered comparisons; all other retained outputs remain available for inspection.",
            "The historical outputs are English translations in a bilingual report, so translation may affect the judge scores.",
        ],
    }


def render_report(summary: dict[str, Any]) -> str:
    averages = summary["arm_averages"]
    findings = summary["scientific_findings"]
    return "\n".join(
        [
            "# Experiment 7-3 retained-training-report audit",
            "",
            "## Result",
            "",
            f"Status: **{summary['status']}**. The historical report retains "
            f"{summary['retained']['outputs']} outputs across the original and QK-Norm + Muon arms "
            "after pretrain, SFT, and DPO. Eight preregistered arm-blind comparisons were judged "
            "from raw retained text by an independent ARK model.",
            "",
            "| Arm | Fluency | Instruction | Factuality | Overall |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| Original | {averages['original']['language_fluency']:.4f} | "
            f"{averages['original']['instruction_following']:.4f} | "
            f"{averages['original']['factuality']:.4f} | {averages['original']['overall']:.4f} |",
            f"| QK-Norm + Muon | {averages['qk_norm_muon']['language_fluency']:.4f} | "
            f"{averages['qk_norm_muon']['instruction_following']:.4f} | "
            f"{averages['qk_norm_muon']['factuality']:.4f} | {averages['qk_norm_muon']['overall']:.4f} |",
            "",
            f"Observed blind-judge overall delta: **{findings['blind_judge_overall_delta_qk_norm_muon_minus_original']:+.4f}**. "
            f"Pairwise decisions: {findings['wins']}.",
            "",
            "The report's loss claims (3.0 reached at 36 versus 12 reported steps; final loss 2.0 "
            "versus 1.7) are retained as author-reported observations, not independently recomputed "
            "measurements, because the historical stepwise logs were not preserved.",
            "",
            "## Provenance and reproduction boundary",
            "",
            "`reproduction_contract.json` freezes the MiniMind source revision, hashes the relevant "
            "source files, freezes a dataset revision with the three Git-LFS object hashes and sizes, "
            "and records all six future reproduction commands. These pins were selected for future "
            "reproduction and are not represented as the exact historical checkout.",
            "",
            "Training checkpoints remain local by book policy and are not an acceptance artifact. "
            "The accepted artifact is this content-hashed training report, its raw retained outputs, "
            "raw independent-judge receipts, and explicit limitations.",
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
        input_record(REPO_ROOT / "pyproject.toml"),
        input_record(REPO_ROOT / "uv.lock"),
        input_record(HERE / "run_training_report_audit.py"),
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
        "schema_version": "exp7-3-manifest-v1",
        "experiment": "7-3",
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
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument(
        "--refresh-manifest",
        action="store_true",
        help="Rehash an existing run after source-only corrections; makes no provider call.",
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
        stored_retained = json.loads(
            (run_dir / "retained_outputs.json").read_text(encoding="utf-8")
        )
        current_retained = parse_retained_outputs()
        # Documentation around the raw transcripts may change, but a refresh
        # must never silently replace the generations that were judged.
        if stored_retained.get("cells") != current_retained.get("cells"):
            raise SystemExit(
                "refusing manifest refresh because retained historical outputs changed"
            )
        stored_retained["source_report_sha256"] = current_retained[
            "source_report_sha256"
        ]
        write_json(run_dir / "retained_outputs.json", stored_retained)
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        write_json(run_dir / "manifest.json", build_manifest(args.run_id, run_dir, summary))
        latest = {
            "schema_version": "exp7-3-latest-v1",
            "experiment": "7-3",
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
        raise SystemExit(f"missing required credential environment variable: {args.api_key_env}")

    retained = parse_retained_outputs()
    comparisons = selected_comparisons(retained)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            comparison["case_id"]: pool.submit(
                call_judge,
                comparison,
                endpoint=args.endpoint,
                model=args.model,
                api_key=api_key,
                timeout=args.timeout,
            )
            for comparison in comparisons
        }
        receipts = [futures[case_id].result() for case_id in sorted(futures)]

    contract = reproduction_contract()
    summary = summarize(retained, receipts, contract)
    run_dir.mkdir(parents=True)
    write_json(run_dir / "retained_outputs.json", retained)
    write_json(
        run_dir / "judge_receipts.json",
        {
            "schema_version": "exp7-3-judge-receipts-v1",
            "experiment": "7-3",
            "credential_headers_retained": False,
            "calls": receipts,
        },
    )
    write_json(run_dir / "reproduction_contract.json", contract)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    write_json(run_dir / "manifest.json", build_manifest(args.run_id, run_dir, summary))
    latest = {
        "schema_version": "exp7-3-latest-v1",
        "experiment": "7-3",
        "run_id": args.run_id,
        "status": summary["status"],
        "run_dir": str(run_dir.relative_to(EXPERIMENT_DIR)),
        "manifest_sha256": sha256_file(run_dir / "manifest.json"),
    }
    write_json(LATEST_PATH, latest)
    print(json.dumps(latest, indent=2, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
