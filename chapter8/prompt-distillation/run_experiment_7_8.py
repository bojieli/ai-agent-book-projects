#!/usr/bin/env python3
"""Run the manuscript's Experiment 7-8 with canonical, leakage-free evidence.

The campaign deliberately uses a small student so that *real parameter training*
can run on Apple Silicon.  It still preserves the experiment's causal contrast:

* teacher: long task prompt + a thinking model (Moonshot ``kimi-k3``);
* student: raw user text only + a non-thinking 135M model;
* data: disjoint public train/test splits with independent gold labels;
* evidence: provider response IDs/usage, adapter weights, hashes, held-out
  quality, actual wall-clock latency, tokenizer counts and provider cost.

No API key or credential value is ever written to disk.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


EXPERIMENT_ID = "7-8"
DATASET_ID = "papluca/language-identification"
DATASET_REVISION = "aa56583bf2bc52b0565770607d6fc3faebecf9e2"
STUDENT_MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct"
STUDENT_REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
TEACHER_MODEL = "kimi-k3"
TEACHER_BASE_URL = "https://api.moonshot.cn/v1"
TEACHER_KEY_ENV = "MOONSHOT_API_KEY"

# Dated native Kimi K3 pricing copied from the verified Chapter 6 campaign
# configuration.  We preserve both the native rate and the dated FX rate.
PRICING = {
    "input_per_million": 20.0,
    "cached_input_per_million": 2.0,
    "output_per_million": 100.0,
    "currency": "CNY",
    "source_url": "https://platform.kimi.com/docs/pricing/chat-k3.md",
    "as_of": "2026-07-29",
    "usd_per_currency_unit": 0.1477922077922078,
    "fx_source_url": "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
    "fx_as_of": "2026-07-29",
}

TARGET_LABELS = {"ar", "de", "el", "en", "es", "fr", "hi", "ru", "tr", "ur", "vi", "zh"}
VALID_LABELS = TARGET_LABELS | {"ot"}

LANGUAGE_CLASSIFICATION_PROMPT = """You are a precise language classifier.

Goal: Classify the language of the provided text into exactly one label:
ar (Arabic), de (German), el (Greek), en (English), es (Spanish), fr (French),
hi (Hindi), ru (Russian), tr (Turkish), ur (Urdu), vi (Vietnamese),
zh (Chinese), or ot (all other languages / unknown).

Rules:
1. Ignore URLs, email addresses, numbers, emoji, punctuation, and code syntax.
2. Use native script first. Distinguish Arabic from Urdu by Urdu-specific
   letters and words. Treat both Simplified and Traditional Chinese as zh.
3. For Latin scripts use vocabulary, function words, and diacritics together;
   do not decide from one proper noun.
4. Deliberate mixed-language text or a language outside the listed set is ot.
5. Very short text is ot unless the language signal is unambiguous.
6. Think through ambiguity before answering, but keep that reasoning private.

Text to classify:
{text}

The visible response must be exactly one line: Final Answer: xx
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def map_gold(source_label: str) -> str:
    return source_label if source_label in TARGET_LABELS else "ot"


def _stable_sample(rows: list[dict[str, str]], n: int, seed: int, split: str) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["labels"], []).append(row)
    selected: list[dict[str, str]] = []
    for source_label in sorted(grouped):
        candidates = sorted(
            grouped[source_label],
            key=lambda r: hashlib.sha256(f"{seed}:{split}:{source_label}:{r['text']}".encode()).hexdigest(),
        )
        for rank, row in enumerate(candidates[:n]):
            selected.append(
                {
                    "id": f"{split}-{source_label}-{rank:03d}",
                    "split": split,
                    "source_label": source_label,
                    "gold_label": map_gold(source_label),
                    "text": row["text"],
                }
            )
    return sorted(selected, key=lambda r: r["id"])


