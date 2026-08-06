"""Recursive decode views — handbook §8.2.3 (encoding obfuscation).

Try Base64 / URL / ROT13 / Unicode-escape layers with a hard depth cap
to avoid decode bombs; return all intermediate plaintext views for scanning.
"""

from __future__ import annotations

import base64
import codecs
import re
from urllib.parse import unquote_plus

from app.scanners.hidden_ascii import decode_unicode_tags, has_unicode_tags

_B64_CHUNK_RE = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
# Non-consecutive %XX (e.g. Ignore%20previous%20instructions) still counts
_URL_PCT_RE = re.compile(r"%[0-9A-Fa-f]{2}")
_UNICODE_ESC_RE = re.compile(r"(?:\\u[0-9a-fA-F]{4}){3,}")
_ROT13_HINT_RE = re.compile(r"(?i)rot[\s_-]?13")
_HEX_HINT_RE = re.compile(r"(?i)(hex|hexadecimal|十六进制)")
_HEX_CHUNK_RE = re.compile(r"(?:[0-9a-fA-F]{2}\s*){12,}")
_MORSE_HINT_RE = re.compile(r"(?i)morse")
_MORSE_CHUNK_RE = re.compile(r"(?:[.\-]{1,6}(?:\s+[.\-]{1,6}){2,}(?:\s*/\s*[.\-\s]+)*)")
_LATIN_SPAN_RE = re.compile(r"[A-Za-z][A-Za-z\s.,!?]{10,160}")
_MORSE_MAP = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
}

MAX_DECODE_DEPTH = 3
MAX_VIEWS = 24


def _try_b64(chunk: str) -> str | None:
    raw = chunk.replace("-", "+").replace("_", "/")
    pad = "=" * ((4 - len(raw) % 4) % 4)
    try:
        dec = base64.b64decode(raw + pad, validate=False).decode("utf-8", "ignore")
    except Exception:
        return None
    if not dec or len(dec) < 4:
        return None
    if any("\u4e00" <= c <= "\u9fff" for c in dec):
        return dec
    printable = sum(1 for c in dec if c.isprintable() or c.isspace())
    if printable / max(1, len(dec)) >= 0.85:
        return dec
    return None


def _try_url(text: str) -> str | None:
    if len(_URL_PCT_RE.findall(text)) < 3:
        return None
    try:
        out = unquote_plus(text)
    except Exception:
        return None
    return out if out != text else None


def _try_unicode_esc(text: str) -> str | None:
    if not _UNICODE_ESC_RE.search(text):
        return None
    try:
        out = codecs.decode(text, "unicode_escape")
        if isinstance(out, bytes):
            out = out.decode("utf-8", "ignore")
    except Exception:
        return None
    return out if out and out != text else None


def _try_rot13_spans(text: str) -> list[str]:
    if not _ROT13_HINT_RE.search(text):
        return []
    out: list[str] = []
    for m in _LATIN_SPAN_RE.finditer(text):
        try:
            out.append(codecs.decode(m.group(0), "rot_13"))
        except Exception:
            continue
    return out


def _try_hex_chunks(text: str) -> list[str]:
    if not (_HEX_HINT_RE.search(text) or _HEX_CHUNK_RE.search(text)):
        return []
    out: list[str] = []
    for m in _HEX_CHUNK_RE.finditer(text):
        raw = re.sub(r"\s+", "", m.group(0))
        if len(raw) < 24 or len(raw) % 2:
            continue
        try:
            dec = bytes.fromhex(raw).decode("utf-8", "ignore")
        except Exception:
            continue
        if dec and sum(1 for c in dec if c.isprintable() or c.isspace()) / max(1, len(dec)) >= 0.85:
            out.append(dec)
    return out


def _try_morse(text: str) -> list[str]:
    if not _MORSE_HINT_RE.search(text):
        return []
    out: list[str] = []
    for m in _MORSE_CHUNK_RE.finditer(text):
        chunk = m.group(0)
        words = []
        for word in re.split(r"\s*/\s*", chunk):
            letters = []
            for token in word.split():
                ch = _MORSE_MAP.get(token)
                if ch:
                    letters.append(ch)
            if letters:
                words.append("".join(letters))
        if words:
            out.append(" ".join(words))
    return out


def recursive_decode_views(text: str, *, max_depth: int = MAX_DECODE_DEPTH) -> list[str]:
    """Return unique decoded views (excluding the original ``text``)."""
    if not text:
        return []
    seen: set[str] = {text}
    views: list[str] = []
    queue: list[tuple[str, int]] = [(text, 0)]

    while queue and len(views) < MAX_VIEWS:
        cur, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        candidates: list[str] = []

        if has_unicode_tags(cur):
            tag_dec = decode_unicode_tags(cur)
            if tag_dec != cur:
                candidates.append(tag_dec)

        for m in _B64_CHUNK_RE.finditer(cur):
            dec = _try_b64(m.group(0))
            if dec:
                candidates.append(dec)

        url_dec = _try_url(cur)
        if url_dec:
            candidates.append(url_dec)

        uni = _try_unicode_esc(cur)
        if uni:
            candidates.append(uni)

        candidates.extend(_try_rot13_spans(cur))
        candidates.extend(_try_hex_chunks(cur))
        candidates.extend(_try_morse(cur))

        for c in candidates:
            if c in seen or len(c) > 50_000:
                continue
            seen.add(c)
            views.append(c)
            queue.append((c, depth + 1))
            if len(views) >= MAX_VIEWS:
                break

    return views
