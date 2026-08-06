"""Offline acceptance checks for the exact Experiment 4-1 campaign."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_experiment_4_1.py"
SPEC = importlib.util.spec_from_file_location("experiment_4_1_runner", RUNNER)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _protocol() -> dict:
    return json.loads((HERE / "experiment_protocol.json").read_text(encoding="utf-8"))


def _receipt(case: str, *, success: bool = True) -> dict:
    return {
        "case": case,
        "tool": runner.CASE_TO_TOOL[case],
        "transport": "mcp-stdio",
        "mcp_result_is_error": False,
        "success": success,
        "substantive_observation": success,
        "backend_provenance": runner.PROVENANCE[runner.CASE_TO_TOOL[case]],
        "simulation_markers": [],
        "error_type": None,
        "payload": {"success": success},
    }


def _all_receipts() -> list[dict]:
    protocol = _protocol()
    return [
        _receipt(case)
        for category in protocol["categories"].values()
        for case in category.get("required_cases", []) + category.get("required_safety_cases", [])
    ]


def _catalog() -> dict:
    names = set(runner.CASE_TO_TOOL.values())
    names.update(f"extra_{index}" for index in range(120))
    return {
        "transport": "mcp-stdio",
        "tools_list_received": True,
        "mcp_sdk_version": "2.0.0",
        "protocol_version": "2026-07-28",
        "tool_count": len(names),
        "unique_tool_count": len(names),
        "tool_names": sorted(names),
    }


def test_catalog_gate_requires_v2_sdk_and_current_protocol():
    catalog = _catalog()
    assert runner.derive_acceptance(
        _protocol(), catalog, _all_receipts(), outside_witness_unchanged=True
    )["gates"]["catalog_from_real_mcp"]

    catalog["protocol_version"] = "2025-11-25"
    assert not runner.derive_acceptance(
        _protocol(), catalog, _all_receipts(), outside_witness_unchanged=True
    )["gates"]["catalog_from_real_mcp"]

    catalog.update(protocol_version="2026-07-28", mcp_sdk_version="1.29.0")
    assert not runner.derive_acceptance(
        _protocol(), catalog, _all_receipts(), outside_witness_unchanged=True
    )["gates"]["catalog_from_real_mcp"]


def test_protocol_covers_every_manuscript_category_and_mutation():
    protocol = _protocol()
    assert list(protocol["categories"]) == [
        "search", "multimodal", "filesystem", "public_data", "private_data"
    ]
    assert {"filesystem_move", "filesystem_copy", "filesystem_delete"} <= set(
        protocol["categories"]["filesystem"]["required_cases"]
    )
    assert {"calendar_events", "notion_search"} == set(
        protocol["categories"]["private_data"]["required_cases"]
    )


def test_acceptance_fails_closed_when_receipts_are_missing():
    result = runner.derive_acceptance(
        _protocol(), _catalog(), [], outside_witness_unchanged=True
    )
    assert result["status"] == "failed"
    assert not result["gates"]["exact_case_set_recorded"]
    assert not result["gates"]["private_data_category_passed"]


def test_private_credential_failure_is_blocked_and_never_passed():
    receipts = _all_receipts()
    for receipt in receipts:
        if receipt["case"] in {"calendar_events", "notion_search"}:
            receipt.update({
                "success": False,
                "substantive_observation": False,
                "error_type": "missing_credentials",
                "payload": {
                    "success": False,
                    "metadata": {"error_type": "missing_credentials"},
                },
            })
        if receipt["case"].startswith("reject_"):
            receipt.update({
                "success": False,
                "substantive_observation": False,
                "error_type": "PermissionError",
                "payload": {"success": False},
            })
    result = runner.derive_acceptance(
        _protocol(), _catalog(), receipts, outside_witness_unchanged=True
    )
    assert result["status"] == "blocked"
    assert result["categories"]["private_data"]["status"] == "blocked"
    assert result["gates"]["private_data_category_passed"] is False


def test_mock_marker_invalidates_an_apparent_success():
    receipt = _receipt("weather")
    receipt["simulation_markers"] = ["mock"]
    assert runner.valid_success(receipt) is False


def test_isolation_probe_must_preserve_outside_witness():
    receipts = _all_receipts()
    for receipt in receipts:
        if receipt["case"].startswith("reject_"):
            receipt.update({
                "success": False,
                "substantive_observation": False,
                "error_type": "PermissionError",
            })
    result = runner.derive_acceptance(
        _protocol(), _catalog(), receipts, outside_witness_unchanged=False
    )
    assert result["status"] == "failed"
    assert result["gates"]["filesystem_isolation_probes_rejected"] is False