def prepare_benchmark(run_dir: Path, train_per_language: int, test_per_language: int, seed: int) -> dict[str, Any]:
    from datasets import load_dataset

    train_ds = load_dataset(DATASET_ID, revision=DATASET_REVISION, split="train")
    test_ds = load_dataset(DATASET_ID, revision=DATASET_REVISION, split="test")
    train = _stable_sample(list(train_ds), train_per_language, seed, "train")
    test = _stable_sample(list(test_ds), test_per_language, seed, "test")
    train_texts = {r["text"] for r in train}
    test_texts = {r["text"] for r in test}
    overlap = train_texts & test_texts
    if overlap:
        raise RuntimeError(f"train/test leakage detected: {len(overlap)} texts")
    write_jsonl(run_dir / "benchmark_train_gold.jsonl", train)
    write_jsonl(run_dir / "benchmark_test_gold.jsonl", test)
    provenance = {
        "dataset": DATASET_ID,
        "revision": DATASET_REVISION,
        "train_source_split": "train",
        "test_source_split": "test",
        "train_fingerprint": train_ds._fingerprint,
        "test_fingerprint": test_ds._fingerprint,
        "seed": seed,
        "train_per_source_language": train_per_language,
        "test_per_source_language": test_per_language,
        "train_rows": len(train),
        "test_rows": len(test),
        "train_unique_texts": len(train_texts),
        "test_unique_texts": len(test_texts),
        "exact_text_overlap": len(overlap),
        "train_rows_sha256": canonical_hash(train),
        "test_rows_sha256": canonical_hash(test),
    }
    write_json(run_dir / "dataset_provenance.json", provenance)
    return provenance


