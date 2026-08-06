"""AES-GCM encrypted PII vault with optional DB persistence."""

from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.vault.kms import fetch_aes_key


def _aes_key() -> bytes:
    """Derive AES key via KMS provider SPI (env|file|aws_kms_stub|http_kms)."""
    return fetch_aes_key()


@dataclass
class VaultEntry:
    token: str
    value: str
    pii_type: str
    tenant_id: str
    request_id: str
    ciphertext: str = ""
    nonce: str = ""


class Vault:
    """In-memory + encryptable store; Gateway uses this for redact/restore."""

    def __init__(self) -> None:
        self._entries: dict[str, VaultEntry] = {}
        self._counters: dict[str, int] = {}
        self._aes = AESGCM(_aes_key())

    def put(
        self, *, tenant_id: str, request_id: str, pii_type: str, value: str
    ) -> str:
        n = self._counters.get(pii_type, 0) + 1
        self._counters[pii_type] = n
        # request-scoped unique token so DB unique(token) never collides across calls
        token = f"[REDACTED_{pii_type}_{n}_{request_id[-8:]}]"
        nonce = hashlib.sha256(f"{tenant_id}:{request_id}:{token}".encode()).digest()[:12]
        ct = self._aes.encrypt(nonce, value.encode("utf-8"), tenant_id.encode("utf-8"))
        self._entries[token] = VaultEntry(
            token=token,
            value=value,
            pii_type=pii_type,
            tenant_id=tenant_id,
            request_id=request_id,
            ciphertext=base64.b64encode(ct).decode("ascii"),
            nonce=base64.b64encode(nonce).decode("ascii"),
        )
        return token

    def get(self, token: str, *, tenant_id: str) -> str | None:
        e = self._entries.get(token)
        if e is None or e.tenant_id != tenant_id:
            return None
        return e.value

    def deanonymize(self, text: str, *, tenant_id: str) -> str:
        def repl(m: re.Match[str]) -> str:
            tok = m.group(0)
            val = self.get(tok, tenant_id=tenant_id)
            return val if val is not None else tok

        return re.sub(r"\[REDACTED_[A-Za-z0-9_]+\]", repl, text)

    def tokens_for_request(self, request_id: str) -> list[str]:
        return [e.token for e in self._entries.values() if e.request_id == request_id]

    def encrypted_entries_for_request(self, request_id: str) -> list[VaultEntry]:
        return [e for e in self._entries.values() if e.request_id == request_id]
