"""Validate the durable real-MCP evidence for Experiment 4-1."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE / "validation" / "experiment_4_1" / "real_mcp_20260729T214721Z"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_campaign_has_honest_category_statuses_and_exact_receipts():
    summary = _json(CAMPAIGN / "summary.json")
    assert summary["status"] == "blocked"
    assert summary["receipt_count"] == 28
    categories = summary["acceptance"]["categories"]
    assert {name: value["status"] for name, value in categories.items()} == {
        "search": "passed",
        "multimodal": "blocked",
        "filesystem": "passed",
        "public_data": "passed",
        "private_data": "blocked",
    }
    assert summary["acceptance"]["gates"]["filesystem_pre_post_hashes_verified"]
    assert summary["acceptance"]["gates"]["filesystem_isolation_probes_rejected"]
    assert summary["acceptance"]["gates"]["all_successes_substantive_and_non_simulated"]
    assert not summary["acceptance"]["gates"]["private_data_category_passed"]
    assert not summary["acceptance"]["gates"]["multimodal_category_passed"]


def test_legacy_catalog_came_from_mcp_and_retains_the_126_tool_contract():
    catalog = _json(CAMPAIGN / "catalog_receipt.json")
    assert catalog["transport"] == "mcp-stdio"
    assert catalog["tools_list_received"] is True
    assert catalog["server_name"] == "perception-tools"
    assert catalog["tool_count"] == catalog["unique_tool_count"] == 126
    names = set(catalog["tool_names"])
    assert {
        "web_search", "document_reader", "image_ocr", "audio_transcribe",
        "filesystem_copy", "filesystem_move", "filesystem_delete",
        "weather", "calendar_events", "notion_search", "code_interpreter",
    } <= names


def test_retained_2026_07_29_campaign_is_explicitly_legacy_evidence():
    """The old receipt must not be mistaken for SDK v2/current-protocol proof."""
    catalog = _json(CAMPAIGN / "catalog_receipt.json")
    assert "mcp_sdk_version" not in catalog
    assert "protocol_version" not in catalog


def test_mutations_have_hash_receipts_and_escape_attempts_failed_closed():
    receipts = {
        path.stem.split("_", 1)[1]: _json(path)
        for path in (CAMPAIGN / "receipts").glob("*.json")
    }
    for case in ("filesystem_copy", "filesystem_move"):
        receipt = receipts[case]
        assert receipt["success"] is True
        assert receipt["substantive_observation"] is True
        assert receipt["payload"]["metadata"]["pre_operation_fingerprint"] == \
            receipt["payload"]["message"]["destination_fingerprint"]
    deleted = receipts["filesystem_delete"]
    assert deleted["success"] is True
    assert deleted["payload"]["message"]["reversible"] is True
    assert deleted["payload"]["metadata"]["pre_operation_fingerprint"] == \
        deleted["payload"]["message"]["quarantine_fingerprint"]

    for case in ("reject_parent_traversal", "reject_absolute_path", "reject_escaping_symlink"):
        receipt = receipts[case]
        assert receipt["success"] is False
        assert receipt["mcp_result_is_error"] is False
        assert receipt["error_type"] == "PermissionError"
    assert _json(CAMPAIGN / "summary.json")["outside_witness_unchanged"] is True


def test_credential_and_quota_blocks_are_real_failures_not_successes():
    receipts = [_json(path) for path in sorted((CAMPAIGN / "receipts").glob("*.json"))]
    by_case = {receipt["case"]: receipt for receipt in receipts}
    for case in ("calendar_events", "notion_search"):
        assert by_case[case]["success"] is False
        assert by_case[case]["error_type"] == "missing_credentials"
        assert by_case[case]["substantive_observation"] is False
    for case in ("image_analyze", "video_analyze"):
        assert by_case[case]["success"] is False
        assert "insufficient_quota" in json.dumps(by_case[case]["payload"])

    preflight = _json(CAMPAIGN / "credential_preflight.json")
    assert preflight["secret_values_recorded"] is False
    assert preflight["google_calendar"]["token_file_exists"] is False
    assert preflight["notion"]["api_key_present"] is False


def test_manifest_hashes_every_durable_campaign_file():
    manifest = _json(CAMPAIGN / "manifest.json")
    assert manifest["file_count"] == len(manifest["files"])
    assert manifest["file_count"] >= 40
    for row in manifest["files"]:
        path = CAMPAIGN / row["path"]
        if row["kind"] == "symlink-target":
            assert path.is_symlink()
            data = os.readlink(path).encode("utf-8")
        else:
            assert path.is_file()
            data = path.read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
