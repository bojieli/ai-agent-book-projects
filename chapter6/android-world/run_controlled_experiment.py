#!/usr/bin/env python3
"""Run a real, evidence-producing Experiment 6-11 T3A ablation.

This companion runner imports the adjacent, unmodified AndroidWorld checkout.
It supports a paired control/treatment experiment and a subsequent candidate
rerun. It never substitutes mock episodes or manuscript example numbers.
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import random
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any

from experiment_core import (
    BASELINE_TASK_COUNT,
    WIFI_TASKS,
    aggregate_episodes,
    choose_decision,
    choose_efficiency_decision,
    dumps_json,
    enforce_scope_claims,
    paired_rows,
    redact_text,
    render_report,
)


DEFAULT_GUIDELINES = (
    "For Wi-Fi tasks, first inspect the visible Settings state. If the requested "
    "state is already achieved, immediately finish with status complete and do not toggle it.",
    "If a change is needed, open Settings and use Network & internet, then Internet, "
    "then the visible Wi-Fi switch. Wait for the UI to settle after toggling.",
    "Before reporting completion, verify the requested on/off state from the visible "
    "switch or status text. Do not repeatedly reopen Settings or toggle without checking state.",
)

HYPOTHESIS_DEFINITIONS = {
    "H1": {
        "layer": "surface",
        "idea": "Add Wi-Fi Settings navigation and final-state verification guidance.",
        "target": "At least one net paired success across the four Wi-Fi tasks, with no regression.",
        "verification": "Paired upstream-prompt versus task-guideline ablation with matched seeds.",
        "change": "Use upstream T3A.set_task_guidelines for only Wi-Fi navigation and verification.",
        "phase": "phase_1_surface",
        "phase_description": "low-cost surface prompt ablation",
        "independent_variable": "task-specific T3A guidelines",
    },
    "H2": {
        "layer": "surface",
        "idea": "Add application-specific recognition rules for the non-standard Tasks UI.",
        "target": "Improve at least two of the six historical Tasks failures with no regression.",
        "verification": "Paired Tasks-only prompt/tool-description ablation after app provisioning.",
    },
    "H3": {
        "layer": "middle",
        "idea": "Repair and validate the multimodal input path for transcription tasks.",
        "target": "Raise transcription success above the historical 0% while bounding added tokens and latency.",
        "verification": "Paired screenshot-disabled versus screenshot-enabled transcription run.",
    },
    "H4": {
        "layer": "middle",
        "idea": "Conditionally enable deeper thinking for counting tasks.",
        "target": "Improve math/counting success without applying the cost to unrelated tasks.",
        "verification": "Paired tag-routed thinking-mode ablation with latency and token guardrails.",
    },
    "H5": {
        "layer": "middle",
        "idea": "Replace the API-35-incompatible gRPC accessibility feed with upstream's UIAutomator observation path.",
        "target": "At least one net paired Wi-Fi success with no regression and at most 1.5x latency/tokens.",
        "verification": "Paired a11y-forwarder versus UIAutomator run with the same upstream T3A prompt and matched seeds.",
        "change": "Select AndroidWorld's UIAUTOMATOR observation method in the companion runner without changing upstream source.",
        "phase": "phase_2_middle",
        "phase_description": "middle-layer input-pipeline ablation prompted by phase-1 residual traces",
        "independent_variable": "accessibility observation pipeline (gRPC forwarder versus UIAutomator)",
    },
    "H5C": {
        "layer": "middle",
        "idea": "Filter non-semantic UIAutomator container nodes after H5 exposed excessive prompt-token cost.",
        "target": "Preserve H5 paired success with no regression while using at most 0.75x raw-UIAutomator tokens and 1.5x latency.",
        "verification": "Paired raw-UIAutomator versus compact-UIAutomator run with matched tasks, seeds, prompt, and evaluator.",
        "change": "Use the real upstream UIAutomator hierarchy but retain only visible text, descriptions, and actionable/scrollable elements.",
        "phase": "phase_2_cost_refinement",
        "phase_description": "middle-layer input-pipeline cost refinement after the H5 success/cost result",
        "independent_variable": "raw versus semantic-filtered UIAutomator element list",
    },
    "H6": {
        "layer": "deep",
        "idea": "Combine screenshots with the structured UI tree and compare stronger vision-capable models.",
        "target": "Improve complex-UI success enough to justify multimodal latency and token cost.",
        "verification": "Factorial UI-tree/screenshot/model ablation on the full tagged slice.",
    },
}

HYPOTHESIS_GUARDRAILS = {
    "H1": (
        "Same model, seed, task parameters, emulator, checkout, and step budget; "
        "require at least four completed pairs, positive net success, no regression, "
        "and at most 1.5x mean latency and tokens."
    ),
    "H5": (
        "Same model, seed, task parameters, emulator, checkout, and step budget; "
        "require at least four completed pairs, positive net success, no regression, "
        "and at most 1.5x mean latency and tokens."
    ),
    "H5C": (
        "Same model, seed, task parameters, emulator, checkout, and step budget; "
        "require at least four completed pairs, every compact-UIAutomator treatment "
        "pair successful, no paired regression, at most 1.5x mean latency, and at "
        "most 0.75x raw-UIAutomator mean tokens."
    ),
}

SCOPE_CAVEAT = (
    " Passing a paired gate permits only a full-suite candidate rerun; it is not "
    "deployment approval, and a subset must never be reported as full-suite success."
)

EXPERIMENT_ID = "6-11"
LEGACY_EXPERIMENT_IDS = {"6-10"}

REQUIRED_APP_PACKAGES = {
    "android world": "com.example.androidworld",
    "audio recorder": "com.dimowner.audiorecorder",
    "camera": "com.android.camera2",
    "chrome": "com.android.chrome",
    "clipper": "ca.zgrs.clipper",
    "clock": "com.google.android.deskclock",
    "contacts": "com.google.android.contacts",
    "dialer": "com.google.android.dialer",
    "files": "com.google.android.documentsui",
    "joplin": "net.cozic.joplin",
    "markor": "net.gsantner.markor",
    "miniwob": "com.google.androidenv.miniwob",
    "open tracks": "de.dennisguse.opentracks",
    "osmand": "net.osmand",
    "pro expense": "com.arduia.expense",
    "recipe": "com.flauschcode.broccoli",
    "retro music": "code.name.monkey.retromusic",
    "settings": "com.android.settings",
    "simple calendar pro": "com.simplemobiletools.calendar.pro",
    "simple draw pro": "com.simplemobiletools.draw.pro",
    "simple gallery pro": "com.simplemobiletools.gallery.pro",
    "simple sms messenger": "com.simplemobiletools.smsmessenger",
    "tasks": "org.tasks",
    "vlc": "org.videolan.vlc",
}

_CONTEXT_LIMIT_ERROR = re.compile(
    r"maximum context length is (\d+).*prompt contains at least (\d+)"
)


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(command: list[str], *, cwd: Path | None = None) -> str:
  return subprocess.run(
      command,
      cwd=cwd,
      check=True,
      text=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
  ).stdout.strip()


def _adb(adb_path: str, console_port: int, *args: str) -> str:
  return _run([adb_path, "-s", f"emulator-{console_port}", *args])


def _jsonable(value: Any) -> Any:
  try:
    json.dumps(value)
    return value
  except TypeError:
    if isinstance(value, dict):
      return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
      return [_jsonable(item) for item in value]
    return str(value)


def _bootstrap_android_world(checkout: Path) -> dict[str, Any]:
  """Imports a source checkout while generating absent protobufs in /tmp."""
  checkout = checkout.resolve()
  if not (checkout / "android_world" / "registry.py").is_file():
    raise FileNotFoundError(f"Not an AndroidWorld checkout: {checkout}")
  sys.path.insert(0, str(checkout))

  proto_package = importlib.import_module(
      "android_world.task_evals.information_retrieval.proto"
  )
  generated = False
  generated_root = None
  try:
    importlib.import_module(
        "android_world.task_evals.information_retrieval.proto.state_pb2"
    )
  except ImportError:
    from grpc_tools import protoc  # Imported lazily for a precise setup error.

    generated_root = Path(tempfile.mkdtemp(prefix="androidworld-proto-"))
    proto_dir = checkout / "android_world/task_evals/information_retrieval/proto"
    for filename in ("state.proto", "task.proto"):
      rc = protoc.main([
          "grpc_tools.protoc",
          f"-I{checkout}",
          f"--python_out={generated_root}",
          str(proto_dir / filename),
      ])
      if rc:
        raise RuntimeError(f"grpc_tools.protoc failed for {filename}: exit {rc}")
    generated_package = (
        generated_root / "android_world/task_evals/information_retrieval/proto"
    )
    proto_package.__path__.insert(0, str(generated_package))
    importlib.import_module(
        "android_world.task_evals.information_retrieval.proto.state_pb2"
    )
    generated = True

  return {
      "generated_protobufs_in_temporary_directory": generated,
      "temporary_directory_persisted": False,
  }


def _read_evidence(path: Path, *, purpose: str) -> dict[str, Any]:
  try:
    evidence = json.loads(path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError) as error:
    raise RuntimeError(f"Could not read {purpose} evidence {path}: {error}") from error
  if (
      evidence.get("experiment") not in {EXPERIMENT_ID, *LEGACY_EXPERIMENT_IDS}
      or not evidence.get("run_id")
  ):
    raise RuntimeError(f"Invalid {purpose} evidence: not an Experiment 6-11 artifact")
  return evidence


def _collect_app_provenance(adb_path: str, console_port: int) -> dict[str, Any]:
  """Records the exact official app-package state visible to the benchmark."""
  installed_output = _adb(adb_path, console_port, "shell", "pm", "list", "packages")
  installed_packages = {
      line.removeprefix("package:").strip()
      for line in installed_output.splitlines()
      if line.startswith("package:")
  }
  rows = []
  missing = []
  for app_name, package_name in REQUIRED_APP_PACKAGES.items():
    installed = package_name in installed_packages
    if not installed:
      missing.append(package_name)
    row: dict[str, Any] = {
        "app": app_name,
        "package": package_name,
        "installed": installed,
        "version_code": None,
        "version_name": None,
        "apk_paths": [],
    }
    if installed:
      package_dump = _adb(
          adb_path, console_port, "shell", "dumpsys", "package", package_name
      )
      version_code = re.search(r"\bversionCode=(\d+)", package_dump)
      version_name = re.search(r"\bversionName=([^\s]+)", package_dump)
      row["version_code"] = int(version_code.group(1)) if version_code else None
      row["version_name"] = version_name.group(1) if version_name else None
      paths = _adb(adb_path, console_port, "shell", "pm", "path", package_name)
      row["apk_paths"] = sorted(
          line.removeprefix("package:").strip()
          for line in paths.splitlines()
          if line.startswith("package:")
      )
    rows.append(row)
  return {
      "source": "direct adb package-manager query at run start",
      "required_package_count": len(REQUIRED_APP_PACKAGES),
      "installed_required_package_count": len(REQUIRED_APP_PACKAGES) - len(missing),
      "complete": not missing,
      "missing_packages": missing,
      "apps": rows,
  }


def _context_safe_output_cap(message: str, requested: int) -> int | None:
  """Returns a one-token-headroom cap from an OpenAI-style context error."""
  context_match = _CONTEXT_LIMIT_ERROR.search(message)
  if not context_match:
    return None
  # vLLM's lower-bound estimate shifted by two tokens between identical
  # retries in the observed Notes prompts. Reserve bounded headroom rather
  # than chasing the moving lower bound one token at a time.
  available = (
      int(context_match.group(1))
      - int(context_match.group(2))
      - 32
  )
  return available if 0 < available < requested else None


def _truncate_current_ui_section(
    prompt: str, *, max_ui_chars: int = 12000
) -> tuple[str, int] | None:
  """Truncates only middles of T3A action or summary UI sections."""
  def compact_middle(
      section: str, retained_chars: int, label: str
  ) -> tuple[str, int] | None:
    if len(section) <= retained_chars:
      return None
    front_chars = retained_chars * 2 // 3
    back_chars = retained_chars - front_chars
    marker = (
        f"\n[Middle {label} UI elements omitted after the model's native "
        "context limit was reached; original element indices are preserved.]\n"
    )
    compact = section[:front_chars] + marker + section[-back_chars:]
    return compact, len(section) - len(compact)

  start_marker = (
      "\n\nHere is a list of descriptions for some UI elements on the current"
      " screen:\n"
  )
  end_marker = "\nHere are some useful guidelines you need to follow:\n"
  start = prompt.find(start_marker)
  if start >= 0:
    start += len(start_marker)
    end = prompt.find(end_marker, start)
    if end >= 0:
      result = compact_middle(prompt[start:end], max_ui_chars, "current-screen")
      if result is not None:
        compact, removed = result
        return prompt[:start] + compact + prompt[end:], removed

  before_marker = "Here is the description for the before screenshot:\n"
  after_marker = "\nHere is the description for the after screenshot:\n"
  action_marker = "\nThis is the action you picked:"
  before_start = prompt.find(before_marker)
  if before_start < 0:
    return None
  before_start += len(before_marker)
  before_end = prompt.find(after_marker, before_start)
  if before_end < 0:
    return None
  after_start = before_end + len(after_marker)
  after_end = prompt.find(action_marker, after_start)
  if after_end < 0:
    return None
  before_result = compact_middle(
      prompt[before_start:before_end], max_ui_chars // 2, "before-screen"
  )
  after_result = compact_middle(
      prompt[after_start:after_end], max_ui_chars // 2, "after-screen"
  )
  if before_result is None or after_result is None:
    return None
  compact_before, removed_before = before_result
  compact_after, removed_after = after_result
  compact_prompt = (
      prompt[:before_start]
      + compact_before
      + after_marker
      + compact_after
      + prompt[after_end:]
  )
  return compact_prompt, removed_before + removed_after


def _install_uiautomator_evaluator_compatibility() -> dict[str, Any]:
  """Keeps the official contact-draft predicate usable without a gRPC forest."""
  from android_world.task_evals import task_eval
  from android_world.task_evals.single import contacts

  original = contacts.ContactsNewContactDraft.is_successful

  def is_successful(self: Any, env: Any) -> float:
    state = env.get_state()
    if state.forest is not None:
      return original(self, env)
    task_eval.TaskEval.is_successful(self, env)
    return float(contacts._contact_info_is_entered(  # pylint: disable=protected-access
        ui_elements=state.ui_elements,
        first=self.params["first"],
        last=self.params["last"],
        phone=self.params["phone"],
        phone_label=self.params["phone_label"],
    ))

  contacts.ContactsNewContactDraft.is_successful = is_successful
  return {
      "task": "ContactsNewContactDraft",
      "reason": "The upstream evaluator assumes state.forest, which is None for UIAutomator.",
      "change": (
          "When forest is None, pass state.ui_elements to the evaluator's unchanged "
          "_contact_info_is_entered predicate."
      ),
      "official_predicate_preserved": True,
  }


def _missing_retro_queue_as_empty(get_queue: Any) -> Any:
  """Maps the pinned Retro APK's absent queue schema to an empty observation."""

  def compatible_get_queue(env: Any) -> list[str]:
    try:
      return get_queue(env)
    except sqlite3.OperationalError as error:
      if str(error) != "no such table: playing_queue":
        raise
      return []

  return compatible_get_queue


