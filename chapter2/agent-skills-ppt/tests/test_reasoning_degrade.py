#!/usr/bin/env python3
"""Regression tests for chat_with_tools() in demo.py.

Bug: gpt-5.x on OpenAI's direct /v1/chat/completions rejects function tools
unless reasoning_effort="none", so the agentic loop died with a 400 for readers
who have only OPENAI_API_KEY. Hardcoding reasoning_effort="none" would fix the
crash by removing the multi-step reasoning this experiment exists to show, and
would send the parameter to OpenRouter too, where the restriction never
applied. So the call keeps reasoning on and degrades only when the endpoint
actually refuses -- once, then remembers.
"""

import pytest

import demo


class _FakeBadRequest(Exception):
    pass


class _FakeCompletions:
    """Records each call's kwargs; can fail the first call with a given error."""

    def __init__(self, fail_first_with=None):
        self.calls = []
        self._fail_first_with = fail_first_with

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._fail_first_with and len(self.calls) == 1:
            raise self._fail_first_with
        return "response"


class _FakeClient:
    def __init__(self, completions):
        self.chat = type("_Chat", (), {"completions": completions})()


@pytest.fixture(autouse=True)
def _patch_exception(monkeypatch):
    monkeypatch.setattr(demo, "BadRequestError", _FakeBadRequest)


def test_reasoning_is_left_on_when_the_endpoint_accepts_tools():
    completions = _FakeCompletions()
    resp, no_reasoning = demo.chat_with_tools(
        _FakeClient(completions), "openai/gpt-5.6-luna", [], False
    )
    assert resp == "response"
    assert no_reasoning is False
    assert "reasoning_effort" not in completions.calls[0]


def test_degrades_once_when_the_endpoint_refuses_reasoning_with_tools():
    error = _FakeBadRequest(
        "Function tools with reasoning_effort are not supported for gpt-5.6-luna "
        "in /v1/chat/completions. To use function tools, use /v1/responses or "
        "set reasoning_effort to 'none'."
    )
    completions = _FakeCompletions(fail_first_with=error)
    resp, no_reasoning = demo.chat_with_tools(
        _FakeClient(completions), "gpt-5.6-luna", [], False
    )
    assert resp == "response"
    # The caller remembers, so later turns do not pay for the same 400 again.
    assert no_reasoning is True
    assert "reasoning_effort" not in completions.calls[0]
    assert completions.calls[1]["reasoning_effort"] == "none"


def test_remembered_degrade_skips_the_failing_attempt():
    completions = _FakeCompletions()
    demo.chat_with_tools(_FakeClient(completions), "gpt-5.6-luna", [], True)
    assert len(completions.calls) == 1
    assert completions.calls[0]["reasoning_effort"] == "none"


def test_unrelated_bad_requests_are_not_swallowed():
    completions = _FakeCompletions(fail_first_with=_FakeBadRequest("context_length_exceeded"))
    with pytest.raises(_FakeBadRequest):
        demo.chat_with_tools(_FakeClient(completions), "gpt-5.6-luna", [], False)
    assert len(completions.calls) == 1
