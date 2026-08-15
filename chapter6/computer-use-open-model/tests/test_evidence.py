import json
from pathlib import Path

from evidence import retain_step_screenshots, sha256_file, write_json, write_manifest


def test_screenshots_are_copied_and_history_is_rewritten(tmp_path: Path) -> None:
    temporary_screenshot = tmp_path / "temporary.png"
    temporary_screenshot.write_bytes(b"not-a-real-png-but-stable")
    run_dir = tmp_path / "run"
    history = {"history": [{"state": {"screenshot_path": str(temporary_screenshot)}}]}

    retained, records = retain_step_screenshots(history, run_dir)

    retained_path = run_dir / "screenshots" / "step-001.png"
    assert retained_path.read_bytes() == temporary_screenshot.read_bytes()
    assert retained["history"][0]["state"]["screenshot_path"] == "screenshots/step-001.png"
    assert records[0]["sha256"] == sha256_file(retained_path)
    assert history["history"][0]["state"]["screenshot_path"] == str(temporary_screenshot)


def test_manifest_hashes_retained_artifacts(tmp_path: Path) -> None:
    write_json(tmp_path / "summary.json", {"status": "complete"})

    manifest_path = write_manifest(tmp_path, {"experiment": "test", "credential_retained": False})
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["credential_retained"] is False
    assert manifest["artifacts"] == [
        {
            "path": "summary.json",
            "bytes": (tmp_path / "summary.json").stat().st_size,
            "sha256": sha256_file(tmp_path / "summary.json"),
        }
    ]
