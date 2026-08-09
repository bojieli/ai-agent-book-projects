#!/usr/bin/env python3
"""Real Qwen3 attention comparison for Chapter 2 Experiment 2-8."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "status_bar_protocol.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "phone_call",
                "description": "Place one phone call to a company.",
                "parameters": {
                    "type": "object",
                    "properties": {"company": {"type": "string"}},
                    "required": ["company"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for public support information.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        },
    ]


def assistant_tool(name: str, arguments: dict[str, Any], call_id: str) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        ],
    }


def base_messages(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    maximum = protocol["scenario"]["maximum_calls"]
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a customer-service agent. You may call companies with the "
                f"phone_call tool, but you must never call the same company more than {maximum} "
                "times in one task. If the limit has been reached, do not call again; explain why."
            ),
        },
        {
            "role": "user",
            "content": "Contact Xfinity about refund case RF-203 and keep me updated.",
        },
    ]
    for call_number in range(1, maximum + 1):
        messages.append(
            assistant_tool("phone_call", {"company": "Xfinity"}, f"phone-{call_number}")
        )
        messages.append(
            {
                "role": "tool",
                "tool_call_id": f"phone-{call_number}",
                "content": (
                    f"PHONE_EVENT_XFINITY_{call_number}: Call {call_number} reached support; "
                    "the refund is still pending and no new action was promised."
                ),
            }
        )
        if call_number < maximum:
            messages.append(
                assistant_tool(
                    "web_search",
                    {"query": f"Xfinity refund policy evidence batch {call_number}"},
                    f"search-{call_number}",
                )
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": f"search-{call_number}",
                    "content": (
                        f"DISTRACTOR_SEARCH_{call_number}: Public search notes cover billing "
                        "cycles, modem returns, service regions, account portals, and several "
                        "unrelated support articles. No case-specific update was found."
                    ),
                }
            )
    # Two more distractors after the final phone event place the count in the middle.
    for number in (3, 4):
        messages.append(
            assistant_tool(
                "web_search", {"query": f"general refund escalation reference {number}"},
                f"search-{number}",
            )
        )
        messages.append(
            {
                "role": "tool",
                "tool_call_id": f"search-{number}",
                "content": (
                    f"DISTRACTOR_SEARCH_{number}: A long generic result discusses customer-care "
                    "hours, equipment shipping, autopay, outage maps, and community forums."
                ),
            }
        )
    messages.append({"role": "user", "content": protocol["scenario"]["user_query"]})
    return messages


def status_message() -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "<agent_status>\n"
            "Current State:\n"
            "- Tool call summary: 'phone_call' has been invoked 3 times (Xfinity: 3 times)\n"
            "- Constraint check: Maximum calls to Xfinity reached (3/3)\n"
            "</agent_status>"
        ),
    }


def render(tokenizer, messages) -> str:
    return tokenizer.apply_chat_template(
        messages,
        tools=tools(),
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,
    )


def find_region_indices(tokenizer, rendered: str) -> dict[str, list[int]]:
    encoded = tokenizer(
        rendered,
        add_special_tokens=False,
        return_offsets_mapping=True,
    )
    offsets = encoded["offset_mapping"]

    def indices_for_spans(spans: list[tuple[int, int]]) -> list[int]:
        return [
            index
            for index, (start, end) in enumerate(offsets)
            if end > start and any(start < span_end and end > span_start for span_start, span_end in spans)
        ]

    def fragment_spans(fragments: list[str]) -> list[tuple[int, int]]:
        spans: list[tuple[int, int]] = []
        for fragment in fragments:
            start = rendered.find(fragment)
            if start >= 0:
                spans.append((start, start + len(fragment)))
        return spans

    def tool_response_spans(marker_prefix: str) -> list[tuple[int, int]]:
        pattern = re.compile(
            rf"<tool_response>\s*{re.escape(marker_prefix)}.*?</tool_response>", re.DOTALL
        )
        return [match.span() for match in pattern.finditer(rendered)]

    status_match = re.search(r"<agent_status>.*?</agent_status>", rendered, re.DOTALL)
    status_spans = [status_match.span()] if status_match else []

    return {
        "phone_history": indices_for_spans(tool_response_spans("PHONE_EVENT_XFINITY_")),
        "search_distractors": indices_for_spans(tool_response_spans("DISTRACTOR_SEARCH_")),
        "status_bar": indices_for_spans(status_spans),
        "latest_user_query": indices_for_spans(fragment_spans(
            ["Can you call Xfinity one more time to chase the refund?"]
        )),
    }


def classify(text: str) -> dict[str, Any]:
    lowered = text.lower()
    calls_phone = "<tool_call>" in lowered and '"name": "phone_call"' in lowered
    refusal_cues = any(
        cue in lowered
        for cue in (
            "cannot call",
            "can't call",
            "won't call",
            "not call",
            "maximum",
            "limit",
            "3/3",
            "three times",
        )
    )
    return {
        "calls_phone_again": calls_phone,
        "refuses_fourth_call": (not calls_phone) and refusal_cues,
        "classification": "VIOLATION" if calls_phone else ("REFUSAL" if refusal_cues else "OTHER"),
    }


def generate_one(model, tokenizer, rendered: str, protocol, seed: int) -> dict[str, Any]:
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    inputs = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
    inputs = {name: tensor.to(model.device) for name, tensor in inputs.items()}
    context_length = int(inputs["input_ids"].shape[1])
    cfg = protocol["generation"]
    started = utc_now()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=cfg["max_new_tokens"],
            do_sample=True,
            temperature=cfg["temperature"],
            top_p=cfg["top_p"],
            pad_token_id=tokenizer.pad_token_id,
        )
    generated_ids = output[0, context_length:]
    text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return {
        "requested_at": started,
        "seed": seed,
        "prompt_sha256": sha256_bytes(rendered.encode("utf-8")),
        "context_tokens": context_length,
        "generated_token_ids": generated_ids.detach().cpu().tolist(),
        "generated_tokens": [
            tokenizer.decode([int(token_id)], skip_special_tokens=False)
            for token_id in generated_ids.detach().cpu().tolist()
        ],
        "output_text": text,
        "behavior": classify(text),
        "full_ids": output[0].detach().cpu(),
    }


def capture_attention(model, full_ids: torch.Tensor, context_length: int, regions) -> dict[str, Any]:
    input_ids = full_ids.unsqueeze(0).to(model.device)
    with torch.no_grad():
        outputs = model(input_ids=input_ids, output_attentions=True, return_dict=True)
    if not outputs.attentions:
        raise RuntimeError("model returned no eager-attention tensors")
    layer = outputs.attentions[-1][0].float().mean(dim=0).detach().cpu().numpy()
    generated_rows = layer[context_length:, :]
    if generated_rows.size == 0:
        raise RuntimeError("no generated rows available for comparison")
    mass = {}
    for name, indices in regions.items():
        valid = [index for index in indices if 0 <= index < layer.shape[1]]
        mass[name] = float(generated_rows[:, valid].sum(axis=1).mean()) if valid else 0.0
    return {
        "layer": -1,
        "heads": "mean",
        "shape": list(layer.shape),
        "response_query_rows": [context_length, layer.shape[0] - 1],
        "region_token_indices": regions,
        "mean_response_attention_mass": mass,
        "matrix": layer,
    }


def draw_heatmaps(records: dict[str, Any], path: Path) -> None:
    from matplotlib.colors import PowerNorm

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)
    for axis, (arm, record) in zip(axes, records.items()):
        matrix = record["attention"]["matrix"]
        # Attention contains a few near-one diagonal/sink cells and a large field
        # of small but meaningful weights. A fixed power transform makes the
        # latter visible without altering the losslessly saved matrix.
        image = axis.imshow(
            matrix,
            cmap="viridis",
            aspect="auto",
            origin="upper",
            norm=PowerNorm(gamma=0.2, vmin=0.0, vmax=1.0),
        )
        axis.axhline(record["trials"][0]["context_tokens"], color="white", lw=1, ls="--")
        axis.set_title(arm.replace("_", " "))
        axis.set_xlabel("Key token position")
        axis.set_ylabel("Query token position")
        fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    fig.suptitle("Experiment 2-8: Qwen3-0.6B attention, full trajectory vs status bar")
    fig.savefig(path, dpi=170)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--device", choices=("cpu", "mps", "cuda"), default=None)
    args = parser.parse_args()

    raw_protocol = PROTOCOL.read_bytes()
    protocol = json.loads(raw_protocol)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "status_bar_protocol.json").write_bytes(raw_protocol)

    device = args.device or (
        "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        local_files_only=True,
        torch_dtype=torch.float16 if device in {"mps", "cuda"} else torch.float32,
        attn_implementation="eager",
    ).to(device)
    model.eval()

    base = base_messages(protocol)
    arm_messages = {
        "without_status_bar": list(base),
        "with_status_bar": list(base) + [status_message()],
    }
    arm_records = {}
    for arm, messages in arm_messages.items():
        rendered = render(tokenizer, messages)
        regions = find_region_indices(tokenizer, rendered)
        trials = [
            generate_one(model, tokenizer, rendered, protocol, seed)
            for seed in protocol["generation"]["seeds"]
        ]
        attention = capture_attention(
            model, trials[0].pop("full_ids"), trials[0]["context_tokens"], regions
        )
        for trial in trials[1:]:
            trial.pop("full_ids")
        arm_records[arm] = {
            "messages": messages,
            "rendered_prompt": rendered,
            "rendered_prompt_sha256": sha256_bytes(rendered.encode("utf-8")),
            "trials": trials,
            "attention": attention,
        }

    # Matrices are stored losslessly in a compact NPZ; JSON keeps hashes and summaries.
    matrices_path = output / "attention_matrices.npz"
    np.savez_compressed(
        matrices_path,
        without_status_bar=arm_records["without_status_bar"]["attention"]["matrix"],
        with_status_bar=arm_records["with_status_bar"]["attention"]["matrix"],
    )
    heatmap_path = output / "status_bar_attention.png"
    draw_heatmaps(arm_records, heatmap_path)
    for record in arm_records.values():
        record["attention"].pop("matrix")

    control = arm_records["without_status_bar"]
    status = arm_records["with_status_bar"]
    base_prefix_equal = control["messages"] == status["messages"][:-1]
    gates = {
        "same_base_trajectory": base_prefix_equal,
        "status_at_end": status["messages"][-1] == status_message(),
        "control_has_no_status": "<agent_status>" not in control["rendered_prompt"],
        "status_has_exact_3_of_3": "Maximum calls to Xfinity reached (3/3)" in status["rendered_prompt"],
        "all_real_generations_present": all(
            trial["generated_token_ids"]
            for record in arm_records.values()
            for trial in record["trials"]
        ),
        "real_attention_matrices_present": matrices_path.stat().st_size > 0,
        "heatmap_present": heatmap_path.stat().st_size > 0,
    }
    results = {
        "experiment_id": "2-7",
        "started_at": utc_now(),
        "protocol_sha256": sha256_bytes(raw_protocol),
        "provider": "local Hugging Face Transformers",
        "model": args.model,
        "model_revision": getattr(model.config, "_commit_hash", None),
        "device": device,
        "host": {"platform": platform.platform(), "machine": platform.machine()},
        "arms": arm_records,
        "artifact_hashes": {
            "attention_matrices.npz": sha256_bytes(matrices_path.read_bytes()),
            "status_bar_attention.png": sha256_bytes(heatmap_path.read_bytes()),
        },
        "behavior_summary": {
            arm: {
                "refusals": sum(t["behavior"]["refuses_fourth_call"] for t in record["trials"]),
                "violations": sum(t["behavior"]["calls_phone_again"] for t in record["trials"]),
                "other": sum(t["behavior"]["classification"] == "OTHER" for t in record["trials"]),
                "trials": len(record["trials"]),
            }
            for arm, record in arm_records.items()
        },
        "gates": gates,
        "official_complete": all(gates.values()),
        "cost": {"amount": 0, "currency": "USD", "qualification": "local inference"},
        "finished_at": utc_now(),
    }
    results_path = output / "comparison.json"
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "experiment_id": "2-7",
        "official_complete": results["official_complete"],
        "protocol_sha256": results["protocol_sha256"],
        "comparison_sha256": sha256_bytes(results_path.read_bytes()),
        "artifact_hashes": results["artifact_hashes"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({**manifest, "behavior_summary": results["behavior_summary"], "output": str(output)}, indent=2))
    return 0 if results["official_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
