"""Three-layer trajectory verifier used by Experiment 8-1.

Environment and policy conclusions stay deterministic.  Only the two open-
ended language dimensions are delegated to a quality Judge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Protocol


PASS = "pass"
FAIL = "fail"
UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class DimensionResult:
    dimension: str
    layer: str
    verdict: str
    score: float
    evidence: List[str]
    confidence: float


class QualityJudge(Protocol):
    """Interface for the only layer that may need an LLM."""

    def evaluate(self, trajectory: Dict[str, Any]) -> Iterable[DimensionResult]: ...


def _successful_calls(trajectory: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(trajectory, dict):
        trajectory = {}
    calls = trajectory.get("tool_calls")
    if not isinstance(calls, list):
        calls = []
    return [
        call
        for call in calls
        if isinstance(call, dict)
        and isinstance(call.get("result"), dict)
        and call.get("result", {}).get("success") is True
    ]


def _precedes(call: Dict[str, Any], promise: Dict[str, Any]) -> bool:
    """Return whether both records have numeric turns and the call came first."""
    call_turn = call.get("turn")
    promise_turn = promise.get("turn")
    return (
        isinstance(call_turn, (int, float))
        and not isinstance(call_turn, bool)
        and isinstance(promise_turn, (int, float))
        and not isinstance(promise_turn, bool)
        and call_turn < promise_turn
    )


def _assistant_text(trajectory: Dict[str, Any]) -> str:
    if not isinstance(trajectory, dict):
        trajectory = {}
    messages = trajectory.get("messages")
    if not isinstance(messages, list):
        messages = []
    return "\n".join(
        str(message.get("content") or "")
        for message in messages
        if isinstance(message, dict) and message.get("role") == "assistant"
    )


class ResultVerifier:
    """Checks the final environment state instead of trusting the reply."""

    def evaluate(self, trajectory: Dict[str, Any]) -> List[DimensionResult]:
        if not isinstance(trajectory, dict):
            trajectory = {}
        expected = trajectory.get("expected_outcome")
        if not isinstance(expected, dict):
            expected = {}
        final_state = trajectory.get("final_state")
        if not isinstance(final_state, dict):
            final_state = {}
        mismatches = [
            f"{key}: expected={value!r}, actual={final_state.get(key)!r}"
            for key, value in expected.items()
            if final_state.get(key) != value
        ]
        if mismatches:
            return [DimensionResult(
                "task_resolution", "environment_result", FAIL, 0.0,
                mismatches, 1.0,
            )]
        evidence = [f"final_state.{key}={value!r}" for key, value in expected.items()]
        if not evidence:
            return [DimensionResult(
                "task_resolution", "environment_result", UNCERTAIN, 0.5,
                ["No machine-checkable expected outcome was supplied"], 0.4,
            )]
        return [DimensionResult(
            "task_resolution", "environment_result", PASS, 1.0, evidence, 1.0,
        )]


class ProcessVerifier:
    """Checks policy, privacy, grounded claims and promise/action consistency."""

    def evaluate(self, trajectory: Dict[str, Any]) -> List[DimensionResult]:
        return [
            self._policy(trajectory),
            self._privacy(trajectory),
            self._grounding(trajectory),
            self._promise_action(trajectory),
        ]
    def _policy(self, trajectory: Dict[str, Any]) -> DimensionResult:
        facts = trajectory.get("process_facts")
        if not isinstance(facts, dict):
            facts = {}
        violations = facts.get("policy_violations")
        if not isinstance(violations, list):
            violations = []
        if violations:
            evidence = [
                f"turn {item.get('turn', '?')}: {item.get('rule', 'policy violation')}"
                for item in violations
                if isinstance(item, dict)
            ]
            return DimensionResult("rule_compliance", "process_rules", FAIL, 0.0, evidence, 1.0)
        checked = facts.get("checked_rules")
        if not isinstance(checked, list):
            checked = []
        evidence = [f"checked: {rule}" for rule in checked] or ["No policy violation in action log"]
        return DimensionResult("rule_compliance", "process_rules", PASS, 1.0, evidence, 0.95)

    def _privacy(self, trajectory: Dict[str, Any]) -> DimensionResult:
        reply = _assistant_text(trajectory)
        sensitive = trajectory.get("sensitive_values")
        if not isinstance(sensitive, list):
            sensitive = []
        leaks = [
            item for item in sensitive
            if isinstance(item, dict) and item.get("value") and str(item["value"]) in reply
        ]
        if leaks:
            return DimensionResult(
                "privacy_boundary", "process_rules", FAIL, 0.0,
                [f"assistant exposed {item.get('label', 'sensitive value')}" for item in leaks],
                1.0,
            )
        return DimensionResult(
            "privacy_boundary", "process_rules", PASS, 1.0,
            ["No supplied sensitive value appears in an assistant message"], 0.98,
        )

    def _grounding(self, trajectory: Dict[str, Any]) -> DimensionResult:
        claims = trajectory.get("claims")
        if not isinstance(claims, list):
            claims = []
        unsupported = [
            claim for claim in claims
            if isinstance(claim, dict) and not claim.get("supported_by")
        ]
        if unsupported:
            return DimensionResult(
                "factual_reliability", "process_rules", FAIL, 0.0,
                [f"turn {claim.get('turn', '?')}: unsupported claim: {claim.get('text', '')}" for claim in unsupported],
                0.95,
            )
        evidence = [
            f"turn {claim.get('turn', '?')}: supported by {claim.get('supported_by')}"
            for claim in claims
            if isinstance(claim, dict)
        ] or ["No externally checkable claim was made"]
        return DimensionResult("factual_reliability", "process_rules", PASS, 1.0, evidence, 0.9)

    def _promise_action(self, trajectory: Dict[str, Any]) -> DimensionResult:
        successful = [
            call for call in _successful_calls(trajectory)
            if isinstance(call, dict)
        ]
        promises = trajectory.get("promises")
        if not isinstance(promises, list):
            promises = []
        missing = [
            promise for promise in promises
            if isinstance(promise, dict) and not any(
                call.get("name") == promise.get("required_tool")
                and _precedes(call, promise)
                for call in successful
            )
        ]
        if missing:
            return DimensionResult(
                "promise_action_consistency", "process_rules", FAIL, 0.0,
                [
                    f"turn {promise.get('turn', '?')}: claimed {promise.get('text', '')!r}, "
                    f"but no successful {promise.get('required_tool')} call preceded it"
                    for promise in missing
                ],
                1.0,
            )
        evidence = [
            f"turn {promise.get('turn', '?')}: {promise.get('required_tool')} succeeded"
            for promise in promises
            if isinstance(promise, dict)
        ] or ["No action promise was made"]
        return DimensionResult(
            "promise_action_consistency", "process_rules", PASS, 1.0, evidence, 0.98,
        )


class HeuristicQualityJudge:
    """Deterministic stand-in for an evidence-citing LLM rubric judge.

    ``quality_facts`` represent facts an online LLM judge would infer from the
    dialogue.  Keeping them explicit makes the calibration demo reproducible.
    """

    def evaluate(self, trajectory: Dict[str, Any]) -> List[DimensionResult]:
        if not isinstance(trajectory, dict):
            trajectory = {}
        facts = trajectory.get("quality_facts")
        if not isinstance(facts, dict):
            facts = {}
        expression_issues = facts.get("expression_issues")
        if not isinstance(expression_issues, list):
            expression_issues = []
        if expression_issues:
            expression = DimensionResult(
                "expression_quality", "llm_rubric", FAIL, 0.0,
                [f"turn {issue.get('turn', '?')}: {issue.get('issue', 'quality issue')}" for issue in expression_issues],
                float(facts.get("expression_confidence", 0.85)),
            )
        else:
            expression = DimensionResult(
                "expression_quality", "llm_rubric", PASS, 1.0,
                ["Reply is concise, natural and non-repetitive"],
                float(facts.get("expression_confidence", 0.8)),
            )

        blocked = facts.get("primary_path_blocked", False)
        alternative = facts.get("allowed_alternative_offered", False)
        if blocked and not alternative:
            flexibility = DimensionResult(
                "compliant_flexibility", "llm_rubric", FAIL, 0.0,
                [f"turn {facts.get('decision_turn', '?')}: stopped at refusal although an allowed alternative existed"],
                float(facts.get("flexibility_confidence", 0.85)),
            )
        else:
            note = "Allowed alternative was offered" if alternative else "Primary path was not blocked"
            flexibility = DimensionResult(
                "compliant_flexibility", "llm_rubric", PASS, 1.0, [note],
                float(facts.get("flexibility_confidence", 0.8)),
            )
        return [expression, flexibility]


class TrajectoryVerifier:
    def __init__(self, quality_judge: QualityJudge | None = None, review_confidence: float = 0.75):
        self.result_verifier = ResultVerifier()
        self.process_verifier = ProcessVerifier()
        self.quality_judge = quality_judge or HeuristicQualityJudge()
        self.review_confidence = review_confidence

    def evaluate(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(trajectory, dict):
            trajectory = {}
        dimensions = [
            *self.result_verifier.evaluate(trajectory),
            *self.process_verifier.evaluate(trajectory),
            *self.quality_judge.evaluate(trajectory),
        ]
        scores = [item.score for item in dimensions]
        critical_failures = [
            item.dimension for item in dimensions
            if item.verdict == FAIL and item.dimension in {
                "task_resolution", "rule_compliance", "privacy_boundary",
                "factual_reliability", "promise_action_consistency",
            }
        ]
        high_risk_failures = [
            item.dimension for item in dimensions
            if item.verdict == FAIL and item.dimension in {
                "rule_compliance", "privacy_boundary", "promise_action_consistency",
            }
        ]
        low_confidence = [
            item.dimension for item in dimensions
            if item.confidence < self.review_confidence or item.verdict == UNCERTAIN
        ]
        if high_risk_failures or low_confidence:
            review = {
                "required": True,
                "destination": "human_review",
                "status": "pending",
                "reasons": {
                    "high_risk_failures": high_risk_failures,
                    "low_confidence_or_uncertain": low_confidence,
                },
            }
        else:
            review = {
                "required": False,
                "destination": None,
                "status": "not_required",
                "reasons": {"high_risk_failures": [], "low_confidence_or_uncertain": []},
            }
        return {
            "trajectory_id": trajectory.get("id"),
            "overall_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
            "release_recommendation": "reject" if critical_failures else "review_or_accept",
            "critical_failures": critical_failures,
            "review": review,
            "eligible_as_automatic_learning_signal": not review["required"],
            "dimensions": [asdict(item) for item in dimensions],
        }


def scalar_baseline(report: Dict[str, Any]) -> Dict[str, Any]:
    """Simulates the information loss of returning one overall number."""
    if not isinstance(report, dict):
        report = {}
    return {"trajectory_id": report.get("trajectory_id"), "score": report.get("overall_score")}


def _item_get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def diagnostic_utility(report: Dict[str, Any]) -> float:
    """Fraction of failed dimensions that include actionable evidence."""
    if not isinstance(report, dict):
        report = {}
    dims = report.get("dimensions")
    if not isinstance(dims, list):
        dims = []
    failures = [item for item in dims if _item_get(item, "verdict") == FAIL]
    if not failures:
        return 1.0
    actionable = sum(bool(_item_get(item, "evidence")) for item in failures)
    return actionable / len(failures)
