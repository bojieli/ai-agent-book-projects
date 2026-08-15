import json
from pathlib import Path

from verify_acceptance import check_llm_receipt


def test_llm_receipt_tamper_is_rejected():
    content = '{"ok":true}'
    request = {"model": "model", "messages": [{"role": "user", "content": "safe"}]}
    raw = {
        "id": "response-1",
        "model": "model",
        "choices": [{"finish_reason": "stop", "message": {"content": content}}],
        "usage": {"total_tokens": 2},
    }
    canonical = lambda value: json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    import hashlib

    receipt = {
        "execution": "real_external_llm",
        "external_request_completed": True,
        "provider_response_id": "response-1",
        "provider_model": "model",
        "requested_model": "model",
        "finish_reason": "stop",
        "usage": {"total_tokens": 2},
        "latency_seconds": 1,
        "request": request,
        "request_sha256": hashlib.sha256(canonical(request).encode()).hexdigest(),
        "raw_response": raw,
        "raw_response_sha256": hashlib.sha256(canonical(raw).encode()).hexdigest(),
        "response_content": content,
        "response_content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "mock": False,
        "probe_only": False,
        "fallback_used": False,
        "credential_fields_retained": False,
    }
    receipt["provider_response_id"] = "tampered"
    failures = []
    check_llm_receipt(receipt, "test: ", failures)
    assert any("response ID" in failure for failure in failures)


def test_verifier_requires_retained_media_artifacts():
    from verify_acceptance import REQUIRED_ARTIFACTS

    assert "media/direct/microphone_rtp_asr_input.wav" in REQUIRED_ARTIFACTS
    assert "media/react/agent_02.wav" in REQUIRED_ARTIFACTS
    assert all(not Path(item).is_absolute() for item in REQUIRED_ARTIFACTS)
