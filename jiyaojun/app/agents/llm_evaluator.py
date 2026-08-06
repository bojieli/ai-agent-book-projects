"""Mock independent LLM Evaluator — fresh context, no generator trace reuse."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from app.agents.evaluator import EvalResult, Evaluator
from app.domain_layer.envelope import validate_envelope


@dataclass
class MockLLMResponse:
    model: str
    prompt_hash: str
    verdict: str  # pass | fail
    rationale: str
    scores: dict[str, float]


class MockLLMClient:
    """Deterministic mock LLM — same prompt → same output (no network)."""

    def __init__(self, model: str = "mock-llm-evaluator-v1") -> None:
        self.model = model
        self.calls: list[dict[str, Any]] = []

    def complete(self, system: str, user: str) -> MockLLMResponse:
        blob = f"{system}\n---\n{user}"
        prompt_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]
        self.calls.append({"system": system[:200], "user": user[:500], "hash": prompt_hash})
        # Heuristics as stand-in for LLM judgment
        fail_markers = ["各方同意", "未确认生产生效", "热切换", "群发全员"]
        hit = [m for m in fail_markers if m in user]
        if hit or "\"blocking_embed\": true" in user and "decision" in user:
            return MockLLMResponse(
                self.model,
                prompt_hash,
                "fail",
                f"mock-llm flagged: {hit or ['blocking unresolved']}",
                {"faithfulness": 0.2, "schema": 0.9},
            )
        return MockLLMResponse(
            self.model,
            prompt_hash,
            "pass",
            "mock-llm: success criteria appear satisfied",
            {"faithfulness": 0.86, "schema": 0.95},
        )


class IndependentLLMEvaluator:
    """
    Fresh-context evaluator (03): must NOT receive generator full trajectory.
    Combines rule Evaluator + mock LLM second opinion for L3/high-risk.
    """

    def __init__(self, llm: MockLLMClient | None = None) -> None:
        self.rules = Evaluator()
        self.llm = llm or MockLLMClient()

    def evaluate(
        self,
        *,
        artifact: dict[str, Any],
        success_criteria: list[str],
        policy_failures: list[str] | None = None,
        ambiguity_open: bool = False,
        prose_claims_all_agree: bool = False,
        require_llm: bool = False,
    ) -> EvalResult:
        base = self.rules.evaluate(
            artifact=artifact,
            success_predicates=success_criteria,
            policy_failures=policy_failures,
            ambiguity_open=ambiguity_open,
            prose_claims_all_agree=prose_claims_all_agree,
        )
        if not require_llm and base.passed:
            return base

        # Fresh context only: schema + payload + criteria (no generator chain)
        system = "You are an independent meeting-artifact evaluator. Reply pass/fail."
        user = json.dumps(
            {
                "success_criteria": success_criteria,
                "artifact": {
                    "kind": artifact.get("artifact_kind"),
                    "payload": artifact.get("payload"),
                    "unresolved": artifact.get("unresolved"),
                    "classification": artifact.get("classification"),
                },
                "envelope_errors": validate_envelope(artifact),
            },
            ensure_ascii=False,
        )
        llm_out = self.llm.complete(system, user)
        failures = list(base.failures)
        checks = list(base.checks) + ["mock_llm_evaluator"]
        if llm_out.verdict == "fail":
            failures.append({"code": "llm_eval_fail", "message": llm_out.rationale})
        return EvalResult(passed=not failures, failures=failures, checks=checks)
