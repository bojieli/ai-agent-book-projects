"""Weighted multi-signal content scoring engine (rule baseline)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.scanners.decode_views import recursive_decode_views
from app.scanners.normalize import despace_alnum, leetspeak_fold, normalize_text, obfuscation_signals

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES = ROOT / "configs" / "content_rules" / "default.yaml"


@dataclass
class ScoreHit:
    category: str
    pattern: str
    score: float
    reason: str


@dataclass
class EngineResult:
    decision: str  # allow|alert_only|block
    score: float
    categories: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    obfuscation: list[str] = field(default_factory=list)
    normalized: str = ""
    hits: list[ScoreHit] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "score": self.score,
            "categories": self.categories,
            "reasons": self.reasons,
            "obfuscation": self.obfuscation,
        }


@lru_cache(maxsize=4)
def load_rules(path: str | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_RULES
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def clear_rules_cache() -> None:
    load_rules.cache_clear()


class ContentScoreEngine:
    def __init__(self, rules_path: str | None = None) -> None:
        self.rules = load_rules(rules_path)
        self.block_threshold = float(self.rules.get("block_threshold", 0.72))
        self.alert_threshold = float(self.rules.get("alert_threshold", 0.45))
        self.obfuscation_bonus = float(self.rules.get("obfuscation_bonus", 0.15))
        self._compiled: dict[str, list[tuple[re.Pattern[str], float, str, list[str], list[str]]]] = {}
        for cat, spec in (self.rules.get("categories") or {}).items():
            entries = []
            for item in spec.get("patterns") or []:
                pat = re.compile(item["pattern"], re.I)
                entries.append(
                    (
                        pat,
                        float(item.get("score", 0.8)),
                        item["pattern"],
                        list(item.get("require_context") or []),
                        list(item.get("suppress_context") or []),
                    )
                )
            self._compiled[cat] = entries

    def score(
        self,
        text: str,
        categories: tuple[str, ...] | list[str] | None = None,
    ) -> EngineResult:
        norm = normalize_text(text)
        views = {norm, despace_alnum(norm), leetspeak_fold(despace_alnum(norm))}
        # Handbook §8.2.3 — score decoded payloads (Base64/URL/ROT13) too
        for dec in recursive_decode_views(text):
            nd = normalize_text(dec)
            views.add(nd)
            views.add(despace_alnum(nd))
            views.add(leetspeak_fold(despace_alnum(nd)))
        ob = obfuscation_signals(text, norm)
        cats = list(categories) if categories else list(self._compiled.keys())
        hits: list[ScoreHit] = []

        for cat in cats:
            for pat, sc, raw_pat, ctx_need, ctx_suppress in self._compiled.get(cat, []):
                matched = False
                for view in views:
                    if pat.search(view):
                        if ctx_need and not any(c.lower() in view for c in ctx_need):
                            continue
                        if ctx_suppress and any(c.lower() in view for c in ctx_suppress):
                            continue
                        matched = True
                        break
                if matched:
                    hits.append(
                        ScoreHit(
                            category=cat,
                            pattern=raw_pat,
                            score=sc,
                            reason=f"content_{cat}",
                        )
                    )

        if not hits:
            # Obfuscation-only → allow here; prompt_injection owns spaced jailbreaks.
            return EngineResult(
                "allow",
                0.0,
                obfuscation=ob,
                normalized=norm,
                reasons=[f"obfuscation:{s}" for s in ob] if ob else [],
            )

        # score = max hit, plus obfuscation bonus when evasion signals present
        best = max(h.score for h in hits)
        if ob:
            best = min(1.0, best + self.obfuscation_bonus)

        reasons = [h.reason for h in hits]
        reasons.extend([f"obfuscation:{s}" for s in ob])
        categories_hit = sorted({h.category for h in hits})

        if best >= self.block_threshold:
            decision = "block"
        elif best >= self.alert_threshold:
            decision = "alert_only"
        else:
            decision = "allow"

        return EngineResult(
            decision=decision,
            score=best,
            categories=categories_hit,
            reasons=reasons,
            obfuscation=ob,
            normalized=norm,
            hits=hits,
        )
