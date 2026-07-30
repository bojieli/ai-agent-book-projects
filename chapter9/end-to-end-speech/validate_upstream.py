#!/usr/bin/env python3
"""Audit whether the exact four-mode Experiment 9-4 can be reproduced."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi

HERE = Path(__file__).parent
GITHUB_TREE = "https://api.github.com/repos/stepfun-ai/Step-Audio-R1/git/trees/main?recursive=1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent-book-experiment-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    tree = fetch_json(GITHUB_TREE)
    paths = sorted(item["path"] for item in tree.get("tree", []))
    lower_paths = [path.lower() for path in paths]
    api = HfApi()
    hf_models = {}
    for repo in ("stepfun-ai/Step-Audio-R1", "stepfun-ai/Step-Audio-R1.1"):
        info = api.model_info(repo, files_metadata=False)
        hf_models[repo] = {
            "revision": info.sha,
            "last_modified": info.last_modified.isoformat() if info.last_modified else None,
            "file_count": len(info.siblings),
        }
    endpoint = os.getenv("STEP_AUDIO_ENDPOINT", "").strip()
    nvidia = shutil.which("nvidia-smi")
    cuda_probe = None
    if nvidia:
        cuda_probe = subprocess.run(
            [nvidia, "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
    has = lambda term: any(term in path for path in lower_paths)
    public_assets = {
        "single_spoken_mqa_example": "assets/spoken_mqa_test.wav" in paths,
        "full_spoken_mqa_dataset_or_evaluator": has("spoken-mqa") or has("spoken_mqa_eval"),
        "uro_bench_dataset_or_evaluator": has("uro-bench") or has("uro_bench"),
        "mps_paper": "assets/MPS.pdf" in paths,
        "no_thinking_serving_mode": has("no_thinking") or has("nothink"),
        "speak_first_serving_mode": has("speak-first") or has("spkfirst"),
        "think_first_serving_mode": has("think-first") or has("thkfirst"),
        "full_tbs_evaluator": has("tbs_eval") or has("think-before-speak"),
    }
    artifact = {
        "schema_version": 2,
        "experiment": "9-4",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Exact Table 9-1 four-configuration reproduction only",
        "required_configurations": [
            "no-thinking direct answer",
            "MPS Speak-First",
            "MPS Think-First",
            "full TBS",
        ],
        "required_benchmarks": ["Spoken-MQA", "URO-Bench"],
        "local": {
            "platform": platform.platform(),
            "step_audio_endpoint_configured": bool(endpoint),
            "endpoint_value_saved": False,
            "nvidia_smi_available": bool(nvidia),
            "cuda_devices": cuda_probe,
        },
        "upstream": {
            "github_repository": "stepfun-ai/Step-Audio-R1",
            "github_tree_revision": tree.get("sha"),
            "github_tree_file_count": len(paths),
            "huggingface_models": hf_models,
            "public_assets": public_assets,
        },
        "diagnostic_scaffold": {
            "not_experiment_acceptance": True,
            "description": "One public Step-Audio R1 customized-vLLM path plus a Whisper→LLM diagnostic comparator.",
            "implementation_sha256": {
                name: sha256(HERE / name)
                for name in ("speech_model.py", "demo.py", "deploy_step_audio_r1.sh", "chat_template.jinja")
            },
        },
        "acceptance": {
            "exact_step_audio_endpoint": bool(endpoint),
            "required_four_gpu_runtime": bool(cuda_probe and len(cuda_probe.splitlines()) >= 4),
            "all_four_public_serving_modes": all(public_assets[key] for key in (
                "no_thinking_serving_mode", "speak_first_serving_mode",
                "think_first_serving_mode", "full_tbs_evaluator",
            )),
            "full_spoken_mqa_assets": public_assets["full_spoken_mqa_dataset_or_evaluator"],
            "full_uro_bench_assets": public_assets["uro_bench_dataset_or_evaluator"],
            "real_results_saved": False,
            "passed": False,
        },
        "cost": {"paid_external_requests": 0, "total_usd": 0},
        "blocker": (
            "No customized-vLLM endpoint or four-GPU CUDA host is available, and the audited public upstream tree "
            "does not expose the four parameterized MPS/TBS serving+evaluation modes and both full benchmark evaluators."
        ),
    }
    output = HERE / "validation" / "upstream_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
