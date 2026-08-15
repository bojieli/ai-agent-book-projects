import json
from pathlib import Path


def test_canonical_manifest_is_hash_complete():
    run_dir = Path(__file__).resolve().parents[1] / "validation" / "runs" / "exp6-6-arena-20260731-v1"
    manifest_path = run_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["experiment"] == "6-6"
    assert manifest["official_complete"] is True
    assert all(manifest["gates"].values())
    assert set(manifest["artifacts"]) >= {
        "summary.json",
        "online_elo.json",
        "bradley_terry.json",
        "win_rate_matrix.json",
        "rating_history.json",
        "leaderboard_animation.html",
    }
