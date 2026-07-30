"""
Regression tests for judge-response robustness (实验 6-5 TTS 质量评估).

Covers two failure classes on LLM/Gemini judge responses:
  - judge_rubric: judge returns "score": null (or a bare null dimension) -> int(None) TypeError
  - judge_gemini_audio: safety-blocked Gemini responses have no
    candidates/content/parts -> KeyError/IndexError instead of a clear error

Network is stubbed: the OpenAI-compatible judge client is replaced with a fake,
and urllib.request.urlopen is monkeypatched for the Gemini REST call.
"""
import io
import json

import pytest

import pipeline


class _FakeMessage:
    content = "{}"


class _FakeChoice:
    message = _FakeMessage()


class _FakeResp:
    choices = [_FakeChoice()]


class _FakeCompletions:
    @staticmethod
    def create(**kwargs):
        return _FakeResp()


class _FakeChat:
    completions = _FakeCompletions()


class _FakeClient:
    chat = _FakeChat()


def _stub_judge(monkeypatch, payload: dict):
    _FakeMessage.content = json.dumps(payload, ensure_ascii=False)
    monkeypatch.setattr(
        pipeline, "get_judge_client_and_model", lambda model=None: (_FakeClient(), "fake-judge"))


def test_judge_rubric_tolerates_null_score(monkeypatch):
    """'score': null in a dimension dict is scored 0, not int(None) TypeError."""
    _stub_judge(monkeypatch, {
        "准确性": {"score": None, "reason": "无法判断"},
        "自然度": {"score": 4, "reason": "语速正常"},
        "情感表达": {"score": 0},
        "音色一致性": {"score": 0, "reason": "无法听到音频"},
    })
    rub = pipeline.judge_rubric("原文文本", "中性", "回译文本", 3.0, 0.05)
    assert rub.scores["准确性"] == 0
    assert rub.scores["自然度"] == 4
    assert rub.scores["音色一致性"] == 0


def test_judge_rubric_tolerates_null_dimension(monkeypatch):
    """A bare null dimension (non-dict) is scored 0, not int(None) TypeError."""
    _stub_judge(monkeypatch, {
        "准确性": None,
        "自然度": 4,
        "情感表达": 0,
        "音色一致性": 0,
    })
    rub = pipeline.judge_rubric("原文文本", "中性", "回译文本", 3.0, 0.05)
    assert rub.scores["准确性"] == 0
    assert rub.scores["自然度"] == 4


class _FakeHTTPResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _stub_gemini(monkeypatch, payload: dict):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(pipeline, "_resolve_gemini_model", lambda key: "gemini-fake")
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda req, timeout=None: _FakeHTTPResp(json.dumps(payload).encode()))


@pytest.mark.parametrize("payload", [
    {"promptFeedback": {"blockReason": "SAFETY"}},      # prompt 被拦截：无 candidates
    {"candidates": []},                                  # 生成被拦截：空 candidates
    {"candidates": [{"finishReason": "SAFETY", "index": 0}]},  # candidate 无 content
])
def test_judge_gemini_audio_blocked_raises_clear_error(monkeypatch, tmp_path, payload):
    """Blocked/empty Gemini responses raise a clear RuntimeError, not KeyError/IndexError."""
    _stub_gemini(monkeypatch, payload)
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"\xff\xfb" + b"\x00" * 256)
    reference = tmp_path / "reference.mp3"
    reference.write_bytes(b"\xff\xfb" + b"\x01" * 256)
    with pytest.raises(RuntimeError, match="Gemini 未返回评审文本"):
        pipeline.judge_gemini_audio("原文", "中性", str(audio), str(reference))


def test_judge_gemini_audio_parses_valid_response(monkeypatch, tmp_path):
    """A normal Gemini response still parses (defensive navigation keeps working)."""
    inner = json.dumps({
        "准确性": {"score": 4, "reason": "ok"},
        "自然度": 4,
        "情感表达": None,
        "音色一致性": {"score": 5},
    }, ensure_ascii=False)
    _stub_gemini(monkeypatch, {
        "candidates": [{"content": {"parts": [{"text": inner}]}}],
    })
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"\xff\xfb" + b"\x00" * 256)
    reference = tmp_path / "reference.mp3"
    reference.write_bytes(b"\xff\xfb" + b"\x01" * 256)
    rub = pipeline.judge_gemini_audio("原文", "中性", str(audio), str(reference))
    assert rub.scores["准确性"] == 4
    assert rub.scores["情感表达"] == 0   # null score -> 0
    assert rub.scores["音色一致性"] == 5


