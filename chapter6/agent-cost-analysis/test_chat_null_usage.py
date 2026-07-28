"""Tracer.chat must tolerate response.usage == None (OpenAI-compatible providers)."""

from types import SimpleNamespace

import config
from tracer import Tracer


class _FakeClient:
    def __init__(self, usage):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )
        self._usage = usage

    def _create(self, **_kwargs):
        return SimpleNamespace(usage=self._usage)


def test_chat_tolerates_null_usage():
    tr = Tracer(_FakeClient(None), pricing=config.default_pricing())
    resp = tr.chat(step="turn-1", tool="query_order", model="m", messages=[])
    assert resp.usage is None
    assert len(tr.spans) == 1
    s = tr.spans[0]
    assert s.prompt_tokens == 0
    assert s.completion_tokens == 0
    assert s.cost_usd == 0.0
    assert s.latency_s >= 0.0


def test_chat_keeps_real_usage():
    usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=20,
        prompt_tokens_details=SimpleNamespace(cached_tokens=10),
    )
    tr = Tracer(_FakeClient(usage), pricing=config.default_pricing())
    tr.chat(step="turn-1", tool="query_order", model="m", messages=[])
    s = tr.spans[0]
    assert s.prompt_tokens == 100
    assert s.completion_tokens == 20
    assert s.cached_tokens == 10
    assert s.cost_usd > 0
