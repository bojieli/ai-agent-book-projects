import datetime
import importlib.util
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("openai")
_module_path = (
    Path(__file__).resolve().parent.parent / "chapter6" / "phone-agent" / "agent.py"
)
_spec = importlib.util.spec_from_file_location("phone_agent", _module_path)
_module = importlib.util.module_from_spec(_spec)
sys.modules["phone_agent"] = _module
_spec.loader.exec_module(_module)
_redact_secrets = _module._redact_secrets


class CustomObject:
    def __str__(self):
        return "CustomObjectRepresentation"


def test_redact_secrets_non_serializable(monkeypatch):
    monkeypatch.setenv("MY_API_KEY", "secret_key_12345678")

    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    data = {
        "timestamp": now,
        "tags": {"tag1", "tag2"},
        "custom": CustomObject(),
        "api_key": "secret_key_12345678",
        "openai_key": "sk-12345678901234567890",
    }

    sanitized = _redact_secrets(data)

    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["openai_key"] == "[REDACTED]"
    assert sanitized["timestamp"] == str(now)
    assert sanitized["custom"] == "CustomObjectRepresentation"
    assert isinstance(sanitized["tags"], str) or isinstance(sanitized["tags"], list)
