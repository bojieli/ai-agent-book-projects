"""Regression: quoted secret assignments must redact the full value, including spaces."""
from regex_sanitizer import sanitize


def test_double_quoted_password_with_spaces():
    text, hits = sanitize('password="hunter 2 with spaces"')
    assert "hunter" not in text
    assert "spaces" not in text
    assert "[REDACTED_SECRET]" in text
    assert any(h["category"] == "secret_assignment" for h in hits)


def test_single_quoted_password_with_spaces():
    text, hits = sanitize("api_key='sk-abc def ghi'")
    assert "sk-abc" not in text
    assert "ghi" not in text
    assert "[REDACTED_SECRET]" in text


def test_unquoted_secret_still_redacted():
    text, hits = sanitize("password=hunter2xyz")
    assert "hunter2xyz" not in text
    assert "[REDACTED_SECRET]" in text
