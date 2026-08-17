"""
SFT training-data quality auditor (chapter 8 CoT distillation).

Every chapter 8 SFT experiment (8-8, 8-9, 8-17, 8-18, 8-19) consumes JSONL
training data: one JSON object per line, each carrying a ``messages`` array of
``{"role", "content"}`` pairs. ``generate_data.py`` synthesizes that data and
``analyze_data.py`` reports coarse statistics, but neither flags the quality
issues that corrupt a fine-tune *before* training starts. This module fills
that gap.

:class:`SFTDataQualityAuditor` walks a dataset (a file or an in-memory list of
parsed lines) and produces an :class:`AuditReport` of :class:`QualityIssue`
records covering six concerns:

1. **Format consistency** — every line has a ``messages`` list whose entries
   carry ``role`` and non-empty ``content`` and whose roles alternate
   ``user``/``assistant``.
2. **Token-length distribution** — per-example approximate token count (word
   count) with outliers flagged below ``min_length`` or above ``max_length``.
3. **Duplicate detection** — exact duplicate examples and near-duplicates
   (same user message, different assistant response = potential label noise).
4. **Label noise** — assistant responses containing placeholder markers
   (``TODO``, ``FIXME``, ``[insert``, ``[TBD``) or self-contradictory
   affirm/deny pairs.
5. **Boundary coverage** — the dataset should span diverse input lengths, not
   cluster around a single bucket.
6. **Tokenizer compatibility** — characters that tokenize inconsistently
   across tokenizers (curly quotes, zero-width spaces, BOM markers).

The auditor is fully offline: it never loads a model or touches the network.
"""
from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
# Data shapes
# --------------------------------------------------------------------------- #
@dataclass
class QualityIssue:
    """A single quality problem found in one example."""

    line_number: int
    issue_type: str  # format_error, length_outlier, duplicate, label_noise, boundary_gap, tokenizer_risk
    severity: str  # warning, error
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditReport:
    """Aggregate quality report for a whole dataset."""

    total_examples: int = 0
    total_issues: int = 0
    issues_by_severity: dict[str, int] = field(default_factory=dict)
    issues_by_type: dict[str, int] = field(default_factory=dict)
    length_stats: dict[str, float] = field(default_factory=dict)
    duplicate_count: int = 0
    near_duplicate_count: int = 0
    issues: list[QualityIssue] = field(default_factory=list)
    overall_quality_score: float = 0.0


# --------------------------------------------------------------------------- #
# Auditor
# --------------------------------------------------------------------------- #
_PLACEHOLDER_RE = re.compile(
    r"\b(TODO|FIXME)\b|\[insert|\[TBD", re.IGNORECASE
)
# Self-contradiction: an affirmative followed later by its negation (or vice
# versa) inside the same assistant turn — "Yes ... No" / "True ... False".
_CONTRADICTION_RE = re.compile(
    r"\b(yes|true|correct|right)\b.*\b(no|false|wrong|incorrect)\b"
    r"|\b(no|false|wrong|incorrect)\b.*\b(yes|true|correct|right)\b",
    re.IGNORECASE,
)
# Tokenizer-hostile characters: curly quotes, zero-width spaces, BOM.
_SPECIAL_CHARS = {
    "\u2018": "left single curly quote",
    "\u2019": "right single curly quote",
    "\u201c": "left double curly quote",
    "\u201d": "right double curly quote",
    "\u200b": "zero-width space",
    "\ufeff": "BOM / zero-width no-break space",
    "\u200c": "zero-width non-joiner",
    "\u200d": "zero-width joiner",
}

_VALID_ROLES = {"user", "assistant", "system", "tool"}
# Number of length buckets used for boundary-coverage analysis.
_LENGTH_BUCKETS = 5


