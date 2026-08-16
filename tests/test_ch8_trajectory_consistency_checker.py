import os
import sys

sys.path.insert(0, os.path.abspath("chapter9/trajectory-verifier"))

import pytest

from consistency_checker import (
    ConsistencyReport,
    ConsistencyViolation,
    TrajectoryConsistencyChecker,
    VIOLATION_CONTRADICTION,
    VIOLATION_HALLUCINATED,
    VIOLATION_UNGROUNDED,
    VIOLATION_UNSUPPORTED,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def checker() -> TrajectoryConsistencyChecker:
    return TrajectoryConsistencyChecker()


def _violation_types(report: ConsistencyReport) -> list[str]:
    return [v.violation_type for v in report.violations]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGroundedClaims:
    def test_grounded_claims_pass(self, checker):
        """A claim whose tokens appear in a prior tool result is grounded."""
        trajectory = [
            {
                "step_id": 0,
                "action": "refund_order",
                "tool_result": {"success": True, "amount": 480},
            },
            {
                "step_id": 1,
                "action": "respond",
                "claims": ["refund amount 480"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert VIOLATION_UNGROUNDED not in _violation_types(report)
        assert report.total_claims == 1
        assert report.dimension_scores["claim_grounding"] == 1.0

    def test_observation_grounds_claim(self, checker):
        """An observation string can ground a subsequent claim."""
        trajectory = [
            {
                "step_id": 0,
                "action": "observe",
                "observation": "order O-100 is refundable",
            },
            {
                "step_id": 1,
                "action": "respond",
                "claims": ["order O-100 is refundable"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert VIOLATION_UNGROUNDED not in _violation_types(report)


class TestUngroundedClaims:
    def test_ungrounded_claims_flagged(self, checker):
        """A claim with no supporting evidence is flagged as ungrounded."""
        trajectory = [
            {
                "step_id": 0,
                "action": "respond",
                "claims": ["the customer is very happy and satisfied"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        types = _violation_types(report)
        assert VIOLATION_UNGROUNDED in types
        ungrounded = [v for v in report.violations if v.violation_type == VIOLATION_UNGROUNDED]
        assert len(ungrounded) == 1
        assert ungrounded[0].step_id == 0
        assert "customer" in ungrounded[0].evidence["claim"]
        assert report.dimension_scores["claim_grounding"] == 0.0


class TestContradictions:
    def test_polarity_contradiction_detected(self, checker):
        """Claim X then claim not-X is a polarity contradiction."""
        trajectory = [
            {"step_id": 0, "action": "reason", "claims": ["order is refundable"]},
            {"step_id": 1, "action": "reason", "claims": ["order is not refundable"]},
        ]
        report = checker.check_trajectory(trajectory)
        types = _violation_types(report)
        assert VIOLATION_CONTRADICTION in types
        contra = [v for v in report.violations if v.violation_type == VIOLATION_CONTRADICTION]
        assert len(contra) == 1
        assert contra[0].step_id == 1
        assert contra[0].evidence["contradiction_type"] == "polarity"
        assert contra[0].evidence["earlier_step"] == 0

    def test_numeric_contradiction_detected(self, checker):
        """Same subject with different numbers is a numeric contradiction."""
        trajectory = [
            {"step_id": 0, "action": "reason", "claims": ["refund amount is 480"]},
            {"step_id": 1, "action": "reason", "claims": ["refund amount is 500"]},
        ]
        report = checker.check_trajectory(trajectory)
        types = _violation_types(report)
        assert VIOLATION_CONTRADICTION in types
        contra = [v for v in report.violations if v.violation_type == VIOLATION_CONTRADICTION]
        assert contra[0].evidence["contradiction_type"] == "numeric"
        assert "480" in contra[0].evidence["earlier_numbers"]
        assert "500" in contra[0].evidence["later_numbers"]

    def test_find_contradictions_directly(self, checker):
        """find_contradictions works standalone with (step_id, text) tuples."""
        claims = [
            (0, "the ticket is refundable"),
            (2, "the ticket is not refundable"),
        ]
        violations = checker.find_contradictions(claims)
        assert len(violations) == 1
        assert violations[0].violation_type == VIOLATION_CONTRADICTION
        assert violations[0].step_id == 2

    def test_no_contradiction_for_unrelated_claims(self, checker):
        """Claims about different subjects do not trigger contradictions."""
        claims = [
            (0, "order is refundable"),
            (1, "customer is happy"),
        ]
        violations = checker.find_contradictions(claims)
        assert violations == []


class TestHallucinatedResults:
    def test_hallucinated_results_detected(self, checker):
        """claimed_tool_result differing from tool_result is hallucinated."""
        trajectory = [
            {
                "step_id": 0,
                "action": "refund_order",
                "tool_result": {"success": False, "amount": 0},
                "claimed_tool_result": {"success": True, "amount": 480},
            },
        ]
        report = checker.check_trajectory(trajectory)
        types = _violation_types(report)
        assert VIOLATION_HALLUCINATED in types
        hallucinated = [v for v in report.violations if v.violation_type == VIOLATION_HALLUCINATED]
        assert len(hallucinated) == 1
        assert hallucinated[0].evidence["actual_result"] == {"success": False, "amount": 0}
        assert hallucinated[0].evidence["claimed_result"] == {"success": True, "amount": 480}
        assert report.dimension_scores["evidence_chain_integrity"] == 0.0

    def test_matching_tool_result_not_flagged(self, checker):
        """When claimed matches actual, no hallucination violation."""
        trajectory = [
            {
                "step_id": 0,
                "action": "query",
                "tool_result": {"status": "ok"},
                "claimed_tool_result": {"status": "ok"},
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert VIOLATION_HALLUCINATED not in _violation_types(report)
        assert report.dimension_scores["evidence_chain_integrity"] == 1.0


class TestUnsupportedConclusions:
    def test_unsupported_conclusion_flagged(self, checker):
        """A final answer with no evidence support is flagged."""
        trajectory = [
            {
                "step_id": 0,
                "action": "query",
                "tool_result": {"status": "ok"},
            },
            {
                "step_id": 1,
                "action": "answer",
                "final_answer": "the moon is made of cheese and pickles",
            },
        ]
        report = checker.check_trajectory(trajectory)
        types = _violation_types(report)
        assert VIOLATION_UNSUPPORTED in types
        unsupported = [v for v in report.violations if v.violation_type == VIOLATION_UNSUPPORTED]
        assert unsupported[0].step_id == 1
        assert report.dimension_scores["conclusion_support"] == 0.0

    def test_supported_conclusion_passes(self, checker):
        """A final answer grounded in the evidence chain passes."""
        trajectory = [
            {
                "step_id": 0,
                "action": "refund_order",
                "tool_result": {"success": True, "amount": 480},
                "claims": ["refund amount 480"],
            },
            {
                "step_id": 1,
                "action": "answer",
                "final_answer": "refund amount 480 processed",
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert VIOLATION_UNSUPPORTED not in _violation_types(report)
        assert report.dimension_scores["conclusion_support"] == 1.0


class TestCleanAndEdgeCases:
    def test_clean_trajectory_passes(self, checker):
        """A well-formed trajectory produces no violations and a perfect score."""
        trajectory = [
            {
                "step_id": 0,
                "action": "search_orders",
                "tool_result": {"order_id": "O-100", "refundable": True},
                "observation": "order O-100 is refundable",
            },
            {
                "step_id": 1,
                "action": "refund_order",
                "tool_result": {"success": True, "amount": 480},
                "claimed_tool_result": {"success": True, "amount": 480},
                "claims": ["refund amount 480", "order O-100 refundable"],
            },
            {
                "step_id": 2,
                "action": "answer",
                "final_answer": "refund amount 480 for order O-100",
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert report.violations == []
        assert report.total_steps == 3
        assert report.total_claims == 2
        assert report.overall_consistency_score == 1.0
        for dim in ("claim_grounding", "contradiction_freedom",
                     "evidence_chain_integrity", "conclusion_support"):
            assert report.dimension_scores[dim] == 1.0

    def test_empty_trajectory(self, checker):
        """An empty trajectory returns zero counts and perfect default scores."""
        report = checker.check_trajectory([])
        assert report.total_steps == 0
        assert report.total_claims == 0
        assert report.violations == []
        assert report.overall_consistency_score == 1.0
        for dim in ("claim_grounding", "contradiction_freedom",
                     "evidence_chain_integrity", "conclusion_support"):
            assert report.dimension_scores[dim] == 1.0

    def test_single_step_trajectory(self, checker):
        """A single step with a grounded claim and no final answer works."""
        trajectory = [
            {
                "step_id": 0,
                "action": "query",
                "tool_result": {"status": "active"},
                "claims": ["status active"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert report.total_steps == 1
        assert report.total_claims == 1
        assert VIOLATION_UNGROUNDED not in _violation_types(report)
        assert report.dimension_scores["claim_grounding"] == 1.0

    def test_single_step_no_evidence(self, checker):
        """A single step with an ungrounded claim is flagged."""
        trajectory = [
            {
                "step_id": 0,
                "action": "respond",
                "claims": ["everything is perfectly fine and dandy"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert VIOLATION_UNGROUNDED in _violation_types(report)
        assert report.dimension_scores["claim_grounding"] == 0.0


class TestMultiViolation:
    def test_multi_violation_trajectory(self, checker):
        """A trajectory with several violation types detects all of them."""
        trajectory = [
            {
                "step_id": 0,
                "action": "query",
                "tool_result": {"success": False, "amount": 0},
                "claimed_tool_result": {"success": True, "amount": 480},
            },
            {
                "step_id": 1,
                "action": "reason",
                "claims": ["the weather is sunny and bright"],
            },
            {
                "step_id": 2,
                "action": "reason",
                "claims": ["refund is possible"],
            },
            {
                "step_id": 3,
                "action": "reason",
                "claims": ["refund is not possible"],
            },
            {
                "step_id": 4,
                "action": "answer",
                "final_answer": "aliens built the pyramids on mars",
            },
        ]
        report = checker.check_trajectory(trajectory)
        types = _violation_types(report)
        assert VIOLATION_HALLUCINATED in types
        assert VIOLATION_UNGROUNDED in types
        assert VIOLATION_CONTRADICTION in types
        assert VIOLATION_UNSUPPORTED in types
        assert len(report.violations) >= 4
        assert report.overall_consistency_score < 0.5


class TestDimensionScoring:
    def test_dimension_scores_partial_grounding(self, checker):
        """claim_grounding reflects the fraction of grounded claims."""
        trajectory = [
            {
                "step_id": 0,
                "action": "query",
                "tool_result": {"amount": 480},
            },
            {
                "step_id": 1,
                "action": "respond",
                "claims": ["amount 480", "weather is sunny"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        assert report.total_claims == 2
        assert report.dimension_scores["claim_grounding"] == 0.5

    def test_dimension_scores_all_four_present(self, checker):
        """Every expected dimension key is present in the report."""
        trajectory = [
            {"step_id": 0, "action": "noop", "claims": ["something random"]},
        ]
        report = checker.check_trajectory(trajectory)
        expected = {"claim_grounding", "contradiction_freedom",
                    "evidence_chain_integrity", "conclusion_support"}
        assert set(report.dimension_scores.keys()) == expected

    def test_overall_score_is_mean_of_dimensions(self, checker):
        """overall_consistency_score equals the mean of the four dimensions."""
        trajectory = [
            {
                "step_id": 0,
                "action": "query",
                "tool_result": {"amount": 480},
            },
            {
                "step_id": 1,
                "action": "respond",
                "claims": ["amount 480"],
            },
        ]
        report = checker.check_trajectory(trajectory)
        dims = list(report.dimension_scores.values())
        expected = round(sum(dims) / len(dims), 4)
        assert report.overall_consistency_score == expected


class TestCheckClaimGroundedDirect:
    def test_check_claim_grounded_returns_true(self, checker):
        """Direct call: overlapping tokens ground the claim."""
        assert checker.check_claim_grounded(
            "refund amount 480",
            ['{"amount": 480, "success": true}'],
        ) is True

    def test_check_claim_grounded_returns_false(self, checker):
        """Direct call: no overlap means ungrounded."""
        assert checker.check_claim_grounded(
            "the moon is cheese",
            ['{"amount": 480}'],
        ) is False

    def test_check_claim_grounded_empty_evidence(self, checker):
        """Direct call: no evidence means ungrounded (unless claim is empty)."""
        assert checker.check_claim_grounded("some claim here", []) is False
        assert checker.check_claim_grounded("", []) is True
