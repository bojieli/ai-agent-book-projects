import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "validation" / "runs" / "exp10-2-kimi-k2.5-tavily-receipts-20260730-v3"


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
        "passed_gates": 15,
        "total_gates": 15,
    }
    for name, expected in manifest["artifact_sha256"].items():
        assert sha256_bytes((RUN / name).read_bytes()) == expected
    for name, expected in manifest["runtime_source_sha256"].items():
        assert sha256_bytes((ROOT / name).read_bytes()) == expected


def test_official_moonshot_receipts_are_raw_hashed_and_unique():
    receipts = json.loads((RUN / "moonshot_receipts.json").read_text(encoding="utf-8"))["receipts"]
    assert len(receipts) == 9
    assert len({item["response_id"] for item in receipts}) == len(receipts)
    assert {item["role"] for item in receipts} == {
        "triage", "research", "data_analysis", "writing",
    }
    for item in receipts:
        assert item["response"]["id"] == item["response_id"]
        assert item["response"]["usage"]["total_tokens"] > 0
        assert sha256_bytes(canonical_bytes(item["request"])) == item["request_sha256"]
        assert sha256_bytes(canonical_bytes(item["response"])) == item["response_sha256"]


def test_official_tavily_receipts_retain_raw_bodies_without_credentials():
    receipts = json.loads((RUN / "tavily_receipts.json").read_text(encoding="utf-8"))["receipts"]
    assert len(receipts) == 3
    for item in receipts:
        assert item["response"]["http_status"] == 200
        assert "api_key" not in item["request"]["body"]
        raw = item["response"]["raw_body"].encode("utf-8")
        assert len(raw) == item["raw_response_bytes"]
        assert sha256_bytes(raw) == item["raw_response_sha256"]
        assert sha256_bytes(canonical_bytes(item["request"])) == item["request_sha256"]


def test_official_acceptance_latest_and_credential_scan_are_consistent():
    acceptance = json.loads((RUN / "acceptance.json").read_text(encoding="utf-8"))
    evidence = json.loads((RUN / "evidence.json").read_text(encoding="utf-8"))
    latest = json.loads((ROOT / "validation" / "latest.json").read_text(encoding="utf-8"))
    assert acceptance["overall_status"] == "pass"
    assert evidence["status"] == "complete"
    assert all(acceptance["behavior_gates"].values())
    assert all(acceptance["provenance_gates"].values())
    assert evidence["handoff_chain"] == [
        "triage", "research", "data_analysis", "writing", "triage",
    ]
    assert latest["run_id"] == acceptance["run_id"]
    assert latest["manifest_sha256"] == sha256_bytes((RUN / "manifest.json").read_bytes())

    combined = b"\n".join(path.read_bytes() for path in RUN.iterdir() if path.is_file())
    assert not re.search(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|")[^"]+"', combined)
    assert not re.search(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}', combined)
