"""Regression: URL passwords containing ':' or '/' must be fully redacted."""
from regex_sanitizer import sanitize


def test_password_with_slash_redacted():
    text, hits = sanitize("DATABASE_URL=postgres://alice:a/b@db.example:5432/app")
    assert "a/b" not in text
    assert "[REDACTED_URL_CRED]" in text
    assert any(h["category"] == "url_credential" for h in hits)


def test_password_with_colon_redacted():
    text, hits = sanitize("redis://default:foo:bar@10.0.0.1:6379/0")
    assert "foo:bar" not in text
    assert "[REDACTED_URL_CRED]" in text
    assert any(h["category"] == "url_credential" for h in hits)


def test_simple_password_still_redacted():
    text, hits = sanitize("postgres://alice:secret@db.example:5432/app")
    assert "secret" not in text
    assert "[REDACTED_URL_CRED]" in text
    assert any(h["category"] == "url_credential" for h in hits)
