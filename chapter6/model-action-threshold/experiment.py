#!/usr/bin/env python3
"""Controlled model action-threshold experiment for Chapter 6.

The experiment holds the coding harness, prompt, tools, task repositories, and
sampling order fixed while swapping only the model identifier.  It measures
how much evidence a model gathers before its first edit and whether acting
earlier or later leads to a correct, low-rework solution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


ROOT = Path(__file__).resolve().parent
TASKS_ROOT = ROOT / "tasks"
DEFAULT_MODELS = ["openai/gpt-5.6-sol", "anthropic/claude-sonnet-5"]
BASE_URL = "https://openrouter.ai/api/v1"
EDIT_TOOLS = {"replace_text", "write_file"}
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache"}

NEUTRAL_SYSTEM_PROMPT = """You are a coding agent working in a small repository.
Complete the user's task using the provided repository tools. Keep the change
scoped, preserve public behavior not mentioned in the task, and use tests when
they help you validate the result. When the task is complete, respond with a
concise summary. The harness will independently run the test command. Do not
ask the user to perform any steps."""

EXPLORE_SYSTEM_SUFFIX = """

Before editing, inspect the repository structure, relevant implementation,
callers, and tests so that you understand the full impact of the change."""


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List repository files under a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search for a literal string in repository text files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_text",
            "description": "Replace one exact text block in an existing UTF-8 file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"},
                },
                "required": ["path", "old_text", "new_text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new UTF-8 text file. Refuses to overwrite an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the task's fixed test command and return its output.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_task(task_id: str) -> dict[str, Any]:
    task_dir = TASKS_ROOT / task_id
    metadata = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    metadata["task_id"] = task_id
    metadata["source_repo"] = task_dir / "repo"
    return metadata


def discover_tasks() -> list[str]:
    return sorted(path.parent.name for path in TASKS_ROOT.glob("*/task.json"))


def safe_path(repo: Path, relative: str) -> Path:
    candidate = (repo / relative).resolve()
    root = repo.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path escapes repository: {relative}")
    return candidate


def visible_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts)
    ]


def snapshot(repo: Path) -> dict[str, str]:
    return {
        str(path.relative_to(repo)): sha256_file(path)
        for path in visible_files(repo)
    }


def changed_files(before: dict[str, str], repo: Path) -> list[str]:
    after = snapshot(repo)
    return sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )


def run_test_command(repo: Path, command: list[str], timeout: int = 30) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            text=True,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
        )
        output = (completed.stdout + completed.stderr)[-12000:]
        return {
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "duration_s": round(time.monotonic() - started, 4),
            "output": output,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "passed": False,
            "returncode": None,
            "duration_s": round(time.monotonic() - started, 4),
            "output": f"test timeout: {exc}",
        }


@dataclass
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0

    def add_response(self, response: Any) -> None:
        raw = getattr(response, "usage", None)
        if raw is None:
            return
        self.input_tokens += int(getattr(raw, "prompt_tokens", 0) or 0)
        self.output_tokens += int(getattr(raw, "completion_tokens", 0) or 0)
        prompt_details = getattr(raw, "prompt_tokens_details", None)
        completion_details = getattr(raw, "completion_tokens_details", None)
        self.cached_input_tokens += int(getattr(prompt_details, "cached_tokens", 0) or 0)
        self.reasoning_tokens += int(getattr(completion_details, "reasoning_tokens", 0) or 0)


@dataclass
class TraceState:
    started: float
    events: list[dict[str, Any]] = field(default_factory=list)
    first_edit_sequence: int | None = None
    first_edit_elapsed_s: float | None = None
    first_successful_edit_sequence: int | None = None
    first_successful_edit_elapsed_s: float | None = None
    first_patch_test_passed: bool | None = None
    edits_after_first_test: int = 0
    tests_after_edit: int = 0
    usage: Usage = field(default_factory=Usage)

    def log(self, event_type: str, **payload: Any) -> dict[str, Any]:
        event = {
            "sequence": len(self.events) + 1,
            "elapsed_s": round(time.monotonic() - self.started, 4),
            "type": event_type,
            **payload,
        }
        self.events.append(event)
        return event

    def record_tool(self, name: str, arguments: dict[str, Any], result: dict[str, Any]) -> None:
        event = self.log("tool", tool=name, arguments=arguments, result=result)
        if name in EDIT_TOOLS:
            if self.first_edit_sequence is None:
                self.first_edit_sequence = event["sequence"]
                self.first_edit_elapsed_s = event["elapsed_s"]
            if result.get("ok") and self.first_successful_edit_sequence is None:
                self.first_successful_edit_sequence = event["sequence"]
                self.first_successful_edit_elapsed_s = event["elapsed_s"]
            elif result.get("ok") and self.first_patch_test_passed is not None:
                self.edits_after_first_test += 1
        elif name == "run_tests" and self.first_successful_edit_sequence is not None:
            self.tests_after_edit += 1
            if self.first_patch_test_passed is None:
                self.first_patch_test_passed = bool(result.get("passed"))


class RepositoryHarness:
    def __init__(self, repo: Path, test_command: list[str], trace: TraceState):
        self.repo = repo
        self.test_command = test_command
        self.trace = trace

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            if name == "list_files":
                base = safe_path(self.repo, arguments.get("path", "."))
                if not base.exists():
                    result = {"error": "path does not exist"}
                else:
                    files = [str(path.relative_to(self.repo)) for path in visible_files(base)]
                    result = {"files": files[:500], "count": len(files)}
            elif name == "read_file":
                path = safe_path(self.repo, arguments["path"])
                text = path.read_text(encoding="utf-8")
                numbered = "\n".join(
                    f"{index:4d}: {line}" for index, line in enumerate(text.splitlines(), 1)
                )
                result = {"path": str(path.relative_to(self.repo)), "content": numbered[:30000]}
            elif name == "search":
                base = safe_path(self.repo, arguments.get("path", "."))
                query = arguments["query"]
                matches: list[str] = []
                for path in visible_files(base):
                    try:
                        lines = path.read_text(encoding="utf-8").splitlines()
                    except UnicodeDecodeError:
                        continue
                    for line_number, line in enumerate(lines, 1):
                        if query in line:
                            matches.append(
                                f"{path.relative_to(self.repo)}:{line_number}:{line}"
                            )
                result = {"matches": matches[:200], "count": len(matches)}
            elif name == "replace_text":
                path = safe_path(self.repo, arguments["path"])
                text = path.read_text(encoding="utf-8")
                old = arguments["old_text"]
                count = text.count(old)
                if count != 1:
                    result = {"error": f"old_text occurs {count} times; expected exactly once"}
                else:
                    path.write_text(text.replace(old, arguments["new_text"], 1), encoding="utf-8")
                    result = {"ok": True, "path": str(path.relative_to(self.repo))}
            elif name == "write_file":
                path = safe_path(self.repo, arguments["path"])
                if path.exists():
                    result = {"error": "file already exists"}
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(arguments["content"], encoding="utf-8")
                    result = {"ok": True, "path": str(path.relative_to(self.repo))}
            elif name == "run_tests":
                result = run_test_command(self.repo, self.test_command)
            else:
                result = {"error": f"unknown tool: {name}"}
        except (KeyError, OSError, UnicodeError, ValueError) as exc:
            result = {"error": f"{type(exc).__name__}: {exc}"}
        self.trace.record_tool(name, arguments, result)
        return result


def pre_edit_metrics(events: list[dict[str, Any]], first_edit_sequence: int | None) -> dict[str, Any]:
    boundary = first_edit_sequence if first_edit_sequence is not None else float("inf")
    tools = [event for event in events if event["type"] == "tool" and event["sequence"] < boundary]
    reads = [event for event in tools if event["tool"] == "read_file"]
    searches = [event for event in tools if event["tool"] == "search"]
    files = {
        event["result"].get("path")
        for event in reads
        if event["result"].get("path") is not None
    }
    return {
        "tool_calls_before_first_edit": len(tools),
        "read_calls_before_first_edit": len(reads),
        "search_calls_before_first_edit": len(searches),
        "unique_files_read_before_first_edit": len(files),
        "files_read_before_first_edit": sorted(files),
    }


def call_model(client: Any, model: str, messages: list[dict[str, Any]]) -> Any:
    return client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=4096,
    )


def run_cell(
    client: Any,
    model: str,
    task: dict[str, Any],
    trial: int,
    policy: str,
    max_turns: int,
) -> dict[str, Any]:
    started_wall = utc_now()
    started = time.monotonic()
    trace = TraceState(started=started)
    with tempfile.TemporaryDirectory(prefix="action-threshold-") as temp_dir:
        repo = Path(temp_dir) / "repo"
        shutil.copytree(task["source_repo"], repo)
        # macOS exposes /var through a /private/var symlink. Resolve once so
        # path-confinement and relative-path reporting use the same root.
        repo = repo.resolve()
        baseline = snapshot(repo)
        baseline_test = run_test_command(repo, task["test_command"])
        system_prompt = NEUTRAL_SYSTEM_PROMPT
        if policy == "explore-first":
            system_prompt += EXPLORE_SYSTEM_SUFFIX
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task["instruction"]},
        ]
        run_error: str | None = None
        final_text = ""

        for turn in range(1, max_turns + 1):
            try:
                response = call_model(client, model, messages)
            except Exception as exc:  # API failures are experiment observations.
                run_error = f"{type(exc).__name__}: {exc}"
                trace.log("api_error", turn=turn, error=run_error)
                break
            trace.usage.add_response(response)
            message = response.choices[0].message
            final_text = message.content or ""
            tool_calls = message.tool_calls or []
            assistant_payload: dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ]
            messages.append(assistant_payload)
            trace.log(
                "assistant",
                turn=turn,
                text=message.content or "",
                tool_names=[call.function.name for call in tool_calls],
            )
            if not tool_calls:
                break
            harness = RepositoryHarness(repo, task["test_command"], trace)
            for tool_call in tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as exc:
                    arguments = {}
                    result = {"error": f"invalid tool JSON: {exc}"}
                    trace.record_tool(tool_call.function.name, arguments, result)
                else:
                    result = harness.execute(tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
        else:
            run_error = f"maximum turns reached ({max_turns})"

        final_test = run_test_command(repo, task["test_command"])
        changed = changed_files(baseline, repo)
        edits = [
            event for event in trace.events
            if event["type"] == "tool" and event["tool"] in EDIT_TOOLS
        ]
        successful_edits = [event for event in edits if event["result"].get("ok")]
        metrics = pre_edit_metrics(trace.events, trace.first_edit_sequence)
        return {
            "schema_version": 1,
            "model": model,
            "task_id": task["task_id"],
            "task_category": task["category"],
            "trial": trial,
            "policy": policy,
            "started_at_utc": started_wall,
            "duration_s": round(time.monotonic() - started, 4),
            "baseline_test_passed": baseline_test["passed"],
            "baseline_test_returncode": baseline_test["returncode"],
            "run_error": run_error,
            "first_edit_sequence": trace.first_edit_sequence,
            "seconds_to_first_edit": trace.first_edit_elapsed_s,
            "first_successful_edit_sequence": trace.first_successful_edit_sequence,
            "seconds_to_first_successful_edit": trace.first_successful_edit_elapsed_s,
            **metrics,
            "first_patch_test_passed": trace.first_patch_test_passed,
            "edit_attempts_total": len(edits),
            "successful_edit_calls_total": len(successful_edits),
            "edits_after_first_test": trace.edits_after_first_test,
            "tests_after_edit": trace.tests_after_edit,
            "changed_files": changed,
            "changed_file_count": len(changed),
            "final_test_passed": final_test["passed"],
            "final_test_returncode": final_test["returncode"],
            "final_test_output": final_test["output"],
            "final_text": final_text,
            "usage": asdict(trace.usage),
            "events": trace.events,
        }


def mean_or_none(values: list[float | int | None]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    return round(statistics.mean(cleaned), 4) if cleaned else None


def summarize(observations: list[dict[str, Any]]) -> dict[str, Any]:
    models = sorted({row["model"] for row in observations})
    by_model: list[dict[str, Any]] = []
    for model in models:
        rows = [row for row in observations if row["model"] == model]
        tested_first_patches = [
            row for row in rows if row["first_patch_test_passed"] is not None
        ]
        by_model.append(
            {
                "model": model,
                "runs": len(rows),
                "completed_without_api_error": sum(row["run_error"] is None for row in rows),
                "final_pass_rate": round(sum(row["final_test_passed"] for row in rows) / len(rows), 4),
                "first_patch_pass_rate": (
                    round(
                        sum(row["first_patch_test_passed"] for row in tested_first_patches)
                        / len(tested_first_patches),
                        4,
                    )
                    if tested_first_patches else None
                ),
                "mean_tool_calls_before_first_edit": mean_or_none(
                    [row["tool_calls_before_first_edit"] for row in rows]
                ),
                "mean_unique_files_read_before_first_edit": mean_or_none(
                    [row["unique_files_read_before_first_edit"] for row in rows]
                ),
                "mean_seconds_to_first_edit": mean_or_none(
                    [row["seconds_to_first_edit"] for row in rows]
                ),
                "mean_edit_attempts": mean_or_none([row["edit_attempts_total"] for row in rows]),
                "mean_successful_edit_calls": mean_or_none(
                    [row["successful_edit_calls_total"] for row in rows]
                ),
                "mean_edits_after_first_test": mean_or_none(
                    [row["edits_after_first_test"] for row in rows]
                ),
                "mean_changed_files": mean_or_none([row["changed_file_count"] for row in rows]),
                "total_input_tokens": sum(row["usage"]["input_tokens"] for row in rows),
                "total_output_tokens": sum(row["usage"]["output_tokens"] for row in rows),
            }
        )
    return {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "observation_count": len(observations),
        "by_model": by_model,
        "by_task": [
            {
                "task_id": task_id,
                "models": [
                    {
                        "model": model,
                        "runs": len(rows := [
                            row for row in observations
                            if row["task_id"] == task_id and row["model"] == model
                        ]),
                        "final_pass_rate": (
                            round(sum(row["final_test_passed"] for row in rows) / len(rows), 4)
                            if rows else None
                        ),
                        "mean_files_read_before_edit": mean_or_none(
                            [row["unique_files_read_before_first_edit"] for row in rows]
                        ),
                    }
                    for model in models
                ],
            }
            for task_id in sorted({row["task_id"] for row in observations})
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_campaign(
    output_dir: Path,
    config: dict[str, Any],
    observations: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "config.json"
    observations_path = output_dir / "observations.jsonl"
    summary_path = output_dir / "summary.json"
    write_json(config_path, config)
    observations_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in observations),
        encoding="utf-8",
    )
    write_json(summary_path, summarize(observations))
    artifacts = [config_path, observations_path, summary_path]
    expected = len(config["models"]) * len(config["tasks"]) * config["trials"]
    api_errors = sum(row["run_error"] is not None for row in observations)
    manifest = {
        "schema_version": 1,
        "created_at_utc": utc_now(),
        "status": (
            "complete" if len(observations) == expected and api_errors == 0 else "incomplete"
        ),
        "expected_observations": expected,
        "actual_observations": len(observations),
        "api_error_count": api_errors,
        "artifacts": {
            path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in artifacts
        },
    }
    write_json(output_dir / "manifest.json", manifest)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--tasks", nargs="+", default=discover_tasks())
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--policy", choices=["neutral", "explore-first"], default="neutral")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    )
    parser.add_argument("--list-tasks", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_tasks:
        for task_id in discover_tasks():
            task = load_task(task_id)
            print(f"{task_id}\t{task['category']}\t{task['instruction']}")
        return 0
    if args.trials < 1:
        raise SystemExit("--trials must be at least 1")
    unknown = sorted(set(args.tasks) - set(discover_tasks()))
    if unknown:
        raise SystemExit(f"unknown tasks: {', '.join(unknown)}")
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"{args.api_key_env} is not set")
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=args.base_url, timeout=180.0)
    config = {
        "schema_version": 1,
        "created_at_utc": utc_now(),
        "models": args.models,
        "tasks": args.tasks,
        "trials": args.trials,
        "policy": args.policy,
        "max_turns": args.max_turns,
        "base_url": args.base_url,
        "system_prompt_sha256": hashlib.sha256(
            (NEUTRAL_SYSTEM_PROMPT + (EXPLORE_SYSTEM_SUFFIX if args.policy == "explore-first" else "")).encode()
        ).hexdigest(),
        "tool_schema_sha256": hashlib.sha256(
            json.dumps(TOOLS, sort_keys=True).encode()
        ).hexdigest(),
    }
    observations_path = args.output / "observations.jsonl"
    observations: list[dict[str, Any]] = []
    if observations_path.exists():
        saved_config_path = args.output / "config.json"
        if not saved_config_path.exists():
            raise SystemExit("cannot resume: observations.jsonl exists without config.json")
        saved_config = json.loads(saved_config_path.read_text(encoding="utf-8"))
        execution_keys = {
            "models", "tasks", "trials", "policy", "max_turns", "base_url",
            "system_prompt_sha256", "tool_schema_sha256",
        }
        if any(saved_config.get(key) != config.get(key) for key in execution_keys):
            raise SystemExit("cannot resume: saved campaign configuration does not match")
        observations = [
            json.loads(line) for line in observations_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        config = saved_config
        print(f"Resuming {len(observations)} saved observations from {args.output}", flush=True)
    completed = {
        (row["model"], row["task_id"], row["trial"], row["policy"])
        for row in observations
    }
    for trial in range(1, args.trials + 1):
        model_order = args.models if trial % 2 else list(reversed(args.models))
        for task_id in args.tasks:
            task = load_task(task_id)
            for model in model_order:
                cell = (model, task_id, trial, args.policy)
                if cell in completed:
                    continue
                print(f"[{len(observations) + 1}] model={model} task={task_id} trial={trial}", flush=True)
                row = run_cell(client, model, task, trial, args.policy, args.max_turns)
                observations.append(row)
                completed.add(cell)
                print(
                    f"    pre-edit files={row['unique_files_read_before_first_edit']} "
                    f"tools={row['tool_calls_before_first_edit']} "
                    f"final_pass={row['final_test_passed']} error={row['run_error']}",
                    flush=True,
                )
                write_campaign(args.output, config, observations)
    print(f"Results: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
