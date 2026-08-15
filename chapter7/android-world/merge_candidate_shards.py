#!/usr/bin/env python3
"""Merge independently executed Experiment 6-11 trial shards without hiding failures."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from experiment_core import (
    BASELINE_TASK_COUNT,
    aggregate_episodes,
    dumps_json,
    enforce_scope_claims,
    paired_rows,
    render_report,
)
from run_controlled_experiment import (
    EXPERIMENT_ID,
    OpenAICompatibleLlm,
    _generate_llm_analysis,
    _utc_now,
)


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("shards", nargs="+", type=Path)
  parser.add_argument("--output-dir", type=Path, required=True)
  parser.add_argument("--source-paired-evidence", type=Path, required=True)
  parser.add_argument("--analysis-base-url")
  parser.add_argument("--analysis-api-key-env", default="LOCAL_API_KEY")
  parser.add_argument("--analysis-model")
  return parser.parse_args()


def _load(path: Path) -> dict[str, Any]:
  data = path.read_bytes()
  evidence = json.loads(data)
  if evidence.get("experiment") != EXPERIMENT_ID:
    raise RuntimeError(f"Not direct Experiment {EXPERIMENT_ID} evidence: {path}")
  return evidence


def _app_versions(evidence: dict[str, Any]) -> list[tuple[str, Any, Any]]:
  apps = evidence.get("environment", {}).get("app_provisioning", {}).get("apps", [])
  return sorted(
      (row.get("package"), row.get("version_code"), row.get("version_name"))
      for row in apps
  )


def main() -> int:
  args = _parse_args()
  if args.output_dir.exists():
    raise RuntimeError(f"Output directory already exists: {args.output_dir}")
  paths = [path.resolve() for path in args.shards]
  shards = [_load(path) for path in paths]
  if len(shards) < 2:
    raise RuntimeError("At least two independent shards are required")

  reference = shards[0]
  reference_tasks = reference.get("scope", {}).get("tasks", [])
  reference_trials = int(reference.get("scope", {}).get("trials_per_task", 0))
  if len(reference_tasks) != BASELINE_TASK_COUNT or reference_trials < 5:
    raise RuntimeError("Shards must declare the complete 116-task, five-trial scope")
  if reference.get("scope", {}).get("mode") != "candidate_rerun":
    raise RuntimeError("Only candidate-rerun shards can be merged")

  selected_trials: set[int] = set()
  episodes: list[dict[str, Any]] = []
  seen_keys: set[tuple[str, int, str]] = set()
  shard_rows = []
  reference_model = reference.get("model")
  reference_source = reference.get("decision", {}).get("source_paired_run_id")
  reference_versions = _app_versions(reference)
  merged_boundaries: list[str] = []
  merged_retry_history: list[dict[str, Any]] = []
  merged_parameter_drift: list[dict[str, Any]] = []
  merged_retry_parameter_drift: list[dict[str, Any]] = []
  for path, shard in zip(paths, shards):
    scope = shard.get("scope", {})
    if scope.get("tasks") != reference_tasks:
      raise RuntimeError(f"Task ordering differs in shard: {path}")
    if int(scope.get("trials_per_task", 0)) != reference_trials:
      raise RuntimeError(f"Trial scope differs in shard: {path}")
    if shard.get("model") != reference_model:
      raise RuntimeError(f"Model configuration differs in shard: {path}")
    if shard.get("decision", {}).get("source_paired_run_id") != reference_source:
      raise RuntimeError(f"Promoted paired source differs in shard: {path}")
    environment = shard.get("environment", {})
    if environment.get("api_level") != 33:
      raise RuntimeError(f"Shard is not on reference API 33: {path}")
    if environment.get("emulator_setup_completed") is not True:
      raise RuntimeError(f"Shard did not complete official emulator/app setup: {path}")
    if not environment.get("app_provisioning", {}).get("complete"):
      raise RuntimeError(f"Shard has an incomplete official app bundle: {path}")
    if _app_versions(shard) != reference_versions:
      raise RuntimeError(f"Official app versions differ in shard: {path}")
    if shard.get("credentials_persisted") is not False:
      raise RuntimeError(f"Shard does not attest credential-free evidence: {path}")
    shard_trials = {int(value) for value in scope.get("selected_trials", [])}
    if not shard_trials or selected_trials.intersection(shard_trials):
      raise RuntimeError(f"Missing or overlapping selected trials in shard: {path}")
    selected_trials.update(shard_trials)
    for episode in shard.get("episodes", []):
      trial = int(episode.get("trial", 0))
      key = (str(episode.get("task")), trial, str(episode.get("arm")))
      if trial not in shard_trials:
        raise RuntimeError(f"Episode lies outside its declared trial shard: {key}")
      if key in seen_keys:
        raise RuntimeError(f"Duplicate direct episode across shards: {key}")
      seen_keys.add(key)
      episodes.append(copy.deepcopy(episode))
    shard_rows.append({
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "run_id": shard.get("run_id"),
        "execution_shard": environment.get("execution_shard"),
        "selected_trials": sorted(shard_trials),
        "episodes": len(shard.get("episodes", [])),
        "completed_episodes": sum(
            row.get("status") == "completed" for row in shard.get("episodes", [])
        ),
        "error_episodes": sum(
            row.get("status") != "completed" for row in shard.get("episodes", [])
        ),
    })
    for boundary in shard.get("environment_boundaries", []):
      if boundary not in merged_boundaries:
        merged_boundaries.append(boundary)
    for retry in shard.get("retry_history", []):
      merged_retry_history.append({
          "execution_shard": environment.get("execution_shard"),
          **copy.deepcopy(retry),
      })
    for drift in shard.get("resume_parameter_drift", []):
      row = {
          "execution_shard": environment.get("execution_shard"),
          **copy.deepcopy(drift),
      }
      if row not in merged_parameter_drift:
        merged_parameter_drift.append(row)
    for drift in shard.get("retry_parameter_drift", []):
      row = {
          "execution_shard": environment.get("execution_shard"),
          **copy.deepcopy(drift),
      }
      if row not in merged_retry_parameter_drift:
        merged_retry_parameter_drift.append(row)

  expected_trials = set(range(1, reference_trials + 1))
  if selected_trials != expected_trials:
    raise RuntimeError(
        f"Shard trial union is {sorted(selected_trials)}; expected {sorted(expected_trials)}"
    )
  task_order = {task: index for index, task in enumerate(reference_tasks)}
  episodes.sort(key=lambda row: (task_order[str(row["task"])], int(row["trial"])))

  merged = copy.deepcopy(reference)
  merged["run_id"] = "exp6-11-merged-" + _utc_now().replace(":", "").replace("-", "")
  merged["generated_at_utc"] = _utc_now()
  merged["command"] = ["merge_candidate_shards.py", *map(str, paths)]
  merged["scope"]["selected_trials"] = sorted(selected_trials)
  merged["episodes"] = episodes
  merged["shards"] = shard_rows
  merged["environment_boundaries"] = merged_boundaries
  merged["retry_history"] = merged_retry_history
  if merged_parameter_drift:
    merged["resume_parameter_drift"] = merged_parameter_drift
  else:
    merged.pop("resume_parameter_drift", None)
  if merged_retry_parameter_drift:
    merged["retry_parameter_drift"] = merged_retry_parameter_drift
  else:
    merged.pop("retry_parameter_drift", None)
  merged["environment"]["execution_shard"] = "merged"
  merged["environment"]["shard_devices"] = [
      {
          "run_id": shard.get("run_id"),
          "execution_shard": shard.get("environment", {}).get("execution_shard"),
          "device_serial": shard.get("environment", {}).get("device_serial"),
          "avd_name": shard.get("environment", {}).get("avd_name"),
          "api_level": shard.get("environment", {}).get("api_level"),
      }
      for shard in shards
  ]
  merged["scope"]["completed_episodes"] = sum(
      row.get("status") == "completed" for row in episodes
  )
  merged["scope"]["error_episodes"] = sum(
      row.get("status") != "completed" for row in episodes
  )
  merged["arm_summary"] = aggregate_episodes(episodes)
  merged["paired_comparison"] = paired_rows(episodes)
  enforce_scope_claims(merged)
  paired_source = json.loads(args.source_paired_evidence.read_text(encoding="utf-8"))
  if paired_source.get("run_id") != reference_source:
    raise RuntimeError("Supplied paired evidence does not match the shard source run ID")
  merged["decision"]["source_paired_evidence"] = str(
      args.source_paired_evidence.resolve()
  )
  merged["decision"]["source_paired_model"] = paired_source.get("model")
  paired_model = paired_source.get("model", {}).get("model")
  candidate_model = merged.get("model", {}).get("model")
  if paired_model and paired_model != candidate_model:
    message = (
        f"The full-suite candidate uses model {candidate_model}, while the promoted paired "
        f"H5C source used {paired_model}. This user-requested local-GPU campaign evaluates "
        "the promoted observation treatment but is not a same-model extension of the paired result."
    )
    if message not in merged.setdefault("environment_boundaries", []):
      merged["environment_boundaries"].append(message)
  if merged["scope"]["full_suite_completed"]:
    merged["decision"].update({
        "outcome": "full_candidate_rerun_completed",
        "deployment_approved": False,
        "reason": (
            "The direct 116-task x five-trial candidate rerun completed on five "
            "independent reference-environment shards. Negative evaluator results are retained."
        ),
    })
  else:
    merged["decision"].update({
        "outcome": "candidate_rerun_has_errors",
        "deployment_approved": False,
        "reason": (
            "The merged candidate evidence contains missing or error episodes and does not "
            "satisfy the strict completion gate."
        ),
    })

  if args.analysis_base_url and args.analysis_model:
    import os

    api_key = os.environ.get(args.analysis_api_key_env)
    if not api_key:
      raise RuntimeError(
          f"Analysis credential variable is unset: {args.analysis_api_key_env}"
      )
    llm = OpenAICompatibleLlm(
        api_key=api_key,
        base_url=args.analysis_base_url,
        model=args.analysis_model,
        seed=int(reference_model.get("seed", 42)),
        max_tokens=int(reference_model.get("max_tokens", 1024)),
        timeout_s=120,
        retries=1,
        input_cost_per_million_usd=0.0,
        output_cost_per_million_usd=0.0,
    )
    merged["llm_analysis"] = _generate_llm_analysis(merged, llm, [api_key])
  else:
    merged["llm_analysis"] = {
        "status": "not_run",
        "error": "Merged analysis endpoint was not configured.",
    }

  args.output_dir.mkdir(parents=True)
  (args.output_dir / "evidence.json").write_text(dumps_json(merged), encoding="utf-8")
  (args.output_dir / "report.md").write_text(render_report(merged), encoding="utf-8")
  print(f"Evidence: {args.output_dir / 'evidence.json'}")
  print(f"Report:   {args.output_dir / 'report.md'}")
  return 0 if merged["scope"]["full_suite_completed"] else 2


if __name__ == "__main__":
  raise SystemExit(main())
