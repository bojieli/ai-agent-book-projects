import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "validation" / "runs" / "exp10-6-real-receipts-20260730-v2"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_bytes(value) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def test_official_manifest_binds_artifacts_and_runtime_sources():
    manifest = json.loads((RUN / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["acceptance"] == {
        "overall_status": "pass",
        "passed_gates": 12,
        "total_gates": 12,
    }
    for name, expected in manifest["artifact_sha256"].items():
        assert sha256_bytes((RUN / name).read_bytes()) == expected
    for name, expected in manifest["runtime_source_sha256"].items():
        assert sha256_bytes((ROOT / name).read_bytes()) == expected


def test_official_receipts_are_raw_hashed_and_cover_all_three_phases():
    browser = json.loads((RUN / "browser_receipts.json").read_text(encoding="utf-8"))["receipts"]
    llm = json.loads((RUN / "llm_receipts.json").read_text(encoding="utf-8"))["receipts"]
    successful = [item for item in llm if item["kind"] == "llm_chat_completion"]

    assert len(browser) == 24
    assert {item["phase"] for item in browser} == {
        "default_parallel", "default_serial", "cascade_stress",
    }
    for item in browser:
        raw = item["rendered_body_text"].encode("utf-8")
        assert len(raw) == item["rendered_body_bytes"]
        assert sha256_bytes(raw) == item["rendered_body_sha256"]

    assert len(successful) == 3
    assert len({item["response_id"] for item in successful}) == 3
    assert {item["context"]["phase"] for item in successful} == {
        "default_parallel", "default_serial", "cascade_stress",
    }
    for item in successful:
        assert item["response"]
        assert item["usage"]["total_tokens"] > 0
        assert sha256_bytes(canonical_bytes(item["request"])) == item["request_sha256"]
        assert sha256_bytes(canonical_bytes(item["response"])) == item["response_sha256"]


def test_official_acceptance_and_latest_pointer_are_consistent_and_credential_free():
    evidence = json.loads((RUN / "evidence.json").read_text(encoding="utf-8"))
    latest = json.loads((ROOT / "validation" / "latest.json").read_text(encoding="utf-8"))
    assert evidence["overall_status"] == "pass"
    assert all(item["status"] == "pass" for item in evidence["gates"].values())
    assert evidence["measured_speedup"] > 1
    assert latest["run_id"] == evidence["run_id"]
    assert latest["manifest_sha256"] == sha256_bytes((RUN / "manifest.json").read_bytes())

    combined = b"\n".join(path.read_bytes() for path in RUN.iterdir() if path.is_file())
    assert not re.search(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|")[^"]+"', combined)
    assert not re.search(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}', combined)
