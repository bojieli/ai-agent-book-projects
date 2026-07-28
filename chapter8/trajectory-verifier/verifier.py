"""Three-layer trajectory verifier used by Experiment 8-1.

The implementation is deliberately offline.  Production systems can replace
``HeuristicQualityJudge`` with an LLM judge, while keeping the same evidence-
bearing report schema and deterministic lower layers.
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
    return [
        call
        for call in trajectory.get("tool_calls", [])
        if call.get("result", {}).get("success") is True
    ]


def _assistant_text(trajectory: Dict[str, Any]) -> str:
    return "\n".join(
        str(message.get("content", ""))
        for message in trajectory.get("messages", [])
        if message.get("role") == "assistant"
    )


class ResultVerifier:
    """Checks the final environment state instead of trusting the reply."""

    def evaluate(self, trajectory: Dict[str, Any]) -> List[DimensionResult]:
        expected = trajectory.get("expected_outcome", {})
        final_state = trajectory.get("final_state", {})
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
        violations = trajectory.get("process_facts", {}).get("policy_violations", [])
        if violations:
            evidence = [
                f"turn {item.get('turn', '?')}: {item.get('rule', 'policy violation')}"
                for item in violations
            ]
            return DimensionResult("rule_compliance", "process_rules", FAIL, 0.0, evidence, 1.0)
        checked = trajectory.get("process_facts", {}).get("checked_rules", [])
        evidence = [f"checked: {rule}" for rule in checked] or ["No policy violation in action log"]
        return DimensionResult("rule_compliance", "process_rules", PASS, 1.0, evidence, 0.95)

    def _privacy(self, trajectory: Dict[str, Any]) -> DimensionResult:
        reply = _assistant_text(trajectory)
        leaks = [
            item for item in trajectory.get("sensitive_values", [])
            if item.get("value") and str(item["value"]) in reply
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
        unsupported = [
            claim for claim in trajectory.get("claims", [])
            if not claim.get("supported_by")
        ]
        if unsupported:
            return DimensionResult(
                "factual_reliability", "process_rules", FAIL, 0.0,
                [f"turn {claim.get('turn', '?')}: unsupported claim: {claim.get('text', '')}" for claim in unsupported],
                0.95,
            )
        claims = trajectory.get("claims", [])
        evidence = [
            f"turn {claim.get('turn', '?')}: supported by {claim.get('supported_by')}"
            for claim in claims
        ] or ["No externally checkable claim was made"]
        return DimensionResult("factual_reliability", "process_rules", PASS, 1.0, evidence, 0.9)

    def _promise_action(self, trajectory: Dict[str, Any]) -> DimensionResult:
        successful = {
            call.get("name") for call in _successful_calls(trajectory)
        }
        missing = [
            promise for promise in trajectory.get("promises", [])
            if promise.get("required_tool") not in successful
        ]
        if missing:
            return DimensionResult(
                "promise_action_consistency", "process_rules", FAIL, 0.0,
                [
                    f"turn {promise.get('turn', '?')}: claimed {promise.get('text', '')!r}, "
                    f"but successful {promise.get('required_tool')} call is absent"
                    for promise in missing
                ],
                1.0,
            )
        evidence = [
            f"turn {promise.get('turn', '?')}: {promise.get('required_tool')} succeeded"
            for promise in trajectory.get("promises", [])
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
        facts = trajectory.get("quality_facts", {})
        expression_issues = facts.get("expression_issues", [])
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
    def __init__(self, quality_judge: QualityJudge | None = None):
        self.result_verifier = ResultVerifier()
        self.process_verifier = ProcessVerifier()
        self.quality_judge = quality_judge or HeuristicQualityJudge()

    def evaluate(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
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
        return {
            "trajectory_id": trajectory.get("id"),
            "overall_score": round(sum(scores) / len(scores), 3),
            "release_recommendation": "reject" if critical_failures else "review_or_accept",
            "critical_failures": critical_failures,
            "dimensions": [asdict(item) for item in dimensions],
        }


def scalar_baseline(report: Dict[str, Any]) -> Dict[str, Any]:
    """Simulates the information loss of returning one overall number."""
    return {"trajectory_id": report["trajectory_id"], "score": report["overall_score"]}


def diagnostic_utility(report: Dict[str, Any]) -> float:
    """Fraction of failed dimensions that include actionable evidence."""
    failures = [item for item in report.get("dimensions", []) if item.get("verdict") == FAIL]
    if not failures:
        return 1.0
    actionable = sum(bool(item.get("evidence")) for item in failures)
    return actionable / len(failures)
