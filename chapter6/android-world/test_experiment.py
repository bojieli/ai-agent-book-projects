"""Focused, offline checks for Experiment 6-11 evidence/reporting."""

from __future__ import annotations

from argparse import Namespace
import sqlite3

import pytest

from experiment_core import (
    BASELINE_TASK_COUNT,
    aggregate_episodes,
    choose_decision,
    choose_efficiency_decision,
    enforce_scope_claims,
    paired_rows,
    redact_text,
    render_report,
)
from run_controlled_experiment import (
    _context_safe_output_cap,
    _missing_retro_queue_as_empty,
    _read_nonempty_with_retry,
    _retry_clipper_foreground,
    _truncate_current_ui_section,
    _validate_resume_evidence,
)


def _episode(arm: str, task: str, success: bool, latency: float) -> dict:
  return {
      "pair_id": task + ":trial-1",
      "task": task,
      "trial": 1,
      "arm": arm,
      "status": "completed",
      "success": success,
      "evaluator_reward": float(success),
      "steps": 3 if success else 10,
      "elapsed_s": latency,
      "llm": {"calls": 4, "input_tokens": 100, "output_tokens": 20},
  }


def test_redaction_covers_explicit_and_pattern_credentials() -> None:
  secret = "definitely-not-for-output"
  text = redact_text(
      f"api_key={secret} Authorization: Bearer abcdefghijk sk-example123456789",
      [secret],
  )
  assert secret not in text
  assert "abcdefghijk" not in text
  assert "sk-example123456789" not in text
  assert text.count("[REDACTED]") >= 3


def test_retro_missing_queue_schema_becomes_empty_observation() -> None:
  def missing_queue(_env: object) -> list[str]:
    raise sqlite3.OperationalError("no such table: playing_queue")

  assert _missing_retro_queue_as_empty(missing_queue)(object()) == []


def test_retro_compatibility_does_not_hide_other_sqlite_errors() -> None:
  def corrupt_database(_env: object) -> list[str]:
    raise sqlite3.OperationalError("database disk image is malformed")

  with pytest.raises(sqlite3.OperationalError, match="malformed"):
    _missing_retro_queue_as_empty(corrupt_database)(object())


def test_context_cap_keeps_headroom_for_provider_lower_bound() -> None:
  error = (
      "This model's maximum context length is 32768 tokens. However, you "
      "requested 1024 output tokens and your prompt contains at least 31745 "
      "input tokens."
  )
  assert _context_safe_output_cap(error, 1024) == 991
  assert _context_safe_output_cap("unrelated provider error", 1024) is None


def test_context_truncation_is_limited_to_middle_of_current_ui() -> None:
  prefix = "prefix and goal"
  ui = "A" * 9000 + "M" * 16384 + "Z" * 9000
  suffix = "guidance and output format"
  prompt = (
      prefix
      + "\n\nHere is a list of descriptions for some UI elements on the current screen:\n"
      + ui
      + "\nHere are some useful guidelines you need to follow:\n"
      + suffix
  )
  result = _truncate_current_ui_section(prompt)
  assert result is not None
  truncated, removed = result
  assert prefix in truncated and suffix in truncated
  assert "A" * 1000 in truncated and "Z" * 1000 in truncated
  assert removed > 0
  assert len(truncated) < len(prompt)


def test_context_truncation_handles_before_and_after_summary_ui() -> None:
  before = "B" * 12000
  after = "A" * 12000
  prompt = (
      "goal and summary rules\n"
      "Here is the description for the before screenshot:\n"
      + before
      + "\nHere is the description for the after screenshot:\n"
      + after
      + "\nThis is the action you picked: click\nBased on the reason: test"
  )
  result = _truncate_current_ui_section(prompt)
  assert result is not None
  truncated, removed = result
  assert "goal and summary rules" in truncated
  assert "This is the action you picked: click" in truncated
  assert "B" * 500 in truncated and "A" * 500 in truncated
  assert removed > 0


