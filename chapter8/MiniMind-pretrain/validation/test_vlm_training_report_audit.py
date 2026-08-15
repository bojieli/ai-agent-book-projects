import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_vlm_training_report_audit as audit
import validate_vlm_evidence as validator

RUN_DIR = HERE / "runs" / audit.DEFAULT_RUN_ID


def write_json(path: Path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def reseal_artifact(run_dir: Path, name: str):
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact = next(row for row in manifest["artifacts"] if row["path"] == name)
    artifact["bytes"] = (run_dir / name).stat().st_size
    artifact["sha256"] = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
    write_json(manifest_path, manifest)


def copied_run(tmp_path: Path) -> Path:
    target = tmp_path / "run"
    shutil.copytree(RUN_DIR, target)
    return target


def test_parser_retains_all_eight_cells_and_64_outputs():
    retained = audit.parse_retained_outputs()
    assert retained["cell_count"] == 8
    assert retained["output_count"] == 64
    assert tuple(cell["config"] for cell in retained["cells"]) == audit.CONFIGS
    assert all(cell["output_count"] == 8 for cell in retained["cells"])
    assert all(
        {row["image"] for row in cell["outputs"]} == set(audit.IMAGE_FILES)
        for cell in retained["cells"]
    )


def test_blind_mapping_is_deterministic_bijective_and_image_specific():
    mappings = [audit.blind_mapping(image) for image in audit.IMAGE_FILES]
    assert all(set(mapping) == set(audit.LABELS) for mapping in mappings)
    assert all(set(mapping.values()) == set(audit.CONFIGS) for mapping in mappings)
    assert all(
        mapping == audit.blind_mapping(image)
        for image, mapping in zip(audit.IMAGE_FILES, mappings, strict=True)
    )
    assert len({tuple(mapping.items()) for mapping in mappings}) > 1


def test_reproduction_contract_separates_original_and_improved_sources():
    contract = audit.reproduction_contract()
    vlm = contract["future_reproduction"]["vlm_source"]
    commands = contract["future_reproduction"]["commands"]
    assert vlm["original_revision"] == audit.ORIGINAL_VLM_REVISION
    assert vlm["qk_norm_muon_revision"] == audit.IMPROVED_VLM_REVISION
    assert vlm["original_revision"] != vlm["qk_norm_muon_revision"]
    assert audit.ORIGINAL_VLM_REVISION in commands["original_source"]
    assert audit.IMPROVED_VLM_REVISION in commands["improved_source"]
    assert "checkout --detach" in commands["original_source"]
    assert "checkout --detach" in commands["improved_source"]
    assert (
        contract["historical_evidence_boundary"]["historical_vlm_checkpoint_hashes_retained"]
        is False
    )
    assert contract["checkpoint_policy"]["acceptance_artifact"] is False


def test_canonical_evidence_passes_fail_closed_validator():
    result = validator.validate_run(RUN_DIR)
    assert result["status"] == "passed"
    assert result["cells"] == 8
    assert result["outputs"] == 64
    assert result["judge_receipts"] == 8


def test_vlm_latest_pointer_does_not_overwrite_experiment_7_3():
    assert audit.LATEST_PATH.name == "latest_vlm.json"
    vlm_latest = json.loads(audit.LATEST_PATH.read_text(encoding="utf-8"))
    llm_latest = json.loads((HERE / "latest.json").read_text(encoding="utf-8"))
    assert vlm_latest["experiment"] == "7-4"
    assert llm_latest["experiment"] == "7-3"


def test_receipts_are_real_image_aware_unique_and_arm_blind():
    receipts = json.loads((RUN_DIR / "judge_receipts.json").read_text(encoding="utf-8"))["calls"]
    assert len({row["response_id"] for row in receipts}) == 8
    retained = audit.parse_retained_outputs()
    for receipt in receipts:
        assert receipt["http_status"] == 200
        assert receipt["usage"]["total_tokens"] > 0
        content = receipt["request"]["messages"][1]["content"]
        assert content[0]["type"] == "image_url"
        assert content[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")
        prompt = json.loads(content[1]["text"])
        expected = audit.outputs_for_image(retained, receipt["image"])
        assert prompt["candidates"] == {
            label: expected[config] for label, config in receipt["blind_map"].items()
        }
        assert not any(config in content[1]["text"] for config in audit.CONFIGS)


def test_tampered_retained_output_fails_even_after_resealing(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "retained_outputs.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["cells"][0]["outputs"][0]["output"] += " tampered"
    write_json(path, data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="retained outputs"):
        validator.validate_run(run_dir, verify_latest=False)


def test_tampered_request_image_fails_even_after_resealing(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "judge_receipts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    url = data["calls"][0]["request"]["messages"][1]["content"][0]["image_url"]["url"]
    prefix, encoded = url.split(",", 1)
    replacement = "A" if encoded[-2] != "A" else "B"
    data["calls"][0]["request"]["messages"][1]["content"][0]["image_url"]["url"] = (
        prefix + "," + encoded[:-2] + replacement + encoded[-1]
    )
    write_json(path, data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="request image bytes"):
        validator.validate_run(run_dir, verify_latest=False)


def test_normalized_judgment_must_match_raw_provider_response(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "judge_receipts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    current = data["calls"][0]["judgment"]["candidates"]["A"]["grounding_accuracy"]
    data["calls"][0]["judgment"]["candidates"]["A"]["grounding_accuracy"] = 0 if current != 0 else 1
    write_json(path, data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="not derived from raw response"):
        validator.validate_run(run_dir, verify_latest=False)


def test_reproduction_pin_tampering_fails_even_after_resealing(tmp_path):
    run_dir = copied_run(tmp_path)
    path = run_dir / "reproduction_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["future_reproduction"]["vlm_source"]["original_revision"] = "0" * 40
    write_json(path, data)
    reseal_artifact(run_dir, path.name)
    with pytest.raises(validator.EvidenceError, match="reproduction contract"):
        validator.validate_run(run_dir, verify_latest=False)
