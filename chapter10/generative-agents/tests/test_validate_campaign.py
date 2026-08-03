from __future__ import annotations

from validate_campaign import (
    compatibility_correction_valid,
    positive_provider_usage,
)


def test_positive_provider_usage_ignores_nested_token_details():
    row = {
        "response": {
            "usage": {
                "prompt_tokens": 49,
                "prompt_tokens_details": {"cached_tokens": 0},
                "total_tokens": 69,
            }
        }
    }
    assert positive_provider_usage(row) is True


def test_compatibility_correction_must_resolve_to_accessible_arena():
    row = {
        "kind": "action_arena_compatibility_correction",
        "raw_output": "{Tom and Jane Moreno's bedroom",
        "normalized_output": "Tom and Jane Moreno's bedroom",
        "accessible_arenas": ["common room", "Tom and Jane Moreno's bedroom"],
        "reason": "stripped_response_wrappers",
        "fallback": False,
    }
    assert compatibility_correction_valid(row) is True
    row["normalized_output"] = "private vault"
    assert compatibility_correction_valid(row) is False
