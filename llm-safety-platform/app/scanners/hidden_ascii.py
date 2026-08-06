"""Hidden Unicode Tag characters (U+E0000–E007F) — LlamaFirewall-inspired.

Steganographic prompt injection can hide Latin letters in Unicode Tags.
Detect + decode into a scan view; block when decoded payload looks injurious.
"""

from __future__ import annotations

import re

from app.scanners.base import ScanContext, ScanResult

_TAG_BASE = 0xE0000
_TAG_MAX = 0xE007F
_INJ_HINT = re.compile(
    r"(?i)(ignore\s+(all\s+)?previous|forget\s+(all\s+)?previous|system\s+prompt|"
    r"reveal|jailbreak|\bDAN\b|exfiltrat|secret\s*key|password)",
)


def decode_unicode_tags(text: str) -> str:
    out: list[str] = []
    for ch in text:
        o = ord(ch)
        if _TAG_BASE <= o <= _TAG_MAX:
            out.append(chr(o - _TAG_BASE))
        else:
            out.append(ch)
    return "".join(out)


def has_unicode_tags(text: str) -> bool:
    return any(_TAG_BASE <= ord(ch) <= _TAG_MAX for ch in text)


class HiddenAsciiScanner:
    """L1 — block steganographic Unicode Tag payloads (PurpleLlama LlamaFirewall)."""

    id = "hidden_ascii"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        if not text or not has_unicode_tags(text):
            return ScanResult(self.id, "allow", 0.0, [])
        decoded = decode_unicode_tags(text)
        reasons = ["hidden_unicode_tags"]
        score = 0.85
        if _INJ_HINT.search(decoded):
            reasons.append("hidden_ascii_injection_payload")
            score = 0.98
        if score >= ctx.spec.threshold:
            return ScanResult(self.id, "block", score, reasons)
        return ScanResult(self.id, "alert_only", score, reasons)
