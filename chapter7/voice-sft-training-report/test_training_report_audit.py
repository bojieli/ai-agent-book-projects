from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_training_report_audit as audit  # noqa: E402
import validate_evidence as validator  # noqa: E402

RUN_DIR = HERE / "validation" / "runs" / audit.DEFAULT_RUN_ID


def write_json(path: Path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def reseal_artifact(run_dir: Path, name: str):
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = next(item for item in manifest["artifacts"] if item["path"] == name)
    row["bytes"] = (run_dir / name).stat().st_size
    row["sha256"] = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
    write_json(manifest_path, manifest)


def copied_run(tmp_path: Path) -> Path:
    target = tmp_path / "run"
    shutil.copytree(RUN_DIR, target)
    return target


def test_canonical_evidence_passes_fail_closed_validator():
    result = validator.validate_run(RUN_DIR)
    assert result["status"] == "passed"
    assert result["notebooks"] == 2
    assert result["loss_rows"] == 358
    assert result["audio_files"] == 4
    assert result["judge_receipts"] == 2
    assert result["failed_attempts"] == 8


def test_immutable_notebooks_retain_complete_training_and_audio():
    source = json.loads((RUN_DIR / "source_audit.json").read_text(encoding="utf-8"))
    assert len(source["upstream_executed_notebooks"]["orpheus"]["training"]["loss_rows"]) == 298
    assert len(source["upstream_executed_notebooks"]["sesame"]["training"]["loss_rows"]) == 60
    assert [row["track"] for row in source["extracted_audio"]] == [
        "orpheus",
        "sesame",
        "sesame",
        "sesame",
    ]
    assert all(
        (RUN_DIR / row["filename"]).read_bytes().startswith(b"RIFF")
        for row in source["extracted_audio"]
    )


def test_mechanism_inversion_is_explicit_and_source_backed():
    source = audit.build_source_audit(RUN_DIR)
    mechanism = source["mechanism_audit"]
    assert mechanism["manuscript_mapping_supported_by_executable_sources"] is False
    assert all(mechanism["checks"].values())
    assert "<giggles>/<laugh>" in mechanism["observed_mapping"]["orpheus"]
    assert "audio context" in mechanism["observed_mapping"]["sesame"]


def test_raw_judge_requests_embed_exact_audio_and_responses_are_unique():
    calls = json.loads((RUN_DIR / "judge_receipts.json").read_text(encoding="utf-8"))["calls"]
    assert len({row["response_id"] for row in calls}) == 2
    assert all(row["usage"]["total_tokens"] > 0 for row in calls)
    summary = json.loads((RUN_DIR / "summary.json").read_text(encoding="utf-8"))
    validator.validate_receipts(
        RUN_DIR,
        {
            "schema_version": "exp7-6-judge-receipts-v1",
            "experiment": "7-6",
            "credential_headers_retained": False,
            "calls": calls,
        },
        summary,
    )


def test_tampered_notebook_fails_even_after_resealing(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "upstream_orpheus.ipynb"
    path.write_bytes(path.read_bytes() + b"\n")
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="Git blob mismatch"):
        validator.validate_run(run_dir, verify_latest=False)


def test_tampered_wav_fails_even_after_resealing(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "sesame_output_2.wav"
    data = bytearray(path.read_bytes())
    data[-1] ^= 1
    path.write_bytes(data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="extracted WAV"):
        validator.validate_run(run_dir, verify_latest=False)


def test_normalized_judgment_must_match_raw_response(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "judge_receipts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    current = data["calls"][0]["judgment"]["naturalness"]
    data["calls"][0]["judgment"]["naturalness"] = 0 if current != 0 else 1
    write_json(path, data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="not derived from the raw response"):
        validator.validate_run(run_dir, verify_latest=False)


def test_tampered_source_audit_fails_even_after_resealing(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "source_audit.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["mechanism_audit"]["manuscript_mapping_supported_by_executable_sources"] = True
    write_json(path, data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="source audit differs"):
        validator.validate_run(run_dir, verify_latest=False)


def test_checkpoint_policy_and_environment_limits_are_not_hidden():
    contract = audit.reproduction_contract()
    assert contract["checkpoint_policy"]["acceptance_artifact"] is False
    assert contract["environment_boundary"]["book_requirements_are_fully_pinned"] is False
    assert contract["environment_boundary"]["cuda_driver_and_container_digest_retained"] is False
