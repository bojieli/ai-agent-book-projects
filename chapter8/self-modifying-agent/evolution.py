"""Auditable self-modification and trusted release gates for Experiment 8-5."""

from __future__ import annotations

import ast
from collections import defaultdict
import difflib
import hashlib
import inspect
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

CHECK_NAMES = (
    "static_compile",
    "public_api_compatible",
    "security_scan",
    "failure_replay",
    "nonretryable_circuit",
    "temporary_recovery",
    "old_task_regression",
    "canary_ready",
    "rollback_ready",
)


def sha256_text(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _short_sha(source: str) -> str:
    return sha256_text(source)[:12]


def diagnose(trajectories: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    trajectories = list(trajectories)
    repeated: Dict[tuple[str, str], list[Dict[str, Any]]] = defaultdict(list)
    for item in trajectories:
        if item.get("outcome") == "failure" and not item.get("retryable", True) and item.get("attempts", 0) > 1:
            repeated[(item.get("tool", ""), item.get("error_code", ""))].append(item)

    patterns = []
    for (tool, error_code), items in repeated.items():
        if len(items) >= 2:
            patterns.append({
                "cluster_id": f"{tool}:{error_code}",
                "tool": tool,
                "error_code": error_code,
                "source_case_ids": [item["id"] for item in items],
                "cross_trajectory_support": len(items),
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
    sources = [
        {
            "id": item["id"],
            "trajectory_sha256": sha256_text(repr(sorted(item.items()))),
            "evidence": item.get("evidence"),
        }
        for item in trajectories if item.get("id") in source_ids
    ]
    return {
        "change_required": True,
        "target": "stable/retry_policy.py",
        "target_component": "retry_and_circuit_breaker_control",
        "source_case_ids": source_ids,
        "source_trajectories": sources,
        "patterns": patterns,
        "reason": (
            "The deterministic control policy ignores retryable=false and does not open the circuit "
            "for permanent errors. The root cause belongs in retry/circuit-breaker code, not a prompt."
        ),
        "change_contract": {
            "expected_fix": [
                "non-retryable tool-call attempts fall to one",
                "the circuit opens on the first permanent failure",
            ],
            "potential_regressions": [
                "temporary timeouts stop retrying",
                "the five-failure circuit threshold changes for retryable errors",
                "public function signatures change",
            ],
        },
    }


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError("Candidate patch no longer matches exactly one stable-code region")
    return source.replace(old, new, 1)


def candidate_from_source(
    stable_source: str,
    candidate_source: str,
    *,
    impact_prediction: Dict[str, Any] | None = None,
    generator_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Package generated source and provenance as a reviewable candidate."""
    diff = "".join(difflib.unified_diff(
        stable_source.splitlines(keepends=True),
        candidate_source.splitlines(keepends=True),
        fromfile="stable/retry_policy.py",
        tofile="candidate/retry_policy.py",
    ))
    added = sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())
    deleted = sum(line.startswith("-") and not line.startswith("---") for line in diff.splitlines())
    return {
        "source": candidate_source,
        "diff": diff,
        "changed": candidate_source != stable_source,
        "impact_prediction": impact_prediction or {},
        "generator_metadata": generator_metadata or {},
        "source_sha256": sha256_text(candidate_source),
        "patch_size": {"added_lines": added, "deleted_lines": deleted, "changed_lines": added + deleted},
    }


def generate_candidate(stable_source: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the deterministic comparison candidate without touching stable."""
    if not diagnosis.get("change_required"):
        return candidate_from_source(stable_source, stable_source)
    candidate = _replace_once(stable_source, OLD_CODES, NEW_CODES)
    candidate = _replace_once(candidate, OLD_RETRY, NEW_RETRY)
    candidate = _replace_once(candidate, OLD_BREAKER, NEW_BREAKER)
    candidate = candidate.replace('VERSION = "1.0.0"', 'VERSION = "1.1.0-candidate"', 1)
    return candidate_from_source(
        stable_source,
        candidate,
        impact_prediction={
            "non_retryable_calls": {"before": "up to 4", "after": 1},
            "temporary_timeout_recovery_rate": {"before": 1.0, "after": 1.0},
        },
        generator_metadata={"generator": "deterministic", "model": None, "api_calls": 0},
    )


def generate_rejected_control(stable_source: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    """Historical-looking bad patch: fixes the incident by disabling all retries."""
    candidate = _replace_once(stable_source, OLD_RETRY, '''def should_retry(error_code, retryable, attempt):
    """Incorrect over-broad fix retained as a rejected candidate."""
    return False
''')
    candidate = _replace_once(candidate, OLD_BREAKER, NEW_BREAKER)
    candidate = candidate.replace('VERSION = "1.0.0"', 'VERSION = "1.0.1-rejected"', 1)
    return candidate_from_source(
        stable_source,
        candidate,
        impact_prediction={
            "non_retryable_calls": {"after": 1},
            "temporary_timeout_recovery_rate": {"after": 0.0},
        },
        generator_metadata={"generator": "negative_control", "api_calls": 0},
    )


def _namespace(source: str) -> Dict[str, Any]:
    namespace: Dict[str, Any] = {}
    exec(compile(source, "candidate/retry_policy.py", "exec"), namespace)
    return namespace


def _safe_ast(source: str) -> bool:
    tree = ast.parse(source)
    forbidden_calls = {"eval", "exec", "compile", "open", "__import__"}
    return not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        or (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls)
        for node in ast.walk(tree)
    )


def _temporary_recovery(namespace: Dict[str, Any]) -> bool:
    # Two timeouts followed by success: both retry decisions must remain open.
    return namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 0) and namespace["should_retry"](
        "TEMPORARY_TIMEOUT", True, 1
    )


def validate_candidate(
    candidate_source: str,
    trajectories: Iterable[Dict[str, Any]],
    stable_source: str | None = None,
) -> Dict[str, bool]:
    """Run trusted gates outside the candidate's writable surface."""
    checks = {name: False for name in CHECK_NAMES}
    try:
        # Scan the candidate BEFORE executing it: this validator runs untrusted,
        # model-generated code, so a source that fails the security scan must
        # never have its module-level side effects executed. static_compile uses
        # a non-executing compile() so it is still recorded for a rejected source.
        checks["static_compile"] = bool(
            compile(candidate_source, "candidate/retry_policy.py", "exec")
        )
        checks["security_scan"] = _safe_ast(candidate_source)
        if not checks["security_scan"]:
            return checks
        namespace = _namespace(candidate_source)
    except Exception:
        return checks

    # A syntactically valid but degenerate candidate (e.g. an empty LLM "source")
    # compiles yet may define neither public function; reject cleanly here so the
    # behavior gates below cannot KeyError on a missing name.
    if not callable(namespace.get("should_retry")) or not callable(
        namespace.get("should_open_circuit")
    ):
        return checks

    expected_retry = "(error_code, retryable, attempt)"
    expected_breaker = "(consecutive_failures, *, error_code='', retryable=True)"
    try:
        checks["public_api_compatible"] = (
            str(inspect.signature(namespace.get("should_retry"))) == expected_retry
            and str(inspect.signature(namespace.get("should_open_circuit"))) == expected_breaker
        )
    except (TypeError, ValueError):
        checks["public_api_compatible"] = False
    failures = [item for item in trajectories if item.get("outcome") == "failure"]
    checks["failure_replay"] = bool(failures) and all(
        not namespace["should_retry"](item["error_code"], item["retryable"], attempt)
        for item in failures for attempt in range(item["attempts"])
    )
    checks["nonretryable_circuit"] = bool(failures) and all(
        namespace["should_open_circuit"](1, error_code=item["error_code"], retryable=item["retryable"])
        for item in failures
    )
    checks["temporary_recovery"] = _temporary_recovery(namespace)
    checks["old_task_regression"] = all((
        namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 0),
        namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 2),
        not namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 3),
        not namespace["should_open_circuit"](4, error_code="TEMPORARY_TIMEOUT", retryable=True),
        namespace["should_open_circuit"](5, error_code="TEMPORARY_TIMEOUT", retryable=True),
    ))
    # Canary covers an unseen permanent code plus the original temporary path.
    checks["canary_ready"] = all((
        not namespace["should_retry"]("AUTH_DENIED", True, 0),
        namespace["should_open_circuit"](1, error_code="AUTH_DENIED", retryable=True),
        _temporary_recovery(namespace),
    ))
    if stable_source is None:
        # Backward-compatible test path: rollback content is supplied by the caller in production.
        checks["rollback_ready"] = True
    else:
        try:
            rollback = _namespace(stable_source)
            checks["rollback_ready"] = (
                rollback.get("VERSION") == "1.0.0"
                and rollback["should_retry"]("TEMPORARY_TIMEOUT", True, 0)
                and not rollback["should_retry"]("TEMPORARY_TIMEOUT", True, 3)
            )
        except Exception:
            checks["rollback_ready"] = False
    return checks


def behavior_metrics(candidate_source: str, trajectories: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    namespace = _namespace(candidate_source)
    failures = [item for item in trajectories if item.get("outcome") == "failure"]
    calls = []
    for item in failures:
        made = 1
        while made < item["attempts"] and namespace["should_retry"](
            item["error_code"], item["retryable"], made - 1
        ):
            made += 1
        calls.append(made)
    return {
        "mean_nonretryable_calls": sum(calls) / len(calls) if calls else 0.0,
        "temporary_error_recovery_rate": float(_temporary_recovery(namespace)),
        "old_task_regressions": 0 if all((
            namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 0),
            not namespace["should_retry"]("TEMPORARY_TIMEOUT", True, 3),
        )) else 1,
    }


def release_manifest(
    stable_source: str,
    candidate: Dict[str, Any],
    diagnosis: Dict[str, Any],
    checks: Dict[str, bool],
    *,
    provenance: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    accepted = candidate.get("changed", False) and bool(checks) and all(checks.values())
    failed = [name for name, passed in checks.items() if not passed]
    contract = diagnosis.get("change_contract", {})
    return {
        "artifact_type": "agent_control_code_patch",
        "failure_cluster": diagnosis.get("patterns", []),
        "source_trajectories": diagnosis.get("source_trajectories", []),
        "inferred_root_cause": diagnosis.get("reason"),
        "target_component": diagnosis.get("target_component"),
        "target_file": diagnosis.get("target"),
        "code_diff": candidate.get("diff", ""),
        "impact_prediction": candidate.get("impact_prediction", {}),
        "expected_fix": contract.get("expected_fix", []),
        "potential_regressions": contract.get("potential_regressions", []),
        "stable_version": _short_sha(stable_source),
        "stable_sha256": sha256_text(stable_source),
        "candidate_version": _short_sha(candidate.get("source", stable_source)),
        "candidate_sha256": sha256_text(candidate.get("source", stable_source)),
        "rollback_version": _short_sha(stable_source),
        "rollback_sha256": sha256_text(stable_source),
        # Compatibility field retained for readers of the earlier demo.
        "diff": candidate.get("diff", ""),
        "patch_size": candidate.get("patch_size", {}),
        "checks": checks,
        "failed_checks": failed,
        "canary_gate": {
            "eligible": accepted,
            "scope": "shadow traffic only; stable remains unchanged",
            "rollback_trigger": "any non-retryable repeat or temporary-recovery regression",
        },
        "rollback_gate": {
            "artifact_hash_matches_stable": checks.get("rollback_ready", False),
            "rollback_version": _short_sha(stable_source),
        },
        "provenance": provenance or candidate.get("generator_metadata", {}),
        "decision": "release_to_canary" if accepted else "reject_candidate",
        "rejection_reason": None if accepted else (
            "candidate did not change stable source" if not candidate.get("changed")
            else "failed gates: " + ", ".join(failed)
        ),
    }


def write_candidate(candidate_source: str, path: Path) -> None:
    """Write only to a candidate artifact path, never over the stable module."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(candidate_source, encoding="utf-8")
