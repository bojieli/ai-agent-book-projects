import json
from pathlib import Path


ROOT = Path(__file__).parent / "validation"


def test_persisted_acceptance_status_does_not_claim_unrun_human_audio():
    status = json.loads((ROOT / "acceptance_status_2026-07-29.json").read_text())
    assert status["safety"]["phone_calls_placed"] == 0
    assert status["safety"]["human_audio_captured"] is False
    assert status["audio_endpoint_probe"]["asr_status"] == "fail"
    assert status["audio_endpoint_probe"]["asr_error_code"] == "insufficient_quota"
    assert "no microphone or human audio" in status["audio_endpoint_probe"]["asr_input"]
    assert status["acceptance_gates"]["authorized_human_participant"]["status"] == "not_run"
    assert status["acceptance_gates"]["real_human_asr"]["status"] == "not_run"
    assert status["implementation_gates"]["consent_refusal_before_live_session_construction"]["status"] == "pass_by_test"
    assert status["implementation_gates"]["barge_in_cancels_playback_and_transcribes"]["status"] == "pass_by_mocked_mechanism_test"
    assert status["implementation_gates"]["deterministic_judge_and_win_rule"]["status"] == "pass_by_test"
    assert status["overall_status"] == "incomplete"


def test_offline_and_real_llm_evidence_are_explicitly_non_acceptance():
    offline = json.loads((ROOT / "offline_privacy_supplement_2026-07-29.json").read_text())
    partial = json.loads((ROOT / "real_llm_partial_2026-07-29.json").read_text())
    trace = json.loads((ROOT / "real_llm_partial_trace_2026-07-29.json").read_text())
    audit = json.loads((ROOT / "real_strategy_audit_supplement_2026-07-29.json").read_text())
    assert offline["acceptance_path"] is False
    assert offline["overall_status"] == "supplemental_only"
    assert offline["information_isolation_pass"] is True
    assert partial["acceptance_path"] is False
    assert partial["gates"]["three_complete_cycles"]["status"] == "fail"
    assert partial["overall_status"] == "incomplete"
    assert trace["complete_cycles"] == 2
    assert trace["trace_complete"] is False
    assert any(e.get("action") == "speech" for e in trace["events"])
    assert any(e.get("phase") == "vote" for e in trace["events"])
    assert audit["acceptance_path"] is False
    assert audit["human_audio_used"] is False
    assert audit["audit"]["schema_valid"] is True
    assert audit["audit"]["overall_pass"] is False
    assert audit["overall_status"] == "supplemental_only"
