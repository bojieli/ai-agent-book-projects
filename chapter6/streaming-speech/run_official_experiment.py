#!/usr/bin/env python3
"""Run Experiment 9-3 unchanged and bind local-model/audio/source provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parent
MODEL_ID = "mlx-community/Qwen2-Audio-7B-Instruct-4bit"
MODEL_REVISION = "c65570002626f41b4dc08b7b54f42f99f3e82e7f"
REFERENCE = "麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，别忘了通知大家。"
SOURCE_FILES = [
    "run_official_experiment.py",
    "demo.py",
    "qwen2_streaming.py",
    "whisper_baseline.py",
    "prepare_scenarios.py",
]
AUDIO_FILES = [
    "audio/sentence.wav",
    "validation/scenarios/normal.wav",
    "validation/scenarios/long_pause.wav",
    "validation/scenarios/background_noise.wav",
]
SECRET_ENV_NAMES = (
    "ARK_API_KEY",
    "MOONSHOT_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def find_credential_hits(payloads: Iterable[bytes]) -> Dict[str, int]:
    blobs = list(payloads)
    actual_secret_hits = 0
    for name in SECRET_ENV_NAMES:
        secret = os.getenv(name, "").encode("utf-8")
        if len(secret) >= 8:
            actual_secret_hits += sum(blob.count(secret) for blob in blobs)
    patterns = (
        re.compile(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|")[^"]+"'),
        re.compile(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}'),
    )
    pattern_hits = sum(len(pattern.findall(blob)) for pattern in patterns for blob in blobs)
    return {"actual_secret_hits": actual_secret_hits, "credential_pattern_hits": pattern_hits}


def bool_gate(value: bool, **details: Any) -> Dict[str, Any]:
    return {"status": "pass" if value else "fail", **details}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="immutable validation/runs directory name")
    parser.add_argument("--output-root", default=str(ROOT / "validation" / "runs"))
    return parser.parse_args()


def main(args: argparse.Namespace) -> int:
    run_id = args.run_id or f"exp9-3-qwen2audio-whisper-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    run_dir = Path(args.output_root).resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    started = time.monotonic()

    source_hashes_before = {name: sha256_file(ROOT / name) for name in SOURCE_FILES}
    audio_hashes = {name: sha256_file(ROOT / name) for name in AUDIO_FILES}
    whisper_path = Path.home() / ".cache" / "whisper" / "tiny.pt"
    if not whisper_path.is_file():
        raise RuntimeError(f"exact Whisper tiny checkpoint is unavailable: {whisper_path}")
    whisper_checkpoint = {
        "path": str(whisper_path),
        "size_bytes": whisper_path.stat().st_size,
        "sha256": sha256_file(whisper_path),
    }

    snapshot = Path(snapshot_download(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_files_only=True,
    ))
    model_files = {}
    for path in sorted(item for item in snapshot.rglob("*") if item.is_file()):
        model_files[str(path.relative_to(snapshot))] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    evidence_path = run_dir / "evidence.json"
    log_path = run_dir / "run.log"
    command = [
        sys.executable,
        str(ROOT / "demo.py"),
        "--model", MODEL_ID,
        "--device", "mlx",
        "--chunk-seconds", "2",
        "--whisper-model", "tiny",
        "--audio", "validation/scenarios/normal.wav",
        "--reference", REFERENCE,
        "--scenario", "normal",
        "--audio", "validation/scenarios/long_pause.wav",
        "--reference", REFERENCE,
        "--scenario", "pause",
        "--audio", "validation/scenarios/background_noise.wav",
        "--reference", REFERENCE,
        "--scenario", "noise",
        "--evidence", str(evidence_path),
    ]
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    if process.returncode != 0:
        raise RuntimeError(f"exact experiment command failed with exit code {process.returncode}")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    source_hashes_after = {name: sha256_file(ROOT / name) for name in SOURCE_FILES}
    by_scenario = {case["scenario"]: case for case in evidence["cases"]}
    qwen_prefixes = [
        prefix
        for case in evidence["cases"]
        for prefix in case["qwen2_audio"]
    ]
    model_weight = model_files.get("weights.safetensors", {})
    credential_scan = find_credential_hits([evidence_path.read_bytes(), log_path.read_bytes()])
    gates = {
        "exact_qwen2audio_mlx_design": bool_gate(
            evidence["model"] == MODEL_ID
            and evidence["device"] == "mlx"
            and evidence["method"] == "growing-prefix full re-encoding (not true streaming)"
            and evidence["parameters"]["chunk_seconds"] == 2.0,
        ),
        "exact_600ms_vad_whisper_tiny_design": bool_gate(
            evidence["parameters"]["vad_silence_ms"] == 600
            and evidence["parameters"]["whisper_model"] == "tiny"
            and all(case.get("whisper_vad") for case in evidence["cases"]),
        ),
        "normal_pause_noise_inputs": bool_gate(
            set(by_scenario) == {"normal", "pause", "noise"}
            and all(
                by_scenario[scenario]["media"]["sha256"] == audio_hashes[path]
                for scenario, path in (
                    ("normal", "validation/scenarios/normal.wav"),
                    ("pause", "validation/scenarios/long_pause.wav"),
                    ("noise", "validation/scenarios/background_noise.wav"),
                )
            ),
        ),
        "raw_qwen_outputs_retained": bool_gate(
            len(qwen_prefixes) == 13
            and all(prefix.get("raw_response") for prefix in qwen_prefixes),
            prefix_count=len(qwen_prefixes),
        ),
        "runtime_sources_stable_and_hashed": bool_gate(
            source_hashes_before == source_hashes_after,
            count=len(source_hashes_before),
        ),
        "full_model_snapshot_hashed": bool_gate(
            snapshot.name == MODEL_REVISION
            and len(model_files) >= 8
            and model_weight.get("size_bytes") == 6562540479
            and len(model_weight.get("sha256", "")) == 64,
            revision=snapshot.name,
            file_count=len(model_files),
            total_bytes=sum(item["size_bytes"] for item in model_files.values()),
        ),
        "whisper_checkpoint_hashed": bool_gate(
            whisper_checkpoint["sha256"]
            == evidence["provenance"]["host"]["whisper_baseline"]["sha256"],
            size_bytes=whisper_checkpoint["size_bytes"],
        ),
        "credential_free_local_artifacts": bool_gate(
            credential_scan["actual_secret_hits"] == 0
            and credential_scan["credential_pattern_hits"] == 0,
            **credential_scan,
        ),
    }
    overall_status = "pass" if all(item["status"] == "pass" for item in gates.values()) else "incomplete"

    acceptance = {
        "schema_version": 1,
        "experiment": "9-3",
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "git_commit": git_commit(),
        "execution_gates": gates,
        "execution_status": overall_status,
        "manuscript_result_claims": evidence["acceptance"]["manuscript_result_claims"],
        "manuscript_results_reproduced": evidence["acceptance"]["manuscript_results_reproduced"],
        "event_evaluation": {
            scenario: by_scenario[scenario]["qwen2_event_evaluation"]
            for scenario in ("normal", "pause", "noise")
        },
        "qwen_inference_seconds": [prefix["inference_seconds"] for prefix in qwen_prefixes],
        "whisper_post_endpoint_response_seconds": {
            scenario: by_scenario[scenario]["whisper_vad"]["post_endpoint_response_seconds"]
            for scenario in ("normal", "pause", "noise")
        },
        "runtime_source_sha256": source_hashes_before,
        "audio_sha256": audio_hashes,
        "whisper_checkpoint": whisper_checkpoint,
        "qwen2_audio_snapshot": {
            "repository": MODEL_ID,
            "revision": snapshot.name,
            "path": str(snapshot),
            "files": model_files,
        },
        "credential_scan": credential_scan,
        "passed_gates": sum(item["status"] == "pass" for item in gates.values()),
        "total_gates": len(gates),
    }
    acceptance_path = run_dir / "acceptance.json"
    write_json(acceptance_path, acceptance)

    manifest = {
        "schema_version": 1,
        "experiment": "9-3",
        "run_id": run_id,
        "generated_at": utc_now(),
        "git_commit": acceptance["git_commit"],
        "runtime_source_sha256": source_hashes_before,
        "audio_sha256": audio_hashes,
        "whisper_checkpoint": whisper_checkpoint,
        "qwen2_audio_snapshot": acceptance["qwen2_audio_snapshot"],
        "artifact_sha256": {
            path.name: sha256_file(path)
            for path in (evidence_path, log_path, acceptance_path)
        },
        "acceptance": {
            "execution_status": overall_status,
            "passed_gates": acceptance["passed_gates"],
            "total_gates": acceptance["total_gates"],
            "manuscript_results_reproduced": acceptance["manuscript_results_reproduced"],
        },
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)

    latest = ROOT / "validation" / "latest_official.json"
    write_json(latest, {
        "schema_version": 1,
        "run_id": run_id,
        "run_directory": str(run_dir.relative_to(ROOT)),
        "manifest_sha256": sha256_file(manifest_path),
        "execution_status": overall_status,
        "manuscript_results_reproduced": acceptance["manuscript_results_reproduced"],
    })
    print(json.dumps({
        "run_id": run_id,
        "run_directory": str(run_dir),
        "execution_status": overall_status,
        "passed_gates": acceptance["passed_gates"],
        "total_gates": acceptance["total_gates"],
        "manuscript_result_claims": acceptance["manuscript_result_claims"],
        "event_evaluation": acceptance["event_evaluation"],
    }, ensure_ascii=False, indent=2))
    return 0 if overall_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
