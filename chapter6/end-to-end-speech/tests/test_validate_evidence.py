import json
import wave
from pathlib import Path

from speech_model import MODEL_ID, MODEL_REVISION, sha256_file
from validate_evidence import validate


def test_complete_evidence_passes(tmp_path):
    wav = tmp_path / "answer.wav"
    with wave.open(str(wav), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00" * 2400)
    arm = {"response": "ok", "transcript": "spoken words"}
    evidence = {
        "experiment": "9-4",
        "model": {
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "cuda_available": True,
            "init_audio": True,
        },
        "protocol": {"enable_thinking": False},
        "cases": [
            {"direct": {"response": "ok"}, "self_cascade": arm}
            for _ in range(4)
        ],
        "speech_output": {
            "output_audio": {
                "path": str(wav),
                "sha256": sha256_file(wav),
                "sample_rate_hz": 24000,
                "duration_seconds": 0.1,
            }
        },
        "implementation_sha256": {
            "requirements.txt": sha256_file(
                Path(__file__).resolve().parents[1] / "requirements.txt"
            )
        },
        "external_api_calls": 0,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    assert validate(path)["passed"] is True


def test_missing_direct_response_fails(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({"experiment": "9-4", "cases": []}), encoding="utf-8")
    assert validate(path)["passed"] is False
