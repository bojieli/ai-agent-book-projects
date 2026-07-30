"""Truncated PEM (BEGIN without END) must be redacted, not leaked."""

from regex_sanitizer import sanitize


def test_truncated_rsa_pem_without_end_redacted():
    blob = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF6PZGFw7\n"
        "ygWyF6PZGFw7morekeymaterialHERE"
    )
    text, hits = sanitize(f"key dump:\n{blob}\n")
    assert "MIIEowIBAAKCAQEA" not in text
    assert "[REDACTED_PRIVATE_KEY]" in text
    assert any(h["category"] == "private_key" for h in hits)


def test_complete_pem_still_redacted():
    blob = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF6PZGFw7\n"
        "-----END RSA PRIVATE KEY-----"
    )
    text, hits = sanitize(blob)
    assert "MIIEowIBAAKCAQEA" not in text
    assert text.strip() == "[REDACTED_PRIVATE_KEY]"
    assert any(h["category"] == "private_key" for h in hits)


def test_non_key_text_unchanged():
    text, hits = sanitize("no secrets here, only BEGIN of a story")
    assert text == "no secrets here, only BEGIN of a story"
    assert hits == []
