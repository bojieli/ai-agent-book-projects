"""Acceptance-ledger regression tests for the durable Experiment 4-6 run."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PATH = HERE / "run_real_experiment.py"
SPEC = importlib.util.spec_from_file_location("experiment_4_6_real", PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _campaign() -> tuple[list[dict], dict]:
    root = HERE / "validation" / "experiment_4_6"
    campaigns = sorted(path for path in root.iterdir() if path.is_dir())
    assert campaigns, "a durable Experiment 4-6 campaign is required"
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