def _read_nonempty_with_retry(
    read: Any, *, attempts: int = 6, delay_s: float = 1.0
) -> list[Any]:
  """Polls an asynchronously populated Android content provider."""
  if attempts < 1:
    raise ValueError("attempts must be positive")
  result: list[Any] = []
  for attempt in range(attempts):
    result = read()
    if result or attempt == attempts - 1:
      return result
    time.sleep(delay_s)
  return result


def _retry_clipper_foreground(call: Any, *args: Any, delay_s: float = 1.0) -> Any:
  """Retries once only for AndroidWorld's documented Clipper foreground race."""
  try:
    return call(*args)
  except RuntimeError as error:
    if not str(error).startswith(
        "Clipper app must be in the foreground to access clipboard."
    ):
      raise
    time.sleep(delay_s)
    return call(*args)


def _install_clipper_timing_compatibility() -> dict[str, Any]:
  """Retries the unchanged clipboard operation after a foreground race."""
  from android_world.env import adb_utils

  original_get = adb_utils.get_clipboard_contents
  original_set = adb_utils.set_clipboard_contents

  def get_clipboard_contents(env: Any) -> str:
    return _retry_clipper_foreground(original_get, env)

  def set_clipboard_contents(content: str, env: Any) -> None:
    _retry_clipper_foreground(original_set, content, env)

  adb_utils.get_clipboard_contents = get_clipboard_contents
  adb_utils.set_clipboard_contents = set_clipboard_contents
  return {
      "task": "clipboard-dependent tasks",
      "reason": (
          "The official Clipper app intermittently returns its documented "
          "foreground-access RuntimeError immediately after launch."
      ),
      "change": (
          "Retry the unchanged clipboard get/set operation once after one second, "
          "only for the exact Clipper foreground-access error."
      ),
      "task_data_and_evaluator_preserved": True,
  }


