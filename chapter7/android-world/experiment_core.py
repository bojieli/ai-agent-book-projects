"""Pure reporting helpers for the Experiment 6-11 AndroidWorld loop.

The runtime runner deliberately keeps AndroidWorld imports out of this module so
the evidence checks and report generation can be tested without an emulator.
"""

from __future__ import annotations

from collections import defaultdict
import json
import re
from typing import Any, Iterable, Mapping


BASELINE_TASK_COUNT = 116
WIFI_TASKS = (
    "SystemWifiTurnOff",
    "SystemWifiTurnOffVerify",
    "SystemWifiTurnOn",
    "SystemWifiTurnOnVerify",
)

_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|secret)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\b(?:sk|ak)-[A-Za-z0-9_-]{12,}\b"),
)


def redact_text(value: object, secrets: Iterable[str] = ()) -> str:
  """Returns a printable error/message with likely credentials removed."""
  text = str(value)
  for secret in secrets:
    if secret:
      text = text.replace(secret, "[REDACTED]")
  text = _SECRET_PATTERNS[0].sub(r"\1[REDACTED]", text)
  text = _SECRET_PATTERNS[1].sub(r"\1[REDACTED]", text)
  text = _SECRET_PATTERNS[2].sub("[REDACTED]", text)
  return text


def _mean(values: Iterable[float]) -> float | None:
  items = list(values)
  if not items:
    return None
  return round(sum(items) / len(items), 6)


