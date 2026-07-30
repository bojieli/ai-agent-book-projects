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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
