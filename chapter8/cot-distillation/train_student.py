#!/usr/bin/env python3
"""Train the Experiment 7-9 student on verified teacher CoT trajectories.

This is the parameter-update stage missing from the original collection-only
companion.  It deliberately has no mock training mode: a successful run writes
a real Hugging Face/PEFT checkpoint plus a provenance manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_verified_messages(path: Path) -> list[list[dict[str, str]]]:
    """Load only complete user/assistant rows with a non-empty final answer."""
    rows: list[list[dict[str, str]]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            messages = item.get("messages")
            if not isinstance(messages, list) or len(messages) != 2:
                raise ValueError(f"{path}:{line_number}: expected exactly two messages")
            if [m.get("role") for m in messages] != ["user", "assistant"]:
                raise ValueError(f"{path}:{line_number}: expected user then assistant")
            if not all(isinstance(m.get("content"), str) and m["content"].strip() for m in messages):
                raise ValueError(f"{path}:{line_number}: empty message content")
            if not re.search(r"Final Answer[:：]", messages[1]["content"], re.IGNORECASE):
                raise ValueError(f"{path}:{line_number}: assistant lacks verified Final Answer")
            rows.append(messages)
    if not rows:
        raise ValueError(f"{path}: no training samples")
    return rows


@dataclass
class EncodedExample:
    input_ids: list[int]
    labels: list[int]


def _chat_template_ids(encoded: Any) -> list[int]:
    """Normalize Transformers 4.x/5.x chat-template return values.

    Transformers 4.x returned a bare list from ``apply_chat_template`` when
    ``tokenize=True``.  Transformers 5.x returns a BatchEncoding containing
    both ``input_ids`` and ``attention_mask``.  Calling ``len`` or slicing the
    latter operates on mapping keys, which can make every assistant trajectory
    appear to have only two tokens and defeats the loss-mask safety check.
    """
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


def encode_messages(tokenizer: Any, messages: list[dict[str, str]], max_length: int) -> EncodedExample:
    """Mask user/prompt tokens and supervise only the teacher assistant trajectory."""
    prompt_ids = _chat_template_ids(
        tokenizer.apply_chat_template(messages[:1], tokenize=True, add_generation_prompt=True)
    )
    full_ids = _chat_template_ids(
        tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False)
    )
    if len(full_ids) > max_length:
        full_ids = full_ids[:max_length]
    prompt_length = min(len(prompt_ids), len(full_ids))
    labels = [-100] * prompt_length + full_ids[prompt_length:]
    if not any(label != -100 for label in labels):
        raise ValueError("max_length truncates the entire assistant response")
    return EncodedExample(input_ids=full_ids, labels=labels)


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Experiment 7-9: real student SFT on verified CoT trajectories",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train-data", type=Path, default=Path("data/sft_cot_distill_aime_kimi_k3.jsonl"))
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--output-dir", type=Path, default=Path("checkpoints/cot-student"))
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lora-rank", type=int, default=32, help="0 disables LoRA and updates all weights")
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--gradient-checkpointing", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="write dependency/GPU readiness evidence without training")
    parser.add_argument("--preflight-output", type=Path, default=Path("validation/student_sft_preflight.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_length <= 0 or args.batch_size <= 0 or args.gradient_accumulation <= 0:
        raise SystemExit("max-length, batch-size, and gradient-accumulation must be positive")
    messages = load_verified_messages(args.train_data)

    if args.preflight:
        dependencies = {
            name: importlib.util.find_spec(name) is not None
            for name in ("torch", "transformers", "accelerate", "peft")
        }
        dependency_versions = {
            name: importlib.metadata.version(name) if installed else None
            for name, installed in dependencies.items()
        }
        cuda_available = False
        gpu_names: list[str] = []
        torch_version = None
        trainer_stack_error = None
        if dependencies["torch"]:
            import torch
            torch_version = torch.__version__
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                gpu_names = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        try:
            from transformers import Trainer  # noqa: F401
        except Exception as exc:  # integration errors include incompatible peft/transformers versions
            trainer_stack_error = f"{type(exc).__name__}: {exc}"
        trainer_stack_importable = trainer_stack_error is None
        payload = {
            "schema_version": 1,
            "experiment": "7-9",
            "stage": "student_sft_preflight",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "ready": all(dependencies.values()) and trainer_stack_importable and cuda_available,
            "training_data": {
                "path": str(args.train_data.resolve()),
                "sha256": sha256(args.train_data.resolve()),
                "samples": len(messages),
            },
            "host": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "torch": torch_version,
                "cuda_available": cuda_available,
                "gpu_names": gpu_names,
            },
            "dependencies": dependencies,
            "dependency_versions": dependency_versions,
            "trainer_stack_importable": trainer_stack_importable,
            "trainer_stack_error": trainer_stack_error,
            "blockers": [
                *[f"missing Python dependency: {name}" for name, ok in dependencies.items() if not ok],
                *([] if trainer_stack_importable else ["transformers/peft trainer stack is not importable"]),
                *([] if cuda_available else ["no CUDA device available"]),
            ],
        }
        args.preflight_output.parent.mkdir(parents=True, exist_ok=True)
        args.preflight_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({"preflight": str(args.preflight_output), "ready": payload["ready"]}, ensure_ascii=False))
        return

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("PyTorch is missing. Install requirements.txt before training.") from exc
    if not torch.cuda.is_available():
        raise SystemExit(
            "Experiment 7-9 student SFT requires a CUDA host; this runner has no synthetic/CPU success fallback."
        )
    try:
        from torch.utils.data import Dataset
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
            set_seed,
        )
    except (ImportError, RuntimeError) as exc:
        raise SystemExit(
            f"The transformers/peft training stack is not importable: {type(exc).__name__}: {exc}"
        ) from exc

    set_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model, trust_remote_code=args.trust_remote_code
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encoded = [encode_messages(tokenizer, item, args.max_length) for item in messages]

    class CotDataset(Dataset):
        def __len__(self) -> int:
            return len(encoded)

        def __getitem__(self, index: int) -> dict[str, list[int]]:
            item = encoded[index]
            return {"input_ids": item.input_ids, "labels": item.labels}

    def collate(batch: list[dict[str, list[int]]]) -> dict[str, Any]:
        width = max(len(item["input_ids"]) for item in batch)
        ids, masks, labels = [], [], []
        for item in batch:
            padding = width - len(item["input_ids"])
            ids.append(item["input_ids"] + [tokenizer.pad_token_id] * padding)
            masks.append([1] * len(item["input_ids"]) + [0] * padding)
            labels.append(item["labels"] + [-100] * padding)
        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "attention_mask": torch.tensor(masks, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        trust_remote_code=args.trust_remote_code,
    )
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False
    if args.lora_rank:
        try:
            from peft import LoraConfig, get_peft_model
        except ImportError as exc:
            raise SystemExit("LoRA requested but peft is not installed") from exc
        model = get_peft_model(model, LoraConfig(
            r=args.lora_rank,
            lora_alpha=args.lora_alpha,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules="all-linear",
        ))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        logging_steps=1,
        save_strategy="epoch",
        seed=args.seed,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        report_to="none",
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=CotDataset(),
        data_collator=collate,
    )
    result = trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    root = Path(__file__).resolve().parents[2]
    manifest = {
        "schema_version": 1,
        "experiment": "7-9",
        "stage": "student_sft",
        "status": "complete",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "book_git_commit": _git_commit(root),
        "training_data": {
            "path": str(args.train_data.resolve()),
            "sha256": sha256(args.train_data.resolve()),
            "samples": len(messages),
        },
        "base_model": args.base_model,
        "output_dir": str(args.output_dir.resolve()),
        "host": {
            "platform": platform.platform(),
            "gpu_names": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
            "torch": torch.__version__,
        },
        "dependency_versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "accelerate", "peft")
        },
        "training": {
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "max_length": args.max_length,
            "batch_size": args.batch_size,
            "gradient_accumulation": args.gradient_accumulation,
            "lora_rank": args.lora_rank,
            "seed": args.seed,
            "metrics": result.metrics,
        },
    }
    (args.output_dir / "training_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"checkpoint": str(args.output_dir), "samples": len(messages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