class SFTDataQualityAuditor:
    """Audit SFT JSONL training data for common quality issues.

    Parameters
    ----------
    max_length:
        Approximate token (word) count above which an example is flagged as a
        length outlier (may truncate at training time).
    min_length:
        Approximate token (word) count below which an example is flagged as a
        length outlier (likely uninformative).
    """

    def __init__(self, max_length: int = 4096, min_length: int = 10) -> None:
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        if min_length < 0:
            raise ValueError("min_length must be non-negative")
        if min_length >= max_length:
            raise ValueError("min_length must be less than max_length")
        self.max_length = max_length
        self.min_length = min_length

    # ------------------------------------------------------------------ #
    # Public entry points
    # ------------------------------------------------------------------ #
    def audit_file(self, path: str | Path) -> AuditReport:
        """Read a JSONL file and audit every non-blank line."""
        p = Path(path)
        lines: list[dict[str, Any]] = []
        with p.open(encoding="utf-8") as f:
            for raw in f:
                stripped = raw.strip()
                if not stripped:
                    continue
                lines.append(json.loads(stripped))
        return self.audit_lines(lines)

    def audit_lines(self, lines: list[dict[str, Any]]) -> AuditReport:
        """Audit an in-memory list of parsed JSONL examples."""
        examples: list[dict[str, Any]] = list(lines)
        total = len(examples)

        issues: list[QualityIssue] = []
        # Per-example approximate token counts (word counts). Format-invalid
        # examples contribute 0 so they don't skew the distribution.
        token_counts: list[int] = []

        for idx, example in enumerate(examples):
            line_number = idx + 1
            fmt_issues = self.check_format(example)
            for issue in fmt_issues:
                issue.line_number = line_number
            issues.extend(fmt_issues)

            token_counts.append(self._example_token_count(example))

            issues.extend(self.check_length(example, line_number))
            issues.extend(self.check_label_noise(example, line_number))
            issues.extend(self.check_tokenizer_compatibility(example, line_number))

        issues.extend(self.find_duplicates(examples))
        issues.extend(self._find_boundary_gaps(token_counts))

        # Deduplicate duplicate/near-duplicate counts from the issue list.
        duplicate_count = sum(
            1 for i in issues if i.issue_type == "duplicate" and i.evidence.get("kind") == "exact"
        )
        near_duplicate_count = sum(
            1 for i in issues if i.issue_type == "duplicate" and i.evidence.get("kind") == "near"
        )

        length_stats = self._length_stats(token_counts)
        issues_by_severity = _count_by(issues, lambda i: i.severity)
        issues_by_type = _count_by(issues, lambda i: i.issue_type)
        score = self._quality_score(total, issues)

        return AuditReport(
            total_examples=total,
            total_issues=len(issues),
            issues_by_severity=issues_by_severity,
            issues_by_type=issues_by_type,
            length_stats=length_stats,
            duplicate_count=duplicate_count,
            near_duplicate_count=near_duplicate_count,
            issues=issues,
            overall_quality_score=score,
        )

    # ------------------------------------------------------------------ #
    # Individual checks
    # ------------------------------------------------------------------ #
    def check_format(self, example: dict[str, Any]) -> list[QualityIssue]:
        """Validate the structural shape of one example.

        Issues are returned with ``line_number=0``; the caller (``audit_lines``)
        stamps the real line number. When called directly the caller is
        responsible for setting it.
        """
        issues: list[QualityIssue] = []

        messages = example.get("messages")
        if not isinstance(messages, list):
            issues.append(
                QualityIssue(
                    line_number=0,
                    issue_type="format_error",
                    severity="error",
                    description="'messages' is missing or not a list",
                    evidence={"messages_type": type(messages).__name__},
                )
            )
            return issues

        if len(messages) == 0:
            issues.append(
                QualityIssue(
                    line_number=0,
                    issue_type="format_error",
                    severity="error",
                    description="'messages' is an empty list",
                    evidence={},
                )
            )
            return issues

        expected_role = "user"
        for pos, msg in enumerate(messages):
            if not isinstance(msg, dict):
                issues.append(
                    QualityIssue(
                        line_number=0,
                        issue_type="format_error",
                        severity="error",
                        description=f"message[{pos}] is not a dict",
                        evidence={"position": pos, "type": type(msg).__name__},
                    )
                )
                continue

            role = msg.get("role")
            content = msg.get("content")

            if not isinstance(role, str) or not role:
                issues.append(
                    QualityIssue(
                        line_number=0,
                        issue_type="format_error",
                        severity="error",
                        description=f"message[{pos}] missing or invalid 'role'",
                        evidence={"position": pos, "role": role},
                    )
                )
            elif role not in _VALID_ROLES:
                issues.append(
                    QualityIssue(
                        line_number=0,
                        issue_type="format_error",
                        severity="error",
                        description=f"message[{pos}] has unknown role {role!r}",
                        evidence={"position": pos, "role": role},
                    )
                )

            if content is None:
                issues.append(
                    QualityIssue(
                        line_number=0,
                        issue_type="format_error",
                        severity="error",
                        description=f"message[{pos}] missing 'content'",
                        evidence={"position": pos},
                    )
                )
            elif not isinstance(content, str):
                issues.append(
                    QualityIssue(
                        line_number=0,
                        issue_type="format_error",
                        severity="error",
                        description=f"message[{pos}] 'content' is not a string",
                        evidence={"position": pos, "content_type": type(content).__name__},
                    )
                )
            elif not content.strip():
                issues.append(
                    QualityIssue(
                        line_number=0,
                        issue_type="format_error",
                        severity="error",
                        description=f"message[{pos}] has empty 'content'",
                        evidence={"position": pos},
                    )
                )

            # Role alternation: the first message should be 'user', then
            # 'assistant', then 'user', etc. System/tool messages are allowed
            # but do not reset the expected alternation.
            if isinstance(role, str) and role in {"user", "assistant"}:
                if role != expected_role:
                    issues.append(
                        QualityIssue(
                            line_number=0,
                            issue_type="format_error",
                            severity="error",
                            description=(
                                f"message[{pos}] role {role!r} breaks expected "
                                f"alternation (expected {expected_role!r})"
                            ),
                            evidence={
                                "position": pos,
                                "role": role,
                                "expected": expected_role,
                            },
                        )
                    )
                expected_role = "assistant" if expected_role == "user" else "user"

        return issues

    def check_length(self, example: dict[str, Any], line_number: int) -> list[QualityIssue]:
        """Flag examples whose approximate token count is an outlier."""
        issues: list[QualityIssue] = []
        count = self._example_token_count(example)
        if count == 0:
            # Format errors already cover empty/missing content.
            return issues

        if count < self.min_length:
            issues.append(
                QualityIssue(
                    line_number=line_number,
                    issue_type="length_outlier",
                    severity="warning",
                    description=(
                        f"example is very short (~{count} tokens, below "
                        f"min_length={self.min_length}); likely uninformative"
                    ),
                    evidence={"token_count": count, "threshold": "min", "limit": self.min_length},
                )
            )
        elif count > self.max_length:
            issues.append(
                QualityIssue(
                    line_number=line_number,
                    issue_type="length_outlier",
                    severity="warning",
                    description=(
                        f"example is very long (~{count} tokens, above "
                        f"max_length={self.max_length}); may truncate at training time"
                    ),
                    evidence={"token_count": count, "threshold": "max", "limit": self.max_length},
                )
            )
        return issues

    def find_duplicates(self, examples: list[dict[str, Any]]) -> list[QualityIssue]:
        """Detect exact duplicates and near-duplicates (same user, different assistant)."""
        issues: list[QualityIssue] = []

        # Exact duplicates: identical serialised form seen more than once.
        seen: dict[str, list[int]] = {}
        for idx, example in enumerate(examples):
            key = json.dumps(example, sort_keys=True, ensure_ascii=False)
            seen.setdefault(key, []).append(idx + 1)
        for key, line_numbers in seen.items():
            if len(line_numbers) > 1:
                for ln in line_numbers[1:]:  # keep the first occurrence clean
                    issues.append(
                        QualityIssue(
                            line_number=ln,
                            issue_type="duplicate",
                            severity="error",
                            description=(
                                f"exact duplicate of line {line_numbers[0]} "
                                f"({len(line_numbers)} copies total)"
                            ),
                            evidence={
                                "kind": "exact",
                                "first_line": line_numbers[0],
                                "copy_count": len(line_numbers),
                            },
                        )
                    )

        # Near-duplicates: same user message, different assistant response.
        by_user: dict[str, list[int]] = {}
        for idx, example in enumerate(examples):
            user_msg = self._first_user_content(example)
            if user_msg is None:
                continue
            by_user.setdefault(user_msg, []).append(idx + 1)
        for user_msg, line_numbers in by_user.items():
            if len(line_numbers) < 2:
                continue
            # Only flag as near-duplicate when the assistant responses differ.
            assistant_responses: dict[int, str] = {}
            for ln in line_numbers:
                resp = self._assistant_content(examples[ln - 1])
                if resp is not None:
                    assistant_responses[ln] = resp
            unique_responses = set(assistant_responses.values())
            if len(unique_responses) > 1:
                for ln in line_numbers[1:]:
                    issues.append(
                        QualityIssue(
                            line_number=ln,
                            issue_type="duplicate",
                            severity="warning",
                            description=(
                                f"near-duplicate: same user message as line "
                                f"{line_numbers[0]} but different assistant response "
                                f"(potential label noise)"
                            ),
                            evidence={
                                "kind": "near",
                                "first_line": line_numbers[0],
                                "user_preview": user_msg[:80],
                                "distinct_responses": len(unique_responses),
                            },
                        )
                    )

        return issues

    def check_label_noise(self, example: dict[str, Any], line_number: int) -> list[QualityIssue]:
        """Flag placeholder text and self-contradictory assistant responses."""
        issues: list[QualityIssue] = []
        assistant = self._assistant_content(example)
        if assistant is None:
            return issues

        placeholders = _PLACEHOLDER_RE.findall(assistant)
        if placeholders:
            matched = [m if isinstance(m, str) else m[0] for m in placeholders]
            issues.append(
                QualityIssue(
                    line_number=line_number,
                    issue_type="label_noise",
                    severity="error",
                    description=(
                        "assistant response contains placeholder text "
                        f"{matched}; likely unfinished generation"
                    ),
                    evidence={"markers": matched},
                )
            )

        if _CONTRADICTION_RE.search(assistant):
            snippet = _CONTRADICTION_RE.search(assistant)
            issues.append(
                QualityIssue(
                    line_number=line_number,
                    issue_type="label_noise",
                    severity="warning",
                    description=(
                        "assistant response contains a potential self-contradiction "
                        "(affirm/deny pair in the same turn)"
                    ),
                    evidence={"match": snippet.group(0)[:80] if snippet else ""},
                )
            )

        return issues

    def check_tokenizer_compatibility(
        self, example: dict[str, Any], line_number: int
    ) -> list[QualityIssue]:
        """Flag characters that tokenize inconsistently across tokenizers."""
        issues: list[QualityIssue] = []
        messages = example.get("messages")
        if not isinstance(messages, list):
            return issues

        found: dict[str, list[str]] = {}
        for pos, msg in enumerate(messages):
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if not isinstance(content, str):
                continue
            for ch, label in _SPECIAL_CHARS.items():
                if ch in content:
                    found.setdefault(label, []).append(f"message[{pos}]")

        if found:
            issues.append(
                QualityIssue(
                    line_number=line_number,
                    issue_type="tokenizer_risk",
                    severity="warning",
                    description=(
                        "example contains characters that may tokenize "
                        "differently across tokenizers: "
                        + ", ".join(found.keys())
                    ),
                    evidence={"characters": found},
                )
            )
        return issues

    # ------------------------------------------------------------------ #
    # Boundary coverage (internal)
    # ------------------------------------------------------------------ #
    def _find_boundary_gaps(self, token_counts: list[int]) -> list[QualityIssue]:
        """Flag when examples cluster into too few length buckets."""
        issues: list[QualityIssue] = []
        valid = [c for c in token_counts if c > 0]
        if len(valid) < _LENGTH_BUCKETS:
            # Not enough examples to meaningfully demand spread across buckets.
            return issues

        lo = float(min(valid))
        hi = float(max(valid))
        if hi <= lo:
            issues.append(
                QualityIssue(
                    line_number=0,
                    issue_type="boundary_gap",
                    severity="warning",
                    description=(
                        "all examples share the same length; no boundary diversity"
                    ),
                    evidence={
                        "occupied_buckets": 1,
                        "total_buckets": _LENGTH_BUCKETS,
                        "min": lo,
                        "max": hi,
                    },
                )
            )
            return issues
        bucket_size = (hi - lo) / _LENGTH_BUCKETS
        occupied = 0
        for b in range(_LENGTH_BUCKETS):
            low_edge = lo + b * bucket_size
            high_edge = lo + (b + 1) * bucket_size
            if b == _LENGTH_BUCKETS - 1:
                in_bucket = any(low_edge <= c <= high_edge for c in valid)
            else:
                in_bucket = any(low_edge <= c < high_edge for c in valid)
            if in_bucket:
                occupied += 1

        if occupied <= _LENGTH_BUCKETS // 2:
            issues.append(
                QualityIssue(
                    line_number=0,
                    issue_type="boundary_gap",
                    severity="warning",
                    description=(
                        f"length distribution covers only {occupied}/"
                        f"{_LENGTH_BUCKETS} buckets; input lengths are clustered"
                    ),
                    evidence={
                        "occupied_buckets": occupied,
                        "total_buckets": _LENGTH_BUCKETS,
                        "min": lo,
                        "max": hi,
                    },
                )
            )
        return issues

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _example_token_count(self, example: dict[str, Any]) -> int:
        """Approximate token count as the total word count across all messages."""
        messages = example.get("messages")
        if not isinstance(messages, list):
            return 0
        total = 0
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if isinstance(content, str):
                total += len(content.split())
        return total

    @staticmethod
    def _first_user_content(example: dict[str, Any]) -> str | None:
        messages = example.get("messages")
        if not isinstance(messages, list):
            return None
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content")
                if isinstance(content, str):
                    return content
        return None

    @staticmethod
    def _assistant_content(example: dict[str, Any]) -> str | None:
        messages = example.get("messages")
        if not isinstance(messages, list):
            return None
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                content = msg.get("content")
                if isinstance(content, str):
                    return content
        return None

    @staticmethod
    def _length_stats(token_counts: list[int]) -> dict[str, float]:
        valid = [c for c in token_counts if c > 0]
        if not valid:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "std": 0.0}
        return {
            "min": float(min(valid)),
            "max": float(max(valid)),
            "mean": statistics.fmean(valid),
            "median": float(statistics.median(valid)),
            "std": float(statistics.pstdev(valid)) if len(valid) > 1 else 0.0,
        }

    @staticmethod
    def _quality_score(total: int, issues: list[QualityIssue]) -> float:
        """Compute a 0.0–1.0 quality score.

        Starts at 1.0 and is penalised per issue: errors cost more than
        warnings. An empty dataset scores 0.0 (no data to train on).
        """
        if total == 0:
            return 0.0
        penalty = 0.0
        for issue in issues:
            if issue.severity == "error":
                penalty += 0.05
            else:
                penalty += 0.02
        # Normalise by dataset size so one issue in a million-example dataset
        # does not dominate, but never let a single issue go free.
        normalised = penalty / max(total, 1)
        score = 1.0 - min(normalised, 1.0)
        # A dataset with any error should not score a perfect 1.0.
        if score == 1.0 and any(i.severity == "error" for i in issues):
            score = max(1.0 - 1.0 / total, 0.0)
        return round(max(score, 0.0), 4)


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _count_by(issues: list[QualityIssue], key) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        k = key(issue)
        counts[k] = counts.get(k, 0) + 1
    return counts


if __name__ == "__main__":  # pragma: no cover - manual smoke
    import sys

    if len(sys.argv) < 2:
        print("usage: sft_data_auditor.py <sft.jsonl>")
        sys.exit(1)
    report = SFTDataQualityAuditor().audit_file(sys.argv[1])
    print(f"examples={report.total_examples} issues={report.total_issues} "
          f"score={report.overall_quality_score}")
    for issue in report.issues[:20]:
        print(f" line {issue.line_number}: [{issue.severity}] {issue.issue_type} - {issue.description}")
