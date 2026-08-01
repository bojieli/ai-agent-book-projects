from pathlib import Path

import pytest

from speech_model import MiniCPMOClient, sha256_file


def test_sha256_file(tmp_path):
    path = tmp_path / "sample"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_inference_requires_loaded_model():
    client = MiniCPMOClient(enable_tts=False)
    with pytest.raises(RuntimeError, match=r"Call load\(\)"):
        client.infer_text("hello")


def test_speech_output_requires_tts(monkeypatch, tmp_path):
    client = MiniCPMOClient(enable_tts=False)
    client.model = object()
    monkeypatch.setattr(client, "load_audio", lambda _: [0.0])
    with pytest.raises(RuntimeError, match="enable_tts=False"):
        client.infer_audio(tmp_path / "input.wav", "answer", output_audio_path=tmp_path / "out.wav")
