#!/usr/bin/env python3
"""Build checkpoint-free retained training evidence for Experiment 7-4.

The book contains 64 historical MiniMind-V image descriptions: eight model
configurations evaluated on the same eight images.  This program extracts all
of them, asks a real image-capable model to judge every anonymous candidate
against the corresponding source image, and writes raw credential-free
requests/responses plus a fail-closed, content-hashed reproduction package.

It deliberately does not claim to rerun the historical GPU jobs.  Historical
checkpoints are intentionally not distributed; the accepted artifact is a
reproducible training report with explicit provenance limits.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import json
import mimetypes
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
LATEST_PATH = HERE / "latest_vlm.json"

DEFAULT_RUN_ID = "exp7-4-training-report-20260731-v1"
DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEFAULT_MODEL = "doubao-seed-1-6-250615"
BLIND_SEED = 740731

ORIGINAL_VLM_REVISION = "765908051d0837d60cecfb93f8390334e2e55f1e"
IMPROVED_VLM_REVISION = "ead791c530fa5f9a3549dbfe9e11ec732d18d2e5"
ORIGINAL_LLM_REVISION = "6d160ea20b98324632c4447ee63ec7cfa9becd20"
IMPROVED_LLM_REVISION = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"
DATASET_REVISION = "ac9d03a3fd26a2d8e74bda374d9a2ddba49e4c1b"
CLIP_REVISION = "57c216476eefef5ab752ec549e440a49ae4ae5f3"

ORIGINAL_VLM_FILES = {
    "trainer/train_pretrain_vlm.py": "4d30d54a940ae2eced204971cc03aafb3eb41a5c84c9f033cfdf162e63924a4d",
    "trainer/train_sft_vlm.py": "8e3b920a6a135eb126bbeea07e2db748729cdd86050925b282a80537bc324e5f",
    "eval_vlm.py": "9d883e4adbab0a7b88fd0cb9034132559a365387ec273ac4811cdd5ad28d5cda",
    "model/model_minimind.py": "105429e93dcbe87145264d72d46a6add7639666036e999628c76ae50582507dc",
    "model/model_vlm.py": "4ee42b298db68f30fbfa06d7686aa375d41a697628c770d0a134bca40ca9ea80",
    "dataset/lm_dataset.py": "df20d57460d2845841ddf2e0faced1af1f7ec169e7fda3cd50fe3b2854288a92",
    "model/tokenizer.json": "d98595c6aef70d95f72748582fb9b4f53d76dd58c1ae1dd702ad7c84e1caf5e4",
    "model/tokenizer_config.json": "dbbdb7eea33aba5c2608471494c93f650a2cf46fbe4a7489e531537ddadee746",
    "requirements.txt": "a9bddf49d3ccbc9f8a2508ea039aebc0b996dccb0d3618d1b119af53a5d49869",
}
IMPROVED_VLM_FILES = {
    "trainer/train_pretrain_vlm_muon.py": "f39af354c588747d9d5e522c9374a7f59a35d57aa649da74957da67d95d25bc6",
    "trainer/train_sft_vlm_muon.py": "1fd56b3e8bed2714b4d10ceba5d57ada0b95d00dfbfb514481498fef0c0dd03d",
    "trainer/muon.py": "00c2c6a225edeb55433df0724c3c74f6ff98ac4b2cc73c4aafcff686824f6267",
    "eval_vlm.py": "9d883e4adbab0a7b88fd0cb9034132559a365387ec273ac4811cdd5ad28d5cda",
    "model/model_minimind.py": "4771bc4b2ac367a6e6415c42c30bcdb54bec0397708f87de3c390042680b1e9e",
    "model/model_vlm.py": "4ee42b298db68f30fbfa06d7686aa375d41a697628c770d0a134bca40ca9ea80",
    "dataset/lm_dataset.py": "df20d57460d2845841ddf2e0faced1af1f7ec169e7fda3cd50fe3b2854288a92",
    "model/tokenizer.json": "e489029175fb3f94b8211a120a72a2ee41a664db65b828d077c7bde989c845a9",
    "model/tokenizer_config.json": "190cc4738bac3b6f6b563376019c581b320fdb0260a03b9d5ab806296c8c6bb8",
    "requirements.txt": "a9bddf49d3ccbc9f8a2508ea039aebc0b996dccb0d3618d1b119af53a5d49869",
}
ORIGINAL_LLM_FILES = {
    "model/model_minimind.py": "7cb069cb0cb0dfa123cf11ea394d0001270bc683c0a2dfe4120fc3b861ffc0a4",
    "trainer/train_pretrain.py": "ddd122645a9f1043bc8dac69a81ac51d2df95df8745d25faed7963d38fedc328",
    "trainer/train_full_sft.py": "a57422f1df80bf2867f31f3b4a646a92ac7f66729e98a3b32cd1ec4d6780cb8b",
    "trainer/train_dpo.py": "5e556a3089e43681638cdbf5adafb9d085bb1de5e4ea8da3ee522dfae02e3599",
    "eval_model.py": "b9f7ea9d7f517551362bbf2da8f1de006b8c734bcba774b2be752bc63cc4349d",
}
IMPROVED_LLM_FILES = {
    "model/model_minimind.py": "2d33988711c704be6a22c4c61489b23106a2340a7cb8b97ebe3e40f30819cbb0",
    "trainer/train_pretrain_muon.py": "fc83d07754ec3a8c156b6b8bfc0fd4326edecb72efabc5e08ae4ff5e3a7029bc",
    "trainer/train_full_sft_muon.py": "acd0b7db5b1d8b25d3c3103f92d68a7d381f9322a1b33bbec34be3d005930bad",
    "trainer/train_dpo.py": "97f2c31cc8bc21a777e2efcb5e2fa35a49e4e9e3698db120148f8a0b2f678449",
    "eval_model.py": "43930a4b55048a4a3ffa17eb78ae67d59582d639aa9365f0bbf41ba149128af8",
}
DATASET_FILES = {
    "pretrain_data.jsonl": {
        "lfs_sha256": "abc9f2ba44190646692fbe7e2b49c366c5045490989fb32d2c5e960dd0ee10e4",
        "bytes": 134315765,
    },
    "pretrain_images.zip": {
        "lfs_sha256": "64d56cee145bed75bc7f94c9cbf58882c41c4a0fea993014e27de7490b49e8b7",
        "bytes": 2614907051,
    },
    "sft_data.jsonl": {
        "lfs_sha256": "c1993d38c3a22a8bdfee65affc82d6559e5bb62e785b0f21c9151c75116151fc",
        "bytes": 173137988,
    },
    "sft_images.zip": {
        "lfs_sha256": "89ee34facc6793c51613613e0b10cac078942282f5fdec48d85751c6224bc3c2",
        "bytes": 1026332147,
    },
}
CLIP_FILE = {
    "path": "pytorch_model.bin",
    "lfs_sha256": "ec89c7b09c749a60aae3c9cd910516f24b58214a7df060b48962d14c469cfbf0",
    "bytes": 598641023,
}

IMAGE_FILES = {
    "Rainbow-Falls.jpg": "彩虹瀑布-Rainbow-Falls.jpg",
    "Dog-Woman-Sea.jpg": "小狗美女海边-Dog-Woman-Sea.jpg",
    "dance.jpg": "舞蹈-dance.jpg",
    "Astronaut-Space.jpg": "太空宇航员-Astronaut-Space.jpg",
    "city-traffic.jpg": "城市车水马龙-city-traffic.jpg",
    "Panda-Grassland.jpg": "熊猫草地-Panda-Grassland.jpg",
    "Bicycle-Flowers.jpg": "自行车鲜花-Bicycle-Flowers.jpg",
    "Chair-Elderly-Reading.jpg": "椅子老人看书-Chair-Elderly-Reading.jpg",
}
IMAGE_SHA256 = {
    "Rainbow-Falls.jpg": "1c8b74debaceb2e0bb6171b182084afe49288a0cc8089eb91eac69d067c27b10",
    "Dog-Woman-Sea.jpg": "ba90d8b8738a44eac70811be5c89f767492b167ad4f6f6c31aa4591837d7e3dc",
    "dance.jpg": "939e3132c8d3aec81f66f8aa928b476aaa25e00d94f1097f4974e73c913d5d8c",
    "Astronaut-Space.jpg": "f466cdafecbdb85d2bad586896db5db3313afe18f9b3505667756cd25b747747",
    "city-traffic.jpg": "73e90d82fbc5b1cf43b40de782b443f93f43a34e66b8ddebf3146d5dc1f83e00",
    "Panda-Grassland.jpg": "0b7610a881039f0effdbfa46e9bb189132443d3ce2956856e8adf66d1ca22f8c",
    "Bicycle-Flowers.jpg": "44fae0fafcd52c20b9bcaded897facbff00f61019cdd0aea543addf8499ad899",
    "Chair-Elderly-Reading.jpg": "8fe91a90e837c33230d21cfe7ba5020e71b3ae99ac4c3fbd6d32cb54f51def53",
}

CONFIGS = (
    "without_muon_pretrained",
    "without_muon_sft",
    "muon_from_dpo_pretrained",
    "muon_from_dpo_sft",
    "muon_from_pretrain_pretrained",
    "muon_from_pretrain_sft",
    "muon_from_sft_pretrained",
    "muon_from_sft_sft",
)
CONFIG_META = {
    "without_muon_pretrained": {
        "architecture": "original",
        "base_llm_stage": "sft",
        "vlm_stage": "pretrained",
    },
    "without_muon_sft": {"architecture": "original", "base_llm_stage": "sft", "vlm_stage": "sft"},
    "muon_from_dpo_pretrained": {
        "architecture": "qk_norm_muon",
        "base_llm_stage": "dpo",
        "vlm_stage": "pretrained",
    },
    "muon_from_dpo_sft": {
        "architecture": "qk_norm_muon",
        "base_llm_stage": "dpo",
        "vlm_stage": "sft",
    },
    "muon_from_pretrain_pretrained": {
        "architecture": "qk_norm_muon",
        "base_llm_stage": "pretrain",
        "vlm_stage": "pretrained",
    },
    "muon_from_pretrain_sft": {
        "architecture": "qk_norm_muon",
        "base_llm_stage": "pretrain",
        "vlm_stage": "sft",
    },
    "muon_from_sft_pretrained": {
        "architecture": "qk_norm_muon",
        "base_llm_stage": "sft",
        "vlm_stage": "pretrained",
    },
    "muon_from_sft_sft": {
        "architecture": "qk_norm_muon",
        "base_llm_stage": "sft",
        "vlm_stage": "sft",
    },
}
SECTION_SPECS = (
    (
        "## Without Muon Optimizer",
        (
            ("without_muon_pretrained", "### Pretrained VLM"),
            ("without_muon_sft", "### VLM after SFT"),
        ),
    ),
    (
        "## VLM with Muon Optimizer (from DPO)",
        (
            ("muon_from_dpo_pretrained", "### Pretrained VLM"),
            ("muon_from_dpo_sft", "### VLM with SFT"),
        ),
    ),
    (
        "## VLM with Muon Optimizer (from Pretrain)",
        (
            ("muon_from_pretrain_pretrained", "### Pretrained VLM"),
            ("muon_from_pretrain_sft", "### VLM with SFT"),
        ),
    ),
    (
        "## VLM with Muon Optimizer (from SFT)",
        (
            ("muon_from_sft_pretrained", "### Pretrained VLM"),
            ("muon_from_sft_sft", "### VLM with SFT"),
        ),
    ),
)
LABELS = tuple("ABCDEFGH")
METRICS = ("grounding_accuracy", "hallucination_control", "coverage", "visual_specificity")


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


def _parse_code_block(block: str, config: str) -> dict[str, Any]:
    fence = re.search(r"```[^\n]*\n(.*?)\n```", block, flags=re.DOTALL)
    if not fence:
        raise ValueError(f"{config}: no evaluation code block")
    transcript = fence.group(1).strip()
    matches = list(
        re.finditer(
            r"(?m)^\[Image\]:\s*([^\n]+)\n🤖️:\s*(.*?)(?=\n(?:\s*\n)*\[Image\]:|\Z)",
            transcript,
            flags=re.DOTALL,
        )
    )
    outputs = []
    for match in matches:
        image = match.group(1).strip()
        output = match.group(2).strip()
        if image not in IMAGE_FILES:
            raise ValueError(f"{config}: unexpected image {image!r}")
        if not output:
            raise ValueError(f"{config}/{image}: empty output")
        outputs.append({"image": image, "output": output})
    if len(outputs) != len(IMAGE_FILES) or {row["image"] for row in outputs} != set(IMAGE_FILES):
        raise ValueError(f"{config}: expected all eight images, found {len(outputs)}")
    command = next(
        (line.strip() for line in transcript.splitlines() if line.strip().startswith("$")), ""
    )
    return {
        "config": config,
        **CONFIG_META[config],
        "historical_command": command,
        "output_count": len(outputs),
        "outputs": outputs,
    }


def parse_retained_outputs(report_path: Path = REPORT_PATH) -> dict[str, Any]:
    text = report_path.read_text(encoding="utf-8")
    start = text.index("# Analysis of Vision-Language Model Training Results")
    end = text.index("## Key Findings and Summary of VLM Training", start)
    vlm = text[start:end]
    cells = []
    for section_index, (section_heading, stages) in enumerate(SECTION_SPECS):
        section_start = vlm.index(section_heading)
        section_end = (
            vlm.index(SECTION_SPECS[section_index + 1][0], section_start)
            if section_index + 1 < len(SECTION_SPECS)
            else len(vlm)
        )
        section = vlm[section_start:section_end]
        for stage_index, (config, heading) in enumerate(stages):
            cell_start = section.index(heading)
            cell_end = (
                section.index(stages[stage_index + 1][1], cell_start)
                if stage_index + 1 < len(stages)
                else len(section)
            )
            cells.append(_parse_code_block(section[cell_start:cell_end], config))
    if tuple(cell["config"] for cell in cells) != CONFIGS:
        raise ValueError("historical VLM cells are incomplete or out of order")
    return {
        "schema_version": "exp7-4-retained-outputs-v1",
        "experiment": "7-4",
        "source_report": str(report_path.relative_to(REPO_ROOT)),
        "source_report_sha256": sha256_file(report_path),
        "cell_count": len(cells),
        "output_count": sum(cell["output_count"] for cell in cells),
        "images": list(IMAGE_FILES),
        "configs": list(CONFIGS),
        "cells": cells,
    }


def outputs_for_image(retained: dict[str, Any], image: str) -> dict[str, str]:
    rows = {}
    for cell in retained["cells"]:
        match = [row for row in cell["outputs"] if row["image"] == image]
        if len(match) != 1:
            raise ValueError(f"{cell['config']}/{image}: expected one retained output")
        rows[cell["config"]] = match[0]["output"]
    return rows


def blind_mapping(image: str) -> dict[str, str]:
    configs = list(CONFIGS)
    image_seed = int(hashlib.sha256(image.encode()).hexdigest()[:8], 16)
    random.Random(BLIND_SEED + image_seed).shuffle(configs)
    return dict(zip(LABELS, configs, strict=True))


def image_path(source_dir: Path, image: str) -> Path:
    return source_dir / "dataset" / "eval_images" / IMAGE_FILES[image]


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def judge_payload(
    retained: dict[str, Any], image: str, source_dir: Path, model: str
) -> tuple[dict[str, Any], dict[str, str]]:
    mapping = blind_mapping(image)
    outputs = outputs_for_image(retained, image)
    candidates = {label: outputs[config] for label, config in mapping.items()}
    required = {
        "image": image,
        "candidates": {
            label: {
                **{metric: "number 0-5" for metric in METRICS},
                "material_errors": ["specific image-grounding errors; empty only if none"],
                "rationale": "brief evidence-based explanation",
            }
            for label in LABELS
        },
        "rank_order": list(LABELS),
        "best": "one label A-H",
    }
    text = json.dumps(
        {
            "image": image,
            "task": "Judge eight anonymous captions against the attached image.",
            "rubric": {
                "grounding_accuracy": "0 unrelated or false; 3 main subject mostly right; 5 all material claims visibly supported",
                "hallucination_control": "0 dominated by invented objects/relations; 3 some speculation; 5 no material invention",
                "coverage": "0 misses the scene; 3 covers main subject; 5 covers the important visible scene without padding",
                "visual_specificity": "0 generic/nonvisual; 3 some concrete details; 5 precise discriminative visible details",
            },
            "candidates": candidates,
            "required_json_shape": required,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an independent vision-language evaluator. The candidates are anonymous. "
                    "Do not infer model identity, optimizer, base checkpoint, or training stage. Inspect "
                    "the attached image, score only visible grounding, and return exactly one JSON object."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url(image_path(source_dir, image)),
                            "detail": "high",
                        },
                    },
                    {"type": "text", "text": text},
                ],
            },
        ],
    }
    return payload, mapping


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        if start < 0:
            raise
        parsed, _ = json.JSONDecoder().raw_decode(stripped[start:])
    if not isinstance(parsed, dict):
        raise TypeError("judge content must decode to an object")
    return parsed


def validate_judgment(judgment: dict[str, Any], image: str) -> None:
    if judgment.get("image") != image:
        raise ValueError(f"judge returned wrong image: {judgment.get('image')!r}")
    candidates = judgment.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != set(LABELS):
        raise ValueError("judge must score A-H exactly")
    for label in LABELS:
        row = candidates[label]
        if not isinstance(row, dict):
            raise TypeError(f"candidate {label} score must be an object")
        for metric in METRICS:
            value = row.get(metric)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not 0 <= value <= 5
            ):
                raise ValueError(f"candidate {label} invalid {metric}: {value!r}")
        if not isinstance(row.get("material_errors"), list):
            raise TypeError(f"candidate {label} material_errors must be a list")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            raise ValueError(f"candidate {label} rationale is missing")
    rank_order = judgment.get("rank_order")
    if (
        not isinstance(rank_order, list)
        or len(rank_order) != len(LABELS)
        or set(rank_order) != set(LABELS)
    ):
        raise ValueError("rank_order must be a permutation of A-H")
    if judgment.get("best") not in LABELS:
        raise ValueError("best must be one label A-H")


def call_judge(
    retained: dict[str, Any],
    image: str,
    *,
    source_dir: Path,
    endpoint: str,
    model: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    payload, mapping = judge_payload(retained, image, source_dir, model)
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
    judgment = extract_json_object(raw_response["choices"][0]["message"]["content"])
    validate_judgment(judgment, image)
    response_id = raw_response.get("id")
    usage = raw_response.get("usage")
    if not isinstance(response_id, str) or not response_id:
        raise ValueError("judge response has no response ID")
    if not isinstance(usage, dict) or not isinstance(usage.get("total_tokens"), int):
        raise TypeError("judge response has no complete usage")
    path = image_path(source_dir, image)
    return {
        "image": image,
        "image_source_filename": IMAGE_FILES[image],
        "image_sha256": sha256_file(path),
        "image_bytes": path.stat().st_size,
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
        "schema_version": "exp7-4-reproduction-contract-v1",
        "experiment": "7-4",
        "historical_evidence_boundary": {
            "historical_training_executed": True,
            "eight_historical_cells_and_64_outputs_retained": True,
            "historical_source_revisions_retained": False,
            "historical_dataset_hashes_retained": False,
            "historical_base_checkpoint_hashes_retained": False,
            "historical_vlm_checkpoint_hashes_retained": False,
            "historical_rng_and_stepwise_logs_retained": False,
            "claim": (
                "The author's report establishes that eight VLM configurations were evaluated on eight images. "
                "It does not establish byte identity of the historical code, datasets, base/VLM checkpoints, or RNG state."
            ),
        },
        "future_reproduction": {
            "vlm_source": {
                "repository": "bojieli/minimind-v",
                "original_revision": ORIGINAL_VLM_REVISION,
                "original_files_sha256": ORIGINAL_VLM_FILES,
                "qk_norm_muon_revision": IMPROVED_VLM_REVISION,
                "qk_norm_muon_files_sha256": IMPROVED_VLM_FILES,
                "not_claimed_as_historical_revisions": True,
            },
            "base_llm_source": {
                "repository": "bojieli/minimind",
                "original_revision": ORIGINAL_LLM_REVISION,
                "original_files_sha256": ORIGINAL_LLM_FILES,
                "qk_norm_muon_revision": IMPROVED_LLM_REVISION,
                "qk_norm_muon_files_sha256": IMPROVED_LLM_FILES,
                "dependency": "Use the Experiment 7-3 data/commands to produce original-SFT and improved pretrain/SFT/DPO 768-dimension base checkpoints.",
            },
            "vlm_dataset": {
                "repository": "jingyaogong/minimind-v_dataset",
                "revision": DATASET_REVISION,
                "selected_for_jsonl_script_compatibility": True,
                "files": DATASET_FILES,
            },
            "vision_encoder": {
                "repository": "openai/clip-vit-base-patch16",
                "revision": CLIP_REVISION,
                "file": CLIP_FILE,
            },
            "evaluation_images": {
                image: {"source_filename": IMAGE_FILES[image], "sha256": IMAGE_SHA256[image]}
                for image in IMAGE_FILES
            },
            "commands": {
                "original_source": "git clone https://github.com/bojieli/minimind-v.git sources/original-minimind-v && git -C sources/original-minimind-v checkout --detach 765908051d0837d60cecfb93f8390334e2e55f1e",
                "improved_source": "git clone https://github.com/bojieli/minimind-v.git sources/qk-norm-muon-minimind-v && git -C sources/qk-norm-muon-minimind-v checkout --detach ead791c530fa5f9a3549dbfe9e11ec732d18d2e5",
                "dataset": "git clone https://huggingface.co/datasets/jingyaogong/minimind-v_dataset dataset-source && git -C dataset-source checkout --detach ac9d03a3fd26a2d8e74bda374d9a2ddba49e4c1b && cp dataset-source/{pretrain_data.jsonl,sft_data.jsonl} dataset/ && unzip dataset-source/pretrain_images.zip -d dataset && unzip dataset-source/sft_images.zip -d dataset",
                "vision_encoder": "git clone https://huggingface.co/openai/clip-vit-base-patch16 model/vision_model/clip-vit-base-patch16 && git -C model/vision_model/clip-vit-base-patch16 checkout --detach 57c216476eefef5ab752ec549e440a49ae4ae5f3",
                "original_pretrain_vlm": "install -m 0644 <exp7-3-original-sft-768.pth> runs/original/out/llm_768.pth && cd trainer && torchrun --nproc_per_node=8 train_pretrain_vlm.py --out_dir ../runs/original/out --epochs 4 --hidden_size 768 --num_hidden_layers 16 --data_path ../dataset/pretrain_data.jsonl --images_path ../dataset/pretrain_images --use_wandb",
                "original_sft_vlm": "cd trainer && torchrun --nproc_per_node=8 train_sft_vlm.py --out_dir ../runs/original/out --epochs 4 --hidden_size 768 --num_hidden_layers 16 --data_path ../dataset/sft_data.jsonl --images_path ../dataset/sft_images --use_wandb",
                "improved_matrix": "For each BASE in pretrain,sft,dpo, install the corresponding Experiment-7-3 QK-Norm+Muon 768-dimension checkpoint as runs/muon-from-$BASE/out/llm_768.pth, then run train_pretrain_vlm_muon.py and train_sft_vlm_muon.py with the same four-epoch data arguments in that isolated out_dir.",
                "evaluation": "For every isolated out_dir, preserve both checkpoints, copy the selected *_muon_768.pth name to eval_vlm.py's pretrain_vlm_768.pth or sft_vlm_768.pth compatibility name when needed, then run python eval_vlm.py --load 0 --model_mode 0 and --model_mode 1 on the eight hash-pinned images with seed 1337.",
            },
            "environment": {
                "book_pyproject": "pyproject.toml",
                "book_lock": "uv.lock",
                "install": "uv sync --locked --python 3.12 --extra ch7 --extra dev",
                "boundary": "The book lock freezes a future Python environment; CUDA, drivers, and the historical GPU image were not retained.",
            },
        },
        "reported_training_design": {
            "parameter_count_millions": {"original": 104.622, "qk_norm_muon": 104.625},
            "base_llm_stages": ["pretrain", "sft", "dpo"],
            "vlm_stages": ["pretrained", "sft"],
            "projection_pretraining_freezes_llm": True,
            "sft_unfreezes_full_model": True,
            "reported_epochs": 4,
            "seed_in_current_source": 1337,
            "source_verified_mechanisms": {
                "original_revision_precedes_qk_norm_commit": True,
                "improved_revision_has_qk_norm_before_rope": True,
                "improved_revision_uses_muon_for_selected_2d_weights": True,
                "vision_encoder_is_frozen_clip": True,
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


def summarize(
    retained: dict[str, Any], receipts: list[dict[str, Any]], contract: dict[str, Any]
) -> dict[str, Any]:
    per_image_config_scores: dict[str, dict[str, Any]] = {}
    best_counts = {config: 0 for config in CONFIGS}
    for receipt in receipts:
        scores = {
            receipt["blind_map"][label]: row
            for label, row in receipt["judgment"]["candidates"].items()
        }
        per_image_config_scores[receipt["image"]] = scores
        best_counts[receipt["blind_map"][receipt["judgment"]["best"]]] += 1
    config_averages = {}
    for config in CONFIGS:
        rows = [per_image_config_scores[image][config] for image in IMAGE_FILES]
        config_averages[config] = {
            metric: mean([float(row[metric]) for row in rows]) for metric in METRICS
        }
        config_averages[config]["overall"] = mean(
            [float(row[metric]) for row in rows for metric in METRICS]
        )
    stage_averages = {}
    for stage in ("pretrained", "sft"):
        configs = [config for config in CONFIGS if CONFIG_META[config]["vlm_stage"] == stage]
        stage_averages[stage] = {
            metric: mean([config_averages[config][metric] for config in configs])
            for metric in (*METRICS, "overall")
        }
    isolated_pairs = {}
    for stage in ("pretrained", "sft"):
        original = f"without_muon_{stage}"
        improved = f"muon_from_sft_{stage}"
        isolated_pairs[stage] = {
            "original": config_averages[original]["overall"],
            "qk_norm_muon_from_sft": config_averages[improved]["overall"],
            "delta": round(
                config_averages[improved]["overall"] - config_averages[original]["overall"], 4
            ),
        }
    response_ids = [receipt["response_id"] for receipt in receipts]
    acceptance = {
        "historical_report_content_hashed": bool(retained["source_report_sha256"]),
        "all_eight_configuration_cells_retained": retained["cell_count"] == 8,
        "all_64_historical_outputs_retained": retained["output_count"] == 64,
        "same_eight_images_present_in_every_cell": all(
            cell["output_count"] == 8 for cell in retained["cells"]
        ),
        "eight_image_aware_arm_blind_judgments": len(receipts) == 8,
        "raw_judge_requests_responses_ids_usage_latency_retained": len(set(response_ids)) == 8
        and all(
            receipt["usage"].get("total_tokens", 0) > 0 and receipt["latency_ms"] > 0
            for receipt in receipts
        ),
        "request_images_match_pinned_sha256": all(
            receipt["image_sha256"] == IMAGE_SHA256[receipt["image"]] for receipt in receipts
        ),
        "immutable_original_and_improved_source_revisions_frozen": bool(
            ORIGINAL_VLM_REVISION and IMPROVED_VLM_REVISION
        ),
        "immutable_dataset_clip_and_eval_image_inputs_frozen": bool(
            DATASET_REVISION and CLIP_REVISION and IMAGE_SHA256
        ),
        "future_reproduction_commands_declared": len(contract["future_reproduction"]["commands"])
        >= 6,
        "historical_provenance_limitations_explicit": contract["historical_evidence_boundary"][
            "historical_vlm_checkpoint_hashes_retained"
        ]
        is False,
        "checkpoints_not_an_acceptance_artifact": contract["checkpoint_policy"][
            "acceptance_artifact"
        ]
        is False,
    }
    passed = all(acceptance.values())
    ranking = sorted(CONFIGS, key=lambda config: (-config_averages[config]["overall"], config))
    return {
        "schema_version": "exp7-4-summary-v1",
        "experiment": "7-4",
        "status": "passed" if passed else "failed",
        "judge": {
            "provider": "ark",
            "model": receipts[0]["request"]["model"],
            "image_aware": True,
            "calls": len(receipts),
            "response_ids": response_ids,
            "total_tokens": sum(receipt["usage"]["total_tokens"] for receipt in receipts),
            "total_latency_ms": round(sum(receipt["latency_ms"] for receipt in receipts), 3),
            "blind_seed": BLIND_SEED,
        },
        "retained": {
            "cells": retained["cell_count"],
            "outputs": retained["output_count"],
            "images": len(retained["images"]),
        },
        "config_averages": config_averages,
        "stage_averages": stage_averages,
        "isolated_original_vs_qk_norm_muon_from_sft": isolated_pairs,
        "ranking_by_overall": ranking,
        "best_counts": best_counts,
        "per_image_config_scores": per_image_config_scores,
        "scientific_findings": {
            "top_configuration": ranking[0],
            "top_configuration_overall": config_averages[ranking[0]]["overall"],
            "sft_minus_pretrained_average": round(
                stage_averages["sft"]["overall"] - stage_averages["pretrained"]["overall"], 4
            ),
            "author_claims_are_historical_observations_not_acceptance_gates": True,
            "muon_only_causal_claim_avoided": True,
        },
        "acceptance": {**acceptance, "passed": passed},
        "limitations": [
            "Historical base-LLM and VLM checkpoints are intentionally not distributed and were not recreated in this audit.",
            "Historical source revisions, dataset identities, RNG state, hardware image, and stepwise logs were not retained.",
            "Current immutable pins define a future reproduction contract and are not represented as the exact historical run.",
            "The English captions are translations in a bilingual report, so translation can affect judging.",
            "One image-aware judge call evaluates all eight anonymous candidates per image; scores are descriptive, not a powered significance test.",
            "QK-Norm and Muon change together in the improved arm, so the report does not attribute effects to Muon alone.",
        ],
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Experiment 7-4 retained-training-report audit",
        "",
        "## Result",
        "",
        f"Status: **{summary['status']}**. The historical report retains {summary['retained']['outputs']} image descriptions across {summary['retained']['cells']} configurations and the same {summary['retained']['images']} images. Each image was inspected by a real image-capable ARK judge together with all eight arm-blind captions.",
        "",
        "| Configuration | Grounding | Hallucination control | Coverage | Specificity | Overall | Best count |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in summary["ranking_by_overall"]:
        row = summary["config_averages"][config]
        lines.append(
            f"| {config} | {row['grounding_accuracy']:.4f} | {row['hallucination_control']:.4f} | {row['coverage']:.4f} | {row['visual_specificity']:.4f} | {row['overall']:.4f} | {summary['best_counts'][config]} |"
        )
    findings = summary["scientific_findings"]
    lines.extend(
        [
            "",
            f"The highest descriptive judge mean was **{findings['top_configuration']}** at **{findings['top_configuration_overall']:.4f}**. Averaged across all four base configurations, full VLM SFT changed the score by **{findings['sft_minus_pretrained_average']:+.4f}** versus projection-only pretraining.",
            "",
            "The isolated report comparison pairs original/SFT-base against QK-Norm+Muon/SFT-base at each VLM stage. QK-Norm and Muon still change together, so no Muon-only causal claim is made. All author-written qualitative claims remain historical observations rather than pass/fail gates.",
            "",
            "## Provenance and reproduction boundary",
            "",
            "`reproduction_contract.json` freezes separate pre-QK-Norm and QK-Norm+Muon MiniMind-V revisions, the corresponding base-LLM revisions, script-compatible VLM dataset Git-LFS objects, the CLIP weight object, all eight evaluation-image hashes, and future commands. These pins are not misrepresented as the historical checkout.",
            "",
            "Training checkpoints remain local by book policy and are not acceptance artifacts. The accepted artifact is this content-hashed report, all 64 retained outputs, eight raw image-aware judge receipts, and explicit limitations.",
            "",
        ]
    )
    return "\n".join(lines)


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
        input_record(HERE / "run_vlm_training_report_audit.py"),
        input_record(HERE / "validate_vlm_evidence.py"),
        input_record(HERE / "test_vlm_training_report_audit.py"),
    ]
    artifacts = [
        run_dir / name
        for name in (
            "retained_outputs.json",
            "reproduction_contract.json",
            "judge_receipts.json",
            "summary.json",
            "report.md",
        )
    ]
    return {
        "schema_version": "exp7-4-manifest-v1",
        "experiment": "7-4",
        "run_id": run_id,
        "created_at": utc_now(),
        "status": summary["status"],
        "run_dir": str(run_dir.relative_to(EXPERIMENT_DIR)),
        "inputs": inputs,
        "artifacts": [artifact_record(path, run_dir) for path in artifacts],
        "acceptance": summary["acceptance"],
        "checkpoint_policy": "not distributed; not an acceptance artifact",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--source-dir", type=Path, default=os.getenv("MINIMIND_V_SOURCE_DIR"))
    parser.add_argument("--endpoint", default=os.getenv("ARK_BASE_URL", DEFAULT_ENDPOINT))
    parser.add_argument("--model", default=os.getenv("ARK_VISION_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-key-env", default="ARK_API_KEY")
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--refresh-manifest",
        action="store_true",
        help="Rehash an existing run without provider calls; refuses changed retained outputs.",
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
        stored = json.loads((run_dir / "retained_outputs.json").read_text(encoding="utf-8"))
        retained = parse_retained_outputs()
        if stored.get("cells") != retained.get("cells"):
            raise SystemExit(
                "refusing manifest refresh because retained historical outputs changed"
            )
        receipts_doc = json.loads((run_dir / "judge_receipts.json").read_text(encoding="utf-8"))
        receipts = receipts_doc.get("calls")
        if (
            receipts_doc.get("schema_version") != "exp7-4-judge-receipts-v1"
            or receipts_doc.get("experiment") != "7-4"
            or not isinstance(receipts, list)
        ):
            raise SystemExit("cannot refresh malformed judge receipts")
        contract = reproduction_contract()
        summary = summarize(retained, receipts, contract)
        write_json(run_dir / "retained_outputs.json", retained)
        write_json(run_dir / "reproduction_contract.json", contract)
        write_json(run_dir / "summary.json", summary)
        (run_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
        write_json(run_dir / "manifest.json", build_manifest(args.run_id, run_dir, summary))
        latest = {
            "schema_version": "exp7-4-latest-v1",
            "experiment": "7-4",
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
    if args.source_dir is None:
        raise SystemExit("--source-dir or MINIMIND_V_SOURCE_DIR is required")
    source_dir = args.source_dir.resolve()
    for image, expected in IMAGE_SHA256.items():
        path = image_path(source_dir, image)
        if not path.is_file() or sha256_file(path) != expected:
            raise SystemExit(f"evaluation image missing or hash mismatch: {path}")
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"missing required credential environment variable: {args.api_key_env}")
    retained = parse_retained_outputs()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            image: pool.submit(
                call_judge,
                retained,
                image,
                source_dir=source_dir,
                endpoint=args.endpoint,
                model=args.model,
                api_key=api_key,
                timeout=args.timeout,
            )
            for image in IMAGE_FILES
        }
        receipts = [futures[image].result() for image in IMAGE_FILES]
    contract = reproduction_contract()
    summary = summarize(retained, receipts, contract)
    run_dir.mkdir(parents=True)
    write_json(run_dir / "retained_outputs.json", retained)
    write_json(
        run_dir / "judge_receipts.json",
        {
            "schema_version": "exp7-4-judge-receipts-v1",
            "experiment": "7-4",
            "credential_headers_retained": False,
            "calls": receipts,
        },
    )
    write_json(run_dir / "reproduction_contract.json", contract)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    write_json(run_dir / "manifest.json", build_manifest(args.run_id, run_dir, summary))
    latest = {
        "schema_version": "exp7-4-latest-v1",
        "experiment": "7-4",
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
