"""Four-phase longitudinal evaluator for Experiment 8-6."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable


PHASES = ("learning", "transfer", "change", "retention")


def _rubric_dimension_total(rubric: dict) -> int:
    """Compatibility helper retained for old result files and tests."""
    dims = ["error_handling", "input_validation", "documentation", "robustness"]
    return sum(int(value) if value is not None else 0 for value in (rubric.get(key) for key in dims))


def _rate(rows: Iterable[Dict[str, Any]], field: str) -> float:
    values = [bool(row[field]) for row in rows]
    return round(sum(values) / len(values), 3) if values else 0.0


class LongitudinalEvaluator:
    def run(self, agent, tasks: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        records = []
        cumulative_correct = 0
        learning_seen = 0
        learning_curve = []

        for index, task in enumerate(tasks):
            if task["phase"] not in PHASES:
                raise ValueError(f"unknown phase {task['phase']}")
            act = agent.act(task)
            correct = act["action"] == task["expected_action"]
            safety_pass = act["action"] not in task.get("forbidden_actions", [])
            observation = agent.observe(task)
            record = {
                "index": index,
                "task_id": task["id"],
                "phase": task["phase"],
                "rule_id": task["rule_id"],
                "expected_action": task["expected_action"],
                "actual_action": act["action"],
                "correct": correct,
                "safety_pass": safety_pass,
                "used_memory": act["used_memory"],
                "memory_version": act["memory_version"],
                "updated_after_task": observation["updated"],
                "tokens": act["tokens"] + observation["tokens"],
                "time_ms": act["time_ms"] + observation["time_ms"],
            }
            records.append(record)
            if task["phase"] == "learning":
                learning_seen += 1
                cumulative_correct += int(correct)
                learning_curve.append({
                    "task_id": task["id"],
                    "cumulative_accuracy": round(cumulative_correct / learning_seen, 3),
                })

        by_phase = defaultdict(list)
        for record in records:
            by_phase[record["phase"]].append(record)
        phase_accuracy = {phase: _rate(by_phase[phase], "correct") for phase in PHASES}

        change_rows = by_phase["change"]
        first_recovered = next((i for i, row in enumerate(change_rows) if row["correct"]), None)
        negative_candidates = [
            row for row in records
            if row["phase"] in {"transfer", "change", "retention"} and row["used_memory"]
        ]
        negative_transfer_rate = (
            round(sum(not row["correct"] for row in negative_candidates) / len(negative_candidates), 3)
            if negative_candidates else 0.0
        )

        return {
            "profile": agent.profile,
            "phase_accuracy": phase_accuracy,
            "learning_curve": learning_curve,
            "transfer_accuracy": phase_accuracy["transfer"],
            "retention_rate": phase_accuracy["retention"],
            "adaptation": {
                "tasks_after_change_signal_to_recover": first_recovered,
                "change_phase_accuracy": phase_accuracy["change"],
            },
            "negative_transfer_rate": negative_transfer_rate,
            "safety_rubric_pass_rate": _rate(records, "safety_pass"),
            "cost": {
                "tokens": sum(row["tokens"] for row in records),
                "time_ms": sum(row["time_ms"] for row in records),
                "storage_bytes": agent.storage_bytes,
            },
            "records": records,
        }
