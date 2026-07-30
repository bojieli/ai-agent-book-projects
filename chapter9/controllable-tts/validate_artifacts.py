#!/usr/bin/env python3
"""Validate real Fish S1 Experiment 9-5 media without making new API calls."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
MANIFEST = HERE / "reference_audio" / "manifest.json"
RUN = HERE / "validation" / "latest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path: Path) -> dict[str, float | int | str]:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size,format_name",
        "-of", "json", str(path),
    ], text=True)
    info = json.loads(raw)["format"]
    return {"duration_seconds": float(info["duration"]), "size_bytes": int(info["size"]), "format": info["format_name"]}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    run = json.loads(RUN.read_text())
    profiles = manifest["profiles"]
    reference_checks = []
    for key, profile in sorted(profiles.items()):
        path = HERE / "reference_audio" / profile["path"]
        media = probe(path)
        reference_checks.append({
            "profile": key,
            "path": str(path.relative_to(HERE)),
            "exists": path.exists(),
            "sha256": sha256(path),
            "manifest_sha256": profile["sha256"],
            "hash_matches": sha256(path) == profile["sha256"],
            **media,
        })
    outputs = {}
    for name, recorded in run["outputs"].items():
        path = HERE / "output" / Path(recorded["path"]).name
        outputs[name] = {
            "path": str(path.relative_to(HERE)),
            "sha256": sha256(path),
            **probe(path),
        }
    dimensions = {
        (profile["emotion"], profile["speed"], profile["style"])
        for profile in profiles.values()
    }
    c_segments = run["outputs"]["C_24_reference_library"]["segments"]
    routed_profiles = [segment["profile"] for segment in c_segments if segment.get("type") == "speech"]
    required_routes = {"happy_fast_casual", "thinking_slow_formal", "neutral_normal_formal"}
    gates = {
        "fish_s1_provider_recorded": run.get("provider") == "Fish Audio" and run.get("backend") == "s1",
        "same_authorized_source_reference": bool(manifest.get("source_reference_id")),
        "exact_4x3x2_reference_library": len(profiles) == 24 and len(dimensions) == 24,
        "all_reference_hashes_match": all(item["hash_matches"] for item in reference_checks),
        "references_approximately_five_seconds": all(3.0 <= item["duration_seconds"] <= 7.0 for item in reference_checks),
        "three_real_comparison_outputs": set(outputs) == {
            "A_no_control_markers", "B_single_reference", "C_24_reference_library"
        } and all(item["size_bytes"] > 1000 and item["duration_seconds"] > 0 for item in outputs.values()),
        "required_marker_routes_exercised": required_routes.issubset(set(routed_profiles)),
        "thinking_pause_1_to_2_seconds": any(
            segment.get("type") == "silence" and 1000 <= segment.get("ms", 0) <= 2000
            for segment in c_segments
        ),
        "thinking_native_filler_exercised": any("(uncertain)" in segment.get("fish_text", "") for segment in c_segments),
    }
    artifact = {
        "schema_version": 2,
        "experiment": "9-5",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_generation": {
            "recorded_timestamp_utc": run["timestamp_utc"],
            "provider": run["provider"],
            "backend": run["backend"],
            "source_reference_id_sha256": hashlib.sha256(manifest["source_reference_id"].encode()).hexdigest(),
            "source_reference_value_saved_in_manifest": True,
            "estimated_paid_api_requests": 30,
            "request_count_basis": "24 reference renders + A(1) + B(1) + C(4 speech segments); local silence is not an API call",
            "provider_reported_cost_usd": None,
            "cost_note": "Fish SDK responses did not expose monetary charges; consult the provider billing ledger.",
        },
        "validation_provenance": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "manifest_sha256": sha256(MANIFEST),
            "run_evidence_sha256": sha256(RUN),
            "implementation_sha256": {
                name: sha256(HERE / name) for name in ("demo.py", "tts.py", "markup.py", "voice_library.py")
            },
        },
        "reference_statistics": {
            "count": len(reference_checks),
            "minimum_duration_seconds": min(item["duration_seconds"] for item in reference_checks),
            "maximum_duration_seconds": max(item["duration_seconds"] for item in reference_checks),
            "mean_duration_seconds": sum(item["duration_seconds"] for item in reference_checks) / len(reference_checks),
        },
        "reference_checks": reference_checks,
        "outputs": outputs,
        "acceptance": {
            "structural_and_media_gates": gates,
            "structural_and_media_passed": all(gates.values()),
            "qualitative_listening_study_present": False,
            "near_human_customer_service_claim_evaluated": False,
            "manuscript_results_fully_reproduced": False,
            "statement": "Real Fish S1 media fulfills the construction and A/B/C comparison. The subjective quality ordering remains unevaluated.",
        },
    }
    output = HERE / "validation" / "acceptance.json"
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0 if artifact["acceptance"]["structural_and_media_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
