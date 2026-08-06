"""Defense-in-depth text normalization before classification."""

from __future__ import annotations

import re
import unicodedata

# Common homoglyph / fullwidth maps (subset for demo; extend in production)
_HOMO = str.maketrans(
    {
        "０": "0",
        "１": "1",
        "２": "2",
        "３": "3",
        "４": "4",
        "５": "5",
        "６": "6",
        "７": "7",
        "８": "8",
        "９": "9",
        "ａ": "a",
        "ｂ": "b",
        "ｃ": "c",
        "ｄ": "d",
        "ｅ": "e",
        "ｆ": "f",
        "ｇ": "g",
        "ｈ": "h",
        "ｉ": "i",
        "ｊ": "j",
        "ｋ": "k",
        "ｌ": "l",
        "ｍ": "m",
        "ｎ": "n",
        "ｏ": "o",
        "ｐ": "p",
        "ｑ": "q",
        "ｒ": "r",
        "ｓ": "s",
        "ｔ": "t",
        "ｕ": "u",
        "ｖ": "v",
        "ｗ": "w",
        "ｘ": "x",
        "ｙ": "y",
        "ｚ": "z",
        "Ａ": "a",
        "Ｂ": "b",
        "Ｃ": "c",
        "＠": "@",
        "．": ".",
        "／": "/",
        "－": "-",
        "—": "-",
        "–": "-",
        "\u3000": " ",
    }
)

_ZW = re.compile(r"[\u200b\u200c\u200d\ufeff\u2060]")
_SPACE_NOISE = re.compile(r"(?<=\w)\s+(?=\w)")  # "b o m b" → keep for detection via de-space variant


def normalize_text(text: str) -> str:
    """NFKC + strip zero-width + homoglyph fold + lower."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = _ZW.sub("", t)
    t = t.translate(_HOMO)
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def despace_alnum(text: str) -> str:
    """Collapse char-spaced tokens ('i g n o r e', 'b o m b', '强 制 导 出')."""

    def _collapse(m: re.Match[str]) -> str:
        return m.group(0).replace(" ", "").replace("\t", "")

    # 3+ single alnum chars separated by spaces → one token
    t = re.sub(r"(?<![a-z0-9])(?:[a-z0-9] ){2,}[a-z0-9](?![a-z0-9])", _collapse, text)
    # 3+ CJK chars separated by spaces
    t = re.sub(
        r"(?<![\u4e00-\u9fff])(?:[\u4e00-\u9fff] ){2,}[\u4e00-\u9fff](?![\u4e00-\u9fff])",
        _collapse,
        t,
    )
    return t


_LEET = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }
)


def leetspeak_fold(text: str) -> str:
    """Light leetspeak fold for scanner multi-views (not for display)."""
    if not text:
        return ""
    return text.translate(_LEET)


def obfuscation_signals(raw: str, norm: str) -> list[str]:
    signals: list[str] = []
    if _ZW.search(raw):
        signals.append("zero_width_chars")
    if raw != unicodedata.normalize("NFKC", raw):
        signals.append("nfkc_changed")
    if len(raw) > 20 and raw.count(" ") / max(1, len(raw)) > 0.25:
        signals.append("space_stuffing")
    if any(ord(c) > 0xFF00 for c in raw):
        signals.append("fullwidth_chars")
    if re.search(r"([a-z0-9] ){4,}[a-z0-9]", norm):
        signals.append("char_spaced_words")
    if re.search(r"([\u4e00-\u9fff] ){4,}[\u4e00-\u9fff]", norm):
        signals.append("char_spaced_cjk")
    if re.search(r"[0-9@$]{2,}", norm) and re.search(
        r"(?i)(p4u|54f|ch3ck|dr4f|v10l|h0w|r3qu|ign0|r3veal)", norm
    ):
        signals.append("leetspeak_like")
    return signals
