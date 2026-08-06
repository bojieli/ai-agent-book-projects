"""Evaluator — required stage; fresh context (no generator transcript reuse)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain_layer.envelope import validate_envelope


@dataclass
class EvalResult:
    passed: bool
    failures: list[dict[str, str]]
    checks: list[str]


class Evaluator:
    """Rule evaluator for Phase 0; LLM evaluator hook reserved for L3."""

    def evaluate(
        self,
        *,
        artifact: dict[str, Any],
        success_predicates: list[str] | None = None,
        policy_failures: list[str] | None = None,
        ambiguity_open: bool = False,
        prose_claims_all_agree: bool = False,
    ) -> EvalResult:
        failures: list[dict[str, str]] = []
        checks: list[str] = []

        env_errs = validate_envelope(artifact)
        checks.append("envelope_schema")
        for e in env_errs:
            failures.append({"code": "envelope_invalid", "message": e})

        for f in policy_failures or []:
            failures.append({"code": f, "message": f})
        checks.append("policy_hooks")

        # unresolved pretending decided
        for u in artifact.get("unresolved") or []:
            if u.get("blocking_embed") and artifact.get("artifact_kind") == "decision":
                failures.append(
                    {
                        "code": "unresolved_blocking",
                        "message": u.get("message", "blocking unresolved"),
                    }
                )
        checks.append("unresolved")

        if ambiguity_open and prose_claims_all_agree:
            failures.append(
                {
                    "code": "ambiguity_fake_agree",
                    "message": "消歧未决却写各方同意",
                }
            )
        checks.append("ambiguity")

        for pred in success_predicates or []:
            checks.append(pred)
            # predicates are soft tags in Phase 0; concrete packs assert via schema

        return EvalResult(passed=not failures, failures=failures, checks=checks)
