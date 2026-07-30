from dataclasses import dataclass
from unittest.mock import patch

import pytest

import pineclaw_tool


@dataclass
class Turn:
    speaker: str
    text: str


@dataclass
class Result:
    call_id: str = "call-real-contract"
    status: str = "completed"
    duration_seconds: int = 42
    summary: str = "Appointment booked."
    transcript: list[Turn] = None
    credits_charged: int = 3

    def __post_init__(self):
        self.transcript = self.transcript or [Turn("agent", "Your confirmation is ABC123")]


class Calls:
    def __init__(self):
        self.kwargs = None

    def create_and_wait(self, **kwargs):
        self.kwargs = kwargs
        return Result()


class FakePineVoice:
    last = None

    def __init__(self, **credentials):
        self.credentials = credentials
        self.calls = Calls()
        FakePineVoice.last = self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_real_sdk_contract_and_normalization(monkeypatch):
    monkeypatch.setenv("PINE_ACCESS_TOKEN", "secret")
    monkeypatch.setenv("PINE_USER_ID", "user")
    monkeypatch.setenv("PINE_AUTHORIZED_TEST_NUMBER", "+14155551234")
    monkeypatch.setenv("PINE_TEST_CALL_CONSENT", "I_HAVE_EXPLICIT_CONSENT")
    fake_module = type("M", (), {"PineVoice": FakePineVoice})
    with patch.dict("sys.modules", {"pine_voice": fake_module}):
        record = pineclaw_tool.make_phone_call(
            "+14155551234",
            "Book Tuesday at 3pm",
            "Patient Jane Doe",
            callee_name="Dr Smith",
            extract_facts=False,
        )
    assert FakePineVoice.last.calls.kwargs["to"] == "+14155551234"
    assert FakePineVoice.last.calls.kwargs["objective"] == "Book Tuesday at 3pm"
    assert FakePineVoice.last.calls.kwargs["enable_summary"] is True
    assert record["provider"] == "pine-voice"
    assert record["call_id"] == "call-real-contract"
    assert record["transcript"][0]["text"] == "Your confirmation is ABC123"


def test_requires_e164_before_any_network_call():
    with pytest.raises(ValueError, match="E.164"):
        pineclaw_tool.make_phone_call("10010", "test", extract_facts=False)


def test_requires_explicit_destination_allowlist(monkeypatch):
    monkeypatch.delenv("PINE_AUTHORIZED_TEST_NUMBER", raising=False)
    monkeypatch.delenv("PINE_TEST_CALL_CONSENT", raising=False)
    with pytest.raises(PermissionError, match="disabled"):
        pineclaw_tool.make_phone_call("+14155551234", "test", extract_facts=False)


def test_rejects_a_different_number_even_with_consent(monkeypatch):
    monkeypatch.setenv("PINE_AUTHORIZED_TEST_NUMBER", "+14155551234")
    monkeypatch.setenv("PINE_TEST_CALL_CONSENT", "I_HAVE_EXPLICIT_CONSENT")
    with pytest.raises(PermissionError, match="not the explicitly authorized"):
        pineclaw_tool.make_phone_call("+14155550000", "test", extract_facts=False)