def _install_sms_inbox_timing_compatibility() -> dict[str, Any]:
  """Waits for an emulator-injected SMS to appear before upstream indexes it."""
  from android_world.env import adb_utils
  from android_world.task_evals.single import sms

  original = sms.SimpleSmsReplyMostRecent._get_received_messages  # pylint: disable=protected-access
  original_text_emulator = adb_utils.text_emulator
  latest_injected: dict[int, tuple[str, str]] = {}

  def text_emulator(
      env: Any, phone_number: str, message: str, timeout_sec: float = 20.0
  ) -> Any:
    response = original_text_emulator(env, phone_number, message, timeout_sec)
    latest_injected[id(env)] = (phone_number, message)
    return response

  def get_received_messages(self: Any, env: Any) -> list[str]:
    rows = _read_nonempty_with_retry(lambda: original(self, env))
    if rows:
      return rows
    injected = latest_injected.get(id(env))
    if injected is None:
      return rows
    phone_number, message = injected
    address_hex = phone_number.encode("utf-8").hex()
    body_hex = message.encode("utf-8").hex()
    adb_utils.execute_sql_command(
        "/data/data/com.android.providers.telephony/databases/mmssms.db",
        (
            "INSERT INTO sms(address,date,read,type,body,seen) VALUES("
            f"CAST(X'{address_hex}' AS TEXT),{int(time.time() * 1000)},1,1,"
            f"CAST(X'{body_hex}' AS TEXT),1);"
        ),
        env,
    )
    return _read_nonempty_with_retry(
        lambda: original(self, env), attempts=3, delay_s=1.0
    )

  adb_utils.text_emulator = text_emulator
  sms.SimpleSmsReplyMostRecent._get_received_messages = get_received_messages  # pylint: disable=protected-access
  return {
      "task": "SimpleSmsReplyMostRecent",
      "reason": (
          "The emulator inbox can remain empty after the upstream fixed five-second "
          "wait; upstream documents the resulting list-index error in "
          "scripts/run_suite_on_docker.py."
      ),
      "change": (
          "Poll the unchanged received-message query for five additional seconds; "
          "if the emulator console still failed to populate the inbox, insert the "
          "exact last injected address/body into the same SMS SQLite database that "
          "upstream already clears directly, then rerun the unchanged query."
      ),
      "task_data_and_evaluator_preserved": True,
  }


def _install_retro_queue_evaluator_compatibility() -> dict[str, Any]:
  """Lets the official queue equality predicate score a known absent schema."""
  from android_world.task_evals.single import retro_music

  retro_music._get_playing_queue = _missing_retro_queue_as_empty(  # pylint: disable=protected-access
      retro_music._get_playing_queue  # pylint: disable=protected-access
  )
  return {
      "task": "RetroPlayingQueue",
      "reason": (
          "The pinned official Retro Music APK does not create the "
          "music_playback_state.playing_queue table; upstream documents the same "
          "runtime error in scripts/run_suite_on_docker.py."
      ),
      "change": (
          "Map only sqlite3.OperationalError('no such table: playing_queue') to an "
          "empty observed queue, then retain the official exact queue comparison."
      ),
      "official_predicate_preserved": True,
      "missing_schema_scores_as_evaluator_failure": True,
  }


def _validate_phase1_source(evidence: dict[str, Any]) -> None:
  if evidence.get("hypothesis", {}).get("id") != "H1":
    raise RuntimeError("Phase-2 H5 requires direct H1 phase-1 evidence")
  if len(evidence.get("paired_comparison", [])) < 4:
    raise RuntimeError("Phase-2 H5 requires at least four completed H1 pairs")
  if evidence.get("decision", {}).get("promote_to_full_suite_candidate"):
    raise RuntimeError("H5 is a residual-failure follow-up; the supplied H1 run was promoted")


def _validate_phase2_source(evidence: dict[str, Any]) -> None:
  if evidence.get("hypothesis", {}).get("id") != "H5":
    raise RuntimeError("H5C requires direct H5 phase-2 evidence")
  if len(evidence.get("paired_comparison", [])) < 4:
    raise RuntimeError("H5C requires at least four completed H5 pairs")
  decision = evidence.get("decision", {})
  if int(decision.get("net_success_delta", 0)) <= 0:
    raise RuntimeError("H5C requires an H5 source with positive paired success gain")
  if decision.get("outcome") != "restrict_candidate_due_to_cost":
    raise RuntimeError("H5C is only justified when H5 was restricted by the cost guardrail")
  pairs = evidence.get("paired_comparison", [])
  if not all(row.get("treatment_success") is True for row in pairs):
    raise RuntimeError("H5C requires H5 source treatment success on every source pair")


def _validate_candidate_source(evidence: dict[str, Any], hypothesis_id: str) -> None:
  if evidence.get("hypothesis", {}).get("id") != hypothesis_id:
    raise RuntimeError(
        f"Candidate hypothesis {hypothesis_id} does not match paired source "
        f"{evidence.get('hypothesis', {}).get('id')}"
    )
  decision = evidence.get("decision", {})
  if len(evidence.get("paired_comparison", [])) < 4:
    raise RuntimeError("Candidate rerun requires at least four completed source pairs")
  if not decision.get("promote_to_full_suite_candidate"):
    raise RuntimeError("Candidate rerun refused: paired source did not pass success/cost guardrails")


def _load_android_env(args: argparse.Namespace, a11y_method: str) -> Any:
  """Loads an upstream environment, selecting UIAutomator without editing upstream."""
  from android_world.env import android_world_controller
  from android_world.env import env_launcher

  if a11y_method == "a11y_forwarder_app":
    return env_launcher.load_and_setup_env(
        console_port=args.console_port,
        emulator_setup=args.perform_emulator_setup,
        freeze_datetime=False,
        adb_path=args.adb_path,
        grpc_port=args.grpc_port,
    )

  from android_env import loader
  from android_env.components import config_classes
  from android_world.env import interface

  config = config_classes.AndroidEnvConfig(
      task=config_classes.FilesystemTaskConfig(
          path=android_world_controller._write_default_task_proto()  # pylint: disable=protected-access
      ),
      simulator=config_classes.EmulatorConfig(
          emulator_launcher=config_classes.EmulatorLauncherConfig(
              emulator_console_port=args.console_port,
              adb_port=args.console_port + 1,
              grpc_port=args.grpc_port,
          ),
          adb_controller=config_classes.AdbControllerConfig(adb_path=args.adb_path),
      ),
  )
  base_env = loader.load(config)
  controller = android_world_controller.AndroidWorldController(
      base_env,
      a11y_method=android_world_controller.A11yMethod.UIAUTOMATOR,
      install_a11y_forwarding_app=False,
  )
  if a11y_method == "uiautomator_compact":
    original_get_ui_elements = controller.get_ui_elements

    def get_compact_ui_elements() -> list[Any]:
      elements = original_get_ui_elements()
      return [
          element for element in elements
          if (
              (element.text or "").strip()
              or (element.content_description or "").strip()
              or element.is_clickable
              or element.is_checkable
              or element.is_editable
              or element.is_scrollable
              or element.is_long_clickable
          )
      ]

    controller.get_ui_elements = get_compact_ui_elements
  env = interface.AsyncAndroidEnv(controller)
  env_launcher.setup_env(
      env,
      emulator_setup=args.perform_emulator_setup,
      freeze_datetime=False,
  )
  return env


def _arm_a11y_method(args: argparse.Namespace, arm: str) -> str:
  if args.hypothesis == "H5" and args.mode == "paired":
    return "a11y_forwarder_app" if arm == "control" else "uiautomator"
  if args.hypothesis == "H5" and args.mode == "candidate-rerun":
    return "uiautomator"
  if args.hypothesis == "H5C" and args.mode == "paired":
    return "uiautomator" if arm == "control" else "uiautomator_compact"
  if args.hypothesis == "H5C" and args.mode == "candidate-rerun":
    return "uiautomator_compact"
  return args.a11y_method


def _arm_guidelines(args: argparse.Namespace, arm: str, task_name: str) -> list[str]:
  if args.hypothesis != "H1":
    return []
  if arm in ("treatment", "candidate"):
    return _guidelines_for(task_name)
  return []


