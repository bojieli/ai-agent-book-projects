import base64
import json

import pytest

from speech_model import StepAudioR1Client, _audio_content


def test_audio_wire_contract_requires_wav(tmp_path):
    path = tmp_path / "input.wav"
    path.write_bytes(b"RIFF-test")
    item = _audio_content(path)
    assert item["type"] == "input_audio"
    assert base64.b64decode(item["input_audio"]["data"]) == b"RIFF-test"


def test_non_wav_is_rejected(tmp_path):
    path = tmp_path / "input.mp3"
    path.write_bytes(b"x")
    with pytest.raises(ValueError, match="WAV"):
        _audio_content(path)


def test_stream_parsing_uses_upstream_tts_fields(monkeypatch, tmp_path):
    path = tmp_path / "input.wav"
    path.write_bytes(b"RIFF-test")

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def raise_for_status(self): pass
        def iter_lines(self):
            yield b'data: {"choices":[{"delta":{"tts_content":{"tts_text":"answer","tts_audio":"<audio_1><audio_2>"}}}]}'
            yield b"data: [DONE]"

    monkeypatch.setattr("speech_model.requests.post", lambda *a, **k: Response())
    result = StepAudioR1Client("http://localhost:9999").infer(path, "solve")
    assert result.response == "answer"
    assert result.audio_token_count == 2