def parse_label(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    matches = re.findall(r"Final Answer:\s*([a-z]{2})", text, re.IGNORECASE)
    if matches and matches[-1].lower() in VALID_LABELS:
        return matches[-1].lower()
    stripped = text.strip().lower()
    return stripped if stripped in VALID_LABELS else None


def usage_cost(usage: dict[str, Any]) -> dict[str, float]:
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    details = usage.get("prompt_tokens_details") or {}
    cached = int(details.get("cached_tokens") or usage.get("cached_tokens") or 0)
    uncached = max(0, prompt - cached)
    cny = (
        uncached * PRICING["input_per_million"]
        + cached * PRICING["cached_input_per_million"]
        + completion * PRICING["output_per_million"]
    ) / 1_000_000
    return {"cny": cny, "usd": cny * PRICING["usd_per_currency_unit"]}


async def collect_teacher(run_dir: Path, concurrency: int, max_retries: int) -> dict[str, Any]:
    from openai import AsyncOpenAI

    key = os.getenv(TEACHER_KEY_ENV)
    if not key:
        raise RuntimeError(f"{TEACHER_KEY_ENV} is not configured")
    train = read_jsonl(run_dir / "benchmark_train_gold.jsonl")
    test = read_jsonl(run_dir / "benchmark_test_gold.jsonl")
    rows = train + test
    raw_path = run_dir / "teacher_receipts.jsonl"
    existing = {r["id"]: r for r in read_jsonl(raw_path)}
    client = AsyncOpenAI(api_key=key, base_url=TEACHER_BASE_URL, timeout=90)
    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()

    async def one(row: dict[str, Any]) -> dict[str, Any]:
        async with sem:
            error: Optional[str] = None
            for attempt in range(max_retries + 1):
                started = utc_now()
                t0 = time.perf_counter()
                try:
                    response = await client.chat.completions.create(
                        model=TEACHER_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": "Reason privately. The visible response must be exactly: Final Answer: xx",
                            },
                            {"role": "user", "content": LANGUAGE_CLASSIFICATION_PROMPT.format(text=row["text"])},
                        ],
                        max_tokens=256,
                        extra_body={"reasoning_effort": "low"},
                    )
                    latency = time.perf_counter() - t0
                    message = response.choices[0].message
                    content = message.content or ""
                    reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
                    usage = response.usage.model_dump() if response.usage else {}
                    record = {
                        **row,
                        "provider": "moonshot",
                        "base_url": TEACHER_BASE_URL,
                        "model_requested": TEACHER_MODEL,
                        "response_id": response.id,
                        "response_model": response.model,
                        "response_created": response.created,
                        "request_started_at": started,
                        "latency_seconds": latency,
                        "attempt": attempt,
                        "content": content,
                        "reasoning_content": reasoning,
                        "prediction": parse_label(content),
                        "usage": usage,
                        "calculated_cost": usage_cost(usage),
                        "request": {
                            "max_tokens": 256,
                            "reasoning_effort": "low",
                            "prompt_sha256": hashlib.sha256(
                                LANGUAGE_CLASSIFICATION_PROMPT.format(text=row["text"]).encode("utf-8")
                            ).hexdigest(),
                        },
                        "error": None,
                    }
                    async with lock:
                        with raw_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    return record
                except Exception as exc:  # noqa: BLE001
                    error = f"{type(exc).__name__}: {exc}"
            record = {**row, "provider": "moonshot", "model_requested": TEACHER_MODEL, "error": error}
            async with lock:
                with raw_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return record

    pending = [row for row in rows if row["id"] not in existing or existing[row["id"]].get("error")]
    if pending:
        results = await asyncio.gather(*(one(row) for row in pending))
        existing.update({r["id"]: r for r in results})
    ordered = [existing[row["id"]] for row in rows]
    write_jsonl(raw_path, ordered)

    accepted_train = [
        {
            "id": r["id"],
            "messages": [
                {"role": "user", "content": r["text"]},
                {"role": "assistant", "content": r["prediction"]},
            ],
            "teacher_response_id": r.get("response_id"),
            "gold_label": r["gold_label"],
        }
        for r in ordered
        if r["split"] == "train" and not r.get("error") and r.get("prediction") == r["gold_label"]
    ]
    write_jsonl(run_dir / "student_train.jsonl", accepted_train)

    def split_summary(split: str) -> dict[str, Any]:
        rs = [r for r in ordered if r["split"] == split]
        valid = [r for r in rs if not r.get("error") and r.get("prediction")]
        costs = [r.get("calculated_cost") or {} for r in valid]
        return {
            "rows": len(rs),
            "valid_receipts": len(valid),
            "unique_response_ids": len({r.get("response_id") for r in valid}),
            "correct": sum(r.get("prediction") == r["gold_label"] for r in valid),
            "gold_accuracy": sum(r.get("prediction") == r["gold_label"] for r in valid) / len(rs),
            "prompt_tokens": sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in valid),
            "completion_tokens": sum((r.get("usage") or {}).get("completion_tokens", 0) for r in valid),
            "latency_seconds_total": sum(r.get("latency_seconds", 0) for r in valid),
            "latency_seconds_mean": statistics.mean(r.get("latency_seconds", 0) for r in valid) if valid else None,
            "provider_cost_cny": sum(c.get("cny", 0) for c in costs),
            "provider_cost_usd": sum(c.get("usd", 0) for c in costs),
        }

    summary = {
        "teacher": {"provider": "moonshot", "model": TEACHER_MODEL, "pricing": PRICING},
        "train": split_summary("train"),
        "test": split_summary("test"),
        "accepted_student_train_rows": len(accepted_train),
    }
    write_json(run_dir / "teacher_summary.json", summary)
    return summary


@dataclass
class EncodedRow:
    input_ids: list[int]
    labels: list[int]


def _chat_template_ids(encoded: Any) -> list[int]:
    """Return one token-id list across Transformers 4.x and 5.x APIs."""
    if isinstance(encoded, dict) or hasattr(encoded, "keys"):
        encoded = encoded["input_ids"]
    if hasattr(encoded, "tolist"):
        encoded = encoded.tolist()
    if encoded and isinstance(encoded[0], list):
        if len(encoded) != 1:
            raise ValueError("expected one chat-template sequence")
        encoded = encoded[0]
    if not isinstance(encoded, list) or not all(isinstance(token, int) for token in encoded):
        raise TypeError("chat template did not return a one-dimensional integer token sequence")
    return encoded


