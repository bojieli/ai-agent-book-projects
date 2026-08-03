from __future__ import annotations

import gzip
import json

from run_campaign import CUSTOM_CURRENTLY, receipt_summary


def test_receipt_summary_counts_calls_usage_and_errors(tmp_path):
    path = tmp_path / "receipts.jsonl.gz"
    rows = [
        {
            "kind": "chat",
            "success": True,
            "latency_seconds": 1.25,
            "response": {"usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6}},
        },
        {
            "kind": "embedding",
            "success": False,
            "latency_seconds": 0.5,
            "response": None,
        },
    ]
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    assert receipt_summary(path) == {
        "calls": 2,
        "by_kind": {"chat": 1, "embedding": 1},
        "errors": 1,
        "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
        "provider_latency_seconds": 1.75,
    }


def test_custom_goal_is_specific_and_time_bounded():
    assert "climate-resilience workshop" in CUSTOM_CURRENTLY
    assert "February 14th, 2023" in CUSTOM_CURRENTLY
    assert "5pm to 7pm" in CUSTOM_CURRENTLY

