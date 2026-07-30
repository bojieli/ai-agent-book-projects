from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domain_tools import execute_tool


ROOT = Path(__file__).resolve().parents[1]


def load_spec():
    return json.loads((ROOT / "domain_spec.json").read_text(encoding="utf-8"))


def record(spec, *, identifier, required, status, evidence):
    return {
        spec["identifier_field"]: identifier,
        spec["required_field"]: required,
        spec["status_field"]: status,
        spec["evidence_field"]: evidence,
    }


def test_required_nonpassing_record_refuses_with_exact_evidence():
    spec = load_spec()
    records = [
        record(
            spec,
            identifier="required-check",
            required=True,
            status="failed",
            evidence="observed failure",
        )
    ]
    result = execute_tool(spec["tool_name"], {spec["records_argument"]: records})
    assert result["ok"] is True
    assert result["result"]["approved"] is False
    assert result["result"]["decision"] == spec["rejected_label"]
    assert result["result"]["failed_required_records"][0]["evidence"] == "observed failure"


def test_only_required_nonpassing_records_block_approval():
    spec = load_spec()
    passing = spec["passing_values"][0]
    records = [
        record(spec, identifier="required", required=True, status=passing, evidence="ok"),
        record(spec, identifier="optional", required=False, status="failed", evidence="optional"),
    ]
    result = execute_tool(spec["tool_name"], {spec["records_argument"]: records})
    assert result["ok"] is True
    assert result["result"]["approved"] is True
    assert result["result"]["decision"] == spec["approved_label"]


def test_missing_or_empty_records_fail_closed():
    spec = load_spec()
    result = execute_tool(spec["tool_name"], {})
    assert result["ok"] is False
    assert spec["records_argument"] in result["error"]
