import datetime
import os
import sys
from pathlib import Path

# Add chapter9/phone-agent to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "chapter9" / "phone-agent"))

from agent import _redact_secrets


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