def _local_device(torch: Any) -> Any:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _encode_sft(tokenizer: Any, messages: list[dict[str, str]], max_length: int) -> EncodedRow:
    prompt = messages[:-1]
    prompt_ids = _chat_template_ids(
        tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True)
    )
    full_ids = _chat_template_ids(
        tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False)
    )
    full_ids = full_ids[:max_length]
    labels = [-100] * min(len(prompt_ids), len(full_ids)) + full_ids[min(len(prompt_ids), len(full_ids)) :]
    return EncodedRow(input_ids=full_ids, labels=labels)


def train_student(run_dir: Path, epochs: int, batch_size: int, learning_rate: float, seed: int) -> dict[str, Any]:
    import torch
    from peft import LoraConfig, get_peft_model
    from torch.utils.data import DataLoader
    from transformers import AutoModelForCausalLM, AutoTokenizer

    random.seed(seed)
    torch.manual_seed(seed)
    device = _local_device(torch)
    tokenizer = AutoTokenizer.from_pretrained(STUDENT_MODEL, revision=STUDENT_REVISION)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    rows = read_jsonl(run_dir / "student_train.jsonl")
    if not rows:
        # A teacher campaign may be interrupted after individual receipts have
        # been durably appended but before its final derived files are written.
        # Rebuild the training view from successful, gold-verified real
        # receipts so the documented phase-resume boundary is actually usable.
        receipts = read_jsonl(run_dir / "teacher_receipts.jsonl")
        rows = [
            {
                "id": receipt["id"],
                "messages": [
                    {"role": "user", "content": receipt["text"]},
                    {"role": "assistant", "content": receipt["prediction"]},
                ],
                "teacher_response_id": receipt.get("response_id"),
                "gold_label": receipt["gold_label"],
            }
            for receipt in receipts
            if receipt.get("split") == "train"
            and not receipt.get("error")
            and receipt.get("response_id")
            and receipt.get("prediction") == receipt.get("gold_label")
        ]
        if rows:
            write_jsonl(run_dir / "student_train.jsonl", rows)
    if not rows:
        raise RuntimeError("no accepted teacher rows available for training")
    encoded = [_encode_sft(tokenizer, r["messages"], 192) for r in rows]

    def collate(items: list[EncodedRow]) -> dict[str, torch.Tensor]:
        length = max(len(x.input_ids) for x in items)
        input_ids, labels, masks = [], [], []
        for item in items:
            pad = length - len(item.input_ids)
            input_ids.append(item.input_ids + [tokenizer.pad_token_id] * pad)
            labels.append(item.labels + [-100] * pad)
            masks.append([1] * len(item.input_ids) + [0] * pad)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(masks, dtype=torch.long),
        }

    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(encoded, batch_size=batch_size, shuffle=True, collate_fn=collate, generator=generator)
    base = AutoModelForCausalLM.from_pretrained(
        STUDENT_MODEL,
        revision=STUDENT_REVISION,
        dtype=torch.bfloat16 if device.type == "cuda" else torch.float32,
    )
    config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.0,
        target_modules=["q_proj", "v_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base, config).to(device)
    model.train()
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=learning_rate)
    losses: list[float] = []
    started = utc_now()
    t0 = time.perf_counter()
    for epoch in range(epochs):
        for batch in loader:
            optimizer.zero_grad(set_to_none=True)
            batch = {k: v.to(device) for k, v in batch.items()}
            output = model(**batch)
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            optimizer.step()
            losses.append(float(output.loss.detach().cpu()))
    if device.type == "mps":
        torch.mps.synchronize()
    runtime = time.perf_counter() - t0
    adapter_dir = run_dir / "student_adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter_dir, safe_serialization=True)
    tokenizer.save_pretrained(adapter_dir)
    receipt = {
        "started_at": started,
        "finished_at": utc_now(),
        "runtime_seconds": runtime,
        "device": str(device),
        "torch_version": torch.__version__,
        "base_model": STUDENT_MODEL,
        "base_model_revision": STUDENT_REVISION,
        "training_rows": len(rows),
        "epochs": epochs,
        "batch_size": batch_size,
        "optimizer": "AdamW",
        "learning_rate": learning_rate,
        "lora": {"r": 16, "alpha": 32, "targets": ["q_proj", "v_proj"]},
        "trainable_parameters": sum(p.numel() for p in params),
        "total_parameters_with_adapter": sum(p.numel() for p in model.parameters()),
        "optimizer_steps": len(losses),
        "first_loss": losses[0],
        "final_loss": losses[-1],
        "mean_loss": statistics.mean(losses),
        "losses": losses,
    }
    write_json(run_dir / "training_receipt.json", receipt)
    del model, base
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()
    return receipt


