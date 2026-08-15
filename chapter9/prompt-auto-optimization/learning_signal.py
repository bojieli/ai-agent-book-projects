"""Turn evaluated customer-service trajectories into a prompt-learning signal."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict


DIMENSIONS = ("rule_compliance", "task_resolution", "compliant_flexibility")


def case_dimensions(result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Derive the three dimensions used by Experiment 8-3.

    The full project would consume Experiment 8-1 reports.  This compact
    airline simulation exposes the same dimensions from its deterministic
    labels and the handled/not-handled judge result.
    """
    should_transfer = bool(result["should_transfer"])
    transferred = bool(result["transferred"])
    boundary = result["group"] == "boundary"
    correct = bool(result["correct"])

    if should_transfer and not transferred:
        compliance = {
            "verdict": "fail",
            "evidence": "Required escalation boundary was ignored",
        }
    else:
        compliance = {
            "verdict": "pass",
            "evidence": "No forbidden action or missed mandatory escalation was observed",
        }

    resolution = {
        "verdict": "pass" if correct else "fail",
        "evidence": result.get("note", ""),
    }

    if boundary:
        flexible = not transferred and bool(result.get("handled"))
        flexibility = {
            "verdict": "pass" if flexible else "fail",
            "evidence": (
                "Explained policy and supplied an allowed alternative"
                if flexible
                else "Policy dispute was transferred or left without a useful compliant alternative"
            ),
        }
    else:
        flexibility = {
            "verdict": "pass",
            "evidence": "This case does not require a blocked-path alternative",
        }
    return {
        "rule_compliance": compliance,
        "task_resolution": resolution,
        "compliant_flexibility": flexibility,
    }


def diagnose_failures(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate failed cases into an evidence-bearing change request."""
    failed_by_dimension: Dict[str, list[Dict[str, str]]] = defaultdict(list)
    all_case_reports = []
    for result in evaluation.get("results", []):
        dimensions = case_dimensions(result)
        all_case_reports.append({"case_id": result["id"], "dimensions": dimensions})
        for dimension, verdict in dimensions.items():
            if verdict["verdict"] == "fail":
                failed_by_dimension[dimension].append({
                    "case_id": result["id"],
                    "evidence": verdict["evidence"],
                })

    source_ids = sorted({
        item["case_id"]
        for failures in failed_by_dimension.values()
        for item in failures
    })
    boundary_ids = [
        item["case_id"]
        for item in failed_by_dimension.get("compliant_flexibility", [])
    ]
    diagnosis = (
        "The prompt over-escalates policy disputes. Preserve mandatory escalation for explicit "
        "human requests and safety emergencies, but require policy explanation and an allowed "
        "alternative before transfer in ordinary disputes."
        if boundary_ids
        else "No repeated prompt-level boundary failure was detected."
    )
    return {
        "source_case_ids": source_ids,
        "scope": "system_prompt.transfer_policy",
        "dimensions": {dimension: failed_by_dimension.get(dimension, []) for dimension in DIMENSIONS},
        "diagnosis": diagnosis,
        "case_reports": all_case_reports,
    }


def format_learning_signal(report: Dict[str, Any]) -> str:
    lines = [
        f"Scope: {report['scope']}",
        f"Source cases: {', '.join(report['source_case_ids']) or 'none'}",
        f"Diagnosis: {report['diagnosis']}",
    ]
    for dimension in DIMENSIONS:
        failures = report["dimensions"].get(dimension, [])
        lines.append(f"{dimension}: {len(failures)} failure(s)")
        lines.extend(f"- {item['case_id']}: {item['evidence']}" for item in failures)
    return "\n".join(lines)
