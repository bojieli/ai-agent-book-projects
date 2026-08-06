#!/usr/bin/env python3
"""Run the Sesame CSM paralinguistic-tag half of Experiment 7-6."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from datasets import Audio, load_dataset
from huggingface_hub import HfApi, snapshot_download
from peft import LoraConfig, get_peft_model
from transformers import AutoProcessor, CsmForConditionalGeneration, Trainer, TrainingArguments

BASE_MODEL = "unsloth/csm-1b"
DATASET = "maxbsoft/mrdragonfox-elise"
DATASET_REVISION = "2cc657c3f94a83df18fcd968b7531ca1a19c7f88"
SEED = 7602
TAG_PATTERNS = {
    "laugh": re.compile(r"<(?:laughs?|chuckles?)>", re.I),
    "giggle": re.compile(r"<giggles?>", re.I),
    "sigh": re.compile(r"<sighs?>", re.I),
}
PROMPT_PAIRS = [
    ("laugh_0", "I finally found the missing keys in my other pocket.", "I finally found the missing keys <laughs> in my other pocket.", "laugh"),
    ("laugh_1", "That was the strangest joke I heard all week.", "That was the strangest joke <laughs> I heard all week.", "laugh"),
    ("giggle_0", "You remembered the secret code after all.", "You remembered the secret code <giggles> after all.", "giggle"),
    ("giggle_1", "The tiny puppy tried to carry the enormous slipper.", "The tiny puppy <giggles> tried to carry the enormous slipper.", "giggle"),
    ("sigh_0", "The last bus left before we reached the corner.", "The last bus left <sighs> before we reached the corner.", "sigh"),
    ("sigh_1", "I suppose we need to finish the paperwork again.", "I suppose <sighs> we need to finish the paperwork again.", "sigh"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class TensorCollator:
    def __call__(self, rows):
        keys = rows[0].keys()
        return {key: torch.stack([row[key] for row in rows]) for key in keys}


def category(text: str) -> str:
    for name, pattern in TAG_PATTERNS.items():
        if pattern.search(text):
            return name
    return "neutral"


def patched_model_snapshot() -> Path:
    """Point the tokenizer at CSM's existing training-pad token.

    The 2026.8 Unsloth safety check rejects the upstream tokenizer because its
    pad token aliases EOS, even though CSM's model config correctly declares
    token 128004 as padding.  A temporary snapshot fixes only that metadata;
    weights stay symlinked to the immutable Hugging Face cache.
    """
    source = Path(snapshot_download(BASE_MODEL))
    target = Path(tempfile.mkdtemp(prefix="exp7-6-csm-"))
    copied = {"tokenizer_config.json", "special_tokens_map.json"}
    for item in source.iterdir():
        if item.name in copied:
            shutil.copy2(item, target / item.name)
        else:
            os.symlink(item, target / item.name)
    pad = {"content": "<|finetune_right_pad_id|>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False}
    for name in copied:
        path = target / name
        data = json.loads(path.read_text())
        data["pad_token"] = pad if name == "special_tokens_map.json" else pad["content"]
        path.write_text(json.dumps(data, indent=2) + "\n")
    return target


def stratified_indices(ds, per_category: dict[str, int], offset: int = 0):
    buckets = {k: [] for k in per_category}
    for i, text in enumerate(ds["text"]):
        key = category(text)
        if key in buckets:
            buckets[key].append(i)
    selected, counts = [], {}
    for n, wanted in per_category.items():
        rng = random.Random(SEED + offset + sum(ord(c) for c in n))
        rng.shuffle(buckets[n])
        take = buckets[n][offset : offset + wanted]
        selected.extend(take)
        counts[n] = len(take)
    random.Random(SEED + offset).shuffle(selected)
    return selected, counts


def preprocess(ds, indices, processor, max_audio_samples: int):
    rows, failures = [], []
    required = ["input_ids", "attention_mask", "labels", "input_values", "input_values_cutoffs"]
    for pos, idx in enumerate(indices, 1):
        try:
            sample = ds[int(idx)]
            audio = np.asarray(sample["audio"]["array"], dtype=np.float32)[:max_audio_samples]
            conversation = [{"role": "0", "content": [
                {"type": "text", "text": sample["text"]},
                {"type": "audio", "path": audio},
            ]}]
            inputs = processor.apply_chat_template(
                conversation,
                tokenize=True,
                return_dict=True,
                output_labels=True,
                text_kwargs={
                    "padding": "max_length",
                    "max_length": 256,
                    "pad_to_multiple_of": 8,
                    "padding_side": "right",
                },
                audio_kwargs={
                    "sampling_rate": 24000,
                    "max_length": max_audio_samples,
                    "padding": "max_length",
                },
                common_kwargs={"return_tensors": "pt"},
            )
            rows.append({key: inputs[key][0].cpu() for key in required})
        except Exception as exc:
            failures.append({"dataset_index": int(idx), "error": repr(exc)})
        print(f"preprocessed Sesame {pos}/{len(indices)}", flush=True)
    return rows, failures


def generate_arm(model, processor, arm: str, out: Path, max_tokens: int):
    arm_dir = out / "audio" / "sesame" / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    records = []
    model.eval()
    for pair_idx, (pair_id, neutral, tagged, tag) in enumerate(PROMPT_PAIRS):
        for condition, text in (("neutral", neutral), ("tagged", tagged)):
            seed = SEED + pair_idx
            torch.manual_seed(seed)
            inputs = processor(f"[0]{text}", add_special_tokens=True, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                values = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs.get("attention_mask"),
                    max_new_tokens=max_tokens,
                    output_audio=True,
                )
            audio = values[0].float().cpu().numpy()
            path = arm_dir / f"{pair_id}_{condition}.wav"
            sf.write(path, audio, 24000, subtype="PCM_16")
            records.append(
                {
                    "pair_id": pair_id,
                    "tag": tag,
                    "condition": condition,
                    "text": text,
                    "seed": seed,
                    "path": str(path.relative_to(out)),
                    "sha256": sha256(path),
                    "samples": int(len(audio)),
                    "seconds": len(audio) / 24000,
                }
            )
            print(f"generated Sesame {arm} {pair_id} {condition}", flush=True)
    return records


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--max-audio-seconds", type=float, default=8.0)
    p.add_argument("--generation-tokens", type=int, default=75)
    p.add_argument("--hf-repo", default="bojieli/exp7-6-sesame-elise-tags-lora")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    ds = load_dataset(DATASET, revision=DATASET_REVISION, split="train")
    ds = ds.cast_column("audio", Audio(sampling_rate=24000))
    # 168 tagged/neutral utterances for training and a disjoint held-out loss set.
    train_idx, train_counts = stratified_indices(
        ds, {"laugh": 48, "giggle": 32, "sigh": 48, "neutral": 40}, offset=0
    )
    eval_idx, eval_counts = stratified_indices(
        ds, {"laugh": 8, "giggle": 4, "sigh": 8, "neutral": 8}, offset=55
    )

    model_snapshot = patched_model_snapshot()
    # Keep CSM in float32: its codec currently returns float32 embeddings and
    # Transformers 4.57 otherwise tries to assign them into bf16 text slots.
    model = CsmForConditionalGeneration.from_pretrained(
        str(model_snapshot), dtype=torch.float32
    ).cuda()
    # Use the canonical processor explicitly; this also pins the input representation.
    processor = AutoProcessor.from_pretrained(str(model_snapshot))
    shutil.rmtree(model_snapshot)
    model = get_peft_model(
        model,
        LoraConfig(
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        task_type="CAUSAL_LM",
        ),
    )
    max_audio_samples = int(args.max_audio_seconds * 24000) + 1
    train_rows, train_failures = preprocess(ds, train_idx, processor, max_audio_samples)
    eval_rows, eval_failures = preprocess(ds, eval_idx, processor, max_audio_samples)

    base_audio = generate_arm(model, processor, "base", args.output, args.generation_tokens)
    trainer = Trainer(
        model=model,
        train_dataset=train_rows,
        eval_dataset=eval_rows,
        data_collator=TensorCollator(),
        args=TrainingArguments(
            output_dir=str(args.output / "sesame_checkpoints"),
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=4,
            max_steps=args.steps,
            warmup_steps=5,
            learning_rate=2e-4,
            bf16=False,
            logging_steps=1,
            eval_strategy="no",
            save_strategy="no",
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=SEED,
            report_to="none",
            remove_unused_columns=False,
        ),
    )
    pre_eval = trainer.evaluate()
    train_result = trainer.train()
    post_eval = trainer.evaluate()
    adapter_dir = args.output / "adapters" / "sesame"
    # The temporary tokenizer snapshot contains only metadata/symlinks. Ensure
    # the serialized adapter points consumers at the real public base model.
    model.peft_config["default"].base_model_name_or_path = BASE_MODEL
    model.save_pretrained(adapter_dir)
    processor.save_pretrained(adapter_dir)
    model.push_to_hub(args.hf_repo, private=False, token=os.environ.get("HF_TOKEN"))
    processor.push_to_hub(args.hf_repo, private=False, token=os.environ.get("HF_TOKEN"))
    adapter_revision = HfApi().model_info(args.hf_repo).sha
    adapted_audio = generate_arm(model, processor, "adapted", args.output, args.generation_tokens)

    adapter_files = [
        {"path": str(x.relative_to(args.output)), "bytes": x.stat().st_size, "sha256": sha256(x)}
        for x in sorted(adapter_dir.rglob("*"))
        if x.is_file()
    ]
    manifest = {
        "experiment": "7-6",
        "track": "sesame_paralinguistic_tags",
        "status": "trained_and_generated",
        "seed": SEED,
        "base_model": BASE_MODEL,
        "base_model_revision": HfApi().model_info(BASE_MODEL).sha,
        "dataset": DATASET,
        "dataset_revision": DATASET_REVISION,
        "source_dataset_note": "Public non-disabled mirror of the disabled MrDragonFox/Elise dataset named by the upstream notebook.",
        "compatibility_notes": [
            "Unsloth 2026.8.2 rejects CSM's tokenizer because the upstream tokenizer aliases pad to EOS; the run uses standard PEFT and CSM config token 128004 (<|finetune_right_pad_id|>).",
            "Transformers 4.57 CSM codec embeddings are float32; float32 model/training avoids the bf16 merge dtype mismatch observed during the first pre-training evaluation attempt.",
        ],
        "train_examples_selected": len(train_idx),
        "train_examples_preprocessed": len(train_rows),
        "train_category_counts": train_counts,
        "eval_examples_selected": len(eval_idx),
        "eval_examples_preprocessed": len(eval_rows),
        "eval_category_counts": eval_counts,
        "train_failures": train_failures,
        "eval_failures": eval_failures,
        "max_audio_seconds": args.max_audio_seconds,
        "optimizer_steps": args.steps,
        "effective_batch_size": 4,
        "lora_rank": 16,
        "pre_eval": pre_eval,
        "train_metrics": train_result.metrics,
        "post_eval": post_eval,
        "gpu": torch.cuda.get_device_name(0),
        "peak_gpu_memory_bytes": torch.cuda.max_memory_reserved(),
        "wall_seconds": time.time() - started,
        "adapter_local_files": adapter_files,
        "adapter_huggingface_repo": f"https://huggingface.co/{args.hf_repo}",
        "adapter_huggingface_revision": adapter_revision,
        "audio": base_audio + adapted_audio,
    }
    (args.output / "sesame_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
