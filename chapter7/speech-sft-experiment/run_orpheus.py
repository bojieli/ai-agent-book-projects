#!/usr/bin/env python3
"""Run the Orpheus half of Experiment 7-6 on one local CUDA GPU.

The campaign deliberately keeps a held-out split and emits base/adapted audio
for identical prompts and seeds.  It is bounded for a workstation, but it is
not a one-batch smoke test: the default run encodes 144 real utterances and
performs 60 optimizer updates with effective batch size four.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio.functional as AF
from datasets import load_dataset
from huggingface_hub import HfApi
from snac import SNAC
from unsloth import FastLanguageModel
from transformers import Trainer, TrainingArguments

BASE_MODEL = "unsloth/orpheus-3b-0.1-ft"
DATASET = "maxbsoft/mrdragonfox-elise"
DATASET_REVISION = "2cc657c3f94a83df18fcd968b7531ca1a19c7f88"
SEED = 7601

PROMPTS = [
    "The morning train crossed the bridge just before sunrise.",
    "Please leave the blue notebook beside the kitchen window.",
    "A patient astronomer mapped every bright star in the winter sky.",
    "We walked home slowly while the last shops turned off their lights.",
    "Could you read the final paragraph one more time for the group?",
    "The small garden stayed green even through the hottest week of July.",
    "I packed a warm coat, two apples, and a compass for the long hike.",
    "Tomorrow's meeting begins at nine, so I will arrive a little early.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class PadCollator:
    def __init__(self, pad_id: int):
        self.pad_id = pad_id

    def __call__(self, rows):
        n = max(len(x["input_ids"]) for x in rows)
        ids, labels, masks = [], [], []
        for row in rows:
            d = n - len(row["input_ids"])
            ids.append(row["input_ids"] + [self.pad_id] * d)
            labels.append(row["labels"] + [-100] * d)
            masks.append(row["attention_mask"] + [0] * d)
        return {
            "input_ids": torch.tensor(ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(masks, dtype=torch.long),
        }


def encode_audio(snac, wave, sample_rate: int, seconds: float) -> list[int]:
    wave = torch.as_tensor(np.asarray(wave), dtype=torch.float32)
    if sample_rate != 24000:
        wave = AF.resample(wave, sample_rate, 24000)
    wave = wave[: int(seconds * 24000)]
    if wave.numel() < 2400:
        raise ValueError("utterance is shorter than 100 ms")
    with torch.inference_mode():
        codes = snac.encode(wave[None, None].cuda())
    out = []
    for i in range(codes[0].shape[1]):
        out.extend(
            [
                codes[0][0][i].item() + 128266,
                codes[1][0][2 * i].item() + 128266 + 4096,
                codes[2][0][4 * i].item() + 128266 + 2 * 4096,
                codes[2][0][4 * i + 1].item() + 128266 + 3 * 4096,
                codes[1][0][2 * i + 1].item() + 128266 + 4 * 4096,
                codes[2][0][4 * i + 2].item() + 128266 + 5 * 4096,
                codes[2][0][4 * i + 3].item() + 128266 + 6 * 4096,
            ]
        )
    # Remove codec frames whose first code repeats, matching the upstream recipe.
    dedup = out[:7]
    for i in range(7, len(out), 7):
        if out[i] != dedup[-7]:
            dedup.extend(out[i : i + 7])
    return dedup


def prepare_rows(ds, tokenizer, snac, indices, seconds):
    result, failures = [], []
    for pos, idx in enumerate(indices, 1):
        try:
            row = ds[int(idx)]
            codes = encode_audio(
                snac, row["audio"]["array"], row["audio"]["sampling_rate"], seconds
            )
            text_ids = tokenizer.encode(row["text"], add_special_tokens=True) + [128009]
            ids = [128259] + text_ids + [128260, 128261, 128257] + codes + [128258, 128262]
            result.append({"input_ids": ids, "labels": ids.copy(), "attention_mask": [1] * len(ids)})
        except Exception as exc:  # retained in the manifest
            failures.append({"dataset_index": int(idx), "error": repr(exc)})
        print(f"encoded {pos}/{len(indices)}", flush=True)
    return result, failures


def decode(snac, ids):
    speech = (ids == 128257).nonzero(as_tuple=True)[0]
    row = ids[speech[-1].item() + 1 :] if speech.numel() else ids
    eos = (row == 128258).nonzero(as_tuple=True)[0]
    if eos.numel():
        row = row[: eos[0].item()]
    values = [int(x) - 128266 for x in row[: (len(row) // 7) * 7]]
    layers = [[], [], []]
    invalid_frame = None
    for i in range(len(values) // 7):
        c = [values[7 * i + j] - j * 4096 for j in range(7)]
        if any(x < 0 or x > 4095 for x in c):
            invalid_frame = i
            break
        layers[0].append(c[0])
        layers[1].extend([c[1], c[4]])
        layers[2].extend([c[2], c[3], c[5], c[6]])
    if not layers[0]:
        return np.zeros(2400, dtype=np.float32), invalid_frame, 0
    tensors = [torch.tensor(x, dtype=torch.long)[None] for x in layers]
    with torch.inference_mode():
        audio = snac.cpu().decode(tensors).squeeze().float().numpy()
    return audio, invalid_frame, len(layers[0])


def generate_arm(model, tokenizer, snac, arm: str, out: Path, max_tokens: int):
    arm_dir = out / "audio" / "orpheus" / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    FastLanguageModel.for_inference(model)
    for i, prompt in enumerate(PROMPTS):
        torch.manual_seed(SEED + i)
        ids = tokenizer(prompt, return_tensors="pt").input_ids
        ids = torch.cat([torch.tensor([[128259]]), ids, torch.tensor([[128009, 128260]])], dim=1).cuda()
        with torch.inference_mode():
            generated = model.generate(
                input_ids=ids,
                attention_mask=torch.ones_like(ids),
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.6,
                top_p=0.95,
                repetition_penalty=1.1,
                eos_token_id=128258,
                use_cache=True,
            )[0].cpu()
        audio, invalid_frame, frames = decode(snac, generated)
        path = arm_dir / f"prompt_{i:02d}.wav"
        sf.write(path, audio, 24000, subtype="PCM_16")
        rows.append(
            {
                "prompt_id": i,
                "prompt": prompt,
                "seed": SEED + i,
                "path": str(path.relative_to(out)),
                "sha256": sha256(path),
                "samples": int(len(audio)),
                "seconds": len(audio) / 24000,
                "decoded_frames": frames,
                "first_invalid_frame": invalid_frame,
            }
        )
        print(f"generated Orpheus {arm} {i + 1}/{len(PROMPTS)}", flush=True)
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--train-examples", type=int, default=128)
    p.add_argument("--eval-examples", type=int, default=16)
    p.add_argument("--max-audio-seconds", type=float, default=4.0)
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--generation-tokens", type=int, default=560)
    p.add_argument("--hf-repo", default="bojieli/exp7-6-orpheus-elise-lora")
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    ds = load_dataset(DATASET, revision=DATASET_REVISION, split="train")
    candidates = [i for i, x in enumerate(ds["duration"]) if 1.0 <= float(x) <= 10.5]
    random.shuffle(candidates)
    selected = candidates[: args.train_examples + args.eval_examples]

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL, max_seq_length=3072, dtype=None, load_in_4bit=False
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=SEED,
    )
    snac = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").cuda().eval()
    train_rows, train_failures = prepare_rows(
        ds, tokenizer, snac, selected[: args.train_examples], args.max_audio_seconds
    )
    eval_rows, eval_failures = prepare_rows(
        ds, tokenizer, snac, selected[args.train_examples :], args.max_audio_seconds
    )
    snac.cpu()
    torch.cuda.empty_cache()

    base_audio = generate_arm(model, tokenizer, snac, "base", args.output, args.generation_tokens)
    FastLanguageModel.for_training(model)
    trainer = Trainer(
        model=model,
        train_dataset=train_rows,
        eval_dataset=eval_rows,
        data_collator=PadCollator(128263),
        args=TrainingArguments(
            output_dir=str(args.output / "orpheus_checkpoints"),
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=4,
            max_steps=args.steps,
            warmup_steps=5,
            learning_rate=2e-4,
            bf16=True,
            logging_steps=1,
            eval_strategy="no",
            save_strategy="no",
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=SEED,
            report_to="none",
        ),
    )
    pre_eval = trainer.evaluate()
    train_result = trainer.train()
    post_eval = trainer.evaluate()
    adapter_dir = args.output / "adapters" / "orpheus"
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    model.push_to_hub(args.hf_repo, private=False, token=os.environ.get("HF_TOKEN"))
    tokenizer.push_to_hub(args.hf_repo, private=False, token=os.environ.get("HF_TOKEN"))
    adapter_revision = HfApi().model_info(args.hf_repo).sha
    adapted_audio = generate_arm(model, tokenizer, snac, "adapted", args.output, args.generation_tokens)

    adapter_files = [
        {"path": str(x.relative_to(args.output)), "bytes": x.stat().st_size, "sha256": sha256(x)}
        for x in sorted(adapter_dir.rglob("*"))
        if x.is_file()
    ]
    manifest = {
        "experiment": "7-6",
        "track": "orpheus_cross_sentence_voice_consistency",
        "status": "trained_and_generated",
        "seed": SEED,
        "base_model": BASE_MODEL,
        "base_model_revision": HfApi().model_info(BASE_MODEL).sha,
        "dataset": DATASET,
        "dataset_revision": DATASET_REVISION,
        "source_dataset_note": "Public non-disabled mirror of the disabled MrDragonFox/Elise dataset named by the upstream notebook.",
        "train_examples_requested": args.train_examples,
        "train_examples_encoded": len(train_rows),
        "eval_examples_requested": args.eval_examples,
        "eval_examples_encoded": len(eval_rows),
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
    (args.output / "orpheus_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
