#!/usr/bin/env python3
"""Canonical real-model campaign for Chapter 2 Experiment 2-2."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from visualization import _configure_cjk_font


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "attention_experiment_protocol.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_layer(index: int, count: int) -> int:
    resolved = index if index >= 0 else count + index
    if not 0 <= resolved < count:
        raise ValueError(f"layer {index} is outside a {count}-layer model")
    return resolved


def region_indices(tokens: list[str], context_length: int) -> dict[str, list[int]]:
    """Locate generated Qwen thinking/answer regions without rewriting text."""
    think_start = next(
        (i for i in range(context_length, len(tokens)) if "<think>" in tokens[i]),
        context_length,
    )
    think_end = next(
        (i for i in range(think_start, len(tokens)) if "</think>" in tokens[i]),
        None,
    )
    if think_end is None:
        return {"thinking": list(range(think_start, len(tokens))), "answer": []}
    return {
        "thinking": list(range(think_start, think_end + 1)),
        "answer": list(range(think_end + 1, len(tokens))),
    }


def matrix_metrics(matrix: np.ndarray) -> dict[str, Any]:
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("attention matrix must be square")
    length = matrix.shape[0]
    upper = matrix[np.triu_indices(length, k=1)]
    thirds = np.array_split(np.arange(length), 3)
    response_rows = np.arange(max(0, length // 2), length)
    per_token_mass = []
    for indices in thirds:
        mass = float(matrix[np.ix_(response_rows, indices)].sum())
        per_token_mass.append(mass / max(1, len(response_rows) * len(indices)))
    return {
        "sequence_length": length,
        "attention_sink_mean": float(matrix[:, 0].mean()),
        "attention_sink_max": float(matrix[:, 0].max()),
        "causal_upper_triangle_max": float(upper.max()) if upper.size else 0.0,
        "causal_upper_triangle_sum": float(upper.sum()),
        "position_mass_per_token": {
            "beginning_third": per_token_mass[0],
            "middle_third": per_token_mass[1],
            "end_third": per_token_mass[2],
        },
    }


def capture(model, ids: torch.Tensor, layers: list[int]):
    with torch.no_grad():
        result = model(input_ids=ids, output_attentions=True, return_dict=True)
    if not result.attentions:
        raise RuntimeError("model returned no eager-attention tensors")
    count = len(result.attentions)
    matrices = {}
    for requested in layers:
        index = resolve_layer(requested, count)
        matrices[f"layer_{index}"] = (
            result.attentions[index][0].float().mean(dim=0).detach().cpu().numpy()
        )
    return matrices, count, int(result.attentions[0].shape[1])


def draw(matrices: dict[str, np.ndarray], tokens: list[str], path: Path, title: str):
    fig, axes = plt.subplots(1, len(matrices), figsize=(6 * len(matrices), 5.5))
    if not isinstance(axes, np.ndarray):
        axes = np.asarray([axes])
    for axis, (name, matrix) in zip(axes, matrices.items()):
        shown = np.log10(np.maximum(matrix, 1e-7))
        image = axis.imshow(shown, origin="upper", aspect="auto", cmap="magma", vmin=-7, vmax=0)
        axis.set_title(f"{name}; sink={matrix[:, 0].mean():.1%}")
        axis.set_xlabel("Key position")
        axis.set_ylabel("Query position")
        fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04, label="log10 attention")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", choices=("cpu", "mps", "cuda"))
    args = parser.parse_args()
    _configure_cjk_font()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw_protocol = PROTOCOL.read_bytes()
    protocol = json.loads(raw_protocol)
    (output / "experiment_protocol.json").write_bytes(raw_protocol)

    if args.device:
        device = args.device
    elif torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    tokenizer = AutoTokenizer.from_pretrained(protocol["model"])
    model = AutoModelForCausalLM.from_pretrained(
        protocol["model"], torch_dtype="auto", attn_implementation="eager"
    ).to(device).eval()

    simple = tokenizer(
        protocol["simple_prompt"], return_tensors="pt", add_special_tokens=False
    )["input_ids"].to(device)
    simple_matrices, layer_count, head_count = capture(model, simple, protocol["layers"])
    simple_tokens = [tokenizer.decode([item], skip_special_tokens=False) for item in simple[0].tolist()]

    messages = [
        {"role": "system", "content": "你是一个会展示简短思考过程的助手。"},
        {"role": "user", "content": protocol["reasoning_prompt"]},
    ]
    rendered = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=True
    )
    inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    torch.manual_seed(protocol["seed"])
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            max_new_tokens=protocol["max_new_tokens"],
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    generated_matrices, _, _ = capture(model, generated, protocol["layers"])
    generated_ids = generated[0].tolist()
    generated_tokens = [tokenizer.decode([item], skip_special_tokens=False) for item in generated_ids]
    regions = region_indices(generated_tokens, int(inputs["input_ids"].shape[1]))

    arrays = {}
    for prefix, matrices in (("simple", simple_matrices), ("generated", generated_matrices)):
        for name, matrix in matrices.items():
            arrays[f"{prefix}_{name}"] = matrix
    matrices_path = output / "attention_matrices.npz"
    np.savez_compressed(matrices_path, **arrays)
    simple_heatmap = output / "beijing_attention_layers.png"
    generated_heatmap = output / "reasoning_answer_attention_layers.png"
    draw(simple_matrices, simple_tokens, simple_heatmap, "Experiment 2-2: 北京 的 天气 怎么样")
    draw(generated_matrices, generated_tokens, generated_heatmap, "Experiment 2-2: reasoning and answer sequence")

    simple_metrics = {name: matrix_metrics(value) for name, value in simple_matrices.items()}
    generated_metrics = {name: matrix_metrics(value) for name, value in generated_matrices.items()}
    revision = getattr(model.config, "_commit_hash", None)
    gates = {
        "exact_model": protocol["model"] == "Qwen/Qwen3-0.6B",
        "pinned_real_model_revision": isinstance(revision, str) and len(revision) == 40,
        "beijing_prompt_exact": protocol["simple_prompt"] == "北京 的 天气 怎么样",
        "three_layers_captured": len(simple_matrices) == 3 and len(generated_matrices) == 3,
        "causal_triangle_exact": all(
            item["causal_upper_triangle_max"] <= 1e-7
            for item in list(simple_metrics.values()) + list(generated_metrics.values())
        ),
        "thinking_region_present": bool(regions["thinking"]),
        "final_answer_region_present": bool(regions["answer"]),
        "lossless_matrices_present": matrices_path.stat().st_size > 0,
        "heatmaps_present": simple_heatmap.stat().st_size > 0 and generated_heatmap.stat().st_size > 0,
    }
    evidence = {
        "experiment_id": "2-2",
        "status": "passed" if all(gates.values()) else "partial",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "local Hugging Face Transformers",
        "model": protocol["model"],
        "model_revision": revision,
        "device": device,
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "architecture": {"layers": layer_count, "attention_heads": head_count},
        "simple": {"prompt": protocol["simple_prompt"], "token_ids": simple[0].tolist(), "tokens": simple_tokens, "metrics": simple_metrics},
        "generated": {
            "prompt": protocol["reasoning_prompt"],
            "context_length": int(inputs["input_ids"].shape[1]),
            "token_ids": generated_ids,
            "tokens": generated_tokens,
            "decoded_completion": tokenizer.decode(generated[0, inputs["input_ids"].shape[1]:], skip_special_tokens=False),
            "regions": regions,
            "metrics": generated_metrics,
        },
        "gates": gates,
        "observational_note": "Position-bias and sink magnitudes are measured outcomes, not response-conditioned completion gates.",
    }
    evidence_path = output / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "experiment_id": "2-2",
        "status": evidence["status"],
        "gates": gates,
        "artifacts": {
            name: sha256(output / name)
            for name in ("experiment_protocol.json", "evidence.json", "attention_matrices.npz", "beijing_attention_layers.png", "reasoning_answer_attention_layers.png")
        },
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = ROOT / "validation" / "latest.json"
    latest.parent.mkdir(exist_ok=True)
    shutil.copyfile(manifest_path, latest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
