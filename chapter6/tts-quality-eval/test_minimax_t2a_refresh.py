"""
Regression tests for the Minimax t2a_v2 synthesis adapter (实验 6-5 TTS 质量评估).

Locks in the refreshed contract:
  - the request targets the /v1/t2a_v2 endpoint with Bearer auth and no GroupId
    query parameter, on the global host by default and the mainland-China host
    when MINIMAX_REGION selects it;
  - the default model is speech-2.8-hd;
  - the response is validated on base_resp.status_code, data.status and
    data.audio, so a bad return code or an unfinished status raises a clear
    RuntimeError instead of yielding empty/garbage audio.

Network is stubbed: pipeline._http_post is replaced with a fake that records the
request and returns a canned JSON body.
"""
import json

import pytest

import config
import pipeline


def _cfg(model="speech-2.8-hd"):
    return config.TTSConfig("minimax-test", provider="minimax",
                            model=model, voice="male-qn-qingse")


def _stub_http_post(monkeypatch, response: dict):
    """Capture the outgoing request and return a canned decoded JSON body."""
    calls = {}

    def fake_post(url, body, headers, timeout=90.0):
        calls["url"] = url
        calls["body"] = body
        calls["headers"] = headers
        return json.dumps(response).encode()

    monkeypatch.setattr(pipeline, "_http_post", fake_post)
    return calls


def _ok_response(audio_bytes: bytes):
    return {
        "data": {"audio": audio_bytes.hex(), "status": pipeline._MINIMAX_STATUS_DONE},
        "base_resp": {"status_code": pipeline._MINIMAX_SUCCESS_CODE, "status_msg": "success"},
    }


def test_default_endpoint_is_global_bearer_no_groupid(monkeypatch):
    """Global host, Bearer auth, no GroupId query param, default model."""
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
    monkeypatch.delenv("MINIMAX_REGION", raising=False)
    calls = _stub_http_post(monkeypatch, _ok_response(b"\xff\xfb\x10\x20"))

    audio = pipeline._synth_minimax(_cfg(), "你好")

    assert calls["url"] == "https://api.minimax.io/v1/t2a_v2"
    assert "GroupId" not in calls["url"]
    assert calls["headers"]["Authorization"] == "Bearer fake-key"
    assert calls["body"]["model"] == "speech-2.8-hd"
    assert audio == b"\xff\xfb\x10\x20"


def test_cn_region_uses_minimaxi_host(monkeypatch):
    """MINIMAX_REGION=cn routes to the mainland-China api.minimaxi.com host."""
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
    monkeypatch.setenv("MINIMAX_REGION", "cn")
    calls = _stub_http_post(monkeypatch, _ok_response(b"\x00\x01"))

    pipeline._synth_minimax(_cfg(), "你好")

    assert calls["url"] == "https://api.minimaxi.com/v1/t2a_v2"


def test_empty_model_falls_back_to_default(monkeypatch):
    """An empty cfg.model falls back to the current default speech-2.8-hd."""
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
    calls = _stub_http_post(monkeypatch, _ok_response(b"\x00"))

    pipeline._synth_minimax(_cfg(model=""), "你好")

    assert calls["body"]["model"] == "speech-2.8-hd"


def test_nonzero_base_resp_raises(monkeypatch):
    """base_resp.status_code != 0 raises a clear error instead of decoding junk."""
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
    _stub_http_post(monkeypatch, {
        "data": {},
        "base_resp": {"status_code": 1004, "status_msg": "authentication failed"},
    })
    with pytest.raises(RuntimeError, match="base_resp"):
        pipeline._synth_minimax(_cfg(), "你好")


def test_unfinished_status_raises(monkeypatch):
    """A non-finished data.status (with no audio) raises rather than returning empty audio."""
    monkeypatch.setenv("MINIMAX_API_KEY", "fake-key")
    _stub_http_post(monkeypatch, {
        "data": {"status": 1, "audio": ""},
        "base_resp": {"status_code": 0, "status_msg": "success"},
    })
    with pytest.raises(RuntimeError, match="finished audio"):
        pipeline._synth_minimax(_cfg(), "你好")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
