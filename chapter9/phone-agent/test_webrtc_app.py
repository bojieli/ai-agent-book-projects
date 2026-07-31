import webrtc_app
from fastapi.testclient import TestClient


def direct_payload():
    return {
        "mode": "direct",
        "callee_name": "Jane",
        "goal": "Confirm a time",
        "context": "Tuesday afternoon",
        "instructions": "Ask for a time and confirmation code, then save both.",
    }


def test_direct_full_record_contract():
    webrtc_app.CALLS.clear()
    client = TestClient(webrtc_app.app)

    created = client.post("/api/calls", json=direct_payload())
    assert created.status_code == 200
    call_id = created.json()["call_id"]
    record_state = webrtc_app.CALLS[call_id]
    record_state["transport"].update(
        {
            "sdp_negotiated": True,
            "offer_sha256": "a" * 64,
            "answer_sha256": "b" * 64,
            "server_received_audio_frames": 20,
            "server_received_audio_samples": 19_200,
            "ice_connected_observed": True,
        }
    )

    events = [
        {
            "type": "rtc.ready",
            "ice_connection_state": "connected",
            "data_channel_open": True,
            "local_audio_track": True,
            "remote_audio_track": True,
        },
        {
            "type": "rtc.stats",
            "ice_connection_state": "connected",
            "inbound_packets": 12,
            "inbound_bytes": 4096,
            "outbound_packets": 15,
            "outbound_bytes": 5000,
        },
        {"type": "client.user_text", "text": "Tuesday at 3pm; code RTC-92."},
        {"type": "response.output_audio_transcript.done", "transcript": "I saved Tuesday at 3pm."},
    ]
    for event in events:
        assert client.post(f"/api/calls/{call_id}/events", json={"event": event}).status_code == 200
    completion = client.post(
        f"/api/calls/{call_id}/complete",
        json={
            "result": "User confirmed the local record.",
            "appointment_time": "Tuesday at 3pm",
            "confirmation_number": "RTC-92",
            "notes": "",
        },
    )
    assert completion.status_code == 200
    record = client.post(f"/api/calls/{call_id}/finish", json={"reason": "test"}).json()
    assert record["acceptance"]["passed"] is True
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


def test_react_rejects_an_empty_task():
    client = TestClient(webrtc_app.app)
    response = client.post("/api/calls", json={"mode": "react", "task": ""})
    assert response.status_code == 422