class OpenAICompatibleLlm:
  """Minimal real API wrapper matching AndroidWorld's LlmWrapper contract."""

  def __init__(
      self,
      *,
      api_key: str,
      base_url: str,
      model: str,
      seed: int,
      max_tokens: int,
      timeout_s: float,
      retries: int,
      input_cost_per_million_usd: float,
      output_cost_per_million_usd: float,
  ):
    from openai import OpenAI

    self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_s)
    self.model = model
    self.seed = seed
    self.max_tokens = max_tokens
    self.retries = retries
    self.input_cost_per_million_usd = input_cost_per_million_usd
    self.output_cost_per_million_usd = output_cost_per_million_usd
    self.calls = 0
    self.input_tokens = 0
    self.output_tokens = 0
    self.reasoning_tokens = 0
    self.total_latency_s = 0.0
    self.system_fingerprints: set[str] = set()
    self.context_cap_adjustments = 0
    self.context_prompt_truncations = 0
    self.context_prompt_chars_removed = 0

  def snapshot(self) -> dict[str, Any]:
    return {
        "calls": self.calls,
        "input_tokens": self.input_tokens,
        "output_tokens": self.output_tokens,
      "reasoning_tokens": self.reasoning_tokens,
      "estimated_cost_usd": round(
          self.input_tokens * self.input_cost_per_million_usd / 1_000_000
          + self.output_tokens * self.output_cost_per_million_usd / 1_000_000,
          9,
      ),
        "latency_s": self.total_latency_s,
      "system_fingerprints": sorted(self.system_fingerprints),
      "context_cap_adjustments": self.context_cap_adjustments,
      "context_prompt_truncations": self.context_prompt_truncations,
      "context_prompt_chars_removed": self.context_prompt_chars_removed,
    }

  @staticmethod
  def delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "calls": after["calls"] - before["calls"],
        "input_tokens": after["input_tokens"] - before["input_tokens"],
        "output_tokens": after["output_tokens"] - before["output_tokens"],
      "reasoning_tokens": after["reasoning_tokens"] - before["reasoning_tokens"],
      "estimated_cost_usd": round(
          after["estimated_cost_usd"] - before["estimated_cost_usd"], 9
      ),
        "latency_s": round(after["latency_s"] - before["latency_s"], 6),
      "system_fingerprints": after["system_fingerprints"],
      "context_cap_adjustments": (
          after["context_cap_adjustments"] - before["context_cap_adjustments"]
      ),
      "context_prompt_truncations": (
          after["context_prompt_truncations"]
          - before["context_prompt_truncations"]
      ),
      "context_prompt_chars_removed": (
          after["context_prompt_chars_removed"]
          - before["context_prompt_chars_removed"]
      ),
    }

  def predict(self, text_prompt: str) -> tuple[str, None, Any]:
    last_error = None
    request_max_tokens = self.max_tokens
    request_prompt = text_prompt
    for attempt in range(1, self.retries + 1):
      started = time.monotonic()
      try:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": request_prompt}],
            temperature=0,
            seed=self.seed,
            max_tokens=request_max_tokens,
        )
        self.total_latency_s += time.monotonic() - started
        self.calls += 1
        usage = response.usage
        if usage is not None:
          self.input_tokens += int(usage.prompt_tokens or 0)
          self.output_tokens += int(usage.completion_tokens or 0)
          details = getattr(usage, "completion_tokens_details", None)
          self.reasoning_tokens += int(getattr(details, "reasoning_tokens", 0) or 0)
        fingerprint = getattr(response, "system_fingerprint", None)
        if fingerprint:
          self.system_fingerprints.add(str(fingerprint))
        content = response.choices[0].message.content
        if not content:
          raise RuntimeError("Model returned empty content")
        return content, None, response
      except Exception as error:  # noqa: BLE001 - API surface is provider-specific.
        self.total_latency_s += time.monotonic() - started
        last_error = error
        message = str(error)
        available = _context_safe_output_cap(message, request_max_tokens)
        if available is not None:
          request_max_tokens = available
          self.context_cap_adjustments += 1
          continue
        if _CONTEXT_LIMIT_ERROR.search(message):
          truncation = _truncate_current_ui_section(request_prompt)
          if truncation is not None:
            request_prompt, removed = truncation
            self.context_prompt_truncations += 1
            self.context_prompt_chars_removed += removed
            continue
        if attempt < self.retries:
          time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"Real model API failed after {self.retries} attempts: {last_error}")


def _extract_json_object(text: str) -> dict[str, Any]:
  start = text.find("{")
  end = text.rfind("}")
  if start < 0 or end <= start:
    raise ValueError("model response did not contain a JSON object")
  value = json.loads(text[start:end + 1])
  if not isinstance(value, dict):
    raise ValueError("model response was not a JSON object")
  return value


def _bounded_string(value: Any, secrets: list[str], limit: int = 1200) -> str:
  return redact_text(value, secrets).strip()[:limit]


def _generate_llm_analysis(
    evidence: dict[str, Any],
    llm: OpenAICompatibleLlm,
    secrets: list[str],
) -> dict[str, Any]:
  """Asks the configured real LLM for a bounded analysis of direct evidence."""
  episode_summary = [
      {
          "task": row.get("task"),
          "arm": row.get("arm"),
          "status": row.get("status"),
          "initial_evaluator_reward": row.get("initial_evaluator_reward"),
          "evaluator_reward": row.get("evaluator_reward"),
          "agent_declared_done": row.get("agent_declared_done"),
          "success": row.get("success"),
          "steps": row.get("steps"),
          "elapsed_s": row.get("elapsed_s"),
          "llm_calls": row.get("llm", {}).get("calls"),
          "total_tokens": int(row.get("llm", {}).get("input_tokens", 0))
          + int(row.get("llm", {}).get("output_tokens", 0)),
          "error": row.get("error"),
      }
      for row in evidence.get("episodes", [])
  ]
  episode_sample_strategy = "all episodes"
  if len(episode_summary) > 200:
    failures = [
        row
        for row in episode_summary
        if row.get("status") != "completed" or row.get("success") is not True
    ]
    episode_summary = failures[:100]
    episode_sample_strategy = (
        f"first {len(episode_summary)} negative/error episodes in canonical order; "
        "aggregate metrics cover every episode"
    )
  analysis_input = {
      "episode_count": len(evidence.get("episodes", [])),
      "episode_sample_strategy": episode_sample_strategy,
      "scope": evidence.get("scope"),
      "hypothesis": evidence.get("hypothesis"),
      "phase": evidence.get("phase"),
      "arm_summary": evidence.get("arm_summary"),
      "paired_comparison": evidence.get("paired_comparison"),
      "decision": evidence.get("decision"),
      "episodes": episode_summary,
      "environment_boundaries": evidence.get("environment_boundaries"),
  }
  prompt = (
      "Analyze the following real Experiment 6-11 AndroidWorld evidence. Return exactly one "
      "JSON object with keys summary (string), observed_failure_pattern (array of strings), "
      "cost_benefit_interpretation (string), and next_hypothesis (object with id, layer, idea, "
      "target, verification). Do not invent results, extrapolate the four-task subset to 116 "
      "tasks, approve deployment, or treat historical/hypothetical numbers as observed. Mention "
      "the API/app boundaries when they affect interpretation. Evidence:\n"
      + json.dumps(analysis_input, ensure_ascii=False, sort_keys=True)
  )
  before = llm.snapshot()
  try:
    content, _, _ = llm.predict(prompt)
    parsed = _extract_json_object(content)
    required = {
        "summary",
        "observed_failure_pattern",
        "cost_benefit_interpretation",
        "next_hypothesis",
    }
    if not required.issubset(parsed):
      raise ValueError(f"model JSON missing keys: {sorted(required - set(parsed))}")
    patterns = parsed["observed_failure_pattern"]
    next_hypothesis = parsed["next_hypothesis"]
    if not isinstance(patterns, list) or not isinstance(next_hypothesis, dict):
      raise ValueError("model JSON used invalid field types")
    return {
        "status": "completed",
        "source": "real configured LLM over aggregate direct evidence",
        "summary": _bounded_string(parsed["summary"], secrets),
        "observed_failure_pattern": [
            _bounded_string(item, secrets) for item in patterns[:8]
        ],
        "cost_benefit_interpretation": _bounded_string(
            parsed["cost_benefit_interpretation"], secrets
        ),
        "next_hypothesis": {
            key: _bounded_string(next_hypothesis.get(key, "n/a"), secrets)
            for key in ("id", "layer", "idea", "target", "verification")
        },
        "llm": OpenAICompatibleLlm.delta(before, llm.snapshot()),
    }
  except Exception as error:  # noqa: BLE001 - preserve a report-generation blocker.
    return {
        "status": "error",
        "source": "real configured LLM over aggregate direct evidence",
        "error": _bounded_string(error, secrets, 2000),
        "llm": OpenAICompatibleLlm.delta(before, llm.snapshot()),
    }


