"""Content safety: sexual / violence / political / self-harm.

Uses weighted YAML rule engine + SafetyClassifier SPI.
SAFETY_SCANNER_MODE=shim|onnx|remote|llm_guard — default shim for CI.
Sensitive PII is handled by anonymize/sensitive scanners + Vault — not here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.scanners.base import ScanContext, ScanResult
from app.scanners.classifier import SafetyClassifier, build_classifier

_CLASSIFIER: SafetyClassifier | None = None


def get_classifier() -> SafetyClassifier:
    global _CLASSIFIER
    if _CLASSIFIER is None:
        _CLASSIFIER = build_classifier()
    return _CLASSIFIER


def reset_classifier() -> None:
    """Test helper: rebuild after env changes."""
    global _CLASSIFIER
    _CLASSIFIER = None


@dataclass
class ContentHit:
    category: str
    decision: str
    score: float
    reason: str


def classify_content(
    text: str, categories: tuple[str, ...] | list[str] | None = None
) -> list[ContentHit]:
    """Backward-compatible multi-hit view over the classifier."""
    r = get_classifier().classify(text, categories)
    if not r.categories and r.decision == "allow":
        return []
    if r.categories:
        return [
            ContentHit(
                category=c,
                decision=r.decision if r.decision != "allow" else "alert_only",
                score=r.score,
                reason=f"content_{c}",
            )
            for c in r.categories
        ]
    # obfuscation / generic escalate without named category
    return [
        ContentHit(
            category="unknown",
            decision=r.decision,
            score=r.score,
            reason=r.reasons[0] if r.reasons else "content_flag",
        )
    ]


class ContentSafetyScanner:
    """L1/L3 content policy scanner (sexual / violence / political / self_harm)."""

    id = "content_safety"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        cats = ctx.spec.categories or None
        r = get_classifier().classify(text, cats)
        if r.decision == "allow":
            return ScanResult(self.id, "allow", 0.0, [])
        reasons = [x for x in r.reasons if x.startswith("content_")] or list(r.reasons)
        if not reasons and r.categories:
            reasons = [f"content_{c}" for c in r.categories]
        score = r.score
        if r.decision == "alert_only" or score < ctx.spec.threshold:
            return ScanResult(self.id, "alert_only", score, reasons)
        return ScanResult(self.id, "block", score, reasons)


class ToxicityScanner:
    """Backward-compatible alias: violence-focused subset + general toxic."""

    id = "toxicity"
    layer = "L3"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        hits = classify_content(text, ("violence", "sexual", "self_harm"))
        if re.search(r"杀掉", text):
            hits.append(
                ContentHit("violence", "block", 0.9, "toxic_heuristic")
            )
        if not hits:
            return ScanResult(self.id, "allow", 0.0, [])
        reasons = [h.reason for h in hits]
        score = max(h.score for h in hits)
        if score < ctx.spec.threshold:
            return ScanResult(self.id, "alert_only", score, reasons)
        decision = (
            "block"
            if any(h.decision == "block" for h in hits) or score >= 0.72
            else "alert_only"
        )
        return ScanResult(self.id, decision, score, reasons)
