import io
import math
import struct
import wave

import pytest

from demo import _rtp_is_bidirectional, _webrtc_answer_plan
from models import FieldSpec
from run_acceptance import _has_credential, _synthetic_values
from webrtc_channel import CALL_PAGE, WebRTCPhoneChannel


class ToneSpeechBackend:
    provider = "deterministic-test-tone"

    async def synthesize(self, _text):
        stream = io.BytesIO()
        sample_rate = 16_000
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            samples = [
                int(10_000 * math.sin(2 * math.pi * 440 * i / sample_rate))
                for i in range(sample_rate // 2)
            ]
            wav.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))
        return stream.getvalue(), "audio/wav", {
            "operation": "tts", "provider": self.provider, "latency_seconds": 0.0,
        }

    async def transcribe(self, audio, mime):
        assert mime.startswith("audio/webm")
        assert len(audio) > 256
        return "accepted answer", {
            "operation": "asr", "provider": self.provider, "latency_seconds": 0.0,
            "raw_audio_retained": False, "transcript_retained": False,
        }


def test_page_uses_real_webrtc_media_and_keeps_answers_off_control_channel():
    assert "new RTCPeerConnection" in CALL_PAGE
    assert "addTrack" in CALL_PAGE
    assert "MediaRecorder(agentInput" in CALL_PAGE
    assert "non-sensitive-control" in CALL_PAGE
    assert "control.send(JSON.stringify({type: 'prompt', text}))" in CALL_PAGE
    assert "answer" not in CALL_PAGE.split("control.send", 1)[1].split(";", 1)[0]


def test_answer_plan_preserves_retry_answers_in_field_order():
    fields = [FieldSpec("name", "Name"), FieldSpec("email", "Email", "email")]
    assert _webrtc_answer_plan(
        '{"email":["bad","me@example.com"],"name":"Alice"}', fields
    ) == ["Alice", "bad", "me@example.com"]


def test_privacy_markers_exclude_public_form_options_but_include_private_values():
    markers = _synthetic_values()
    assert "Female" not in markers
    assert "alice@example.com" in markers
    assert "9123456789" in markers
    assert not _has_credential("ask_one_fill_one_concurrency")
    assert _has_credential("sk-examplecredential123")


@pytest.mark.asyncio
async def test_real_browser_webrtc_offer_answer_and_bidirectional_rtp():
    channel = WebRTCPhoneChannel(
        headless=True,
        synthetic_answers=["synthetic answer"],
        speech_backend=ToneSpeechBackend(),
    )
    try:
        await channel.start()
        await channel.say("question")
        assert await channel.listen(timeout=10) == "accepted answer"
    finally:
        await channel.close()

    receipt = channel.acceptance_receipt()
    assert receipt["offers"] == receipt["answers"] == 1
    assert receipt["media_recordings"] == 1
    assert receipt["status"] == "completed"
    assert _rtp_is_bidirectional(receipt)
    assert receipt["raw_audio_retained"] is False
    assert receipt["transcripts_retained"] is False
