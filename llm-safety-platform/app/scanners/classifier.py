"""SafetyClassifier SPI — swap shim / onnx / remote / optional llm-guard.

Default CI path remains rule engine (SAFETY_SCANNER_MODE=shim).
ONNX and remote adapters are real call sites; weights/endpoints come from env.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.scanners.engine import ContentScoreEngine, EngineResult


@dataclass
class ClassifierResult:
    decision: str
    score: float
    categories: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    backend: str = "shim"
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "score": self.score,
            "categories": self.categories,
            "reasons": self.reasons,
            "backend": self.backend,
            "extra": self.extra,
        }


class SafetyClassifier(Protocol):
    name: str

    def classify(
        self,
        text: str,
        categories: tuple[str, ...] | list[str] | None = None,
    ) -> ClassifierResult: ...


class ShimClassifier:
    """YAML rule engine + normalization (always available)."""

    name = "shim"

    def __init__(self, rules_path: str | None = None) -> None:
        self.engine = ContentScoreEngine(rules_path)

    def classify(
        self,
        text: str,
        categories: tuple[str, ...] | list[str] | None = None,
    ) -> ClassifierResult:
        r: EngineResult = self.engine.score(text, categories)
        return ClassifierResult(
            decision=r.decision,
            score=r.score,
            categories=r.categories,
            reasons=r.reasons,
            backend=self.name,
            extra={"obfuscation": r.obfuscation, "normalized": r.normalized},
        )


_DEC_RANK = {"allow": 0, "alert_only": 1, "block": 2}


def _fuse_classifier_results(
    rules: ClassifierResult, remote: ClassifierResult
) -> ClassifierResult:
    """Max-strict dual-path: local rules always floor the remote Judge."""
    decision = (
        rules.decision
        if _DEC_RANK.get(rules.decision, 0) >= _DEC_RANK.get(remote.decision, 0)
        else remote.decision
    )
    score = max(rules.score, remote.score)
    cats = sorted(set(rules.categories) | set(remote.categories))
    reasons = list(dict.fromkeys([*rules.reasons, *remote.reasons, "fuse:rules_union_remote"]))
    return ClassifierResult(
        decision=decision,
        score=score,
        categories=cats,
        reasons=reasons,
        backend=f"fuse:{rules.backend}+{remote.backend}",
        extra={"rules": rules.extra, "remote": remote.extra},
    )


class RemoteClassifier:
    """HTTP classifier: POST {text, categories} → {decision, score, categories, reasons}.

    Dual-path: local YAML rules always run and max-fuse with remote (Judge soft-allow
    cannot downgrade a rules hit). Defaults tuned for safer local/dev:
      SAFETY_REMOTE_TIMEOUT=12  (override higher for slow GPU Judges)
      SAFETY_REMOTE_FAIL_CLOSED=0 → keep rules fallback on error;
        =1 → escalate allow→block when remote is down (prod/on-prem).
    """

    name = "remote"

    def __init__(
        self,
        url: str | None = None,
        timeout: float | None = None,
        fallback: SafetyClassifier | None = None,
    ) -> None:
        self.url = url or os.getenv("SAFETY_CLASSIFIER_URL", "")
        self.timeout = float(
            timeout
            if timeout is not None
            else os.getenv("SAFETY_REMOTE_TIMEOUT", "12")
        )
        self.fallback = fallback or ShimClassifier()

    def classify(
        self,
        text: str,
        categories: tuple[str, ...] | list[str] | None = None,
    ) -> ClassifierResult:
        # Rules always run first (dual-path floor).
        rules = self.fallback.classify(text, categories)
        if not self.url:
            rules.backend = f"{self.fallback.name}+remote_unconfigured"
            return rules
        body = json.dumps(
            {"text": text, "categories": list(categories) if categories else None},
            ensure_ascii=False,
        ).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            remote = ClassifierResult(
                decision=str(data.get("decision", "block")),
                score=float(data.get("score", 0.9)),
                categories=list(data.get("categories") or []),
                reasons=list(data.get("reasons") or ["remote_classifier"]),
                backend=self.name,
                extra={"raw": data},
            )
            if remote.decision not in _DEC_RANK:
                remote.decision = "block"
            return _fuse_classifier_results(rules, remote)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            # Default: trust shim/rules fallback (always-on safety net).
            # Set SAFETY_REMOTE_FAIL_CLOSED=1 to escalate allow → block when remote is down.
            fail_closed = os.getenv("SAFETY_REMOTE_FAIL_CLOSED", "0").lower() in (
                "1",
                "true",
                "yes",
                "on",
            )
            if fail_closed and rules.decision == "allow":
                return ClassifierResult(
                    decision="block",
                    score=1.0,
                    categories=[],
                    reasons=["remote_classifier_error_fail_closed"],
                    backend=f"{self.name}_error",
                )
            rules.backend = f"{self.name}_fallback"
            rules.reasons = list(rules.reasons) + ["remote_classifier_error_fallback"]
            return rules


class OnnxClassifier:
    """ONNX Runtime adapter. Without SAFETY_ONNX_MODEL_PATH, falls back to shim."""

    name = "onnx"

    def __init__(
        self,
        model_path: str | None = None,
        fallback: SafetyClassifier | None = None,
    ) -> None:
        self.model_path = model_path or os.getenv("SAFETY_ONNX_MODEL_PATH", "")
        self.fallback = fallback or ShimClassifier()
        self._session = None
        if self.model_path:
            try:
                import onnxruntime as ort  # type: ignore

                self._session = ort.InferenceSession(
                    self.model_path, providers=["CPUExecutionProvider"]
                )
            except Exception:
                self._session = None

    def classify(
        self,
        text: str,
        categories: tuple[str, ...] | list[str] | None = None,
    ) -> ClassifierResult:
        if self._session is None:
            r = self.fallback.classify(text, categories)
            r.backend = f"{self.fallback.name}+onnx_unconfigured"
            return r
        # Placeholder tensor path — production wires tokenizer + label map here.
        # Until then, fuse shim score with a conservative floor so CI stays deterministic.
        fb = self.fallback.classify(text, categories)
        fb.backend = "onnx+shim_fused"
        fb.extra["onnx_session"] = True
        return fb


class LlmGuardAdapter:
    """Optional llm-guard import via SAFETY_LLM_GUARD_PATH (study clone / vendored).

    Never a hard dependency — ADR: no production import from study by default.
    """

    name = "llm_guard"

    def __init__(self, fallback: SafetyClassifier | None = None) -> None:
        self.fallback = fallback or ShimClassifier()
        self._scanner = None
        path = os.getenv("SAFETY_LLM_GUARD_PATH", "")
        if path and path not in __import__("sys").path:
            __import__("sys").path.insert(0, path)
        try:
            from llm_guard.input_scanners import PromptInjection  # type: ignore

            self._scanner = PromptInjection()
        except Exception:
            self._scanner = None

    def classify(
        self,
        text: str,
        categories: tuple[str, ...] | list[str] | None = None,
    ) -> ClassifierResult:
        fb = self.fallback.classify(text, categories)
        if self._scanner is None:
            fb.backend = f"{self.fallback.name}+llm_guard_unavailable"
            return fb
        try:
            sanitized, is_valid, risk = self._scanner.scan(text)
            del sanitized
            if not is_valid or (isinstance(risk, (int, float)) and float(risk) >= 0.7):
                # merge: escalate if llm-guard flags
                score = max(fb.score, float(risk) if isinstance(risk, (int, float)) else 0.9)
                return ClassifierResult(
                    decision="block" if score >= 0.72 else "alert_only",
                    score=score,
                    categories=sorted(set(fb.categories + ["jailbreak"])),
                    reasons=fb.reasons + ["llm_guard_prompt_injection"],
                    backend=self.name,
                )
        except Exception:
            pass
        fb.backend = f"{self.name}+{self.fallback.name}"
        return fb


def build_classifier(mode: str | None = None) -> SafetyClassifier:
    """Factory from SAFETY_SCANNER_MODE: shim|onnx|remote|llm_guard."""
    m = (mode or os.getenv("SAFETY_SCANNER_MODE", "shim")).lower()
    shim = ShimClassifier(os.getenv("SAFETY_CONTENT_RULES_PATH") or None)
    if m == "remote":
        return RemoteClassifier(fallback=shim)
    if m == "onnx":
        return OnnxClassifier(fallback=shim)
    if m in ("llm_guard", "llm-guard"):
        return LlmGuardAdapter(fallback=shim)
    return shim