def test_sms_inbox_poll_preserves_empty_then_observed_result() -> None:
  reads = iter([[], [], ["Row: 0, address=123, body=hello"]])
  assert _read_nonempty_with_retry(
      lambda: next(reads), attempts=3, delay_s=0
  ) == ["Row: 0, address=123, body=hello"]


def test_clipper_retry_is_limited_to_exact_foreground_error() -> None:
  attempts = iter([
      RuntimeError(
          "Clipper app must be in the foreground to access clipboard. "
          "Additionally, app privileges must be granted manually."
      ),
      "clipboard value",
  ])

  def flaky_call() -> str:
    result = next(attempts)
    if isinstance(result, Exception):
      raise result
    return result

  assert _retry_clipper_foreground(flaky_call, delay_s=0) == "clipboard value"
  with pytest.raises(RuntimeError, match="unrelated"):
    _retry_clipper_foreground(
        lambda: (_ for _ in ()).throw(RuntimeError("unrelated")), delay_s=0
    )


def test_paired_comparison_and_conservative_candidate_decision() -> None:
  episodes = []
  for index in range(4):
    task = f"wifi-{index}"
    episodes.extend([
        _episode("control", task, index > 0, 10.0),
        _episode("treatment", task, True, 11.0),
    ])
  summary = aggregate_episodes(episodes)
  pairs = paired_rows(episodes)
  decision = choose_decision(summary, pairs)
  assert len(pairs) == 4
  assert decision["net_success_delta"] == 1
  assert decision["paired_regressions"] == 0
  assert decision["promote_to_full_suite_candidate"] is True
  assert decision["outcome"] == "promote_candidate_to_full_suite_rerun"


def test_subset_can_never_claim_full_suite_completion() -> None:
  evidence = {
      "scope": {
          "mode": "candidate_rerun",
          "tasks": ["a", "b", "c", "d"],
          "trials_per_task": 5,
          "completed_episodes": 20,
          "error_episodes": 0,
      },
      "decision": {"source_paired_run_id": "paired-real"},
  }
  enforce_scope_claims(evidence)
  assert evidence["scope"]["full_suite_completed"] is False
  assert evidence["experiment_complete"] is False


def test_full_suite_gate_requires_direct_116_by_5_evidence() -> None:
  tasks = [f"task-{index}" for index in range(BASELINE_TASK_COUNT)]
  episodes = [
      {
          "task": task,
          "trial": trial,
          "pair_seed": task_index * 1009 + trial,
          "arm": "candidate",
          "status": "completed",
          "evaluator_reward": 1.0,
      }
      for task_index, task in enumerate(tasks)
      for trial in range(1, 6)
  ]
  evidence = {
      "scope": {
          "mode": "candidate_rerun",
          "tasks": tasks,
          "trials_per_task": 5,
          "completed_episodes": BASELINE_TASK_COUNT * 5,
          "error_episodes": 0,
      },
      "episodes": episodes,
      "decision": {"source_paired_run_id": "paired-real"},
      "environment": {
          "api_level": 33,
          "emulator_setup_completed": True,
          "app_provisioning": {"complete": True},
      },
  }
  enforce_scope_claims(evidence)
  assert evidence["scope"]["full_suite_completed"] is True
  assert evidence["experiment_complete"] is True


def test_full_suite_gate_requires_reference_api_and_apps() -> None:
  tasks = [f"task-{index}" for index in range(BASELINE_TASK_COUNT)]
  episodes = [
      {
          "task": task,
          "trial": trial,
          "pair_seed": task_index * 1009 + trial,
          "arm": "candidate",
          "status": "completed",
          "evaluator_reward": 0.0,
      }
      for task_index, task in enumerate(tasks)
      for trial in range(1, 6)
  ]
  evidence = {
      "scope": {
          "mode": "candidate_rerun",
          "tasks": tasks,
          "trials_per_task": 5,
      },
      "episodes": episodes,
      "decision": {"source_paired_run_id": "paired-real"},
      "environment": {
          "api_level": 35,
          "emulator_setup_completed": False,
          "app_provisioning": {"complete": False},
      },
  }
  enforce_scope_claims(evidence)
  assert evidence["scope"]["direct_episode_gate_completed"] is True
  assert evidence["scope"]["full_suite_completed"] is False
  assert evidence["experiment_complete"] is False