def aggregate_episodes(episodes: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
  """Aggregates real episode records by arm."""
  groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
  for episode in episodes:
    groups[str(episode["arm"])].append(episode)

  output: dict[str, dict[str, Any]] = {}
  for arm, rows in sorted(groups.items()):
    completed = [row for row in rows if row.get("status") == "completed"]
    output[arm] = {
        "episodes": len(rows),
        "completed_episodes": len(completed),
        "error_episodes": len(rows) - len(completed),
        "successes": sum(bool(row.get("success")) for row in completed),
        "success_rate": _mean(float(bool(row.get("success"))) for row in completed),
        "mean_evaluator_reward": _mean(
            float(row.get("evaluator_reward", 0.0)) for row in completed
        ),
        "mean_steps": _mean(float(row.get("steps", 0)) for row in completed),
        "mean_latency_s": _mean(
            float(row.get("elapsed_s", 0.0)) for row in completed
        ),
        "mean_llm_calls": _mean(
            float(row.get("llm", {}).get("calls", 0)) for row in completed
        ),
        "mean_llm_latency_s": _mean(
            float(row.get("llm", {}).get("latency_s", 0.0)) for row in completed
        ),
        "mean_total_tokens": _mean(
            float(row.get("llm", {}).get("input_tokens", 0))
            + float(row.get("llm", {}).get("output_tokens", 0))
            for row in completed
        ),
        "total_input_tokens": sum(
            int(row.get("llm", {}).get("input_tokens", 0)) for row in completed
        ),
        "total_output_tokens": sum(
            int(row.get("llm", {}).get("output_tokens", 0)) for row in completed
        ),
        "total_tokens": sum(
            int(row.get("llm", {}).get("input_tokens", 0))
            + int(row.get("llm", {}).get("output_tokens", 0))
            for row in completed
        ),
        "estimated_cost_usd": round(
            sum(
                float(row.get("llm", {}).get("estimated_cost_usd", 0.0))
                for row in completed
            ),
            9,
        ),
    }
  return output


def paired_rows(episodes: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
  """Builds paired control/treatment comparisons without inventing missing arms."""
  groups: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
  for episode in episodes:
    if episode.get("arm") in ("control", "treatment"):
      groups[str(episode["pair_id"])][str(episode["arm"])] = episode

  rows = []
  for pair_id, arms in sorted(groups.items()):
    if set(arms) != {"control", "treatment"}:
      continue
    control = arms["control"]
    treatment = arms["treatment"]
    if control.get("status") != "completed" or treatment.get("status") != "completed":
      continue
    rows.append({
        "pair_id": pair_id,
        "task": control["task"],
        "trial": control["trial"],
        "control_success": bool(control.get("success")),
        "treatment_success": bool(treatment.get("success")),
        "success_delta": int(bool(treatment.get("success"))) - int(bool(control.get("success"))),
        "control_reward": float(control.get("evaluator_reward", 0.0)),
        "treatment_reward": float(treatment.get("evaluator_reward", 0.0)),
        "reward_delta": round(
            float(treatment.get("evaluator_reward", 0.0))
            - float(control.get("evaluator_reward", 0.0)),
            6,
        ),
        "control_steps": int(control.get("steps", 0)),
        "treatment_steps": int(treatment.get("steps", 0)),
        "control_latency_s": float(control.get("elapsed_s", 0.0)),
        "treatment_latency_s": float(treatment.get("elapsed_s", 0.0)),
    })
  return rows


def choose_decision(
    arm_summary: Mapping[str, Mapping[str, Any]],
    pairs: Iterable[Mapping[str, Any]],
    *,
    minimum_pairs: int = 4,
    maximum_latency_ratio: float = 1.5,
    maximum_token_ratio: float = 1.5,
) -> dict[str, Any]:
  """Makes a conservative success/cost candidate decision from paired evidence."""
  pair_list = list(pairs)
  control = arm_summary.get("control")
  treatment = arm_summary.get("treatment")
  if not control or not treatment or len(pair_list) < minimum_pairs:
    return {
        "outcome": "insufficient_evidence",
        "promote_to_full_suite_candidate": False,
        "deployment_approved": False,
        "reason": f"Need at least {minimum_pairs} completed pairs; observed {len(pair_list)}.",
    }

  improvement_count = sum(int(row["success_delta"]) for row in pair_list)
  regressions = sum(row["success_delta"] < 0 for row in pair_list)
  control_latency = control.get("mean_latency_s")
  treatment_latency = treatment.get("mean_latency_s")
  latency_ratio = None
  if control_latency and treatment_latency is not None:
    latency_ratio = round(float(treatment_latency) / float(control_latency), 6)
  control_tokens = control.get("mean_total_tokens")
  treatment_tokens = treatment.get("mean_total_tokens")
  token_ratio = None
  if control_tokens and treatment_tokens is not None:
    token_ratio = round(float(treatment_tokens) / float(control_tokens), 6)
  control_calls = control.get("mean_llm_calls")
  treatment_calls = treatment.get("mean_llm_calls")
  call_ratio = None
  if control_calls and treatment_calls is not None:
    call_ratio = round(float(treatment_calls) / float(control_calls), 6)

  acceptable_cost = (
      latency_ratio is not None
      and token_ratio is not None
      and latency_ratio <= maximum_latency_ratio
      and token_ratio <= maximum_token_ratio
  )

  if improvement_count > 0 and regressions == 0 and acceptable_cost:
    outcome = "promote_candidate_to_full_suite_rerun"
    promote = True
    reason = (
        f"Treatment improved {improvement_count} net paired task(s) with no paired regression. "
        "This is a candidate decision, not deployment approval or a full-suite result."
    )
  elif improvement_count > 0 and regressions == 0:
    outcome = "restrict_candidate_due_to_cost"
    promote = False
    reason = (
        "Treatment improved paired success without regressions, but exceeded the "
        f"latency/token guardrails ({maximum_latency_ratio:.2f}x / "
        f"{maximum_token_ratio:.2f}x). Restrict it to targeted follow-up; do not "
        "promote it to the full suite yet."
    )
  elif improvement_count < 0 or regressions:
    outcome = "reject_candidate"
    promote = False
    reason = (
        f"Treatment has {regressions} paired regression(s) and net success delta "
        f"{improvement_count}; do not promote."
    )
  else:
    outcome = "inconclusive_no_success_gain"
    promote = False
    reason = "Treatment produced no paired success gain; keep the upstream control prompt."

  return {
      "outcome": outcome,
      "promote_to_full_suite_candidate": promote,
      "deployment_approved": False,
      "reason": reason,
      "completed_pairs": len(pair_list),
      "net_success_delta": improvement_count,
      "paired_regressions": regressions,
      "mean_latency_ratio_treatment_over_control": latency_ratio,
      "mean_token_ratio_treatment_over_control": token_ratio,
      "mean_llm_call_ratio_treatment_over_control": call_ratio,
      "guardrails": {
          "maximum_latency_ratio": maximum_latency_ratio,
          "maximum_token_ratio": maximum_token_ratio,
          "passed": acceptable_cost,
      },
      "scope_recommendation": (
          "full_suite_candidate_only" if promote else "do_not_deploy"
      ),
  }


def choose_efficiency_decision(
    arm_summary: Mapping[str, Mapping[str, Any]],
    pairs: Iterable[Mapping[str, Any]],
    *,
    minimum_pairs: int = 4,
    maximum_latency_ratio: float = 1.5,
    maximum_token_ratio: float = 0.75,
) -> dict[str, Any]:
  """Promotes a cost refinement only when H5 success is preserved and cost falls."""
  pair_list = list(pairs)
  control = arm_summary.get("control")
  treatment = arm_summary.get("treatment")
  if not control or not treatment or len(pair_list) < minimum_pairs:
    return {
        "outcome": "insufficient_evidence",
        "promote_to_full_suite_candidate": False,
        "deployment_approved": False,
        "reason": f"Need at least {minimum_pairs} completed pairs; observed {len(pair_list)}.",
    }

  net_success_delta = sum(int(row["success_delta"]) for row in pair_list)
  regressions = sum(row["success_delta"] < 0 for row in pair_list)
  treatment_successes = sum(bool(row["treatment_success"]) for row in pair_list)
  required_treatment_successes = len(pair_list)
  success_preserved = treatment_successes == required_treatment_successes
  control_latency = control.get("mean_latency_s")
  treatment_latency = treatment.get("mean_latency_s")
  latency_ratio = (
      round(float(treatment_latency) / float(control_latency), 6)
      if control_latency and treatment_latency is not None else None
  )
  control_tokens = control.get("mean_total_tokens")
  treatment_tokens = treatment.get("mean_total_tokens")
  token_ratio = (
      round(float(treatment_tokens) / float(control_tokens), 6)
      if control_tokens and treatment_tokens is not None else None
  )
  control_calls = control.get("mean_llm_calls")
  treatment_calls = treatment.get("mean_llm_calls")
  call_ratio = (
      round(float(treatment_calls) / float(control_calls), 6)
      if control_calls and treatment_calls is not None else None
  )
  passed = (
      regressions == 0
      and net_success_delta >= 0
      and success_preserved
      and latency_ratio is not None
      and token_ratio is not None
      and latency_ratio <= maximum_latency_ratio
      and token_ratio <= maximum_token_ratio
  )
  if passed:
    outcome = "promote_efficient_candidate_to_full_suite_rerun"
    reason = (
        "Treatment preserved paired success with no regression and passed the "
        "latency/token efficiency guardrails. This is a candidate decision only."
    )
  elif not success_preserved or regressions or net_success_delta < 0:
    outcome = "reject_efficiency_candidate_due_to_regression"
    reason = (
        f"Treatment succeeded on {treatment_successes}/{required_treatment_successes} "
        f"completed pairs, with {regressions} paired regression(s) and net success "
        f"delta {net_success_delta}; it did not preserve the H5 success baseline."
    )
  else:
    outcome = "reject_efficiency_candidate_due_to_cost"
    reason = (
        "Treatment preserved success but did not reduce tokens to the required "
        f"{maximum_token_ratio:.2f}x ratio within the latency guardrail."
    )
  return {
      "outcome": outcome,
      "promote_to_full_suite_candidate": passed,
      "deployment_approved": False,
      "reason": reason,
      "completed_pairs": len(pair_list),
      "net_success_delta": net_success_delta,
      "paired_regressions": regressions,
      "treatment_successes": treatment_successes,
      "required_treatment_successes": required_treatment_successes,
      "success_preservation_passed": success_preserved,
      "mean_latency_ratio_treatment_over_control": latency_ratio,
      "mean_token_ratio_treatment_over_control": token_ratio,
      "mean_llm_call_ratio_treatment_over_control": call_ratio,
      "guardrails": {
          "objective": "success_noninferiority_and_token_reduction",
          "require_all_treatment_pairs_successful": True,
          "maximum_latency_ratio": maximum_latency_ratio,
          "maximum_token_ratio": maximum_token_ratio,
          "passed": passed,
      },
      "scope_recommendation": (
          "full_suite_candidate_only" if passed else "do_not_deploy"
      ),
  }


def enforce_scope_claims(evidence: dict[str, Any]) -> None:
  """Sets completion gates from direct episode evidence, never from counters."""
  scope = evidence.setdefault("scope", {})
  distinct_tasks = len(set(scope.get("tasks", [])))
  configured_trials = int(scope.get("trials_per_task", 0))
  mode = scope.get("mode")
  tasks = list(dict.fromkeys(str(task) for task in scope.get("tasks", [])))
  expected_episode_keys = {
      (task, trial)
      for task in tasks
      for trial in range(1, configured_trials + 1)
  }
  episodes = evidence.get("episodes", [])
  actual_episode_keys = {
      (str(row.get("task")), int(row.get("trial", 0))) for row in episodes
  }
  direct_episode_gate = (
      len(episodes) == len(expected_episode_keys)
      and actual_episode_keys == expected_episode_keys
      and all(
          row.get("arm") == "candidate"
          and row.get("status") == "completed"
          and row.get("evaluator_reward") is not None
          and isinstance(row.get("pair_seed"), int)
          for row in episodes
      )
      and all(
          len({
              row["pair_seed"] for row in episodes if row.get("task") == task
          }) == configured_trials
          for task in tasks
      )
  )
  full_suite = (
      mode == "candidate_rerun"
      and distinct_tasks == BASELINE_TASK_COUNT
      and configured_trials >= 5
      and direct_episode_gate
      and evidence.get("environment", {}).get("api_level") == 33
      and evidence.get("environment", {}).get("emulator_setup_completed") is True
      and evidence.get("environment", {})
      .get("app_provisioning", {})
      .get("complete")
  )
  scope["direct_episode_gate_completed"] = direct_episode_gate
  scope["full_suite_completed"] = full_suite
  scope["manuscript_five_seed_gate_completed"] = full_suite
  evidence["experiment_complete"] = bool(
      full_suite and evidence.get("decision", {}).get("source_paired_run_id")
  )


def _fmt(value: Any) -> str:
  if value is None:
    return "n/a"
  if isinstance(value, float):
    return f"{value:.3f}"
  return str(value)


def render_report(evidence: Mapping[str, Any]) -> str:
  """Renders the five-stage report from machine-readable evidence."""
  scope = evidence["scope"]
  environment = evidence["environment"]
  arm_summary = evidence.get("arm_summary", {})
  decision = evidence.get("decision", {})
  pairs = evidence.get("paired_comparison", [])
  blockers = evidence.get("environment_boundaries", [])
  hypotheses = evidence.get("diagnosis", {}).get("layered_hypotheses", [])
  phase = evidence.get("phase", {})
  llm_analysis = evidence.get("llm_analysis", {})
  controls = (
      "same checkout, model, task parameters, generated seed policy, step budget, "
      "Pixel 6/API-33 device class, upstream setup, and app versions across isolated shards."
      if environment.get("shard_devices")
      else "same checkout, model, task parameters, generated seed, step budget, and "
      "emulator; arm order alternates by pair."
  )

  lines = [
      "# Experiment 6-11 AndroidWorld iteration report",
      "",
      f"- Run ID: `{evidence['run_id']}`",
      f"- Generated (UTC): `{evidence['generated_at_utc']}`",
      f"- Upstream commit: `{environment.get('android_world_commit', 'not reached')}`",
      f"- Device: `{environment.get('device_model', 'not reached')}`, API "
      f"`{environment.get('api_level', 'not reached')}` (upstream tested reference: API "
      f"`{environment.get('upstream_tested_api_level', 33)}`)",
      f"- Observation method: `{environment.get('a11y_method', 'a11y_forwarder_app')}`",
      f"- Provider/model: `{evidence['model']['provider']}` / `{evidence['model']['model']}`",
      f"- Model source/runtime: `{evidence['model'].get('source', 'not recorded')}` / "
      f"`{evidence['model'].get('runtime', 'not recorded')}`",
      f"- Accelerator: `{evidence['model'].get('accelerator', 'not recorded')}`",
      f"- Required apps: "
      f"`{environment.get('app_provisioning', {}).get('installed_required_package_count', 'not reached')}/"
      f"{environment.get('app_provisioning', {}).get('required_package_count', 'not reached')}`",
      f"- Scope: {len(scope['tasks'])} task(s), {scope['trials_per_task']} trial(s), "
      f"mode `{scope['mode']}`",
      f"- Full 116-task × 5-seed suite completed: **{str(scope['full_suite_completed']).lower()}**",
      "",
      "The bundled ~88% baseline is historical input evidence. The manuscript's 88%→94% "
      "numbers are explicitly hypothetical and are not used as rerun results here.",
      "",
      "## 1. Diagnose",
      "",
  ]
  for item in evidence["diagnosis"]["findings"]:
    lines.append(f"- {item}")

  lines.extend([
      "",
      "## 2. Hypothesis",
      "",
      "The diagnosis produced explicit surface, middle, and deep hypotheses. Only one "
      "variable is changed in this run; the other hypotheses remain untested.",
      "",
      "| Layer / ID | Proposed change | Target | Verification | Status |",
      "| --- | --- | --- | --- | --- |",
  ])
  for row in hypotheses:
    lines.append(
        f"| {row.get('layer', 'n/a')} / `{row.get('id', 'n/a')}` | "
        f"{row.get('idea', 'n/a')} | {row.get('target', 'n/a')} | "
        f"{row.get('verification', 'n/a')} | {row.get('status', 'not tested')} |"
    )

  lines.extend([
      "",
      f"Selected hypothesis: `{evidence['hypothesis']['id']}`",
      f"- Change: {evidence['hypothesis']['change']}",
      f"- Expected measurable result: {evidence['hypothesis']['expected_result']}",
      f"- Guardrails: {evidence['hypothesis']['guardrails']}",
      "",
      "## 3. Controlled experiment",
      "",
      f"- Phase: `{phase.get('id', 'phase_1_surface')}` — "
      f"{phase.get('description', 'low-cost surface prompt ablation')}",
      f"- Independent variable: {phase.get('independent_variable', 'task-specific T3A guidelines')}",
      f"- Controls: {controls}",
      "",
      "| Arm | Episodes | Success | Reward | Steps | Latency (s) | LLM calls | Mean tokens | Input / output tokens | Est. cost (USD) |",
      "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
  ])
  for arm, row in sorted(arm_summary.items()):
    lines.append(
        f"| {arm} | {row['completed_episodes']}/{row['episodes']} | "
        f"{_fmt(row['success_rate'])} | {_fmt(row['mean_evaluator_reward'])} | "
        f"{_fmt(row['mean_steps'])} | {_fmt(row['mean_latency_s'])} | "
        f"{_fmt(row['mean_llm_calls'])} | {_fmt(row.get('mean_total_tokens'))} | "
        f"{row['total_input_tokens']} / {row['total_output_tokens']} | "
        f"{row.get('estimated_cost_usd', 0.0):.6f} |"
    )

  if pairs:
    lines.extend([
        "",
        "| Task / trial | Control | Treatment | Δ success | Control→treatment steps |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for row in pairs:
      lines.append(
          f"| {row['task']} / {row['trial']} | {int(row['control_success'])} | "
          f"{int(row['treatment_success'])} | {row['success_delta']:+d} | "
          f"{row['control_steps']}→{row['treatment_steps']} |"
      )

  lines.extend([
      "",
      "## 4. Data-driven decision",
      "",
      f"- Outcome: **`{decision.get('outcome', 'not_applicable')}`**",
      f"- Reason: {decision.get('reason', 'This artifact is a candidate rerun, not a paired decision run.')}",
      f"- Treatment/control mean latency ratio: "
      f"{_fmt(decision.get('mean_latency_ratio_treatment_over_control'))}",
      f"- Treatment/control mean token ratio: "
      f"{_fmt(decision.get('mean_token_ratio_treatment_over_control'))}",
      f"- Treatment/control mean LLM-call ratio: "
      f"{_fmt(decision.get('mean_llm_call_ratio_treatment_over_control'))}",
      f"- Cost guardrails passed: **{str(decision.get('guardrails', {}).get('passed', False)).lower()}**",
      f"- Deployment approved: **{str(decision.get('deployment_approved', False)).lower()}**",
      "",
      "## 5. Rerun and next report",
      "",
  ])
  if scope["full_suite_completed"]:
    lines.append(
        "The complete 116-task, five-trial candidate rerun gate is satisfied by direct episode evidence."
    )
  else:
    lines.append(
        "This run is a real controlled subset/smoke rerun, not the complete AndroidWorld benchmark. "
        "The next gate is a conditionally enabled candidate rerun over all 116 tasks with five "
        "seeds after provisioning the upstream API-33 app environment."
    )
  failed = [
      episode for episode in evidence.get("episodes", [])
      if episode.get("status") != "completed" or not episode.get("success")
  ]
  if failed:
    lines.append("")
    lines.append("Observed residual failures:")
    for episode in failed:
      if episode.get("error"):
        detail = episode["error"]
      elif episode.get("evaluator_reward") == 1.0 and not episode.get("agent_declared_done"):
        detail = "final evaluator state passed, but the agent never declared completion"
      elif episode.get("agent_declared_done") and episode.get("evaluator_reward") != 1.0:
        detail = "agent declared completion, but the real evaluator state failed"
      else:
        detail = "evaluator reward / completion gate was not satisfied"
      lines.append(f"- `{episode['arm']} / {episode['task']} / trial {episode['trial']}`: {detail}")

  lines.extend(["", "### LLM analysis of this run", ""])
  if llm_analysis.get("status") == "completed":
    lines.append(
        "The following bounded interpretation was produced by the configured real LLM from "
        "the aggregate evidence (the JSON remains authoritative):"
    )
    lines.append("")
    lines.append(f"- Summary: {llm_analysis.get('summary', 'n/a')}")
    lines.append(
        f"- Cost/benefit interpretation: {llm_analysis.get('cost_benefit_interpretation', 'n/a')}"
    )
    for item in llm_analysis.get("observed_failure_pattern", []):
      lines.append(f"- Residual pattern: {item}")
    next_hypothesis = llm_analysis.get("next_hypothesis", {})
    if next_hypothesis:
      lines.append(
          f"- Next hypothesis `{next_hypothesis.get('id', 'n/a')}` "
          f"({next_hypothesis.get('layer', 'n/a')}): {next_hypothesis.get('idea', 'n/a')} "
          f"Target: {next_hypothesis.get('target', 'n/a')} Verification: "
          f"{next_hypothesis.get('verification', 'n/a')}"
      )
  else:
    lines.append(
        f"No LLM analysis was accepted: {llm_analysis.get('error', 'analysis was not requested for this artifact')}"
    )

  lines.extend(["", "## Environment boundaries", ""])
  if blockers:
    lines.extend(f"- {item}" for item in blockers)
  else:
    lines.append("- None recorded.")
  lines.extend([
      "",
      "The JSON beside this report is the authoritative evidence. It contains episode-level "
      "evaluator rewards, actions, timing, token counts, configuration, and explicit completion gates; "
      "credentials and raw prompts are not stored.",
      "",
  ])
  return "\n".join(lines)


def dumps_json(evidence: Mapping[str, Any]) -> str:
  return json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
