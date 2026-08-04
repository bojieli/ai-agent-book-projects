#!/usr/bin/env python3
"""Checkpointed runner for the pinned Stanford Generative Agents experiment."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable


SOURCE_COMMIT = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"
BASE_SIM = "base_the_ville_n25"
SEED_SIM = "exp10_7_history_seed"
TARGET_STEPS = 17_280
DEFAULT_CHUNK_STEPS = 360
ARMS = ("baseline", "custom_goal", "no_reflection")
CUSTOM_CURRENTLY = (
    "Isabella Rodriguez is organizing a community climate-resilience workshop "
    "at Hobbs Cafe on February 14th, 2023, from 5pm to 7pm. She is gathering "
    "workshop materials, recruiting helpers, and inviting everyone she meets."
)
TASK_DECOMP_MARKER = "Describe subtasks in 5 min increments."
TASK_DECOMP_DURATION = re.compile(r"\(duration in minutes:\s*(\d+)\s*,")
TASK_DECOMP_TOTAL = re.compile(r"total duration in minutes:?\s*(\d+)")
TASK_DECOMP_PARSE_ERRORS = (IndexError, TypeError, ValueError)
TASK_DECOMP_ATTEMPTS = 5
POIGNANCY_SCALE_INSTRUCTION = "scale of 1 to 10"


class ValidatedZero(int):
    """Keep a parsed integer zero distinct from the legacy False sentinel."""

    def __new__(cls) -> "ValidatedZero":
        return super().__new__(cls, 0)

    def __eq__(self, other: object) -> bool:
        if other is False:
            return False
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        if other is False:
            return True
        return super().__ne__(other)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def git_commit(upstream: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=upstream, text=True
    ).strip()


def configure_imports(upstream: Path, storage: Path, temp_storage: Path) -> None:
    experiment_root = Path(__file__).resolve().parent
    backend = upstream / "reverie" / "backend_server"
    os.environ["GA_MAZE_ASSETS_ROOT"] = str(
        (upstream / "environment" / "frontend_server" / "static_dirs" / "assets").resolve()
    )
    os.environ["GA_STORAGE_ROOT"] = str(storage.resolve())
    os.environ["GA_TEMP_STORAGE_ROOT"] = str(temp_storage.resolve())
    temp_storage.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(experiment_root / "compat"))
    sys.path.insert(1, str(backend))
    os.chdir(backend)


def install_provider(receipt_path: Path) -> None:
    from provider_adapter import install

    install(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        api_base=os.environ.get(
            "GA_OPENAI_API_BASE",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        ),
        chat_model=os.environ.get("GA_CHAT_MODEL", "qwen3.7-flash"),
        embedding_model=os.environ.get(
            "GA_EMBEDDING_MODEL", "text-embedding-v4"
        ),
        receipt_path=receipt_path,
    )


def normalize_task_decomp_response(response: str, prompt: str) -> str | None:
    """Keep only parseable duration rows, bounded by the requested total."""

    total_match = TASK_DECOMP_TOTAL.search(prompt)
    if not total_match:
        return None
    expected = int(total_match.group(1))
    accumulated = 0
    rows = []
    for line in response.splitlines():
        stripped = line.strip()
        duration_match = TASK_DECOMP_DURATION.search(stripped)
        if not duration_match:
            continue
        rows.append(stripped)
        accumulated += int(duration_match.group(1))
        if accumulated >= expected:
            break
    return "\n".join(rows) if rows else None


def safe_task_decomp_generate(
    request: Callable[[str, dict[str, Any]], str],
    prompt: str,
    parameters: dict[str, Any],
    repeat: int,
    fail_safe: Any,
    validate: Callable[..., Any],
    clean_up: Callable[..., Any],
) -> Any:
    """Use raw output when valid, otherwise clean deterministic task rows."""

    last_parse_error: BaseException | None = None
    for _ in range(repeat):
        response = request(prompt, parameters)
        try:
            if validate(response, prompt=prompt):
                return clean_up(response, prompt=prompt)
        except TASK_DECOMP_PARSE_ERRORS as exc:
            last_parse_error = exc
        normalized = normalize_task_decomp_response(response, prompt)
        if normalized and normalized != response:
            try:
                return clean_up(normalized, prompt=prompt)
            except TASK_DECOMP_PARSE_ERRORS as exc:
                last_parse_error = exc
    if last_parse_error is not None:
        raise last_parse_error
    return fail_safe


def install_task_decomp_compat() -> None:
    """Repair task-decomposition parser input without editing upstream."""

    from persona.prompt_template import gpt_structure, run_gpt_prompt

    current = run_gpt_prompt.safe_generate_response
    if getattr(current, "_exp10_7_task_decomp_compat", False):
        return

    def guarded(
        prompt: str,
        parameters: dict[str, Any],
        repeat: int = TASK_DECOMP_ATTEMPTS,
        fail_safe_response: Any = "error",
        func_validate: Callable[..., Any] | None = None,
        func_clean_up: Callable[..., Any] | None = None,
        verbose: bool = False,
    ) -> Any:
        if (
            TASK_DECOMP_MARKER not in prompt
            or func_validate is None
            or func_clean_up is None
        ):
            return current(
                prompt,
                parameters,
                repeat,
                fail_safe_response,
                func_validate,
                func_clean_up,
                verbose,
            )
        return safe_task_decomp_generate(
            gpt_structure.GPT_request,
            prompt,
            parameters,
            repeat,
            fail_safe_response,
            func_validate,
            func_clean_up,
        )

    guarded._exp10_7_task_decomp_compat = True  # type: ignore[attr-defined]
    run_gpt_prompt.safe_generate_response = guarded


def install_validated_zero_compat() -> None:
    """Preserve validated zero poignancy instead of treating it as failure."""

    from persona.prompt_template import run_gpt_prompt

    current = run_gpt_prompt.ChatGPT_safe_generate_response
    if getattr(current, "_exp10_7_validated_zero_compat", False):
        return

    def guarded(
        prompt: str,
        example_output: Any,
        special_instruction: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        output = current(
            prompt,
            example_output,
            special_instruction,
            *args,
            **kwargs,
        )
        if (
            type(output) is int
            and output == 0
            and POIGNANCY_SCALE_INSTRUCTION in special_instruction
        ):
            return ValidatedZero()
        return output

    guarded._exp10_7_validated_zero_compat = True  # type: ignore[attr-defined]
    run_gpt_prompt.ChatGPT_safe_generate_response = guarded


def set_receipt_path(path: Path) -> None:
    from provider_adapter import RECORDER

    RECORDER.set_path(path)


def load_history(server: Any, history_path: Path) -> dict[str, int]:
    from persona.cognitive_modules.converse import load_history_via_whisper

    whispers: list[list[str]] = []
    with history_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = row["Name"].strip()
            whispers.extend(
                [name, item.strip()]
                for item in row["Whisper"].split(";")
                if item.strip()
            )
    for persona in server.personas.values():
        persona.scratch.curr_time = server.curr_time
    load_history_via_whisper(server.personas, whispers)
    for persona in server.personas.values():
        persona.scratch.curr_time = None
        memory_dir = (
            Path(os.environ["GA_STORAGE_ROOT"])
            / server.sim_code
            / "personas"
            / persona.name
            / "bootstrap_memory"
            / "associative_memory"
        )
        persona.a_mem.save(str(memory_dir))
    return {
        "rows": len({row[0] for row in whispers}),
        "whispers": len(whispers),
        "thought_nodes": sum(len(p.a_mem.seq_thought) for p in server.personas.values()),
    }


def _load_complete_json(path: Path, failures: "queue.Queue[BaseException]") -> dict:
    while True:
        if not failures.empty():
            raise failures.get()
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        time.sleep(0.01)


def drive_frontend(
    storage: Path,
    sim_code: str,
    starting_step: int,
    steps: int,
    failures: "queue.Queue[BaseException]",
) -> None:
    try:
        sim_dir = storage / sim_code
        for step in range(starting_step, starting_step + steps):
            movement = _load_complete_json(sim_dir / "movement" / f"{step}.json", failures)
            current = _load_complete_json(sim_dir / "environment" / f"{step}.json", failures)
            next_environment = {}
            for name, state in current.items():
                x, y = movement["persona"][name]["movement"]
                next_environment[name] = {"maze": state["maze"], "x": x, "y": y}
            output = sim_dir / "environment" / f"{step + 1}.json"
            temporary = output.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(next_environment, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, output)
    except BaseException as exc:
        failures.put(exc)


def compress_receipt(path: Path) -> Path:
    target = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as source, gzip.open(target, "wb", compresslevel=9) as output:
        shutil.copyfileobj(source, output)
    path.unlink()
    return target


def quarantine_artifact(path: Path) -> Path | None:
    """Move a non-canonical attempt aside without changing its file format."""

    if not path.exists():
        return None
    name = path.name
    for ending in (".jsonl.gz", ".jsonl"):
        if name.endswith(ending):
            stem = name[: -len(ending)]
            target = path.with_name(
                f"{stem}.failed-{time.time_ns()}{ending}"
            )
            path.rename(target)
            return target
    target = path.with_name(f"{name}.failed-{time.time_ns()}")
    path.rename(target)
    return target


def receipt_summary(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    counts: dict[str, int] = {}
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    calls = errors = 0
    transport_retries = 0
    latency = 0.0
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            calls += 1
            kind = row.get("kind", "unknown")
            counts[kind] = counts.get(kind, 0) + 1
            errors += not row.get("success", False)
            transport_retries += len(row.get("transport_retries") or [])
            latency += float(row.get("latency_seconds", 0))
            response_usage = (row.get("response") or {}).get("usage") or {}
            for key in usage:
                usage[key] += int(response_usage.get(key, 0) or 0)
    return {
        "calls": calls,
        "by_kind": counts,
        "errors": errors,
        "transport_retries": transport_retries,
        "usage": usage,
        "provider_latency_seconds": round(latency, 3),
    }


def validated_receipt_summary(
    receipt_path: Path, correction_path: Path
) -> dict[str, Any]:
    """Reject recovered checkpoints whose canonical receipt contains errors."""

    summary = receipt_summary(receipt_path)
    if summary["errors"]:
        failed_receipt = quarantine_artifact(receipt_path)
        failed_correction = quarantine_artifact(correction_path)
        raise RuntimeError(
            "provider errors make checkpoint non-canonical: "
            f"errors={summary['errors']}, receipt={failed_receipt}, "
            f"compatibility={failed_correction}"
        )
    return summary


def jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def ensure_base(upstream: Path, storage: Path) -> None:
    source = (
        upstream / "environment" / "frontend_server" / "storage" / BASE_SIM
    )
    target = storage / BASE_SIM
    storage.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copytree(source, target)


def prepare_seed(upstream: Path, output: Path) -> None:
    from reverie import ReverieServer

    storage = output / "storage"
    seed_dir = storage / SEED_SIM
    status_path = output / "seed_status.json"
    if status_path.exists() and seed_dir.exists():
        status = json.loads(status_path.read_text())
        if status.get("complete"):
            print(json.dumps(status, indent=2))
            return
    if seed_dir.exists():
        shutil.rmtree(seed_dir)
    receipt_path = output / "receipts" / "seed_history.jsonl"
    if receipt_path.exists():
        failed = receipt_path.with_name(
            f"seed_history.failed-{int(time.time())}.jsonl"
        )
        receipt_path.rename(failed)
    set_receipt_path(receipt_path)
    started = time.perf_counter()
    with open(os.devnull, "w") as sink, redirect_stdout(sink):
        server = ReverieServer(BASE_SIM, SEED_SIM)
        history_path = (
            upstream
            / "environment"
            / "frontend_server"
            / "static_dirs"
            / "assets"
            / "the_ville"
            / "agent_history_init_n25.csv"
        )
        history = load_history(server, history_path)
    compressed = compress_receipt(receipt_path)
    status = {
        "schema_version": 1,
        "experiment": "10-7",
        "complete": True,
        "source_commit": SOURCE_COMMIT,
        "seed_sim": SEED_SIM,
        "personas": len(server.personas),
        "step": server.step,
        "current_time": server.curr_time.isoformat(),
        "history": history,
        "receipt": str(compressed.relative_to(output)),
        "receipt_summary": receipt_summary(compressed),
        "wall_seconds": round(time.perf_counter() - started, 3),
    }
    atomic_json(status_path, status)
    print(json.dumps(status, indent=2))


def configure_arm(server: Any, arm: str, starting_step: int) -> None:
    if arm == "custom_goal" and starting_step == 0:
        server.personas["Isabella Rodriguez"].scratch.currently = CUSTOM_CURRENTLY
    if arm == "no_reflection":
        from persona.persona import Persona

        Persona.reflect = lambda self: None
        for persona in server.personas.values():
            persona.scratch.importance_trigger_max = 1_000_000_000
            persona.scratch.importance_trigger_curr = 1_000_000_000


def run_arm(
    upstream: Path,
    output: Path,
    arm: str,
    target_steps: int,
    chunk_steps: int,
    max_chunks: int | None,
) -> None:
    from reverie import ReverieServer
    from action_arena_compat import install as install_action_arena_compat

    correction_recorder = install_action_arena_compat()
    install_task_decomp_compat()
    install_validated_zero_compat()

    seed_status = json.loads((output / "seed_status.json").read_text())
    if not seed_status.get("complete"):
        raise RuntimeError("history seed is incomplete")
    storage = output / "storage"
    status_path = output / "status" / f"{arm}.json"
    if status_path.exists():
        status = json.loads(status_path.read_text())
    else:
        status = {
            "schema_version": 1,
            "experiment": "10-7",
            "source_commit": SOURCE_COMMIT,
            "arm": arm,
            "personas": 25,
            "target_steps": target_steps,
            "sec_per_step": 10,
            "current_sim": SEED_SIM,
            "completed_steps": 0,
            "checkpoints": [],
            "complete": False,
        }
    chunks_this_run = 0
    while status["completed_steps"] < target_steps:
        if max_chunks is not None and chunks_this_run >= max_chunks:
            break
        start_step = int(status["completed_steps"])
        steps = min(chunk_steps, target_steps - start_step)
        end_step = start_step + steps
        sim_code = f"exp10_7_{arm}_{end_step:05d}"
        target_dir = storage / sim_code
        if target_dir.exists():
            shutil.rmtree(target_dir)
        receipt_path = output / "receipts" / arm / f"steps_{start_step:05d}_{end_step:05d}.jsonl"
        quarantine_artifact(receipt_path)
        quarantine_artifact(receipt_path.with_suffix(receipt_path.suffix + ".gz"))
        correction_path = (
            output
            / "compatibility"
            / arm
            / f"steps_{start_step:05d}_{end_step:05d}.jsonl"
        )
        quarantine_artifact(correction_path)
        set_receipt_path(receipt_path)
        correction_recorder.set_path(correction_path)
        started = time.perf_counter()
        failures: "queue.Queue[BaseException]" = queue.Queue()
        with open(os.devnull, "w") as sink, redirect_stdout(sink):
            server = ReverieServer(status["current_sim"], sim_code)
            (target_dir / "movement").mkdir(exist_ok=True)
            if server.step != start_step:
                raise RuntimeError(
                    f"checkpoint step mismatch: expected {start_step}, got {server.step}"
                )
            configure_arm(server, arm, start_step)
            server.server_sleep = 0.001
            controller = threading.Thread(
                target=drive_frontend,
                args=(storage, sim_code, start_step, steps, failures),
                daemon=True,
            )
            controller.start()
            server.start_server(steps)
            controller.join(timeout=30)
            if controller.is_alive():
                raise RuntimeError("headless frontend controller did not finish")
            if not failures.empty():
                raise failures.get()
            server.save()
        compressed = compress_receipt(receipt_path)
        provider_summary = validated_receipt_summary(compressed, correction_path)
        checkpoint = {
            "start_step": start_step,
            "end_step": end_step,
            "start_time": (server.curr_time - dt.timedelta(seconds=10 * steps)).isoformat(),
            "end_time": server.curr_time.isoformat(),
            "sim_code": sim_code,
            "receipt": str(compressed.relative_to(output)),
            "receipt_summary": provider_summary,
            "compatibility_receipt": (
                str(correction_path.relative_to(output))
                if correction_path.exists()
                else None
            ),
            "compatibility_corrections": jsonl_rows(correction_path),
            "wall_seconds": round(time.perf_counter() - started, 3),
        }
        previous_sim = status["current_sim"]
        status["current_sim"] = sim_code
        status["completed_steps"] = end_step
        status["checkpoints"].append(checkpoint)
        status["complete"] = end_step == target_steps
        atomic_json(status_path, status)
        if previous_sim not in {SEED_SIM, BASE_SIM} and start_step != 8_640:
            previous_dir = storage / previous_sim
            if previous_dir.exists():
                shutil.rmtree(previous_dir)
        chunks_this_run += 1
        print(json.dumps(checkpoint, ensure_ascii=False), flush=True)
    print(json.dumps(status, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("seed", "arm"), required=True)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--target-steps", type=int, default=TARGET_STEPS)
    parser.add_argument("--chunk-steps", type=int, default=DEFAULT_CHUNK_STEPS)
    parser.add_argument("--max-chunks", type=int)
    args = parser.parse_args()
    upstream = args.upstream.resolve()
    output = args.output.resolve()
    if git_commit(upstream) != SOURCE_COMMIT:
        raise SystemExit(f"upstream must be pinned to {SOURCE_COMMIT}")
    output.mkdir(parents=True, exist_ok=True)
    storage = output / "storage"
    temp_storage = output / "temp" / (args.arm or "seed")
    ensure_base(upstream, storage)
    configure_imports(upstream, storage, temp_storage)
    initial_receipt = output / "receipts" / "bootstrap.jsonl"
    install_provider(initial_receipt)
    if args.mode == "seed":
        prepare_seed(upstream, output)
    else:
        if not args.arm:
            parser.error("--arm is required with --mode arm")
        run_arm(
            upstream,
            output,
            args.arm,
            args.target_steps,
            args.chunk_steps,
            args.max_chunks,
        )
    if initial_receipt.exists() and initial_receipt.stat().st_size == 0:
        initial_receipt.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
