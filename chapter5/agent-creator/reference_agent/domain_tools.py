"""Deterministic policy-record adapter configured by ``domain_spec.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def _spec() -> dict[str, Any]:
    with (ROOT / "domain_spec.json").open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("domain_spec.json must contain an object")
    return value


def evaluate_policy_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    spec = _spec()
    required_field = spec["required_field"]
    status_field = spec["status_field"]
    identifier_field = spec["identifier_field"]
    evidence_field = spec["evidence_field"]
    passing = {str(value).casefold() for value in spec["passing_values"]}
    remediation = {
        str(key).casefold(): value
        for key, value in spec["remediation_by_status"].items()
    }
    failures: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} must be an object")
        missing = [
            field
            for field in (identifier_field, required_field, status_field, evidence_field)
            if field not in record
        ]
        if missing:
            raise ValueError(f"record {index} missing fields: {', '.join(missing)}")
        if not isinstance(record[required_field], bool):
            raise ValueError(f"record {index} {required_field} must be boolean")
        status = str(record[status_field])
        row = {
            "id": record[identifier_field],
            "required": record[required_field],
            "status": status,
            "evidence": record[evidence_field],
            "passed": status.casefold() in passing,
        }
        normalized.append(row)
        if row["required"] and not row["passed"]:
            failures.append(
                {
                    **row,
                    "remediation": remediation.get(
                        status.casefold(), spec["default_remediation"]
                    ),
                }
            )
    approved = not failures
    return {
        "approved": approved,
        "decision": spec["approved_label"] if approved else spec["rejected_label"],
        "evaluated_count": len(normalized),
        "failed_required_count": len(failures),
        "failed_required_records": failures,
        "records": normalized,
    }


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    spec = _spec()
    if name == spec["tool_name"]:
        records = arguments.get(spec["records_argument"])
        if not isinstance(records, list) or not records:
            return {
                "ok": False,
                "error": f"{spec['records_argument']} must be a non-empty array",
            }
        try:
            return {"ok": True, "result": evaluate_policy_records(records)}
        except (KeyError, TypeError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}
    return {"ok": False, "error": f"unknown tool: {name}"}
