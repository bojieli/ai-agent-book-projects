"""Trajectory consistency checker for chapter 8.

Detects ungrounded claims, contradictions, hallucinated tool results, and
unsupported conclusions in agent trajectories.  Purely heuristic and
deterministic: no network calls, no LLM dependency.

A trajectory is a list of step dictionaries.  Each step may contain:

    step_id              int   -- ordinal identifier (defaults to list index)
    action               str   -- what the agent did in this step
    claims               list[str] -- assertions made by the agent
    tool_result          Any   -- the actual result returned by a tool
    claimed_tool_result  Any   -- what the agent says the tool returned
    observation          str   -- a textual observation the agent received
    final_answer         str   -- the agent's final conclusion (last step)

The checker scores four dimensions:

    claim_grounding           -- fraction of claims backed by prior evidence
    contradiction_freedom     -- 1 minus the contradiction rate
    evidence_chain_integrity  -- fraction of tool results reported faithfully
    conclusion_support        -- whether the final answer follows from evidence
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VIOLATION_UNGROUNDED = "ungrounded_claim"
VIOLATION_CONTRADICTION = "contradiction"
VIOLATION_HALLUCINATED = "hallucinated_result"
VIOLATION_UNSUPPORTED = "unsupported_conclusion"

DIMENSIONS = (
    "claim_grounding",
    "contradiction_freedom",
    "evidence_chain_integrity",
    "conclusion_support",
)

# Tokens that flip a claim's polarity.
_NEGATION_TOKENS = frozenset({
    "not", "no", "never", "none", "nobody", "nothing", "neither",
    "nor", "cannot", "cant", "wont", "dont", "doesnt", "didnt",
    "isnt", "wasnt", "arent", "werent", "hasnt", "havent", "hadnt",
    "wouldnt", "couldnt", "shouldnt",
})

# Stopwords excluded when computing token overlap for grounding.
_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "with", "about", "as",
    "into", "from", "that", "this", "these", "those", "it", "its",
    "has", "have", "had", "do", "does", "did", "will", "would", "can",
    "could", "should", "shall", "may", "might", "must", "and", "or",
    "but", "if", "then", "so", "than", "too", "very", "just", "also",
    "i", "we", "you", "they", "he", "she", "my", "our", "your",
    "been", "being", "am",
})

# Minimum significant-token overlap ratio for a claim to be considered grounded.
_GROUNDING_THRESHOLD = 0.5

# Minimum Jaccard similarity between claim cores for a contradiction check.
_CONTRADICTION_SIMILARITY = 0.5


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ConsistencyViolation:
    """A single consistency violation found in a trajectory step."""

    step_id: int
    violation_type: str  # ungrounded_claim, contradiction, hallucinated_result, unsupported_conclusion
    description: str
    evidence: dict[str, Any]


@dataclass
class ConsistencyReport:
    """Structured report returned by ``check_trajectory``."""

    total_steps: int
    total_claims: int
    violations: list[ConsistencyViolation]
    dimension_scores: dict[str, float]
    overall_consistency_score: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens of length > 1."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1]


def _significant_tokens(text: str) -> set[str]:
    """Tokens that carry semantic weight (stopwords and negations removed)."""
    return {
        t
        for t in _tokenize(text)
        if t not in _STOPWORDS and t not in _NEGATION_TOKENS
    }


def _serialize_evidence(value: Any) -> str:
    """Convert a tool result or observation into a comparable string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _step_id(step: dict[str, Any], idx: int) -> int:
    sid = step.get("step_id", idx)
    if isinstance(sid, bool) or not isinstance(sid, int):
        return idx
    return sid


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class TrajectoryConsistencyChecker:
    """Check agent trajectories for internal consistency."""

    def __init__(self) -> None:
        self.grounding_threshold: float = _GROUNDING_THRESHOLD
        self.contradiction_similarity: float = _CONTRADICTION_SIMILARITY

    # -- public API ---------------------------------------------------------

    def check_trajectory(self, trajectory: list[dict[str, Any]]) -> ConsistencyReport:
        """Run all consistency checks and return a structured report."""
        if not trajectory:
            return ConsistencyReport(
                total_steps=0,
                total_claims=0,
                violations=[],
                dimension_scores={d: 1.0 for d in DIMENSIONS},
                overall_consistency_score=1.0,
            )

        violations: list[ConsistencyViolation] = []
        total_claims = 0
        grounded_claims = 0

        all_claims: list[tuple[int, str]] = []
        evidence_strings: list[str] = []

        steps_with_tool_results = 0
        steps_with_valid_results = 0

        final_answer: str | None = None
        final_step_id: int | None = None

        for idx, step in enumerate(trajectory):
            sid = _step_id(step, idx)

            # --- accumulate evidence from this step ------------------------
            observation = step.get("observation")
            if isinstance(observation, str) and observation.strip():
                evidence_strings.append(observation)

            tool_result = step.get("tool_result")
            if tool_result is not None:
                serialized = _serialize_evidence(tool_result)
                if serialized:
                    evidence_strings.append(serialized)
                steps_with_tool_results += 1

                claimed = step.get("claimed_tool_result")
                if claimed is not None:
                    if tool_result != claimed:
                        violations.append(ConsistencyViolation(
                            step_id=sid,
                            violation_type=VIOLATION_HALLUCINATED,
                            description=(
                                f"Step {sid} claims a tool result that differs "
                                f"from the actual result"
                            ),
                            evidence={
                                "actual_result": tool_result,
                                "claimed_result": claimed,
                            },
                        ))
                    else:
                        steps_with_valid_results += 1
                else:
                    steps_with_valid_results += 1

            # --- check claim grounding -------------------------------------
            claims = step.get("claims", [])
            if not isinstance(claims, list):
                claims = []
            for claim in claims:
                if not isinstance(claim, str) or not claim.strip():
                    continue
                total_claims += 1
                all_claims.append((sid, claim))
                if self.check_claim_grounded(claim, list(evidence_strings)):
                    grounded_claims += 1
                else:
                    violations.append(ConsistencyViolation(
                        step_id=sid,
                        violation_type=VIOLATION_UNGROUNDED,
                        description=(
                            f"Claim at step {sid} is not grounded in prior "
                            f"evidence: {claim}"
                        ),
                        evidence={
                            "claim": claim,
                            "available_evidence": list(evidence_strings),
                        },
                    ))

            # --- track final answer ---------------------------------------
            fa = step.get("final_answer")
            if isinstance(fa, str) and fa.strip():
                final_answer = fa
                final_step_id = sid

        # --- contradictions ------------------------------------------------
        contradiction_violations = self.find_contradictions(all_claims)
        violations.extend(contradiction_violations)

        # --- unsupported conclusion ---------------------------------------
        conclusion_supported = True
        if final_answer is not None and final_step_id is not None:
            conclusion_evidence = evidence_strings + [text for _, text in all_claims]
            if not self.check_claim_grounded(final_answer, conclusion_evidence):
                conclusion_supported = False
                violations.append(ConsistencyViolation(
                    step_id=final_step_id,
                    violation_type=VIOLATION_UNSUPPORTED,
                    description=(
                        f"Final answer at step {final_step_id} is not supported "
                        f"by the evidence chain"
                    ),
                    evidence={
                        "final_answer": final_answer,
                        "available_evidence": conclusion_evidence,
                    },
                ))

        # --- dimension scores ---------------------------------------------
        claim_grounding = grounded_claims / total_claims if total_claims else 1.0
        contradiction_freedom = (
            max(0.0, 1.0 - len(contradiction_violations) / total_claims)
            if total_claims
            else 1.0
        )
        evidence_chain_integrity = (
            steps_with_valid_results / steps_with_tool_results
            if steps_with_tool_results
            else 1.0
        )
        conclusion_support = 1.0 if conclusion_supported else 0.0

        dimension_scores = {
            "claim_grounding": round(claim_grounding, 4),
            "contradiction_freedom": round(contradiction_freedom, 4),
            "evidence_chain_integrity": round(evidence_chain_integrity, 4),
            "conclusion_support": round(conclusion_support, 4),
        }
        overall = round(sum(dimension_scores.values()) / len(dimension_scores), 4)

        return ConsistencyReport(
            total_steps=len(trajectory),
            total_claims=total_claims,
            violations=violations,
            dimension_scores=dimension_scores,
            overall_consistency_score=overall,
        )

    def check_claim_grounded(self, claim: str, available_evidence: list[str]) -> bool:
        """Return ``True`` if *claim* is backed by any evidence string."""
        claim_tokens = _significant_tokens(claim)
        if not claim_tokens:
            return True
        for evidence in available_evidence:
            ev_tokens = _significant_tokens(evidence)
            if not ev_tokens:
                continue
            overlap = len(claim_tokens & ev_tokens) / len(claim_tokens)
            if overlap >= self.grounding_threshold:
                return True
        return False

    def find_contradictions(
        self, claims: list[tuple[int, str]]
    ) -> list[ConsistencyViolation]:
        """Detect contradictions between claims across steps.

        Two contradiction patterns are recognised:

        * **polarity** -- one claim affirms X, a later claim denies X.
        * **numeric** -- two claims share the same subject but cite
          disjoint numeric values.
        """
        violations: list[ConsistencyViolation] = []
        parsed: list[tuple[int, str, bool, set[str], set[str]]] = []

        for step_id, text in claims:
            tokens = _tokenize(text)
            negated = any(t in _NEGATION_TOKENS for t in tokens)
            core = _significant_tokens(text)
            numbers = set(re.findall(r"\d+", text.lower()))
            parsed.append((step_id, text, negated, core, numbers))

        for i in range(len(parsed)):
            sid_a, text_a, neg_a, core_a, nums_a = parsed[i]
            if not core_a:
                continue
            for j in range(i + 1, len(parsed)):
                sid_b, text_b, neg_b, core_b, nums_b = parsed[j]
                if sid_b <= sid_a:
                    continue
                if not core_b:
                    continue
                jaccard = len(core_a & core_b) / len(core_a | core_b)
                if jaccard < self.contradiction_similarity:
                    continue

                if neg_a != neg_b:
                    violations.append(ConsistencyViolation(
                        step_id=sid_b,
                        violation_type=VIOLATION_CONTRADICTION,
                        description=(
                            f"Claim at step {sid_b} contradicts claim at "
                            f"step {sid_a}"
                        ),
                        evidence={
                            "earlier_step": sid_a,
                            "earlier_claim": text_a,
                            "later_step": sid_b,
                            "later_claim": text_b,
                            "contradiction_type": "polarity",
                        },
                    ))
                elif nums_a and nums_b and nums_a.isdisjoint(nums_b):
                    violations.append(ConsistencyViolation(
                        step_id=sid_b,
                        violation_type=VIOLATION_CONTRADICTION,
                        description=(
                            f"Claim at step {sid_b} contradicts numeric value "
                            f"in claim at step {sid_a}"
                        ),
                        evidence={
                            "earlier_step": sid_a,
                            "earlier_claim": text_a,
                            "later_step": sid_b,
                            "later_claim": text_b,
                            "contradiction_type": "numeric",
                            "earlier_numbers": sorted(nums_a),
                            "later_numbers": sorted(nums_b),
                        },
                    ))
        return violations
