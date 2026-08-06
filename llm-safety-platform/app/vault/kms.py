"""KMS provider SPI for Vault master key material (ADR-026).

Providers (SAFETY_KMS_PROVIDER):
  env           — SAFETY_MASTER_KEY (default)
  file          — read bytes/text from SAFETY_KMS_FILE_PATH
  aws_kms_stub  — local stub simulating AWS KMS Decrypt (ciphertext file/env)
  http_kms      — POST to SAFETY_KMS_HTTP_URL → {"plaintext_b64": "..."}

Gateway decrypts PII with derived AES-256 key; production swaps provider without
changing Vault encrypt/decrypt call sites.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.request
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any


class KmsProvider(ABC):
    name: str

    @abstractmethod
    def fetch_master_key(self) -> bytes:
        """Return raw key material (any length; caller SHA-256 → AES-256)."""


class EnvKmsProvider(KmsProvider):
    name = "env"

    def fetch_master_key(self) -> bytes:
        raw = os.getenv("SAFETY_MASTER_KEY", "dev-only-change-me-32bytes-key!!")
        return raw.encode("utf-8")


class FileKmsProvider(KmsProvider):
    name = "file"

    def fetch_master_key(self) -> bytes:
        path = os.getenv("SAFETY_KMS_FILE_PATH", "")
        if not path:
            raise RuntimeError("SAFETY_KMS_FILE_PATH required for file KMS")
        with open(path, "rb") as f:
            data = f.read().strip()
        if not data:
            raise RuntimeError("empty KMS key file")
        return data


class AwsKmsStubProvider(KmsProvider):
    """Simulates AWS KMS Decrypt: decrypts base64 blob with a local wrapping key.

    Env:
      SAFETY_KMS_STUB_CIPHERTEXT_B64 — envelope ciphertext (or file via path)
      SAFETY_KMS_STUB_WRAP_KEY       — local wrap key (dev/test only)
    """

    name = "aws_kms_stub"

    def fetch_master_key(self) -> bytes:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        ct_b64 = os.getenv("SAFETY_KMS_STUB_CIPHERTEXT_B64", "").strip()
        path = os.getenv("SAFETY_KMS_STUB_CIPHERTEXT_PATH", "").strip()
        if not ct_b64 and path:
            ct_b64 = open(path, encoding="utf-8").read().strip()
        if not ct_b64:
            # Dev convenience: if no ciphertext, fall back to env master key
            # but mark provider as stub-ready.
            return os.getenv("SAFETY_MASTER_KEY", "dev-only-change-me-32bytes-key!!").encode()
        wrap = os.getenv("SAFETY_KMS_STUB_WRAP_KEY", "aws-kms-stub-wrap-key-32b!!!!").encode()
        wrap_key = hashlib.sha256(wrap).digest()
        blob = base64.b64decode(ct_b64)
        nonce, ct = blob[:12], blob[12:]
        return AESGCM(wrap_key).decrypt(nonce, ct, b"llm-safety-vault")


class HttpKmsProvider(KmsProvider):
    name = "http_kms"

    def fetch_master_key(self) -> bytes:
        url = os.getenv("SAFETY_KMS_HTTP_URL", "").strip()
        if not url:
            raise RuntimeError("SAFETY_KMS_HTTP_URL required for http_kms")
        token = os.getenv("SAFETY_KMS_HTTP_TOKEN", "")
        body = json.dumps({"op": "get_master_key", "key_id": os.getenv("SAFETY_KMS_KEY_ID", "vault")}).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        timeout = float(os.getenv("SAFETY_KMS_HTTP_TIMEOUT", "5"))
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        if "plaintext_b64" in data:
            return base64.b64decode(data["plaintext_b64"])
        if "plaintext" in data:
            return str(data["plaintext"]).encode("utf-8")
        raise RuntimeError("http_kms response missing plaintext")


_PROVIDERS: dict[str, type[KmsProvider]] = {
    "env": EnvKmsProvider,
    "file": FileKmsProvider,
    "aws_kms_stub": AwsKmsStubProvider,
    "http_kms": HttpKmsProvider,
}


def get_kms_provider(name: str | None = None) -> KmsProvider:
    key = (name or os.getenv("SAFETY_KMS_PROVIDER", "env")).strip().lower()
    cls = _PROVIDERS.get(key)
    if cls is None:
        raise ValueError(f"unknown KMS provider: {key}; choose from {sorted(_PROVIDERS)}")
    return cls()


@lru_cache(maxsize=1)
def fetch_aes_key() -> bytes:
    """SHA-256 of provider master material → 32-byte AES key."""
    material = get_kms_provider().fetch_master_key()
    return hashlib.sha256(material).digest()


def reset_kms_cache() -> None:
    fetch_aes_key.cache_clear()


def seal_for_stub(plaintext: bytes, wrap_key: bytes | None = None) -> str:
    """Test helper: produce SAFETY_KMS_STUB_CIPHERTEXT_B64."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    wrap = wrap_key or b"aws-kms-stub-wrap-key-32b!!!!"
    key = hashlib.sha256(wrap).digest()
    nonce = hashlib.sha256(b"stub-nonce").digest()[:12]
    ct = AESGCM(key).encrypt(nonce, plaintext, b"llm-safety-vault")
    return base64.b64encode(nonce + ct).decode("ascii")