def test_judge_gemini_audio_falls_back_to_openrouter(monkeypatch, tmp_path):
    """An unavailable direct key keeps both clips on a direct-audio fallback route."""
    monkeypatch.setenv("GEMINI_API_KEY", "invalid-direct-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-openrouter-key")
    monkeypatch.setattr(pipeline, "_resolve_gemini_model", lambda key: "gemini-fake")

    def _http_error(req, timeout=None):
        import urllib.error
        raise urllib.error.HTTPError(req.full_url, 400, "bad key", {}, io.BytesIO(b"invalid"))

    monkeypatch.setattr("urllib.request.urlopen", _http_error)
    expected = pipeline.RubricResult(
        scores={dim: 4 for dim in pipeline.RUBRIC_DIMENSIONS},
        reasons={dim: "audible evidence" for dim in pipeline.RUBRIC_DIMENSIONS},
        judge_model="openrouter/google/gemini-3.5-flash",
        evidence_mode="direct-audio-with-reference",
        provider_attempts=[],
    )
    monkeypatch.setattr(pipeline, "_judge_openrouter_audio", lambda *args, **kwargs: expected)
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"\xff\xfb" + b"\x00" * 256)
    reference = tmp_path / "reference.mp3"
    reference.write_bytes(b"\xff\xfb" + b"\x01" * 256)

    rub = pipeline.judge_gemini_audio("原文", "中性", str(audio), str(reference))
    assert rub is expected
    assert rub.evidence_mode == "direct-audio-with-reference"


def test_openrouter_failure_preserves_both_route_attempts(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "invalid-direct-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "invalid-openrouter-key")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(pipeline, "_resolve_gemini_model", lambda key: "gemini-fake")

    def _http_error(req, timeout=None):
        import urllib.error
        body = b"direct invalid" if "googleapis" in req.full_url else b"router invalid"
        code = 400 if "googleapis" in req.full_url else 401
        raise urllib.error.HTTPError(req.full_url, code, "unavailable", {}, io.BytesIO(body))

    monkeypatch.setattr("urllib.request.urlopen", _http_error)
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"\xff\xfb" + b"\x00" * 256)
    reference = tmp_path / "reference.mp3"
    reference.write_bytes(b"\xff\xfb" + b"\x01" * 256)

    with pytest.raises(pipeline.JudgeRouteError) as caught:
        pipeline.judge_gemini_audio("原文", "中性", str(audio), str(reference))
    assert [attempt["status"] for attempt in caught.value.provider_attempts] == [
        "unavailable", "unavailable"
    ]
    assert [attempt["provider"] for attempt in caught.value.provider_attempts] == [
        "Google Gemini API", "OpenRouter audio route"
    ]


def test_openrouter_failure_falls_back_to_exact_mistral_two_audio_route(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "invalid-direct-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "invalid-openrouter-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "fake-mistral-key")
    monkeypatch.setattr(pipeline, "_resolve_gemini_model", lambda key: "gemini-fake")
    monkeypatch.setattr(pipeline.time, "sleep", lambda seconds: None)
    observed_mistral_body = {}
    mistral_calls = 0
    inner = json.dumps({
        dim: {"score": 4, "reason": "audible evidence"}
        for dim in pipeline.RUBRIC_DIMENSIONS
    }, ensure_ascii=False)

    def _route(req, timeout=None):
        nonlocal mistral_calls
        import urllib.error
        if "googleapis" in req.full_url:
            raise urllib.error.HTTPError(
                req.full_url, 400, "bad key", {}, io.BytesIO(b"direct invalid")
            )
        if "openrouter" in req.full_url:
            raise urllib.error.HTTPError(
                req.full_url, 401, "bad key", {}, io.BytesIO(b"router invalid")
            )
        mistral_calls += 1
        if mistral_calls == 1:
            raise urllib.error.HTTPError(
                req.full_url, 500, "transient", {}, io.BytesIO(b"service unavailable")
            )
        observed_mistral_body.update(json.loads(req.data))
        return _FakeHTTPResp(json.dumps({
            "choices": [{"message": {"content": inner}}]
        }).encode())

    monkeypatch.setattr("urllib.request.urlopen", _route)
    audio_bytes = b"\xff\xfb" + b"\x00" * 256
    reference_bytes = b"\xff\xfb" + b"\x01" * 256
    audio = tmp_path / "a.mp3"
    audio.write_bytes(audio_bytes)
    reference = tmp_path / "reference.mp3"
    reference.write_bytes(reference_bytes)

    rub = pipeline.judge_gemini_audio("原文", "中性", str(audio), str(reference))

    content = observed_mistral_body["messages"][0]["content"]
    assert [item["type"] for item in content] == [
        "text", "text", "input_audio", "text", "input_audio"
    ]
    audio_chunks = [item for item in content if item["type"] == "input_audio"]
    assert len(audio_chunks) == 2
    assert audio_chunks[0]["input_audio"].startswith("data:audio/mpeg;base64,")
    assert audio_chunks[1]["input_audio"].startswith("data:audio/mpeg;base64,")
    assert rub.judge_model == "mistral/voxtral-small-latest"
    assert rub.evidence_mode == "direct-audio-with-reference"
    assert [attempt["provider"] for attempt in rub.provider_attempts] == [
        "Google Gemini API", "OpenRouter audio route", "Mistral Voxtral API"
    ]
    assert [attempt["status"] for attempt in rub.provider_attempts] == [
        "unavailable", "unavailable", "ok"
    ]
    assert rub.provider_attempts[-1]["attempts"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
