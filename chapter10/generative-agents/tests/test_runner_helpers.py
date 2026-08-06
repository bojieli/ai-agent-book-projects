from __future__ import annotations

import gzip
import json

import pytest

from action_arena_compat import normalize_action_arena
from run_campaign import (
    CUSTOM_CURRENTLY,
    ValidatedZero,
    normalize_task_decomp_response,
    quarantine_artifact,
    receipt_summary,
    safe_task_decomp_generate,
    validated_receipt_summary,
)


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
        "transport_retries": 0,
        "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
        "provider_latency_seconds": 1.75,
    }


def test_custom_goal_is_specific_and_time_bounded():
    assert "climate-resilience workshop" in CUSTOM_CURRENTLY
    assert "February 14th, 2023" in CUSTOM_CURRENTLY
    assert "5pm to 7pm" in CUSTOM_CURRENTLY


def test_validated_zero_is_numeric_but_not_the_false_sentinel():
    value = ValidatedZero()

    assert value == 0
    assert value != False  # noqa: E712 - verifies the upstream comparison exactly
    assert int(value) == 0
    assert json.dumps({"poignancy": value}) == '{"poignancy": 0}'


def test_task_decomp_normalization_discards_prose_and_bounds_duration():
    prompt = "Describe subtasks in 5 min increments. (total duration in minutes 10):"
    response = """The prompt is contradictory.
1) Wolfgang is resting. (duration in minutes: 5, minutes left: 5)
2) Wolfgang is resting. (duration in minutes: 5, minutes left: 0)
Here is an alternative.
1) Wolfgang is studying. (duration in minutes: 10, minutes left: 0)"""

    assert normalize_task_decomp_response(response, prompt) == (
        "1) Wolfgang is resting. (duration in minutes: 5, minutes left: 5)\n"
        "2) Wolfgang is resting. (duration in minutes: 5, minutes left: 0)"
    )


def test_task_decomp_generation_cleans_malformed_response_without_requery():
    calls = 0
    prompt = "Describe subtasks in 5 min increments. (total duration in minutes 10):"
    response = """Commentary.
1) Wolfgang is resting. (duration in minutes: 5, minutes left: 5)
2) Wolfgang is resting. (duration in minutes: 5, minutes left: 0)"""

    def request(prompt, parameters):
        nonlocal calls
        calls += 1
        return response

    def clean_up(value, prompt):
        if value.startswith("Commentary"):
            raise IndexError("missing duration")
        return value.splitlines()

    result = safe_task_decomp_generate(
        request, prompt, {}, 5, ["asleep"], lambda value, prompt: value, clean_up
    )

    assert len(result) == 2
    assert calls == 1


def test_task_decomp_generation_raises_after_five_unparseable_responses():
    calls = 0

    def request(prompt, parameters):
        nonlocal calls
        calls += 1
        return "unstructured prose"

    def clean_up(value, prompt):
        raise ValueError("invalid duration")

    with pytest.raises(ValueError, match="invalid duration"):
        safe_task_decomp_generate(
            request,
            "Describe subtasks in 5 min increments. (total duration in minutes 60):",
            {},
            5,
            ["asleep"],
            lambda value, prompt: value,
            clean_up,
        )

    assert calls == 5


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


def test_provider_error_checkpoint_is_quarantined_with_compatibility_receipt(tmp_path):
    receipt = tmp_path / "steps_00000_00360.jsonl.gz"
    with gzip.open(receipt, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "kind": "chat",
                    "success": False,
                    "latency_seconds": 1,
                    "response": None,
                }
            )
            + "\n"
        )
    compatibility = tmp_path / "steps_00000_00360.jsonl"
    compatibility.write_text("{}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="provider errors make checkpoint"):
        validated_receipt_summary(receipt, compatibility)

    assert not receipt.exists()
    assert not compatibility.exists()
    assert len(list(tmp_path.glob("steps_00000_00360.failed-*.jsonl.gz"))) == 1
    assert len(list(tmp_path.glob("steps_00000_00360.failed-*.jsonl"))) == 1


def test_quarantine_preserves_non_receipt_suffix(tmp_path):
    artifact = tmp_path / "state.bin"
    artifact.write_bytes(b"state")
    target = quarantine_artifact(artifact)
    assert target is not None
    assert target.read_bytes() == b"state"
    assert target.name.startswith("state.bin.failed-")
