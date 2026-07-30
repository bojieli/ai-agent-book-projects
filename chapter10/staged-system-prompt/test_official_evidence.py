"""Focused structural tests for the strict Experiment 10-1 evidence path."""

from agent import STAGE_PROMPTS, STAGE_TOOLS
from run_official_experiment import usage_cost, validate_manifest


def test_stage_contracts_are_distinct_and_tool_gated():
    assert len(set(STAGE_PROMPTS.values())) == 3
    names = {
        stage: {tool["function"]["name"] for tool in tools}
        for stage, tools in STAGE_TOOLS.items()
    }
    assert "write_file" not in names["requirements"]
    assert "approve_code" not in names["implementation"]
    assert "write_file" not in names["review"]


def test_usage_cost_uses_observed_cache_split():
    value = usage_cost(
        {"prompt_tokens": 1000, "cached_prompt_tokens": 400,
         "completion_tokens": 100, "requests": 2},
        {"uncached_input_per_million": 20.0, "cached_input_per_million": 2.0,
         "output_per_million": 100.0, "currency": "CNY", "as_of": "x", "source_url": "u"},
    )
    assert value["uncached_prompt_tokens"] == 600
    assert value["cost"] == 0.0228


def test_validator_requires_real_rollback_and_reentry():
    manifest = {
        "protocol": {"value": {"required_transitions": [
            "to_implementation", "to_review", "request_revision", "to_review", "approve"]}},
        "result": {"approved": True, "completion_reason": "approved", "revision_count": 1,
                   "transition_events": [{"kind": x} for x in [
                       "to_implementation", "to_review", "request_revision", "to_review", "approve"]],
                   "stage_entries": [{"stage": x} for x in [
                       "requirements", "implementation", "review", "implementation", "review"]]},
        "provider_receipts": [{"response_id": "id", "usage_complete": True, "provider": "moonshot"}],
        "usage_and_cost": {"requests": 1},
        "execution_logs": [{"action": x} for x in [
            "run_linter", "run_tests", "analyze_complexity", "审查不通过 -> 回退实现"]],
        "workspace": {"files": {"x.py": {}}},
    }
    assert validate_manifest(manifest) == []
