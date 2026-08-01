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


def test_real_user_simulator_runs_prove_e2e_and_keep_negative_results_separate():
    runs = ROOT / "runs"
    strategy_run = json.loads(
        (runs / "exp10-8-simulated-user-openrouter-20260801" / "acceptance_report.json").read_text()
    )
    three_cycle_run = json.loads(
        (runs / "exp10-8-simulated-user-openrouter-20260801-v2" / "acceptance_report.json").read_text()
    )

    strategy_validation = json.loads(
        (runs / "exp10-8-simulated-user-openrouter-20260801" / "independent_validation.json").read_text()
    )
    three_cycle_validation = json.loads(
        (runs / "exp10-8-simulated-user-openrouter-20260801-v2" / "independent_validation.json").read_text()
    )

    assert strategy_run["strategy_audit_pass"] is True
    assert strategy_validation["strict_audio_action_boundary"] == "fail"
    assert "not an explicit abstention" in strategy_validation["errors"][0]

    report = three_cycle_run
    assert report["execution_mode"] == "simulated_user"
    assert report["acceptance_path"] is True
    assert report["gates"]["one_llm_user_simulator"]["status"] == "pass"
    assert report["gates"]["information_isolation"]["status"] == "pass"
    assert report["gates"]["winner_determined_by_game_rule"]["status"] == "pass"
    assert report["simulator_llm_tool_calls"] == 2
    assert report["simulator_audio_roundtrips"] == 2
    ids = [
        event.get("response_id") or event.get("request_id")
        for event in report["voice_events"]
        if event["type"] in {"simulator_llm_tool", "simulator_asr"}
    ]
    assert all(ids)
    assert len(ids) == len(set(ids))
    asr_events = [event for event in report["voice_events"] if event["type"] == "simulator_asr"]
    assert all(
        event["usage"]["prompt_tokens_details"]["audio_tokens"] > 0
        for event in asr_events
    )
    assert three_cycle_validation["strict_audio_action_boundary"] == "pass"
    assert three_cycle_run["completed_day_night_vote_cycles"] == 3
    assert three_cycle_run["strategy_audit_pass"] is False
    assert three_cycle_run["overall_status"] == "incomplete"


def test_fixed_abstention_has_real_audio_api_receipt():
    probe = json.loads((ROOT / "fixed_abstention_probe_20260801.json").read_text())
    assert probe["synthetic_audio_only"] is True
    assert probe["spoken_text"] == "I choose to abstain."
    assert probe["asr_transcript"] == "I choose to abstain."
    assert probe["explicit_abstention"] is True
    assert probe["parsed_target"] is None
    assert probe["provider"] == "OpenRouter multimodal audio API"
    assert probe["response_id"].startswith("gen-")
    assert probe["usage"]["prompt_tokens_details"]["audio_tokens"] > 0
    assert len(probe["source_audio_sha256"]) == 64
    assert probe["status"] == "pass"
