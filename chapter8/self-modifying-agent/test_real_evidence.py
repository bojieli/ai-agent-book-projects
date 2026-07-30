import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent


def test_canonical_real_coding_agent_evidence_closes_all_gates():
    evidence = json.loads((ROOT / "validation" / "latest.json").read_text(encoding="utf-8"))
    expected_sha = (ROOT / "validation" / "latest.sha256").read_text(encoding="utf-8").split()[0]
    assert expected_sha == hashlib.sha256((ROOT / "validation" / "latest.json").read_bytes()).hexdigest()
    assert evidence["execution_mode"] == "real_api_coding_agent_plus_model_external_release_harness"
    assert evidence["accepted"] is True
    assert all(evidence["gates"].values())
    assert evidence["manifests"]["real_llm"]["decision"] == "release_to_canary"
    assert evidence["manifests"]["deterministic"]["decision"] == "release_to_canary"
    assert evidence["manifests"]["rejected_control"]["decision"] == "reject_candidate"
    assert evidence["behavior_metrics"]["stable_buggy_baseline"]["mean_nonretryable_calls"] == 3.5
    assert evidence["behavior_metrics"]["real_llm"]["mean_nonretryable_calls"] == 1.0
    assert evidence["raw_api_receipts"][0]["response"]["id"]
    stable = (ROOT / "stable" / "retry_policy.py").read_bytes()
    assert evidence["input_artifacts"]["stable_sha256"] == hashlib.sha256(stable).hexdigest()
    assert evidence["cost"]["total_tokens"] > 0
    assert evidence["cost"]["provider_reported_cost_usd"] is None
