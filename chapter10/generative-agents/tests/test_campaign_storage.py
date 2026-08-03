from __future__ import annotations

import json
from pathlib import Path

from supervise_campaigns import live_receipt_has_error


def test_runner_creates_movement_directory_after_fork():
    source = Path(__file__).resolve().parents[1] / "run_campaign.py"
    text = source.read_text(encoding="utf-8")
    constructor = 'server = ReverieServer(status["current_sim"], sim_code)'
    mkdir = '(target_dir / "movement").mkdir(exist_ok=True)'
    assert constructor in text
    assert mkdir in text
    assert text.index(constructor) < text.index(mkdir)


def test_packager_retains_action_arena_compatibility_receipts():
    source = Path(__file__).resolve().parents[1] / "package_evidence.py"
    text = source.read_text(encoding="utf-8")
    assert 'compatibility = output / "compatibility"' in text
    assert 'shutil.copytree(compatibility, destination / "compatibility")' in text


def test_supervisor_detects_provider_error_in_live_checkpoint(tmp_path):
    status = tmp_path / "status" / "baseline.json"
    status.parent.mkdir()
    status.write_text(json.dumps({"completed_steps": 360}), encoding="utf-8")
    receipt = tmp_path / "receipts" / "baseline" / "steps_00360_00720.jsonl"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps({"success": True})
        + "\n"
        + json.dumps({"success": False})
        + "\n",
        encoding="utf-8",
    )
    assert live_receipt_has_error(tmp_path, "baseline", 17_280, 360) is True
    receipt.write_text(json.dumps({"success": True}) + "\n", encoding="utf-8")
    assert live_receipt_has_error(tmp_path, "baseline", 17_280, 360) is False
