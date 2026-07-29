"""Regression: URL credentials with an empty username must be redacted."""
from regex_sanitizer import sanitize


def test_redis_empty_user_password_redacted():
    text, hits = sanitize("redis://:secretpass@10.0.0.1:6379/0")
    assert "secretpass" not in text
    assert "[REDACTED_URL_CRED]" in text
    assert any(h["category"] == "url_credential" for h in hits)


def test_postgres_empty_user_password_redacted():
    text, hits = sanitize("DATABASE_URL=postgres://:hunter2@localhost:5432/db")
    assert "hunter2" not in text
    assert "[REDACTED_URL_CRED]" in text
    assert any(h["category"] == "url_credential" for h in hits)


def test_named_user_password_still_redacted():
    text, hits = sanitize("redis://default:secretpass@10.0.0.1:6379/0")
    assert "secretpass" not in text
    assert "[REDACTED_URL_CRED]" in text
