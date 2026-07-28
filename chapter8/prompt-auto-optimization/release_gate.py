"""Candidate manifest and release gate for prompt updates."""

from __future__ import annotations

from typing import Any, Dict


def build_candidate_manifest(
    optimization: Dict[str, Any], learning_signal: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "artifact_type": "system_prompt_patch",
        "source_case_ids": list(learning_signal.get("source_case_ids", [])),
        "scope": learning_signal.get("scope", "system_prompt"),
        "rationale": optimization.get("rationale") or learning_signal.get("diagnosis", ""),
        "diff": optimization.get("diff", ""),
        "status": "candidate",
    }


def evaluate_release_gate(
    before: Dict[str, Any], after: Dict[str, Any], manifest: Dict[str, Any]
) -> Dict[str, Any]:
    holdout_before, holdout_total = before["holdout"]
    holdout_after, _ = after["holdout"]
    boundary_before, boundary_total = before["boundary"]
    boundary_after, _ = after["boundary"]

    checks = {
        "patch_is_nonempty": bool(manifest.get("diff", "").strip()),
        "source_cases_are_recorded": bool(manifest.get("source_case_ids")),
        "holdout_did_not_regress": holdout_after >= holdout_before,
        "boundary_improved": boundary_after > boundary_before,
    }
    accepted = all(checks.values())
    return {
        "decision": "release_to_canary" if accepted else "reject_candidate",
        "accepted": accepted,
        "checks": checks,
        "metrics": {
            "holdout_before": [holdout_before, holdout_total],
            "holdout_after": [holdout_after, holdout_total],
            "boundary_before": [boundary_before, boundary_total],
            "boundary_after": [boundary_after, boundary_total],
        },
    }
