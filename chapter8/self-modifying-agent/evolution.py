"""Auditable self-modification pipeline for Experiment 8-5."""

from __future__ import annotations

from collections import defaultdict
import difflib
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable


OLD_CODES = 'NON_RETRYABLE_CODES = {"AUTH_DENIED", "INVALID_ARGUMENT"}'
NEW_CODES = 'NON_RETRYABLE_CODES = {"AUTH_DENIED", "INVALID_ARGUMENT", "PAYMENT_DECLINED"}'

OLD_RETRY = '''def should_retry(error_code, retryable, attempt):
    """Return whether another tool call should be attempted."""
    return attempt < MAX_RETRIES
'''
NEW_RETRY = '''def should_retry(error_code, retryable, attempt):
    """Return whether another tool call should be attempted."""
    if not retryable or error_code in NON_RETRYABLE_CODES:
        return False
    return attempt < MAX_RETRIES
'''

OLD_BREAKER = '''def should_open_circuit(consecutive_failures, *, error_code="", retryable=True):
    """Open after repeated failures."""
    return consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD
'''
NEW_BREAKER = '''def should_open_circuit(consecutive_failures, *, error_code="", retryable=True):
    """Open immediately for permanent errors; otherwise use the threshold."""
    if not retryable or error_code in NON_RETRYABLE_CODES:
        return consecutive_failures >= 1
    return consecutive_failures >= CIRCUIT_BREAKER_THRESHOLD
'''


def _sha(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def diagnose(trajectories: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    repeated: Dict[tuple[str, str], list[Dict[str, Any]]] = defaultdict(list)
    for item in trajectories:
        if item.get("outcome") == "failure" and not item.get("retryable", True) and item.get("attempts", 0) > 1:
            repeated[(item.get("tool", ""), item.get("error_code", ""))].append(item)

    patterns = []
    for (tool, error_code), items in repeated.items():
        if len(items) >= 2:
            patterns.append({
                "tool": tool,
                "error_code": error_code,
                "source_case_ids": [item["id"] for item in items],
                "total_redundant_calls": sum(item["attempts"] - 1 for item in items),
            })
    if not patterns:
        return {
            "change_required": False,
            "target": None,
            "source_case_ids": [],
            "reason": "No repeated non-retryable failure pattern has enough support.",
        }
    source_ids = sorted({case_id for pattern in patterns for case_id in pattern["source_case_ids"]})
    return {
        "change_required": True,
        "target": "stable/retry_policy.py",
        "source_case_ids": source_ids,
        "patterns": patterns,
        "reason": (
            "The control policy ignores the environment's retryable=false signal. "
            "This belongs in retry/circuit-breaker code, not in a conversational prompt."
        ),
    }


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError("Candidate patch no longer matches exactly one stable-code region")
    return source.replace(old, new, 1)


def generate_candidate(stable_source: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a minimal candidate without touching the stable file."""
    if not diagnosis.get("change_required"):
        return {"source": stable_source, "diff": "", "changed": False}
    candidate = _replace_once(stable_source, OLD_CODES, NEW_CODES)
    candidate = _replace_once(candidate, OLD_RETRY, NEW_RETRY)
    candidate = _replace_once(candidate, OLD_BREAKER, NEW_BREAKER)
    candidate = candidate.replace('VERSION = "1.0.0"', 'VERSION = "1.1.0-candidate"', 1)
    return candidate_from_source(stable_source, candidate)


def candidate_from_source(stable_source: str, candidate_source: str) -> Dict[str, Any]:
    """Package any generated source as a reviewable candidate diff."""
    diff = "".join(difflib.unified_diff(
        stable_source.splitlines(keepends=True),
        candidate_source.splitlines(keepends=True),
        fromfile="stable/retry_policy.py",
        tofile="candidate/retry_policy.py",
    ))
    return {
        "source": candidate_source,
        "diff": diff,
        "changed": candidate_source != stable_source,
    }


def validate_candidate(candidate_source: str, trajectories: Iterable[Dict[str, Any]]) -> Dict[str, bool]:
    checks: Dict[str, bool] = {}
    try:
        compile(candidate_source, "candidate/retry_policy.py", "exec")
        namespace: Dict[str, Any] = {}
        exec(candidate_source, namespace)
        checks["static_compile"] = True
    except Exception:
        return {"static_compile": False, "failure_replay": False, "old_task_regression": False}

    failures = [item for item in trajectories if item.get("outcome") == "failure"]
    checks["failure_replay"] = all(
        not namespace["should_retry"](item["error_code"], item["retryable"], 0)
        and namespace["should_open_circuit"](
            1, error_code=item["error_code"], retryable=item["retryable"]
        )
        for item in failures
    )
    checks["old_task_regression"] = all((
        namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 0),
        namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 2),
        not namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 3),
        not namespace["should_open_circuit"](4, error_code="TEMPORARY_TIMEOUT", retryable=True),
        namespace["should_open_circuit"](5, error_code="TEMPORARY_TIMEOUT", retryable=True),
    ))
    return checks


def release_manifest(
    stable_source: str,
    candidate: Dict[str, Any],
    diagnosis: Dict[str, Any],
    checks: Dict[str, bool],
) -> Dict[str, Any]:
    accepted = candidate.get("changed", False) and bool(checks) and all(checks.values())
    return {
        "artifact_type": "agent_control_code_patch",
        "target": diagnosis.get("target"),
        "source_case_ids": diagnosis.get("source_case_ids", []),
        "rationale": diagnosis.get("reason"),
        "stable_version": _sha(stable_source),
        "candidate_version": _sha(candidate.get("source", stable_source)),
        "rollback_version": _sha(stable_source),
        "diff": candidate.get("diff", ""),
        "checks": checks,
        "decision": "release_to_canary" if accepted else "reject_candidate",
    }


def write_candidate(candidate_source: str, path: Path) -> None:
    """Write only to a candidate artifact path, never over the stable module."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(candidate_source, encoding="utf-8")