def _parse_args() -> argparse.Namespace:
  here = Path(__file__).resolve().parent
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "--android-world-checkout",
      type=Path,
      default=here.parent / "android_world",
  )
  parser.add_argument("--mode", choices=("paired", "candidate-rerun"), default="paired")
  parser.add_argument("--hypothesis", choices=("H1", "H5", "H5C"), default="H1")
  parser.add_argument("--tasks", default=",".join(WIFI_TASKS))
  parser.add_argument("--full-suite", action="store_true")
  parser.add_argument("--trials", type=int, default=1)
  parser.add_argument(
      "--trial-indices",
      help="Optional comma-separated 1-based trial shard; --trials still declares total scope.",
  )
  parser.add_argument("--execution-shard")
  parser.add_argument("--seed", type=int, default=42)
  parser.add_argument("--model-seed", type=int, default=42)
  parser.add_argument("--max-steps", type=int, default=10)
  parser.add_argument("--transition-pause", type=float, default=None)
  parser.add_argument("--provider", default="ark")
  parser.add_argument("--model", default="doubao-seed-1-6-250615")
  parser.add_argument("--base-url", default="https://ark.cn-beijing.volces.com/api/v3")
  parser.add_argument("--api-key-env", default="ARK_API_KEY")
  parser.add_argument("--max-model-tokens", type=int, default=1024)
  parser.add_argument("--model-timeout-s", type=float, default=90.0)
  parser.add_argument("--model-retries", type=int, default=3)
  parser.add_argument("--input-cost-per-million-usd", type=float, default=0.0)
  parser.add_argument("--output-cost-per-million-usd", type=float, default=0.0)
  parser.add_argument("--model-source", default="hosted_api")
  parser.add_argument("--model-revision")
  parser.add_argument("--model-runtime")
  parser.add_argument("--accelerator")
  parser.add_argument(
      "--adb-path",
      default=str(Path.home() / "Library/Android/sdk/platform-tools/adb"),
  )
  parser.add_argument("--console-port", type=int, default=5554)
  parser.add_argument("--grpc-port", type=int, default=8554)
  parser.add_argument("--perform-emulator-setup", action="store_true")
  parser.add_argument(
      "--a11y-method",
      choices=("a11y_forwarder_app", "uiautomator"),
      default="a11y_forwarder_app",
      help="Fixed observation method for H1/candidate runs; H5 paired runs vary it by arm.",
  )
  parser.add_argument(
      "--skip-device-time",
      action="store_true",
      help="Skip AndroidWorld's per-task date command (needed on this non-root API-35 AVD).",
  )
  parser.add_argument("--source-paired-run-id")
  parser.add_argument("--source-paired-evidence", type=Path)
  parser.add_argument("--source-phase1-evidence", type=Path)
  parser.add_argument("--source-phase2-evidence", type=Path)
  parser.add_argument("--output-dir", type=Path)
  parser.add_argument(
      "--resume",
      action="store_true",
      help="Continue missing arms from an existing output-dir evidence checkpoint.",
  )
  parser.add_argument(
      "--retry-errors",
      action="store_true",
      help="With --resume, discard checkpointed error episodes and execute them again.",
  )
  args = parser.parse_args()
  if args.trials <= 0 or args.max_steps <= 0:
    parser.error("--trials and --max-steps must be positive")
  if args.input_cost_per_million_usd < 0 or args.output_cost_per_million_usd < 0:
    parser.error("model token prices cannot be negative")
  if args.trial_indices:
    try:
      args.trial_indices = sorted(
          {int(value.strip()) for value in args.trial_indices.split(",") if value.strip()}
      )
    except ValueError:
      parser.error("--trial-indices must contain only comma-separated integers")
    if not args.trial_indices or any(
        trial < 1 or trial > args.trials for trial in args.trial_indices
    ):
      parser.error("--trial-indices must be between 1 and --trials")
  else:
    args.trial_indices = list(range(1, args.trials + 1))
  if args.full_suite and args.mode != "candidate-rerun":
    parser.error("--full-suite is only valid with --mode candidate-rerun")
  if args.mode == "candidate-rerun" and not args.source_paired_evidence:
    parser.error("candidate reruns require --source-paired-evidence")
  if args.hypothesis in ("H5", "H5C") and args.mode == "paired" and not args.source_phase1_evidence:
    parser.error(f"paired {args.hypothesis} runs require --source-phase1-evidence")
  if args.hypothesis == "H5C" and args.mode == "paired" and not args.source_phase2_evidence:
    parser.error("paired H5C runs require --source-phase2-evidence")
  if args.resume and not args.output_dir:
    parser.error("--resume requires --output-dir")
  if args.retry_errors and not args.resume:
    parser.error("--retry-errors requires --resume")
  return args


def _select_tasks(args: argparse.Namespace, registry_map: dict[str, Any]) -> list[str]:
  if args.full_suite:
    names = sorted(registry_map)
    if len(names) != BASELINE_TASK_COUNT:
      raise RuntimeError(
          f"Expected {BASELINE_TASK_COUNT} AndroidWorld tasks at pinned commit; found {len(names)}"
      )
    return names
  names = [name.strip() for name in args.tasks.split(",") if name.strip()]
  unknown = sorted(set(names) - set(registry_map))
  if unknown:
    raise ValueError(f"Unknown AndroidWorld task(s): {', '.join(unknown)}")
  return names


def _guidelines_for(task_name: str) -> list[str]:
  return list(DEFAULT_GUIDELINES) if task_name in WIFI_TASKS else []


def _trace_step(index: int, result: Any, elapsed_s: float, secrets: list[str]) -> dict[str, Any]:
  from android_world.agents import agent_utils, m3a_utils

  data = result.data
  raw = data.get("action_output") or ""
  reason, action_text = m3a_utils.parse_reason_action_output(raw)
  action: dict[str, Any] = {}
  if action_text:
    try:
      action = agent_utils.extract_json(action_text)
    except Exception:  # noqa: BLE001 - malformed model output is evidence.
      action = {}
  return {
      "step": index,
      "done": bool(result.done),
      "elapsed_s": round(elapsed_s, 6),
      "action_type": action.get("action_type", "unparsed"),
      "goal_status": action.get("goal_status"),
      "reason": redact_text(reason or data.get("summary") or "", secrets)[:1000],
  }


def _run_episode(
    *,
    env: Any,
    task_type: Any,
    params: dict[str, Any],
    task_name: str,
    trial: int,
    pair_id: str,
    pair_seed: int,
    arm: str,
    order_position: int,
    observation_method: str,
    task_guidelines: list[str],
    llm: OpenAICompatibleLlm,
    max_steps: int,
    transition_pause: float | None,
    secrets: list[str],
) -> dict[str, Any]:
  from android_world.agents import t3a

  episode = {
      "pair_id": pair_id,
      "task": task_name,
      "trial": trial,
      "pair_seed": pair_seed,
      "arm": arm,
      "order_position": order_position,
      "observation_method": observation_method,
      "task_guidelines_applied": bool(task_guidelines),
      "status": "error",
      "params": _jsonable(params),
      "goal": None,
      "initial_evaluator_reward": None,
      "evaluator_reward": None,
      "agent_declared_done": False,
      "success": False,
      "steps": 0,
      "elapsed_s": 0.0,
      "llm": {},
      "trace": [],
      "error": None,
  }
  task = task_type(copy.deepcopy(params))
  llm_before = llm.snapshot()
  started = time.monotonic()
  initialized = False
  try:
    env.reset(go_home=True)
    task.initialize_task(env)
    initialized = True
    episode["goal"] = str(task.goal)
    episode["initial_evaluator_reward"] = float(task.is_successful(env))
    agent = t3a.T3A(env, llm, name=f"T3A-{arm}")
    agent.transition_pause = transition_pause
    if task_guidelines:
      agent.set_task_guidelines(task_guidelines)

    for step_number in range(1, max_steps + 1):
      step_started = time.monotonic()
      result = agent.step(task.goal)
      episode["trace"].append(
          _trace_step(step_number, result, time.monotonic() - step_started, secrets)
      )
      episode["steps"] = step_number
      if result.done:
        episode["agent_declared_done"] = True
        break

    episode["evaluator_reward"] = float(task.is_successful(env))
    # Match upstream minimal_task_runner: final state alone is insufficient;
    # the agent must also explicitly terminate the episode.
    episode["success"] = bool(
        episode["agent_declared_done"] and episode["evaluator_reward"] == 1.0
    )
    episode["status"] = "completed"
  except Exception as error:  # noqa: BLE001 - preserve per-episode failures.
    episode["error"] = redact_text(error, secrets)[:4000]
  finally:
    episode["elapsed_s"] = round(time.monotonic() - started, 6)
    episode["llm"] = OpenAICompatibleLlm.delta(llm_before, llm.snapshot())
    if initialized:
      try:
        task.tear_down(env)
      except Exception as error:  # noqa: BLE001
        teardown_error = redact_text(error, secrets)[:2000]
        episode["teardown_error"] = teardown_error
  return episode


