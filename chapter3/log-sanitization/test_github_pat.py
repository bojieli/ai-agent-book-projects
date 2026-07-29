"""Regression: fine-grained github_pat_* tokens must be redacted."""
from regex_sanitizer import sanitize


def test_github_pat_fine_grained_redacted():
    token = "github_pat_" + "A" * 20 + "_" + "B" * 40
    text, hits = sanitize(f"Authorization: {token}")
    assert token not in text
    assert "[REDACTED_GITHUB_TOKEN]" in text
    assert any(h["category"] == "github_token" for h in hits)


def test_classic_ghp_token_still_redacted():
    token = "ghp_" + "x" * 36
    text, hits = sanitize(token)
    assert token not in text
    assert "[REDACTED_GITHUB_TOKEN]" in text
    assert any(h["category"] == "github_token" for h in hits)
