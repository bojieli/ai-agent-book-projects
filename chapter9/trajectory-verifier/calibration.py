"""Calibration helpers for comparing the verifier with expert labels."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from verifier import FAIL, _item_get


def calibration_report(
    trajectories: Iterable[Dict[str, Any]], reports: Iterable[Dict[str, Any]]
) -> Dict[str, Any]:
    pairs = list(zip(trajectories, reports))
    dimensions = sorted({
        dimension
        for trajectory, _ in pairs
        for dimension in (trajectory.get("expert_labels") if isinstance(trajectory, dict) and isinstance(trajectory.get("expert_labels"), dict) else {})
    })
    per_dimension: Dict[str, Any] = {}
    total_equal = 0
    total = 0
    for dimension in dimensions:
        tp = fp = fn = tn = 0
        for trajectory, report in pairs:
            labels = trajectory.get("expert_labels") if isinstance(trajectory, dict) and isinstance(trajectory.get("expert_labels"), dict) else {}
            expected = labels.get(dimension)
            if expected is None:
                continue
            dims = report.get("dimensions") if isinstance(report, dict) and isinstance(report.get("dimensions"), list) else getattr(report, "dimensions", [])
            predicted_map = {_item_get(item, "dimension"): _item_get(item, "verdict") for item in dims}
            predicted = predicted_map.get(dimension)
            expected_fail = expected == FAIL
            predicted_fail = predicted == FAIL
            tp += int(expected_fail and predicted_fail)
            fp += int(not expected_fail and predicted_fail)
            fn += int(expected_fail and not predicted_fail)
            tn += int(not expected_fail and not predicted_fail)
            total_equal += int(expected == predicted)
            total += 1
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        per_dimension[dimension] = {
            "precision_on_failures": round(precision, 3),
            "recall_on_failures": round(recall, 3),
            "support": tp + fp + fn + tn,
        }
    return {
        "exact_label_agreement": round(total_equal / total, 3) if total else 0.0,
        "per_dimension": per_dimension,
    }
