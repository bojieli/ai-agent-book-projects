from pathlib import Path

import webrtc_app
from fastapi.testclient import TestClient


def direct_payload():
    return {
        "mode": "direct",
        "callee_name": "Jane",
        "goal": "Confirm a time and code",
        "context": "Tuesday afternoon",
        "instructions": "Ask for a time and confirmation code, then save both.",
    }


def test_direct_record_starts_fail_closed_with_audio_provenance_slots():
    webrtc_app.CALLS.clear()
    client = TestClient(webrtc_app.app)
    created = client.post("/api/calls", json=direct_payload())
    assert created.status_code == 200
    call_id = created.json()["call_id"]
    record = client.get(f"/api/calls/{call_id}").json()
    assert record["acceptance"]["passed"] is False
    assert record["models"]["llm_receipts"] == []
    assert record["models"]["asr_receipts"] == []
    assert record["models"]["tts_receipts"] == []
    assert record["transport"]["pstn_used"] is False
    assert record["transport"]["e164_required"] is False


def test_session_endpoint_rejects_non_sdp_without_creating_a_peer():
    webrtc_app.CALLS.clear()
    client = TestClient(webrtc_app.app)
    call_id = client.post("/api/calls", json=direct_payload()).json()["call_id"]
    response = client.post(
        f"/api/calls/{call_id}/session",
        content="not sdp",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415
    assert call_id not in webrtc_app.PEERS


def test_react_rejects_an_empty_task_before_provider_call():
    client = TestClient(webrtc_app.app)
    response = client.post("/api/calls", json={"mode": "react", "task": ""})
    assert response.status_code == 422


def test_browser_code_has_no_semantic_text_or_browser_speech_bypass():
    script = (Path(__file__).parent / "static" / "app.js").read_text()
    assert "getUserMedia" in script
    assert "client.audio.commit" in script
    assert "agent.caption" in script
    assert "user.message" not in script
    assert "speechSynthesis" not in script
    assert "SpeechRecognition" not in script


def test_acceptance_gate_names_are_exact_and_fail_closed():
    client = TestClient(webrtc_app.app)
    call_id = client.post("/api/calls", json=direct_payload()).json()["call_id"]
    checks = client.get(f"/api/calls/{call_id}").json()["acceptance"]["checks"]
    assert set(checks) == {
        "sdp_offer_answer_negotiated",
        "ice_connected",
        "data_channel_open",
        "browser_microphone_track",
        "server_downlink_audio_track",
        "outbound_audio_rtp",
        "inbound_audio_rtp",
        "server_buffered_microphone_rtp",
        "real_asr_consumed_microphone_audio",
        "external_react_planner_or_fixed_direct_control",
        "real_external_post_asr_dialogue",
        "real_tts_assets_synthesized",
        "tts_audio_transmitted_on_downlink",
        "media_is_canonical_transcript_source",
        "data_channel_is_control_and_caption_only",
        "missing_fields_were_clarified_aloud",
        "explicit_confirmation_observed",
        "structured_completion_saved",
        "no_mock_probe_or_fallback",
        "privacy_boundary_preserved",
    }
    assert not all(checks.values())
