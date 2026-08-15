from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load_module("exp75_run_report_audit", HERE / "run_report_audit.py")
validator = load_module("exp75_validate_evidence", HERE / "validate_evidence.py")


def test_raw_report_parser_retains_exact_five_by_three_matrix() -> None:
    retained = audit.parse_retained_outputs()
    assert retained["test_count"] == 5
    assert retained["output_count"] == 15
    assert [test["test_id"] for test in retained["tests"]] == [1, 2, 3, 4, 5]
    assert all(set(test["outputs"]) == set(audit.STAGES) for test in retained["tests"])

    kimchi = retained["tests"][2]["outputs"]
    assert "칠면조" in kimchi["pretrained"]
    assert "콩나물" in kimchi["finetuned"]


def test_blind_maps_are_deterministic_complete_permutations() -> None:
    first = [audit.blind_mapping(test_id) for test_id in range(1, 6)]
    second = [audit.blind_mapping(test_id) for test_id in range(1, 6)]
    assert first == second
    assert all(set(mapping) == {"A", "B", "C"} for mapping in first)
    assert all(set(mapping.values()) == set(audit.STAGES) for mapping in first)


def test_judge_payload_does_not_reveal_training_stages() -> None:
    test = audit.parse_retained_outputs()["tests"][0]
    payload = audit.judge_payload(test, audit.blind_mapping(1), "judge-model")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert all(stage not in serialized for stage in audit.STAGES)


def test_canonical_evidence_validates() -> None:
    result = validator.validate()
    assert result["status"] == "passed"
    assert result["judge_receipts_verified"] == 5
    assert result["outputs_verified"] == 15
