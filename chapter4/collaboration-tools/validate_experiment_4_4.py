#!/usr/bin/env python3
"""Independently validate a retained Experiment 4-4 interactive campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


EXPECTED_BLOCKERS = [
    "real_email_notification",
    "real_im_notification",
    "real_slack_notification",
]
SYNTHETIC_PRIVACY_CANARY = "PRIVATE-MARKER-MUST-BE-FILTERED"
REQUIRED_TRUE_GATES = {
    "real_mcp_catalog_has_required_primitives",
    "two_real_context_strategies_compared",
    "raw_model_usage_latency_receipts",
    "sync_async_message_cancel_status_lifecycle",
    "hitl_pending_response_and_conservative_timeout",
    "real_human_decision",
}
CREDENTIAL = re.compile(
    rb"sk-ant-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|"
    rb"sk-[A-Za-z0-9_-]{20,}|https://hooks\.slack\.com/services/|"
    rb"[0-9]{6,}:[A-Za-z0-9_-]{20,}"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()

    summary = load(run_dir / "summary.json")
    human = load(run_dir / "human_decision.json")
    manifest = load(run_dir / "manifest.json")
    model_receipts = load(run_dir / "llm_receipts.json")
    receipts = [load(path) for path in sorted((run_dir / "receipts").glob("*.json"))]
    by_case = {row["case"]: row for row in receipts}

    elapsed = (
        datetime.fromisoformat(human["responded_at"])
        - datetime.fromisoformat(human["presented_at"])
    ).total_seconds()
    manifest_files = {row["path"]: row for row in manifest["files"]}
    actual_files = {
        str(path.relative_to(run_dir))
        for path in run_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }

    gates = {
        "campaign_identity": summary.get("experiment") == "4-4"
        and summary.get("campaign_id") == run_dir.name,
        "blocked_only_on_real_delivery": summary.get("status") == "blocked"
        and summary.get("official_complete") is False
        and summary.get("blockers") == EXPECTED_BLOCKERS,
        "all_non_delivery_gates_pass": REQUIRED_TRUE_GATES
        <= {name for name, passed in summary.get("gates", {}).items() if passed},
        "delivery_gates_are_not_claimed": all(
            summary.get("gates", {}).get(name) is False for name in EXPECTED_BLOCKERS
        )
        and summary.get("real_notifications_enabled") is False,
        "live_human_decision_within_window": human.get("approved") is True
        and human.get("decision") == "approved"
        and human.get("operator_channel")
        == "live-user-chat-forwarded-verbatim-to-runner-stdin"
        and 0 <= elapsed < human.get("timeout_seconds", 0),
        "mcp_human_receipts_match": by_case["hitl_pending"]["payload"]["count"] == 1
        and by_case["hitl_human_response"]["payload"].get("success") is True
        and by_case["hitl_approval"]["payload"].get("success") is True
        and by_case["hitl_approval"]["payload"].get("approved") is True
        and {
            human.get("request_id"),
            by_case["hitl_human_response"]["payload"].get("request_id"),
            by_case["hitl_approval"]["payload"].get("request_id"),
        }
        == {human.get("request_id")},
        "conservative_timeout_retained": by_case["hitl_timeout"]["payload"].get("timeout")
        is True
        and by_case["hitl_timeout"]["payload"].get("approved") is False,
        "six_real_kimi_receipts": len(model_receipts) == 6
        and len({row.get("response", {}).get("id") for row in model_receipts}) == 6
        and all(
            row.get("response", {}).get("id")
            and row.get("response", {}).get("model") == "kimi-k3"
            and row.get("usage", {}).get("total_tokens", 0) > 0
            and row.get("latency_seconds", 0) > 0
            for row in model_receipts
        ),
        "synthetic_privacy_canary_filtered": all(
            SYNTHETIC_PRIVACY_CANARY
            in by_case[case]["arguments"]["parent_context"].get("private_note", "")
            and SYNTHETIC_PRIVACY_CANARY
            not in by_case[case]["payload"].get("prepared_context", "")
            for case in ("minimal_sync", "llm_generated_sync")
        ),
        "manifest_exact_and_valid": set(manifest_files) == actual_files
        and all(
            (run_dir / path).stat().st_size == row["bytes"]
            and sha256(run_dir / path) == row["sha256"]
            for path, row in manifest_files.items()
        ),
        "no_credential_material": not any(
            CREDENTIAL.search(path.read_bytes())
            for path in run_dir.rglob("*")
            if path.is_file()
        ),
    }
    result = {
        "experiment": "4-4",
        "campaign_id": run_dir.name,
        "passed": all(gates.values()),
        "gates": gates,
        "counts": {
            "mcp_tool_calls": len(receipts),
            "model_receipts": len(model_receipts),
            "manifest_files": len(manifest_files),
            "human_response_seconds": round(elapsed, 3),
        },
        "remaining_blockers": summary.get("blockers"),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