def _base_evidence(args: argparse.Namespace, run_id: str) -> dict[str, Any]:
  guideline_text = "\n".join(DEFAULT_GUIDELINES)
  selected = HYPOTHESIS_DEFINITIONS[args.hypothesis]
  layered_hypotheses = []
  for hypothesis_id, definition in HYPOTHESIS_DEFINITIONS.items():
    row = {
        key: definition[key]
        for key in ("layer", "idea", "target", "verification")
    }
    row["id"] = hypothesis_id
    if hypothesis_id == args.hypothesis:
      row["status"] = "tested in this run"
    elif args.hypothesis in ("H5", "H5C") and hypothesis_id == "H1":
      row["status"] = "tested in source phase 1"
    elif args.hypothesis == "H5C" and hypothesis_id == "H5":
      row["status"] = "tested in source phase 2"
    else:
      row["status"] = "not tested"
    layered_hypotheses.append(row)
  return {
      "schema_version": 1,
      "experiment": EXPERIMENT_ID,
      "run_id": run_id,
      "generated_at_utc": _utc_now(),
      "command": [Path(sys.argv[0]).name, *sys.argv[1:]],
      "credentials_persisted": False,
      "baseline": {
          "source": "t3a_summary.md and t3a_failed_analysis.md",
          "run_date": "2025-07-02",
          "agent": "t3a_claude4_sonnet",
          "tasks": BASELINE_TASK_COUNT,
          "trials_per_task": 1,
          "reported_success_rate_approx": 0.88,
          "provenance": "historical bundled report; not generated by this runner",
      },
      "diagnosis": {
          "findings": [
              "The historical run evaluated 116 tasks once each and reports approximately 88% overall success.",
              "Wi-Fi is a concentrated failure cluster: three of the four SystemWifiTurn* rows failed in the bundled per-task table.",
              "The capability matrix links the cluster to weak complex_ui_understanding, information_retrieval, and requires_setup behavior.",
              "The failed traces show navigation/state-verification loops; increasing the step cap alone would treat a symptom rather than the cause.",
          ],
          "layered_hypotheses": layered_hypotheses,
      },
      "hypothesis": {
          "id": args.hypothesis,
          "layer": selected["layer"],
          "change": selected["change"],
          "expected_result": selected["target"],
          "verification": selected["verification"],
          "guardrails": HYPOTHESIS_GUARDRAILS[args.hypothesis] + SCOPE_CAVEAT,
          "guideline_sha256": (
              hashlib.sha256(guideline_text.encode()).hexdigest()
              if args.hypothesis == "H1" else None
          ),
          "guidelines": list(DEFAULT_GUIDELINES) if args.hypothesis == "H1" else [],
      },
      "phase": {
          "id": selected["phase"],
          "description": selected["phase_description"],
          "independent_variable": selected["independent_variable"],
          "source_phase1_evidence": (
              str(args.source_phase1_evidence.resolve())
              if args.source_phase1_evidence else None
          ),
          "source_phase2_evidence": (
              str(args.source_phase2_evidence.resolve())
              if args.source_phase2_evidence else None
          ),
      },
      "model": {
          "provider": args.provider,
          "model": args.model,
          "base_url": args.base_url,
          "temperature": 0,
          "seed": args.model_seed,
          "max_tokens": args.max_model_tokens,
          "source": args.model_source,
          "revision": args.model_revision,
          "runtime": args.model_runtime,
          "accelerator": args.accelerator,
          "input_cost_per_million_usd": args.input_cost_per_million_usd,
          "output_cost_per_million_usd": args.output_cost_per_million_usd,
      },
      "environment": {},
      "environment_boundaries": [],
      "scope": {
          "mode": args.mode.replace("-", "_"),
          "tasks": [],
          "trials_per_task": args.trials,
          "selected_trials": args.trial_indices,
          "max_steps": args.max_steps,
          "base_pair_seed": args.seed,
          "transition_pause_s": args.transition_pause,
          "completed_episodes": 0,
          "error_episodes": 0,
      },
      "episodes": [],
      "arm_summary": {},
      "paired_comparison": [],
      "decision": {},
      "llm_analysis": {"status": "pending"},
      "experiment_complete": False,
  }


def _validate_resume_evidence(evidence: dict[str, Any], args: argparse.Namespace) -> None:
  scope = evidence.get("scope", {})
  if getattr(args, "full_suite", False):
    expected_tasks = list(scope.get("tasks", []))
    if len(expected_tasks) != BASELINE_TASK_COUNT:
      raise RuntimeError("Full-suite resume checkpoint does not contain 116 tasks")
  else:
    expected_tasks = [name.strip() for name in args.tasks.split(",") if name.strip()]
  recorded_transition_pause = scope.get("transition_pause_s")
  if recorded_transition_pause is None:
    original_command = evidence.get("command", [])
    if "--transition-pause" in original_command:
      pause_index = original_command.index("--transition-pause") + 1
      try:
        recorded_transition_pause = float(original_command[pause_index])
      except (IndexError, TypeError, ValueError):
        raise RuntimeError(
            "Resume checkpoint has an invalid original --transition-pause value"
        ) from None
  if evidence.get("experiment") not in {EXPERIMENT_ID, *LEGACY_EXPERIMENT_IDS}:
    raise RuntimeError("Resume checkpoint is not Experiment 6-11 evidence")
  checks = {
      "hypothesis": (evidence.get("hypothesis", {}).get("id"), args.hypothesis),
      "mode": (scope.get("mode"), args.mode.replace("-", "_")),
      "tasks": (scope.get("tasks"), expected_tasks),
      "trials": (scope.get("trials_per_task"), args.trials),
      "selected_trials": (
          scope.get("selected_trials", list(range(1, args.trials + 1))),
          getattr(args, "trial_indices", list(range(1, args.trials + 1))),
      ),
      "max_steps": (scope.get("max_steps"), args.max_steps),
      "model": (evidence.get("model", {}).get("model"), args.model),
      "model_seed": (evidence.get("model", {}).get("seed"), args.model_seed),
      "provider": (evidence.get("model", {}).get("provider"), args.provider),
      "base_url": (evidence.get("model", {}).get("base_url"), args.base_url),
      "max_model_tokens": (
          evidence.get("model", {}).get("max_tokens"), args.max_model_tokens
      ),
      "model_source": (
          evidence.get("model", {}).get("source", "hosted_api"),
          getattr(args, "model_source", "hosted_api"),
      ),
      "model_revision": (
          evidence.get("model", {}).get("revision"),
          getattr(args, "model_revision", None),
      ),
      "model_runtime": (
          evidence.get("model", {}).get("runtime"),
          getattr(args, "model_runtime", None),
      ),
      "accelerator": (
          evidence.get("model", {}).get("accelerator"),
          getattr(args, "accelerator", None),
      ),
      "input_cost": (
          evidence.get("model", {}).get("input_cost_per_million_usd", 0.0),
          getattr(args, "input_cost_per_million_usd", 0.0),
      ),
      "output_cost": (
          evidence.get("model", {}).get("output_cost_per_million_usd", 0.0),
          getattr(args, "output_cost_per_million_usd", 0.0),
      ),
      "transition_pause": (recorded_transition_pause, args.transition_pause),
      "skip_device_time": (
          evidence.get("environment", {}).get("skip_device_time"),
          args.skip_device_time,
      ),
      "console_port": (
          evidence.get("environment", {}).get("device_serial"),
          f"emulator-{args.console_port}",
      ),
      "grpc_port": (
          evidence.get("environment", {}).get("grpc_port"), args.grpc_port
      ),
      "execution_shard": (
          evidence.get("environment", {}).get("execution_shard"),
          getattr(args, "execution_shard", None),
      ),
  }
  mismatches = [
      f"{name}: checkpoint={observed!r}, command={expected!r}"
      for name, (observed, expected) in checks.items()
      if observed != expected
  ]
  if mismatches:
    raise RuntimeError("Resume configuration mismatch: " + "; ".join(mismatches))
  seen = set()
  for row in evidence.get("episodes", []):
    key = (row.get("task"), row.get("trial"), row.get("arm"))
    if key in seen:
      raise RuntimeError(f"Resume checkpoint contains duplicate episode arm: {key}")
    seen.add(key)
    try:
      task_index = expected_tasks.index(str(row.get("task")))
      trial_index = int(row.get("trial")) - 1
    except (ValueError, TypeError):
      raise RuntimeError("Resume checkpoint has an invalid task/trial episode key") from None
    expected_pair_seed = args.seed + task_index * 1009 + trial_index
    if row.get("pair_seed") != expected_pair_seed:
      raise RuntimeError(
          "Resume seed mismatch for "
          f"{row.get('task')} trial {row.get('trial')}: "
          f"checkpoint={row.get('pair_seed')!r}, command={expected_pair_seed!r}"
      )


def _append_boundary(evidence: dict[str, Any], message: str) -> None:
  boundaries = evidence.setdefault("environment_boundaries", [])
  if message not in boundaries:
    boundaries.append(message)


def _choose_paired_decision(
    args: argparse.Namespace,
    arm_summary: dict[str, dict[str, Any]],
    pairs: list[dict[str, Any]],
) -> dict[str, Any]:
  if args.hypothesis == "H5C":
    return choose_efficiency_decision(arm_summary, pairs)
  return choose_decision(arm_summary, pairs)


