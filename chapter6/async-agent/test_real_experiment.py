"""Acceptance-ledger regression tests for the durable Experiment 6-2 run."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PATH = HERE / "run_real_experiment.py"
SPEC = importlib.util.spec_from_file_location("experiment_6_2_real", PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _campaign() -> tuple[list[dict], dict]:
    root = HERE / "validation" / "experiment_6_2"
    campaigns = sorted(path for path in root.iterdir() if path.is_dir())
    assert campaigns, "a durable Experiment 6-2 campaign is required"
    campaign = campaigns[-1]
    scenarios = [json.loads(path.read_text(encoding="utf-8"))
                 for path in sorted((campaign / "scenarios").glob("*.json"))]
    protocol = json.loads((campaign / "protocol.json").read_text(encoding="utf-8"))
    return scenarios, protocol


def test_durable_campaign_passes_every_derived_gate():
    scenarios, protocol = _campaign()
    acceptance = runner.derive_acceptance(scenarios, protocol)
    assert acceptance["status"] == "passed"
    assert all(acceptance["gates"].values())


def test_simulated_or_missing_process_receipt_cannot_pass():
    scenarios, protocol = _campaign()
    tampered = copy.deepcopy(scenarios)
    tampered[0]["tasks"][0]["executable"]["mode"] = "simulated"
    acceptance = runner.derive_acceptance(tampered, protocol)
    assert acceptance["status"] == "failed"
    assert not acceptance["gates"]["real_subprocess_receipts_only"]


def test_empty_evidence_fails_closed():
    protocol = json.loads((HERE / "experiment_protocol.json").read_text(encoding="utf-8"))
    acceptance = runner.derive_acceptance([], protocol)
    assert acceptance["status"] == "failed"
    assert not any(acceptance["gates"].values())



def test_protocol_coverage_mapping_is_complete_and_enforced():
    """Every protocol acceptance key must map to at least one gate, and the
    coverage report must reflect gate pass/fail status correctly."""
    scenarios, protocol = _campaign()
    acceptance = runner.derive_acceptance(scenarios, protocol)
    coverage = acceptance["protocol_coverage"]
    # Every protocol acceptance key must appear in the coverage report.
    protocol_keys = set(protocol.get("acceptance", {}))
    assert set(coverage) == protocol_keys, (
        f"coverage keys {set(coverage)} != protocol keys {protocol_keys}"
    )
    # Every coverage entry must reference at least one gate key.
    for proto_key, entry in coverage.items():
        assert len(entry["enforced_by"]) >= 1, f"{proto_key} has no enforcing gate"
    # When all gates pass, every coverage entry must report all_gates_passed=True.
    if acceptance["status"] == "passed":
        assert all(entry["all_gates_passed"] for entry in coverage.values())


def test_protocol_coverage_detects_unmapped_acceptance_key():
    """Adding an acceptance key to the protocol without a PROTOCOL_TO_GATE
    mapping must raise an assertion at run time."""
    scenarios, protocol = _campaign()
    tampered_protocol = copy.deepcopy(protocol)
    tampered_protocol["acceptance"]["bogus_unmapped_key"] = "must be enforced"
    try:
        runner.derive_acceptance(scenarios, tampered_protocol)
    except AssertionError as exc:
        assert "bogus_unmapped_key" in str(exc)
    else:
        raise AssertionError("expected AssertionError for unmapped acceptance key")


def test_protocol_coverage_reflects_gate_failure():
    """When a gate fails, the coverage entries that depend on it must report
    all_gates_passed=False."""
    scenarios, protocol = _campaign()
    tampered = copy.deepcopy(scenarios)
    tampered[0]["tasks"][0]["executable"]["mode"] = "simulated"
    acceptance = runner.derive_acceptance(tampered, protocol)
    coverage = acceptance["protocol_coverage"]
    # real_subprocess_receipts_only gate should have failed.
    assert not acceptance["gates"]["real_subprocess_receipts_only"]
    # Every protocol key enforced by that gate must report failure.
    for proto_key, entry in coverage.items():
        if "real_subprocess_receipts_only" in entry["enforced_by"]:
            assert not entry["all_gates_passed"], (
                f"{proto_key} should report gate failure"
            )