def test_full_suite_gate_rejects_counters_without_direct_episodes() -> None:
  evidence = {
      "scope": {
          "mode": "candidate_rerun",
          "tasks": [f"task-{index}" for index in range(BASELINE_TASK_COUNT)],
          "trials_per_task": 5,
          "completed_episodes": BASELINE_TASK_COUNT * 5,
          "error_episodes": 0,
      },
      "episodes": [],
      "decision": {"source_paired_run_id": "paired-real"},
  }
  enforce_scope_claims(evidence)
  assert evidence["scope"]["direct_episode_gate_completed"] is False
  assert evidence["scope"]["full_suite_completed"] is False
  assert evidence["experiment_complete"] is False


def test_success_gain_over_cost_guardrail_is_not_promoted() -> None:
  episodes = []
  for index in range(4):
    task = f"wifi-{index}"
    control = _episode("control", task, index > 0, 10.0)
    treatment = _episode("treatment", task, True, 20.0)
    treatment["llm"]["input_tokens"] = 1000
    treatment["llm"]["output_tokens"] = 200
    episodes.extend([control, treatment])
  summary = aggregate_episodes(episodes)
  decision = choose_decision(summary, paired_rows(episodes))
  assert decision["outcome"] == "restrict_candidate_due_to_cost"
  assert decision["guardrails"]["passed"] is False
  assert decision["promote_to_full_suite_candidate"] is False
  assert decision["deployment_approved"] is False


def test_efficiency_refinement_can_promote_without_inventing_success_gain() -> None:
  episodes = []
  for index in range(4):
    task = f"wifi-{index}"
    control = _episode("control", task, True, 10.0)
    treatment = _episode("treatment", task, True, 9.0)
    treatment["llm"]["input_tokens"] = 40
    treatment["llm"]["output_tokens"] = 10
    episodes.extend([control, treatment])
  decision = choose_efficiency_decision(
      aggregate_episodes(episodes), paired_rows(episodes)
  )
  assert decision["net_success_delta"] == 0
  assert decision["paired_regressions"] == 0
  assert decision["guardrails"]["passed"] is True
  assert decision["promote_to_full_suite_candidate"] is True
  assert decision["deployment_approved"] is False


def test_efficiency_refinement_rejects_cheap_but_unsuccessful_treatment() -> None:
  episodes = []
  for index in range(4):
    task = f"wifi-{index}"
    control = _episode("control", task, False, 10.0)
    treatment = _episode("treatment", task, False, 9.0)
    treatment["llm"]["input_tokens"] = 40
    treatment["llm"]["output_tokens"] = 10
    episodes.extend([control, treatment])
  decision = choose_efficiency_decision(
      aggregate_episodes(episodes), paired_rows(episodes)
  )
  assert decision["mean_token_ratio_treatment_over_control"] < 0.75
  assert decision["success_preservation_passed"] is False
  assert decision["guardrails"]["passed"] is False
  assert decision["outcome"] == "reject_efficiency_candidate_due_to_regression"
  assert decision["promote_to_full_suite_candidate"] is False


