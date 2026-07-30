import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent


def test_canonical_repeated_real_model_campaign_closes_all_gates():
    run_dir = ROOT / "validation" / "real_seeded_campaign"
    evidence_path = run_dir / "evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["execution_mode"] == "repeated_seeded_real_model_longitudinal_campaign"
    assert evidence["seeds"] == [8601, 8602, 8603]
    assert len(evidence["runs"]) == 9
    assert evidence["cost"]["api_calls"] == 126
    assert evidence["accepted"] is True
    assert all(evidence["gates"].values())
    receipts = [receipt for run in evidence["runs"] for receipt in run["raw_api_receipts"]]
    assert len(receipts) == 126
    assert len({receipt["response"]["id"] for receipt in receipts}) == 126
    assert all(not receipt["backend"]["credential_value_recorded"] for receipt in receipts)
    expected_sha = (run_dir / "evidence.sha256").read_text(encoding="utf-8").split()[0]
    assert expected_sha == hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    latest_sha = (ROOT / "validation" / "latest.sha256").read_text(encoding="utf-8").split()[0]
    assert latest_sha == hashlib.sha256((ROOT / "validation" / "latest.json").read_bytes()).hexdigest()
    stats = evidence["statistics"]["by_arm"]
    assert stats["evolving"]["rule_replacement_accuracy"]["mean"] == 1.0
    assert stats["append_only"]["obsolete_rule_reference_rate"]["mean"] == 1.0
    assert evidence["cost"]["total_tokens"] > 0
