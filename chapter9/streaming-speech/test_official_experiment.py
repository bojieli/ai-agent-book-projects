import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "validation" / "runs" / "exp9-3-qwen2audio-whisper-provenance-20260730-v3"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def test_official_manifest_binds_artifacts_sources_audio_and_local_checkpoints():
    manifest = json.loads((RUN / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["acceptance"] == {
        "execution_status": "pass",
        "passed_gates": 8,
        "total_gates": 8,
        "manuscript_results_reproduced": False,
    }
    for name, expected in manifest["artifact_sha256"].items():
        assert sha256_file(RUN / name) == expected
    for name, expected in manifest["runtime_source_sha256"].items():
        assert sha256_file(ROOT / name) == expected
    for name, expected in manifest["audio_sha256"].items():
        assert sha256_file(ROOT / name) == expected
    whisper = manifest["whisper_checkpoint"]
    assert sha256_file(Path(whisper["path"])) == whisper["sha256"]

    snapshot = Path(manifest["qwen2_audio_snapshot"]["path"])
    files = manifest["qwen2_audio_snapshot"]["files"]
    assert files["weights.safetensors"] == {
        "size_bytes": 6562540479,
        "sha256": "0967cde270ad62aa4824f0bbce283d0a2a6da2825ccf587640753c527d4174da",
    }
    for name, item in files.items():
        assert (snapshot / name).stat().st_size == item["size_bytes"]
        if name != "weights.safetensors":
            assert sha256_file(snapshot / name) == item["sha256"]


def test_official_run_retains_raw_prefixes_and_negative_manuscript_results():
    evidence = json.loads((RUN / "evidence.json").read_text(encoding="utf-8"))
    acceptance = json.loads((RUN / "acceptance.json").read_text(encoding="utf-8"))
    prefixes = [prefix for case in evidence["cases"] for prefix in case["qwen2_audio"]]
    assert len(prefixes) == 13
    assert all(prefix["raw_response"] for prefix in prefixes)
    assert all(item["status"] == "pass" for item in acceptance["execution_gates"].values())
    assert acceptance["manuscript_result_claims"] == {
        "qwen_incremental_latency_100_to_200ms": False,
        "traditional_post_endpoint_latency_800_to_1100ms": False,
        "pause_split_into_two_segments": True,
        "pause_specific_two_to_zero_error": False,
        "noise_token_detected": True,
        "noise_caused_earlier_vad_start": False,
    }
    assert acceptance["manuscript_results_reproduced"] is False
    assert acceptance["event_evaluation"]["pause"]["false_negative"] == ["<|silence|>"]
    assert acceptance["event_evaluation"]["noise"]["false_positive"] == [
        "<|cough|>", "<|laughter|>",
    ]


def test_official_latest_and_credential_scan_are_consistent():
    latest = json.loads((ROOT / "validation" / "latest_official.json").read_text(encoding="utf-8"))
    acceptance = json.loads((RUN / "acceptance.json").read_text(encoding="utf-8"))
    assert latest["run_id"] == acceptance["run_id"]
    assert latest["manifest_sha256"] == sha256_file(RUN / "manifest.json")
    assert acceptance["credential_scan"] == {
        "actual_secret_hits": 0,
        "credential_pattern_hits": 0,
    }
    combined = b"\n".join(path.read_bytes() for path in RUN.iterdir() if path.is_file())
    assert not re.search(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|")[^"]+"', combined)
    assert not re.search(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}', combined)