def _sync(device: Any) -> None:
    import torch

    if device.type == "mps":
        torch.mps.synchronize()
    elif device.type == "cuda":
        torch.cuda.synchronize(device)


def summarize_retained_teacher_receipts(run_dir: Path) -> dict[str, Any]:
    """Summarize durable teacher receipts, including interrupted campaigns."""
    expected = read_jsonl(run_dir / "benchmark_train_gold.jsonl") + read_jsonl(
        run_dir / "benchmark_test_gold.jsonl"
    )
    expected_by_split = {
        split: [row for row in expected if row["split"] == split]
        for split in ("train", "test")
    }
    receipts = read_jsonl(run_dir / "teacher_receipts.jsonl")

    def split_summary(split: str) -> dict[str, Any]:
        expected_rows = expected_by_split[split]
        rs = [r for r in receipts if r.get("split") == split]
        valid = [r for r in rs if not r.get("error") and r.get("prediction")]
        costs = [r.get("calculated_cost") or {} for r in valid]
        correct = sum(r.get("prediction") == r.get("gold_label") for r in valid)
        return {
            "rows": len(expected_rows),
            "retained_receipts": len(rs),
            "coverage": len(valid) / len(expected_rows) if expected_rows else 0.0,
            "valid_receipts": len(valid),
            "unique_response_ids": len({r.get("response_id") for r in valid}),
            "correct": correct,
            # Missing calls do not silently disappear from the campaign score.
            "gold_accuracy": correct / len(expected_rows) if expected_rows else 0.0,
            "observed_gold_accuracy": correct / len(valid) if valid else 0.0,
            "prompt_tokens": sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in valid),
            "completion_tokens": sum((r.get("usage") or {}).get("completion_tokens", 0) for r in valid),
            "latency_seconds_total": sum(r.get("latency_seconds", 0) for r in valid),
            "latency_seconds_mean": statistics.mean(r.get("latency_seconds", 0) for r in valid) if valid else None,
            "provider_cost_cny": sum(c.get("cny", 0) for c in costs),
            "provider_cost_usd": sum(c.get("usd", 0) for c in costs),
        }

    summary = {
        "teacher": {"provider": "moonshot", "model": TEACHER_MODEL, "pricing": PRICING},
        "train": split_summary("train"),
        "test": split_summary("test"),
        "campaign_complete": len(receipts) == len(expected)
        and all(not r.get("error") and r.get("response_id") for r in receipts),
    }
    write_json(run_dir / "teacher_summary.json", summary)
    return summary


