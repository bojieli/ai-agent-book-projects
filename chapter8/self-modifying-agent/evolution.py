"""Auditable self-modification and trusted release gates for Experiment 8-5."""

from __future__ import annotations

import ast
from collections import defaultdict
import difflib
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable

from candidate_sandbox import MAX_SOURCE_BYTES, SandboxError, run_in_sandbox


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
    "security_scan",
    "sandbox_execution",
    "public_api_compatible",
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


def _safe_ast(source: str) -> bool:
    """Apply a fast defense-in-depth filter before sandboxed execution."""
    tree = ast.parse(source)
    forbidden_calls = {"eval", "exec", "compile", "open", "__import__"}
    return not any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        or (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls)
        for node in ast.walk(tree)
    )


def validate_candidate(
    candidate_source: str,
    trajectories: Iterable[Dict[str, Any]],
    stable_source: str | None = None,
) -> Dict[str, bool]:
    """Run release gates with candidate execution confined to Docker."""
    checks = {name: False for name in CHECK_NAMES}
    try:
        oversized = len(candidate_source.encode("utf-8")) > MAX_SOURCE_BYTES
    except UnicodeError:
        return checks
    if oversized:
        return checks
    try:
        # Compilation and the AST scan do not execute the source. The scan is a
        # fast prefilter; the container, not this deny-list, is the security boundary.
        compile(candidate_source, "candidate/retry_policy.py", "exec")
        checks["static_compile"] = True
        checks["security_scan"] = _safe_ast(candidate_source)
        if not checks["security_scan"]:
            return checks
    except Exception:
        return checks

    try:
        result = run_in_sandbox(
            "validate",
            candidate_source,
            trajectories,
            stable_source=stable_source,
        )
    except SandboxError:
        return checks
    sandbox_checks = result.get("checks")
    if not isinstance(sandbox_checks, dict):
        return checks
    checks["sandbox_execution"] = True
    for name in CHECK_NAMES:
        if name not in {"static_compile", "security_scan", "sandbox_execution"}:
            checks[name] = sandbox_checks.get(name) is True
    return checks


def behavior_metrics(candidate_source: str, trajectories: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Measure candidate behavior inside the same locked-down sandbox."""
    try:
        result = run_in_sandbox("metrics", candidate_source, trajectories)
    except SandboxError:
        return {
            "mean_nonretryable_calls": None,
            "temporary_error_recovery_rate": None,
            "old_task_regressions": None,
            "evaluation_failed": True,
        }
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        return {
            "mean_nonretryable_calls": None,
            "temporary_error_recovery_rate": None,
            "old_task_regressions": None,
            "evaluation_failed": True,
        }
    return metrics


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
