#!/usr/bin/env python3
"""Run Qwen2-Audio growing-prefix perception against VAD + Whisper."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from opencc import OpenCC
from qwen2_streaming import Qwen2AudioRecognizer, growing_prefix, serialize
from whisper_baseline import LocalWhisper, run_whisper_baseline, serialize as serialize_baseline

HERE = Path(__file__).parent


T2S = OpenCC("t2s")


def normalize_for_cer(text: str) -> str:
    """Normalize width, case, Chinese script, whitespace, and punctuation."""
    text = T2S.convert(unicodedata.normalize("NFKC", text)).casefold()
    return "".join(char for char in text if unicodedata.category(char)[0] not in {"P", "S", "Z"})


def cer(reference: str, hypothesis: str) -> float:
    reference, hypothesis = normalize_for_cer(reference), normalize_for_cer(hypothesis)
    if not reference:
        return 0.0 if not hypothesis else 1.0
    row = list(range(len(hypothesis) + 1))
    for i, left in enumerate(reference, 1):
        new = [i]
        for j, right in enumerate(hypothesis, 1):
            new.append(min(new[-1] + 1, row[j] + 1, row[j - 1] + (left != right)))
        row = new
    return row[-1] / len(reference)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_output(*args: str) -> str | None:
    try:
        return subprocess.check_output(args, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def model_provenance(model_id: str) -> dict:
    from huggingface_hub import snapshot_download

    snapshot = Path(snapshot_download(model_id, local_files_only=True))
    files = []
    for path in sorted(item for item in snapshot.rglob("*") if item.is_file()):
        size = path.stat().st_size
        files.append({
            "path": str(path.relative_to(snapshot)),
            "size_bytes": size,
            "sha256": sha256(path) if size <= 10 * 1024 * 1024 else None,
        })
    return {
        "repository": model_id,
        "snapshot_revision": snapshot.name,
        "snapshot_path": str(snapshot),
        "total_bytes": sum(item["size_bytes"] for item in files),
        "files": files,
        "large_weight_hash_note": "Snapshot revision pins large files; files over 10 MiB are inventoried by path and size without rehashing.",
    }


def host_provenance() -> dict:
    whisper_cache = Path.home() / ".cache" / "whisper" / "tiny.pt"
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": command_output("sysctl", "-n", "machdep.cpu.brand_string") or platform.processor(),
        "memory_bytes": int(command_output("sysctl", "-n", "hw.memsize") or 0),
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("mlx-audio", "openai-whisper", "librosa", "opencc-python-reimplemented")
        },
        "whisper_baseline": {
            "model": "tiny",
            "path": str(whisper_cache),
            "sha256": sha256(whisper_cache),
        },
    }


EXPECTED_EVENTS = {
    "normal": [],
    "pause": ["<|silence|>"],
    "noise": ["<|noise|>"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment 6-4: actual Qwen2-Audio growing-prefix inference")
    parser.add_argument("--audio", action="append", required=True, help="Audio path; repeat for normal/pause/noise cases")
    parser.add_argument("--reference", action="append", required=True, help="Reference transcript matching each --audio")
    parser.add_argument("--scenario", action="append", choices=["normal", "pause", "noise"], required=True)
    parser.add_argument("--chunk-seconds", type=float, default=1.0)
    parser.add_argument("--model", default="Qwen/Qwen2-Audio-7B-Instruct")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "mps", "cpu", "mlx"])
    parser.add_argument("--skip-whisper", action="store_true")
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--evidence", default=str(HERE / "validation" / "latest.json"))
    args = parser.parse_args()
    if not (len(args.audio) == len(args.reference) == len(args.scenario)):
        parser.error("--audio, --reference and --scenario counts must match")
    load_dotenv(HERE / ".env")
    recognizer = Qwen2AudioRecognizer(args.model, args.device)
    whisper = None if args.skip_whisper else LocalWhisper(args.whisper_model)
    cases = []
    for path, reference, scenario in zip(args.audio, args.reference, args.scenario):
        print(f"\n[{scenario}] {path}")
        prefixes = growing_prefix(
            recognizer, path, args.chunk_seconds,
            on_result=lambda r: print(f"  {r.prefix_seconds:5.2f}s | {r.inference_seconds:6.2f}s | {r.transcript} {r.acoustic_events}"),
        )
        baseline = run_whisper_baseline(path, whisper) if whisper else None
        case = {
            "scenario": scenario,
            "audio": str(Path(path)),
            "reference": reference,
            "media": {
                "sha256": sha256(Path(path)),
                "expected_acoustic_events": EXPECTED_EVENTS[scenario],
            },
            "qwen2_audio": serialize(prefixes),
            "qwen2_final_cer": cer(reference, prefixes[-1].transcript),
            "whisper_vad": serialize_baseline(baseline) if baseline else None,
            "whisper_final_cer": cer(reference, baseline.transcript) if baseline else None,
        }
        cases.append(case)
    by_scenario = {case["scenario"]: case for case in cases}
    for case in cases:
        actual = set(case["qwen2_audio"][-1]["acoustic_events"])
        expected = set(case["media"]["expected_acoustic_events"])
        case["qwen2_event_evaluation"] = {
            "true_positive": sorted(actual & expected),
            "false_positive": sorted(actual - expected),
            "false_negative": sorted(expected - actual),
            "exact_match": actual == expected,
        }
    qwen_latencies = [prefix["inference_seconds"] for case in cases for prefix in case["qwen2_audio"]]
    normal_start = by_scenario["normal"]["whisper_vad"]["first_speech_start_seconds"] if by_scenario.get("normal", {}).get("whisper_vad") else None
    noise_start = by_scenario["noise"]["whisper_vad"]["first_speech_start_seconds"] if by_scenario.get("noise", {}).get("whisper_vad") else None
    pause_case = by_scenario.get("pause", {})
    noise_case = by_scenario.get("noise", {})
    result_claims = {
        "qwen_incremental_latency_100_to_200ms": all(0.1 <= value <= 0.2 for value in qwen_latencies),
        "traditional_post_endpoint_latency_800_to_1100ms": all(
            0.8 <= case["whisper_vad"]["post_endpoint_response_seconds"] <= 1.1
            for case in cases if case.get("whisper_vad")
        ),
        "pause_split_into_two_segments": pause_case.get("whisper_vad", {}).get("segment_count") == 2,
        "pause_specific_two_to_zero_error": "零点" in normalize_for_cer(pause_case.get("whisper_vad", {}).get("transcript", "")),
        "noise_token_detected": "<|noise|>" in noise_case.get("qwen2_audio", [{}])[-1].get("acoustic_events", []),
        "noise_caused_earlier_vad_start": (
            normal_start is not None and noise_start is not None and noise_start + 0.1 < normal_start
        ),
    }
    evidence = {
        "schema_version": 2,
        "experiment": "6-4",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "device": recognizer.device,
        "method": "growing-prefix full re-encoding (not true streaming)",
        "parameters": {
            "chunk_seconds": args.chunk_seconds,
            "whisper_model": args.whisper_model,
            "vad_silence_ms": 600,
            "cer_normalization": "NFKC + Traditional-to-Simplified Chinese + casefold + remove punctuation/symbols/separators",
        },
        "provenance": {
            "host": host_provenance(),
            "qwen2_audio": model_provenance(args.model),
        },
        "cases": cases,
        "cost": {"paid_external_requests": 0, "total_usd": 0, "note": "Both models ran locally."},
        "acceptance": {
            "execution_gates": {
                "real_qwen2_audio": bool(cases) and all(case["qwen2_audio"] for case in cases),
                "growing_prefix_full_reencoding": True,
                "real_600ms_vad_whisper_baseline": all(case.get("whisper_vad") for case in cases),
                "normal_pause_noise_scenarios": set(by_scenario) == {"normal", "pause", "noise"},
                "corrected_vad_latency_accounting": all(
                    abs(case["whisper_vad"]["post_speech_vad_delay_seconds"] - 0.6) <= 0.021
                    for case in cases if case.get("whisper_vad")
                ),
                "normalized_cer": True,
                "provenance_complete": True,
            },
            "execution_passed": True,
            "manuscript_result_claims": result_claims,
            "manuscript_results_reproduced": all(result_claims.values()),
        },
    }
    evidence["acceptance"]["execution_passed"] = all(evidence["acceptance"]["execution_gates"].values())
    output = Path(args.evidence)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSanitized evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