def evaluate_local_arm(run_dir: Path, arm: str) -> dict[str, Any]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = _local_device(torch)
    tokenizer = AutoTokenizer.from_pretrained(STUDENT_MODEL, revision=STUDENT_REVISION)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        STUDENT_MODEL,
        revision=STUDENT_REVISION,
        dtype=torch.bfloat16 if device.type == "cuda" else torch.float32,
    ).to(device)
    model = base if arm == "baseline" else PeftModel.from_pretrained(base, run_dir / "student_adapter").to(device)
    model.eval()
    rows = read_jsonl(run_dir / "benchmark_test_gold.jsonl")

    # Warmup is measured separately and excluded from reported case latency.
    warm = tokenizer.apply_chat_template(
        [{"role": "user", "content": "Hello world."}], tokenize=True, add_generation_prompt=True, return_tensors="pt"
    )
    if isinstance(warm, dict) or hasattr(warm, "keys"):
        warm = warm["input_ids"]
    warm = warm.to(device)
    with torch.no_grad():
        _ = model.generate(warm, max_new_tokens=4, do_sample=False, pad_token_id=tokenizer.eos_token_id)
    _sync(device)

    results: list[dict[str, Any]] = []
    for row in rows:
        ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": row["text"]}],
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        if isinstance(ids, dict) or hasattr(ids, "keys"):
            ids = ids["input_ids"]
        ids = ids.to(device)
        _sync(device)
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(
                ids,
                max_new_tokens=8,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        _sync(device)
        latency = time.perf_counter() - t0
        generated = out[0, ids.shape[1] :]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        pred = parse_label(text) or (text.lower() if text.lower() in VALID_LABELS else None)
        results.append(
            {
                "id": row["id"],
                "gold_label": row["gold_label"],
                "source_label": row["source_label"],
                "prediction": pred,
                "response": text,
                "correct": pred == row["gold_label"],
                "input_tokens": int(ids.shape[1]),
                "output_tokens": int(generated.shape[0]),
                "latency_seconds": latency,
            }
        )
    output_path = run_dir / f"student_{arm}_heldout.jsonl"
    write_jsonl(output_path, results)
    summary = {
        "arm": arm,
        "rows": len(results),
        "correct": sum(r["correct"] for r in results),
        "accuracy": sum(r["correct"] for r in results) / len(results),
        "parse_rate": sum(r["prediction"] is not None for r in results) / len(results),
        "input_tokens": sum(r["input_tokens"] for r in results),
        "output_tokens": sum(r["output_tokens"] for r in results),
        "latency_seconds_total": sum(r["latency_seconds"] for r in results),
        "latency_seconds_mean": statistics.mean(r["latency_seconds"] for r in results),
        "latency_seconds_median": statistics.median(r["latency_seconds"] for r in results),
        "provider_charge_usd": 0.0,
        "provider_charge_note": "Local inference made no provider API calls; electricity/hardware amortization is excluded.",
    }
    write_json(run_dir / f"student_{arm}_summary.json", summary)
    del model, base
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()
    return summary


def package_evidence(run_dir: Path, command: str) -> dict[str, Any]:
    teacher = summarize_retained_teacher_receipts(run_dir)
    baseline = json.loads((run_dir / "student_baseline_summary.json").read_text())
    trained = json.loads((run_dir / "student_trained_summary.json").read_text())
    train_rows = read_jsonl(run_dir / "benchmark_train_gold.jsonl")
    test_rows = read_jsonl(run_dir / "benchmark_test_gold.jsonl")
    train_ids = {r["text"] for r in train_rows}
    test_ids = {r["text"] for r in test_rows}
    teacher_test = [r for r in read_jsonl(run_dir / "teacher_receipts.jsonl") if r["split"] == "test"]
    trained_rows = {r["id"]: r for r in read_jsonl(run_dir / "student_trained_heldout.jsonl")}
    agreement = sum(
        trained_rows[r["id"]]["prediction"] == r.get("prediction")
        for r in teacher_test
        if r["id"] in trained_rows and r.get("prediction")
    ) / len(teacher_test)
    comparison = {
        "heldout_rows": len(test_rows),
        "train_test_exact_text_overlap": len(train_ids & test_ids),
        "teacher_gold_accuracy": teacher["test"]["gold_accuracy"],
        "baseline_gold_accuracy": baseline["accuracy"],
        "trained_gold_accuracy": trained["accuracy"],
        "trained_absolute_uplift": trained["accuracy"] - baseline["accuracy"],
        "trained_teacher_agreement": agreement,
        "teacher_mean_latency_seconds": teacher["test"]["latency_seconds_mean"],
        "trained_mean_latency_seconds": trained["latency_seconds_mean"],
        "latency_speedup": teacher["test"]["latency_seconds_mean"] / trained["latency_seconds_mean"],
        "teacher_input_tokens": teacher["test"]["prompt_tokens"],
        "trained_input_tokens": trained["input_tokens"],
        "input_token_reduction": 1 - trained["input_tokens"] / teacher["test"]["prompt_tokens"],
        "teacher_provider_cost_usd": teacher["test"]["provider_cost_usd"],
        "trained_provider_charge_usd": trained["provider_charge_usd"],
        "cost_scope_note": trained["provider_charge_note"],
    }
    write_json(run_dir / "comparison.json", comparison)
    required_files = [
        p
        for p in run_dir.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    ]
    artifact_hashes = {
        str(p.relative_to(run_dir)): {"sha256": sha256_file(p), "bytes": p.stat().st_size}
        for p in sorted(required_files)
    }
    receipts = read_jsonl(run_dir / "teacher_receipts.jsonl")
    gates = {
        "disjoint_heldout": len(train_ids & test_ids) == 0,
        "real_teacher_receipts": len(receipts) == len(train_rows) + len(test_rows)
        and len({r.get("response_id") for r in receipts}) == len(receipts),
        "real_parameter_training": (run_dir / "student_adapter" / "adapter_model.safetensors").exists(),
        "before_after_quality": trained["accuracy"] > baseline["accuracy"],
        "quality_near_teacher": trained["accuracy"] >= teacher["test"]["gold_accuracy"] - 0.15,
        "measured_latency": teacher["test"]["latency_seconds_mean"] > 0 and trained["latency_seconds_mean"] > 0,
        "measured_tokens": teacher["test"]["prompt_tokens"] > 0 and trained["input_tokens"] > 0,
        "dollar_accounting": teacher["test"]["provider_cost_usd"] > 0,
    }
    manifest = {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "status": "complete" if all(gates.values()) else "incomplete",
        "created_at": utc_now(),
        "command": command,
        "host": {"platform": sys.platform, "python": sys.version, "credential_env": TEACHER_KEY_ENV},
        "student": {"model": STUDENT_MODEL, "revision": STUDENT_REVISION},
        "teacher": {"model": TEACHER_MODEL, "base_url": TEACHER_BASE_URL, "pricing": PRICING},
        "gates": gates,
        "comparison": comparison,
        "artifacts": artifact_hashes,
        "credential_values_retained": False,
    }
    write_json(run_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run canonical Experiment 7-8")
    parser.add_argument("--run-dir", default="./validation/exp7-8-real")
    parser.add_argument("--phase", choices=["all", "prepare", "teacher", "train", "evaluate", "package"], default="all")
    parser.add_argument("--train-per-language", type=int, default=8)
    parser.add_argument("--test-per-language", type=int, default=4)
    parser.add_argument("--seed", type=int, default=78)
    parser.add_argument("--concurrency", type=int, default=12)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    phases = {args.phase} if args.phase != "all" else {"prepare", "teacher", "train", "evaluate", "package"}
    if "prepare" in phases:
        prepare_benchmark(run_dir, args.train_per_language, args.test_per_language, args.seed)
    if "teacher" in phases:
        asyncio.run(collect_teacher(run_dir, args.concurrency, args.max_retries))
    if "train" in phases:
        train_student(run_dir, args.epochs, args.batch_size, args.learning_rate, args.seed)
    if "evaluate" in phases:
        evaluate_local_arm(run_dir, "baseline")
        evaluate_local_arm(run_dir, "trained")
    if "package" in phases:
        command = " ".join([sys.executable, *sys.argv])
        manifest = package_evidence(run_dir, command)
        print(json.dumps({"run_dir": str(run_dir), "status": manifest["status"], "comparison": manifest["comparison"]}, indent=2))


if __name__ == "__main__":
    main()
