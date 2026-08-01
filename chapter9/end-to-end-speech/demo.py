#!/usr/bin/env python3
"""Run the local MiniCPM-o 4.5 direct-vs-self-cascade campaign."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from speech_model import MODEL_ID, MODEL_REVISION, MiniCPMOClient, sha256_file


HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "fixtures" / "cases.json"
DEFAULT_EVIDENCE = HERE / "validation" / "latest.json"
IMPLEMENTATION_FILES = (
    "demo.py",
    "speech_model.py",
    "validate_evidence.py",
    "requirements.txt",
    "fixtures/cases.json",
)


def matches_expected(response: str, aliases: list[str]) -> bool:
    normalized = response.casefold()
    return any(re.search(rf"(?<!\w){re.escape(alias.casefold())}(?!\w)", normalized) for alias in aliases)


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    required = {"id", "audio", "category", "instruction", "expected_aliases"}
    if not cases or any(required - set(case) for case in cases):
        raise ValueError(f"Malformed case manifest: {path}")
    return cases


def git_metadata() -> dict[str, Any]:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root, text=True
        ).strip())
        return {"commit": commit, "workspace_dirty_at_run": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "workspace_dirty_at_run": None}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Experiment 9-4: local MiniCPM-o 4.5 omni speech evaluation"
    )
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--revision", default=MODEL_REVISION)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--skip-speech-output", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    output_dir = args.output_dir or args.evidence.parent / "outputs"
    client = MiniCPMOClient(
        args.model,
        args.revision,
        enable_tts=not args.skip_speech_output,
        local_files_only=args.local_files_only,
    )
    client.load()

    results = []
    for case in cases:
        audio_path = (args.cases.parent / case["audio"]).resolve()
        direct = client.infer_audio(
            audio_path, case["instruction"], max_new_tokens=args.max_new_tokens
        )
        cascade = client.self_cascade(
            audio_path, case["instruction"], max_new_tokens=args.max_new_tokens
        )
        direct_pass = matches_expected(direct.response, case["expected_aliases"])
        cascade_pass = matches_expected(cascade.response, case["expected_aliases"])
        print(
            f"[{case['id']}] direct={direct.response!r} ({direct.latency_seconds:.3f}s, pass={direct_pass})"
        )
        print(
            f"[{case['id']}] cascade={cascade.response!r} ({cascade.latency_seconds:.3f}s, pass={cascade_pass})"
        )
        results.append({
            **case,
            "audio_path": str(audio_path.relative_to(HERE)),
            "audio_sha256": sha256_file(audio_path),
            "direct": {**direct.to_dict(), "passed": direct_pass},
            "self_cascade": {**cascade.to_dict(), "passed": cascade_pass},
        })

    speech_output = None
    if not args.skip_speech_output:
        speech_case = cases[0]
        audio_path = (args.cases.parent / speech_case["audio"]).resolve()
        output_audio_path = (output_dir / f"{speech_case['id']}-response.wav").resolve()
        speech_output = client.infer_audio(
            audio_path,
            "Listen to the question and answer aloud in one short sentence.",
            max_new_tokens=args.max_new_tokens,
            output_audio_path=output_audio_path,
        ).to_dict()
        speech_output["output_audio"]["path"] = str(output_audio_path.relative_to(HERE))
        print(f"[speech-output] {speech_output['response']!r}")

    direct_passes = sum(result["direct"]["passed"] for result in results)
    cascade_passes = sum(result["self_cascade"]["passed"] for result in results)
    evidence = {
        "schema_version": 1,
        "experiment": "9-4",
        "title": "MiniCPM-o 4.5 local end-to-end omni speech",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": client.runtime_metadata(),
        "host": {"platform": platform.platform(), **git_metadata()},
        "protocol": {
            "case_count": len(results),
            "direct_arm": "audio -> MiniCPM-o latent processing -> text",
            "self_cascade_arm": "audio -> MiniCPM-o transcript -> MiniCPM-o text reasoning",
            "speech_arm": "audio -> MiniCPM-o latent processing -> text + generated waveform",
            "enable_thinking": False,
            "sampling": False,
            "max_new_tokens": args.max_new_tokens,
        },
        "cases": results,
        "aggregate": {
            "direct_correct": direct_passes,
            "self_cascade_correct": cascade_passes,
            "total_cases": len(results),
            "direct_accuracy": direct_passes / len(results),
            "self_cascade_accuracy": cascade_passes / len(results),
            "direct_mean_latency_seconds": sum(r["direct"]["latency_seconds"] for r in results) / len(results),
            "self_cascade_mean_latency_seconds": sum(r["self_cascade"]["latency_seconds"] for r in results) / len(results),
        },
        "speech_output": speech_output,
        "implementation_sha256": {
            name: sha256_file(HERE / name) for name in IMPLEMENTATION_FILES
        },
        "external_api_calls": 0,
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Evidence: {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
