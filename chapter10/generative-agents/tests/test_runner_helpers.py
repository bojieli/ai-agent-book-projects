from __future__ import annotations

import gzip
import json

from action_arena_compat import normalize_action_arena
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


def test_action_arena_strips_legacy_leading_brace():
    allowed = ["common room", "Tom and Jane Moreno's bedroom", "kitchen"]
    result = normalize_action_arena(
        "{Tom and Jane Moreno's bedroom}", allowed, "common room"
    )
    assert result.value == "Tom and Jane Moreno's bedroom"
    assert result.reason == "stripped_response_wrappers"
    assert result.fallback is False


def test_action_arena_matches_case_insensitively_to_exact_allowed_value():
    allowed = ["common room", "Tom and Jane Moreno's bedroom", "kitchen"]
    result = normalize_action_arena(
        "  {TOM AND JANE MORENO'S BEDROOM}  ", allowed, "common room"
    )
    assert result.value == "Tom and Jane Moreno's bedroom"
    assert result.reason == "case_insensitive_exact_match"
    assert result.fallback is False


def test_action_arena_invalid_output_falls_back_only_within_accessible_arenas():
    allowed = ["common room", "kitchen"]
    current_result = normalize_action_arena("private vault", allowed, "kitchen")
    assert current_result.value == "kitchen"
    assert current_result.value in allowed
    assert current_result.fallback is True

    first_result = normalize_action_arena("private vault", allowed, "bedroom")
    assert first_result.value == "common room"
    assert first_result.value in allowed
    assert first_result.fallback is True
