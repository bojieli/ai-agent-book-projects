from __future__ import annotations

from pathlib import Path


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
