"""Model-external four-phase longitudinal evaluator for Experiment 8-7."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable


PHASES = ("learning", "transfer", "change", "retention")


def _rubric_dimension_total(rubric: dict) -> int:
    """Compatibility helper retained for older result files and tests."""
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
            # This is the sole update boundary and is intentionally after act.
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
                "memory_available": act.get("memory_available", False),
                "memory_adherence": (
                    act["action"] == act.get("active_memory_value")
                    if act.get("memory_available") else None
                ),
                "memory_version": act["memory_version"],
                "updated_after_task": observation["updated"],
                "candidate_proposed": observation.get("candidate_proposed", False),
                "candidate_valid": observation.get("candidate_valid"),
                "event_order_valid": observation.get("event_order_valid", True),
                "tokens": act["tokens"] + observation["tokens"],
                "prompt_tokens": act.get("prompt_tokens", 0),
                "completion_tokens": act.get("completion_tokens", 0),
                "provider_reported_cost_usd": act.get("provider_reported_cost_usd"),
                "time_ms": act["time_ms"] + observation["time_ms"],
                "response_id": act.get("response_id"),
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
        # C1 carries the new signal only after its action. Recovery is measured
        # on subsequent tasks, so C2 correct means one task after the signal.
        first_recovered = next((i for i, row in enumerate(change_rows[1:], 1) if row["correct"]), None)
        negative_candidates = [
            row for row in records
            if row["phase"] in {"transfer", "change", "retention"} and row["used_memory"]
        ]
        negative_transfer_rate = (
            round(sum(not row["correct"] for row in negative_candidates) / len(negative_candidates), 3)
            if negative_candidates else 0.0
        )
        unchanged_retention = [row for row in by_phase["retention"] if row["rule_id"] != "baggage.economy_allowance"]
        current_rule_retention = [row for row in by_phase["retention"] if row["rule_id"] == "baggage.economy_allowance"]
        replacement_rows = change_rows[1:] + current_rule_retention
        proposed = [row for row in records if row["candidate_proposed"]]
        activated = [row for row in records if row["phase"] != "learning" and row["memory_available"]]
        adherence = [row for row in records if row["memory_adherence"] is not None]
        native_costs = [row["provider_reported_cost_usd"] for row in records if row["provider_reported_cost_usd"] is not None]

        return {
            "profile": agent.profile,
            "phase_accuracy": phase_accuracy,
            "learning_curve": learning_curve,
            "transfer_accuracy": phase_accuracy["transfer"],
            "retention_rate": phase_accuracy["retention"],
            "old_capability_retention_rate": _rate(unchanged_retention, "correct"),
            "current_rule_retention_rate": _rate(current_rule_retention, "correct"),
            "adaptation": {
                "recovered": first_recovered is not None,
                "tasks_after_change_signal_to_recover": first_recovered,
                "recovery_score": 1 / (1 + first_recovered) if first_recovered is not None else 0.0,
                "change_phase_accuracy": phase_accuracy["change"],
            },
            "replacement": {
                "rule_replacement_accuracy": _rate(replacement_rows, "correct"),
                "obsolete_rule_reference_rate": round(
                    sum(row["actual_action"] == "answer_20kg" for row in replacement_rows) / len(replacement_rows), 3
                ) if replacement_rows else 0.0,
            },
            "negative_transfer_rate": negative_transfer_rate,
            "safety_rubric_pass_rate": _rate(records, "safety_pass"),
            "post_learning_safety_pass_rate": _rate(
                [row for row in records if row["phase"] != "learning"], "safety_pass"
            ),
            "update_metrics": {
                "candidate_modification_validity": _rate(proposed, "candidate_valid") if proposed else None,
                "artifact_activation_rate": _rate(activated, "used_memory") if activated else None,
                "memory_adherence_rate": _rate(adherence, "memory_adherence") if adherence else None,
            },
            "feedback_order_valid": all(row["event_order_valid"] for row in records),
            "cost": {
                "tokens": sum(row["tokens"] for row in records),
                "prompt_tokens": sum(row["prompt_tokens"] for row in records),
                "completion_tokens": sum(row["completion_tokens"] for row in records),
                "time_ms": sum(row["time_ms"] for row in records),
                "storage_bytes": agent.storage_bytes,
                "provider_reported_cost_usd": round(sum(native_costs), 9) if native_costs else None,
                "cost_qualification": (
                    "sum of provider-native usage.cost" if native_costs
                    else "provider did not expose monetary cost; no price was guessed"
                ),
            },
            "records": records,
        }
