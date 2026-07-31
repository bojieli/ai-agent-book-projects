from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

import run_training_report_audit as audit
import validate_evidence as validator


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_historical_report_parser_retains_complete_six_cell_matrix() -> None:
    retained = audit.parse_retained_outputs()
    assert retained["cell_count"] == 6
    assert retained["output_count"] == 49
    assert {
        (cell["arm"], cell["stage"]): cell["pair_count"]
        for cell in retained["cells"]
    } == audit.EXPECTED_COUNTS
    comparisons = audit.selected_comparisons(retained)
    assert len(comparisons) == 8
    assert {row["stage"] for row in comparisons} == set(audit.STAGES)
    assert all(set(row["arms"]) == set(audit.ARMS) for row in comparisons)


def test_judge_requests_are_arm_blind_and_bound_to_exact_outputs() -> None:
    retained = audit.parse_retained_outputs()
    for comparison in audit.selected_comparisons(retained):
        mapping = audit.blind_mapping(comparison["case_id"])
        payload = audit.judge_payload(comparison, mapping, "judge-model")
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        assert "qk_norm_muon" not in serialized
        assert '"original"' not in serialized
        user_payload = json.loads(payload["messages"][1]["content"])
        for label, arm in mapping.items():
            assert user_payload["candidates"][label]["historical_output"] == comparison["arms"][arm]["output"]


def make_validation_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    latest = json.loads(audit.LATEST_PATH.read_text(encoding="utf-8"))
    canonical_run = audit.EXPERIMENT_DIR / latest["run_dir"]
    temp_repo = tmp_path / "repo"
    temp_experiment = temp_repo / "chapter7/MiniMind-pretrain"
    temp_run = temp_experiment / latest["run_dir"]
    temp_run.parent.mkdir(parents=True)
    shutil.copytree(canonical_run, temp_run)

    manifest = json.loads((canonical_run / "manifest.json").read_text(encoding="utf-8"))
    for record in manifest["inputs"]:
        source = audit.REPO_ROOT / record["path"]
        destination = temp_repo / record["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    temp_latest = temp_experiment / "validation/latest.json"
    temp_latest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(audit.LATEST_PATH, temp_latest)
    monkeypatch.setattr(validator, "REPO_ROOT", temp_repo)
    monkeypatch.setattr(validator, "EXPERIMENT_DIR", temp_experiment)
    return temp_latest, temp_run


def refresh_outer_hashes(latest_path: Path, run_dir: Path, artifact_name: str) -> None:
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_path = run_dir / artifact_name
    record = next(record for record in manifest["artifacts"] if record["path"] == artifact_name)
    record["bytes"] = artifact_path.stat().st_size
    record["sha256"] = digest(artifact_path)
    write_json(manifest_path, manifest)
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    latest["manifest_sha256"] = digest(manifest_path)
    write_json(latest_path, latest)


def test_canonical_evidence_passes_fail_closed_validator() -> None:
    result = validator.validate()
    assert result["status"] == "passed"
    assert result["outputs_verified"] == 49
    assert result["judge_receipts_verified"] == 8


def test_validator_rejects_raw_response_normalization_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    latest_path, run_dir = make_validation_copy(tmp_path, monkeypatch)
    receipts_path = run_dir / "judge_receipts.json"
    receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
    response = receipts["calls"][0]["response"]
    raw_judgment = json.loads(response["choices"][0]["message"]["content"])
    raw_judgment["winner"] = "tie" if raw_judgment["winner"] != "tie" else "A"
    response["choices"][0]["message"]["content"] = json.dumps(raw_judgment)
    write_json(receipts_path, receipts)
    refresh_outer_hashes(latest_path, run_dir, "judge_receipts.json")
    with pytest.raises(AssertionError, match="normalized judgment"):
        validator.validate(latest_path)


def test_validator_rejects_retained_output_request_binding_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    latest_path, run_dir = make_validation_copy(tmp_path, monkeypatch)
    retained_path = run_dir / "retained_outputs.json"
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    retained["cells"][0]["pairs"][3]["output"] += " altered"
    write_json(retained_path, retained)
    refresh_outer_hashes(latest_path, run_dir, "retained_outputs.json")
    with pytest.raises(AssertionError, match="not bound to the retained output"):
        validator.validate(latest_path)


def test_validator_rejects_frozen_dataset_revision_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    latest_path, run_dir = make_validation_copy(tmp_path, monkeypatch)
    contract_path = run_dir / "reproduction_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["future_reproduction"]["dataset"]["revision"] = "0" * 40
    write_json(contract_path, contract)
    refresh_outer_hashes(latest_path, run_dir, "reproduction_contract.json")
    with pytest.raises(AssertionError, match="dataset revision mismatch"):
        validator.validate(latest_path)