def main() -> int:
  args = _parse_args()
  retry_error_params: dict[tuple[str, int], Any] = {}
  if args.resume:
    output_dir = args.output_dir
    evidence = _read_evidence(
        output_dir / "evidence.json", purpose="resume checkpoint"
    )
    _validate_resume_evidence(evidence, args)
    run_id = evidence["run_id"]
    evidence.setdefault("resume_commands", []).append(
        [Path(sys.argv[0]).name, *sys.argv[1:]]
    )
    if args.retry_errors:
      error_episodes = [
          copy.deepcopy(row)
          for row in evidence.get("episodes", [])
          if row.get("status") != "completed"
      ]
      error_count = sum(
          row.get("status") != "completed" for row in evidence.get("episodes", [])
      )
      for row in error_episodes:
        key = (str(row.get("task")), int(row.get("trial", 0)))
        if key in retry_error_params and retry_error_params[key] != row.get("params"):
          raise RuntimeError(
              f"Error checkpoint contains inconsistent paired params for {key}"
          )
        retry_error_params[key] = copy.deepcopy(row.get("params"))
      evidence["episodes"] = [
          row for row in evidence.get("episodes", []) if row.get("status") == "completed"
      ]
      evidence.setdefault("retry_history", []).append({
          "at_utc": _utc_now(),
          "discarded_error_episodes": error_count,
          "reused_checkpoint_params": len(retry_error_params),
          "error_episode_keys": [
              {
                  "task": row.get("task"),
                  "trial": row.get("trial"),
                  "arm": row.get("arm"),
              }
              for row in error_episodes
          ],
      })
    # Upgrade interrupted schema-v1 checkpoints with the exact active policy.
    evidence["hypothesis"]["guardrails"] = (
        HYPOTHESIS_GUARDRAILS[args.hypothesis] + SCOPE_CAVEAT
    )
    evidence["scope"]["base_pair_seed"] = args.seed
    evidence["scope"]["transition_pause_s"] = args.transition_pause
    evidence["llm_analysis"] = {"status": "pending"}
    evidence.pop("fatal_error", None)
  else:
    run_id = "exp6-11-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path(__file__).resolve().parent / "validation" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    evidence = _base_evidence(args, run_id)
  secret_values = [value for key, value in os.environ.items() if "KEY" in key or "TOKEN" in key]
  env = None
  active_a11y_method = None
  emulator_setup_completed = bool(
      args.resume
      and evidence.get("environment", {}).get("emulator_setup_completed") is True
  )
  llm = None
  fatal_error = None

  try:
    bootstrap = _bootstrap_android_world(args.android_world_checkout)
    from android_world import registry
    from android_world.task_evals import task_eval

    checkout = args.android_world_checkout.resolve()
    commit = _run(["git", "rev-parse", "HEAD"], cwd=checkout)
    checkout_status = _run(["git", "status", "--porcelain"], cwd=checkout)
    if checkout_status:
      raise RuntimeError("AndroidWorld checkout is dirty; refusing an ambiguous run")

    if args.source_phase1_evidence:
      phase1_source = _read_evidence(
          args.source_phase1_evidence.resolve(), purpose="phase-1"
      )
      _validate_phase1_source(phase1_source)
      recorded_phase1 = evidence.get("phase", {}).get("source_phase1_run_id")
      if args.resume and recorded_phase1 and recorded_phase1 != phase1_source["run_id"]:
        raise RuntimeError("Resume phase-1 source does not match the checkpoint")
      evidence["phase"]["source_phase1_run_id"] = phase1_source["run_id"]
      evidence["phase"]["source_phase1_decision"] = phase1_source.get("decision")

    if args.source_phase2_evidence:
      phase2_source = _read_evidence(
          args.source_phase2_evidence.resolve(), purpose="phase-2"
      )
      _validate_phase2_source(phase2_source)
      recorded_phase2 = evidence.get("phase", {}).get("source_phase2_run_id")
      if args.resume and recorded_phase2 and recorded_phase2 != phase2_source["run_id"]:
        raise RuntimeError("Resume phase-2 source does not match the checkpoint")
      evidence["phase"]["source_phase2_run_id"] = phase2_source["run_id"]
      evidence["phase"]["source_phase2_decision"] = phase2_source.get("decision")

    if args.source_paired_evidence:
      paired_source = _read_evidence(
          args.source_paired_evidence.resolve(), purpose="paired candidate-source"
      )
      _validate_candidate_source(paired_source, args.hypothesis)
      if args.source_paired_run_id and args.source_paired_run_id != paired_source["run_id"]:
        raise RuntimeError("--source-paired-run-id does not match --source-paired-evidence")
      evidence["decision"] = {
          "outcome": "candidate_rerun_in_progress",
          "promote_to_full_suite_candidate": True,
          "deployment_approved": False,
          "source_paired_run_id": paired_source["run_id"],
          "source_paired_evidence": str(args.source_paired_evidence.resolve()),
          "source_paired_decision": paired_source.get("decision"),
          "reason": "The source paired run passed success/cost guardrails; direct candidate rerun evidence is still required.",
      }
      evidence["decision"]["source_paired_model"] = paired_source.get("model")
      source_model = paired_source.get("model", {}).get("model")
      if source_model and source_model != args.model:
        _append_boundary(
            evidence,
            "The full-suite candidate uses model "
            f"{args.model}, while the promoted paired H5C source used {source_model}. "
            "This local-GPU campaign evaluates the promoted observation treatment but is "
            "not a same-model extension of the paired result.",
        )

    api_level = int(_adb(args.adb_path, args.console_port, "shell", "getprop", "ro.build.version.sdk"))
    evidence["environment"] = {
        "android_world_checkout": str(checkout),
        "android_world_commit": commit,
        "android_world_checkout_clean": True,
        "upstream_tested_device": "Pixel 6",
        "upstream_tested_api_level": 33,
        "device_serial": f"emulator-{args.console_port}",
        "device_model": _adb(args.adb_path, args.console_port, "shell", "getprop", "ro.product.model"),
        "avd_name": _adb(args.adb_path, args.console_port, "shell", "getprop", "ro.boot.qemu.avd_name"),
        "api_level": api_level,
        "physical_size": _adb(args.adb_path, args.console_port, "shell", "wm", "size"),
        "grpc_port": args.grpc_port,
        "execution_shard": args.execution_shard,
        "perform_emulator_setup": args.perform_emulator_setup,
        "emulator_setup_completed": emulator_setup_completed,
        "skip_device_time": args.skip_device_time,
        "a11y_method": (
            "varies_by_arm:a11y_forwarder_app_vs_uiautomator"
            if args.hypothesis == "H5" and args.mode == "paired"
            else "varies_by_arm:uiautomator_vs_uiautomator_compact"
            if args.hypothesis == "H5C" and args.mode == "paired"
            else _arm_a11y_method(args, "candidate" if args.mode == "candidate-rerun" else "control")
        ),
        "protobuf_bootstrap": bootstrap,
    }
    app_provisioning = _collect_app_provenance(
        args.adb_path, args.console_port
    )
    evidence["environment"]["app_provisioning"] = app_provisioning
    if args.hypothesis in ("H5", "H5C") or args.a11y_method == "uiautomator":
      evidence["environment"]["evaluator_compatibility"] = [
          _install_uiautomator_evaluator_compatibility(),
          _install_clipper_timing_compatibility(),
          _install_sms_inbox_timing_compatibility(),
          _install_retro_queue_evaluator_compatibility(),
      ]
      evidence["environment"]["model_context_compatibility"] = {
          "trigger": "provider context-limit error after compact UIAutomator",
          "change": (
              "Retain at most 12,000 characters from the ends of the indexed "
              "current-screen UI section, or 6,000 characters from the ends of each "
              "before/after UI section in the summary prompt. Preserve prompt prefix, goal, history, "
              "leading/trailing UI elements with original indices, chosen action, "
              "reason, guidance, and output format; retry once."
          ),
          "per_episode_counters": (
              "llm.context_prompt_truncations and "
              "llm.context_prompt_chars_removed"
          ),
      }
      _append_boundary(
          evidence,
          "ContactsNewContactDraft's official success predicate was fed the upstream "
          "UIAutomator state.ui_elements because that observation mode does not populate "
          "state.forest; the predicate and requested contact fields were not changed.",
      )
      _append_boundary(
          evidence,
          "Clipboard get/set retries once after the exact Clipper foreground-access "
          "runtime error; the operation, content, task, and evaluator are unchanged.",
      )
      _append_boundary(
          evidence,
          "SimpleSmsReplyMostRecent polls the unchanged inbox query for up to five "
          "additional seconds because emulator-injected SMS delivery can lag past "
          "upstream's fixed wait. If the inbox remains empty, the exact last injected "
          "address/body is inserted into the same SMS database that upstream clears "
          "directly; task data and the evaluator are unchanged.",
      )
      _append_boundary(
          evidence,
          "The pinned official Retro Music APK omits the playing_queue table, a known "
          "upstream runtime error. Only that exact missing-table condition was mapped "
          "to an empty observed queue so the unchanged exact queue predicate records "
          "an evaluator failure instead of losing the episode.",
      )
      _append_boundary(
          evidence,
          "If compact UIAutomator still exceeds the pinned model's native 32,768-token "
          "context, the retry removes a bounded middle span only from indexed UI "
          "descriptions: at most 12,000 retained characters for action selection or "
          "6,000 for each before/after summary screen. Prompt prefix, goal, history, action, reason, "
          "leading/trailing UI elements and indices, guidance, and output format remain; "
          "per-episode removal counters are retained.",
      )
    if api_level != 33:
      _append_boundary(evidence,
          f"The available AVD is API {api_level}, while upstream is tested on Pixel 6 / API 33. Results are real but not reference-environment comparable."
      )
    if not app_provisioning["complete"]:
      _append_boundary(evidence,
          "The official AndroidWorld app bundle is incomplete; missing packages: "
          + ", ".join(app_provisioning["missing_packages"])
      )
    if args.hypothesis in ("H5", "H5C") or args.a11y_method == "uiautomator":
      _append_boundary(evidence,
          "UIAutomator is an upstream AndroidWorld observation option selected by the companion runner; it preserves real UI actions/evaluators but is a compatibility path, not the upstream API-33 reference configuration."
      )
    if args.hypothesis == "H5C":
      _append_boundary(evidence,
          "Compact UIAutomator removes only non-semantic container nodes; observations, coordinates, Android actions, and AndroidWorld evaluators remain real."
      )
    if retry_error_params:
      _append_boundary(
          evidence,
          "Runtime-error retries reuse the exact task parameters retained in the "
          "discarded error checkpoints; upstream parameter-generator drift cannot "
          "silently change the retried task.",
      )
    if args.skip_device_time:
      task_eval.TaskEval.initialize_device_time = lambda self, environment: None
      _append_boundary(evidence,
          "Per-task device-time setting was skipped because the non-root API-35 AVD rejects `adb shell date`; Wi-Fi evaluators do not depend on time."
      )

    task_registry = registry.TaskRegistry()
    registry_map = task_registry.get_registry(task_registry.ANDROID_WORLD_FAMILY)
    task_names = _select_tasks(args, registry_map)
    evidence["scope"]["tasks"] = task_names

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
      raise RuntimeError(f"Required real API credential is not set: {args.api_key_env}")
    llm = OpenAICompatibleLlm(
        api_key=api_key,
        base_url=args.base_url,
        model=args.model,
        seed=args.model_seed,
        max_tokens=args.max_model_tokens,
        timeout_s=args.model_timeout_s,
        retries=args.model_retries,
        input_cost_per_million_usd=args.input_cost_per_million_usd,
        output_cost_per_million_usd=args.output_cost_per_million_usd,
    )
    checkpoint_arm_keys = {
        (row["task"], int(row["trial"]), row["arm"])
        for row in evidence.get("episodes", [])
    }
    for task_index, task_name in enumerate(task_names):
      task_type = registry_map[task_name]
      for trial in (index - 1 for index in args.trial_indices):
        pair_seed = args.seed + task_index * 1009 + trial
        random.seed(pair_seed)
        params = task_type.generate_random_params()
        pair_id = f"{task_name}:trial-{trial + 1}:seed-{pair_seed}"
        retry_key = (task_name, trial + 1)
        if retry_key in retry_error_params:
          generated_params = _jsonable(params)
          params = copy.deepcopy(retry_error_params[retry_key])
          if generated_params != _jsonable(params):
            evidence.setdefault("retry_parameter_drift", []).append({
                "pair_id": pair_id,
                "reason": (
                    "The upstream generator drifted on resume; the exact parameters "
                    "from the runtime-error checkpoint were reused."
                ),
            })
        for checkpoint_episode in evidence.get("episodes", []):
          if checkpoint_episode.get("pair_id") == pair_id:
            if checkpoint_episode.get("params") != _jsonable(params):
              if args.mode == "candidate-rerun" and checkpoint_episode.get("arm") == "candidate":
                evidence.setdefault("resume_parameter_drift", []).append({
                    "pair_id": pair_id,
                    "reason": (
                        "The upstream parameter generator is not fully controlled by "
                        "Python random.seed; the completed checkpoint remains canonical "
                        "and was skipped rather than rerun."
                    ),
                })
              else:
                raise RuntimeError(
                    f"Generated params do not match checkpoint for {pair_id}"
                )
        if args.mode == "paired":
          arms = ["control", "treatment"]
          if (task_index + trial) % 2:
            arms.reverse()
        else:
          arms = ["candidate"]
        for order_position, arm in enumerate(arms, start=1):
          arm_key = (task_name, trial + 1, arm)
          if arm_key in checkpoint_arm_keys:
            print(f"\n=== {pair_id} / {arm} already checkpointed; skipping ===", flush=True)
            continue
          arm_a11y_method = _arm_a11y_method(args, arm)
          if env is None or active_a11y_method != arm_a11y_method:
            if env is not None:
              env.close()
              env = None
              active_a11y_method = None
            load_args = copy.copy(args)
            load_args.perform_emulator_setup = bool(
                args.perform_emulator_setup and not emulator_setup_completed
            )
            env = _load_android_env(load_args, arm_a11y_method)
            if load_args.perform_emulator_setup:
              emulator_setup_completed = True
              evidence["environment"]["emulator_setup_completed"] = True
              evidence["environment"]["app_provisioning"] = _collect_app_provenance(
                  args.adb_path, args.console_port
              )
            active_a11y_method = arm_a11y_method
          print(f"\n=== {pair_id} / {arm} ({order_position}/{len(arms)}) ===", flush=True)
          episode = _run_episode(
              env=env,
              task_type=task_type,
              params=params,
              task_name=task_name,
              trial=trial + 1,
              pair_id=pair_id,
              pair_seed=pair_seed,
              arm=arm,
              order_position=order_position,
              observation_method=arm_a11y_method,
              task_guidelines=_arm_guidelines(args, arm, task_name),
              llm=llm,
              max_steps=args.max_steps,
              transition_pause=args.transition_pause,
              secrets=secret_values,
          )
          evidence["episodes"].append(episode)
          # Checkpoint after every real episode so interruption does not erase evidence.
          evidence["scope"]["completed_episodes"] = sum(
              row["status"] == "completed" for row in evidence["episodes"]
          )
          evidence["scope"]["error_episodes"] = sum(
              row["status"] != "completed" for row in evidence["episodes"]
          )
          evidence["arm_summary"] = aggregate_episodes(evidence["episodes"])
          evidence["paired_comparison"] = paired_rows(evidence["episodes"])
          if args.mode == "paired":
            evidence["decision"] = _choose_paired_decision(
                args, evidence["arm_summary"], evidence["paired_comparison"]
            )
          enforce_scope_claims(evidence)
          (output_dir / "evidence.json").write_text(dumps_json(evidence), encoding="utf-8")
          if episode["status"] != "completed" and env is not None:
            env.close()
            env = None
            active_a11y_method = None

  except Exception as error:  # noqa: BLE001 - always persist an external blocker.
    fatal_error = redact_text(error, secret_values)[:4000]
    evidence["fatal_error"] = fatal_error
    _append_boundary(evidence, f"Run stopped by environment/runtime blocker: {fatal_error}")
  finally:
    if env is not None:
      try:
        env.close()
      except Exception as error:  # noqa: BLE001
        _append_boundary(evidence,
            "Environment close error: " + redact_text(error, secret_values)[:1000]
        )
    evidence["generated_at_utc"] = _utc_now()
    evidence["scope"]["completed_episodes"] = sum(
        row["status"] == "completed" for row in evidence["episodes"]
    )
    evidence["scope"]["error_episodes"] = sum(
        row["status"] != "completed" for row in evidence["episodes"]
    )
    evidence["arm_summary"] = aggregate_episodes(evidence["episodes"])
    evidence["paired_comparison"] = paired_rows(evidence["episodes"])
    if args.mode == "paired":
      evidence["decision"] = _choose_paired_decision(
          args, evidence["arm_summary"], evidence["paired_comparison"]
      )
    enforce_scope_claims(evidence)
    if args.mode == "candidate-rerun":
      if evidence["scope"]["full_suite_completed"]:
        evidence["decision"].update({
            "outcome": "full_candidate_rerun_completed",
            "deployment_approved": False,
            "reason": "The direct 116-task × five-trial candidate rerun completed. Deployment still requires reviewing the observed success/cost result against product thresholds.",
        })
      elif evidence["scope"]["error_episodes"]:
        evidence["decision"].update({
            "outcome": "candidate_rerun_has_errors",
            "deployment_approved": False,
            "reason": "The candidate rerun contains episode errors and cannot satisfy the completion or deployment gate.",
        })
      else:
        evidence["decision"].update({
            "outcome": "candidate_subset_rerun_completed",
            "deployment_approved": False,
            "reason": "A real modified candidate subset rerun completed, but it is not the 116-task × five-trial gate and cannot approve deployment.",
        })
    if llm is not None and evidence["episodes"]:
      evidence["llm_analysis"] = _generate_llm_analysis(
          evidence, llm, secret_values
      )
    elif fatal_error:
      evidence["llm_analysis"] = {
          "status": "not_run",
          "error": "No completed episode evidence was available for LLM analysis.",
      }
    (output_dir / "evidence.json").write_text(dumps_json(evidence), encoding="utf-8")
    (output_dir / "report.md").write_text(render_report(evidence), encoding="utf-8")
    print(f"Evidence: {output_dir / 'evidence.json'}")
    print(f"Report:   {output_dir / 'report.md'}")

  return 2 if fatal_error else 0


if __name__ == "__main__":
  raise SystemExit(main())