def test_report_labels_historical_and_hypothetical_numbers() -> None:
  evidence = {
      "run_id": "test-run",
      "generated_at_utc": "2026-07-29T00:00:00Z",
      "environment": {
          "android_world_commit": "abc123",
          "device_model": "emulator",
          "api_level": 35,
          "upstream_tested_api_level": 33,
      },
      "model": {"provider": "real-provider", "model": "real-model"},
      "scope": {
          "tasks": ["SystemWifiTurnOn"],
          "trials_per_task": 1,
          "mode": "paired",
          "full_suite_completed": False,
      },
      "diagnosis": {"findings": ["Historical finding."]},
      "hypothesis": {
          "id": "H1",
          "change": "Add a task guideline.",
          "expected_result": "Improve paired reward.",
          "guardrails": "Same task and model.",
      },
      "arm_summary": {},
      "paired_comparison": [],
      "decision": {
          "outcome": "insufficient_evidence",
          "reason": "Need four pairs.",
      },
      "episodes": [],
      "environment_boundaries": ["API mismatch."],
      "llm_analysis": {
          "status": "completed",
          "summary": "Observed subset summary.",
          "observed_failure_pattern": ["One bounded residual pattern."],
          "cost_benefit_interpretation": "No deployment approval.",
          "next_hypothesis": {
              "id": "H5",
              "layer": "middle",
              "idea": "Test the input path.",
              "target": "One paired gain.",
              "verification": "Matched paired run.",
          },
      },
  }
  report = render_report(evidence)
  assert "historical input evidence" in report
  assert "explicitly hypothetical" in report
  assert "not the complete AndroidWorld benchmark" in report
  assert "Full 116-task × 5-seed suite completed: **false**" in report
  assert "Observed subset summary." in report
  assert "No deployment approval." in report


def test_resume_rejects_changed_configuration() -> None:
  evidence = {
      "experiment": "6-10",
      "hypothesis": {"id": "H5"},
      "scope": {
          "mode": "paired",
          "tasks": ["SystemWifiTurnOff"],
          "trials_per_task": 1,
          "max_steps": 10,
      },
      "model": {
          "model": "real-model",
          "seed": 42,
          "provider": "real-provider",
          "base_url": "https://provider.invalid/v1",
          "max_tokens": 1024,
      },
      "environment": {
          "skip_device_time": True,
          "device_serial": "emulator-5554",
          "grpc_port": 8554,
      },
      "episodes": [],
  }
  args = Namespace(
      tasks="SystemWifiTurnOff",
      hypothesis="H5",
      mode="paired",
      trials=1,
      max_steps=11,
      model="real-model",
      model_seed=42,
      provider="real-provider",
      base_url="https://provider.invalid/v1",
      max_model_tokens=1024,
      transition_pause=None,
      skip_device_time=True,
      console_port=5554,
      grpc_port=8554,
      seed=42,
  )
  with pytest.raises(RuntimeError, match="max_steps"):
    _validate_resume_evidence(evidence, args)


def test_resume_rejects_changed_pair_seed() -> None:
  evidence = {
      "experiment": "6-10",
      "hypothesis": {"id": "H5C"},
      "scope": {
          "mode": "paired",
          "tasks": ["SystemWifiTurnOff"],
          "trials_per_task": 1,
          "max_steps": 10,
      },
      "model": {
          "model": "real-model",
          "seed": 42,
          "provider": "real-provider",
          "base_url": "https://provider.invalid/v1",
          "max_tokens": 1024,
      },
      "environment": {
          "skip_device_time": True,
          "device_serial": "emulator-5554",
          "grpc_port": 8554,
      },
      "episodes": [{
          "task": "SystemWifiTurnOff",
          "trial": 1,
          "arm": "control",
          "pair_seed": 42,
      }],
  }
  args = Namespace(
      tasks="SystemWifiTurnOff",
      hypothesis="H5C",
      mode="paired",
      trials=1,
      max_steps=10,
      model="real-model",
      model_seed=42,
      provider="real-provider",
      base_url="https://provider.invalid/v1",
      max_model_tokens=1024,
      transition_pause=None,
      skip_device_time=True,
      console_port=5554,
      grpc_port=8554,
      seed=43,
  )
  with pytest.raises(RuntimeError, match="Resume seed mismatch"):
    _validate_resume_evidence(evidence, args)
