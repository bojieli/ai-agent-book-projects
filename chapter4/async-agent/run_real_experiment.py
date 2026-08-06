#!/usr/bin/env python3
"""Run all four Experiment 4-6 scenarios with real child processes."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tasks
from tasks import TaskManager, TaskState

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"
VALIDATION_ROOT = HERE / "validation" / "experiment_4_6"
UTC = timezone.utc


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8")


def task_receipt(state: TaskState) -> dict[str, Any]:
    result: Any = state.result
    try:
        result = json.loads(state.result) if state.result else None
    except json.JSONDecodeError:
        pass
    return {
        "task_id": state.task_id, "command": state.command,
        "status": state.status, "progress": state.progress,
        "pid": state.pid, "returncode": state.returncode,
        "started_at": state.started_at, "completed_at": state.completed_at,
        "elapsed_seconds": (
            round(state.completed_at - state.started_at, 3)
            if state.started_at and state.completed_at else None
        ),
        "stdout_sha256": state.stdout_sha256,
        "stderr_tail": state.stderr_tail,
        "result": result,
        "executable": state.executable_receipt,
    }


class ReceiptLog:
    def __init__(self):
        self.started = time.perf_counter()
        self.events: list[dict[str, Any]] = []

    def __call__(self, source: str, text: str) -> None:
        self.events.append({"elapsed_seconds": round(time.perf_counter() - self.started, 3),
                            "source": source, "text": text})

    def add(self, source: str, event: str, **details: Any) -> float:
        elapsed = round(time.perf_counter() - self.started, 3)
        self.events.append({"elapsed_seconds": elapsed, "source": source,
                            "event": event, **details})
        return elapsed


async def _await_cancelled(state: TaskState) -> None:
    if state._task is None:
        return
    try:
        await state._task
    except asyncio.CancelledError:
        pass


async def scenario_1() -> dict[str, Any]:
    log = ReceiptLog()
    completed_at: dict[str, float] = {}

    async def complete(state: TaskState) -> None:
        completed_at[state.task_id] = log.add("SYSTEM", "async_result_injected",
                                               task_id=state.task_id)

    manager = TaskManager(complete, log)
    before = time.perf_counter()
    state = manager.start("python analyze_logs.py")
    placeholder_latency = round(time.perf_counter() - before, 6)
    placeholder_at = log.add("TOOL", "placeholder_returned", task_id=state.task_id,
                             placeholder_latency_seconds=placeholder_latency)
    await asyncio.sleep(0.5)
    time_answer = datetime.now().astimezone().isoformat(timespec="seconds")
    time_answer_at = log.add("AGENT", "immediate_time_answer", answer=time_answer,
                             task_still_running=state.status == "running")
    assert state._task is not None
    await state._task
    return {
        "id": "async_command_and_immediate_question",
        "placeholder_latency_seconds": placeholder_latency,
        "placeholder_at": placeholder_at, "time_answer_at": time_answer_at,
        "completion_event_at": completed_at.get(state.task_id),
        "time_answer": time_answer, "events": log.events,
        "tasks": [task_receipt(state)],
    }


async def scenario_2(campaign_dir: Path) -> dict[str, Any]:
    log = ReceiptLog()
    pending: list[dict[str, Any]] = []
    batch: list[dict[str, Any]] = []

    async def complete(state: TaskState) -> None:
        batch.append({"type": "async.result", "task_id": state.task_id,
                      "result_sha256": sha256(state.result)})
        batch.extend(pending)
        log.add("SYSTEM", "batch_appended", event_count=len(batch),
                deferred_count=len(pending))

    manager = TaskManager(complete, log)
    state = manager.start("python analyze_logs.py")
    log.add("TOOL", "placeholder_returned", task_id=state.task_id)
    await asyncio.sleep(0.5)
    pending.append({"type": "user.input", "instruction": "記得最後用日語回覆"})
    first_at = log.add("QUEUE", "deferred_instruction", instruction="japanese")
    await asyncio.sleep(0.2)
    pending.append({"type": "user.input", "instruction": "結果をHTMLウェブページに整理"})
    second_at = log.add("QUEUE", "deferred_instruction", instruction="html")
    assert state._task is not None
    await state._task
    metrics = json.loads(state.result)
    html = (
        "<!DOCTYPE html><html lang=\"ja\"><meta charset=\"utf-8\">"
        "<title>非同期分析レポート</title><body><h1>分析結果</h1>"
        f"<p>対象ファイルは {metrics['lines']} 行、{metrics['bytes']} バイトです。</p>"
        f"<p>非同期に関する言及は {metrics['async_mentions']} 件でした。</p>"
        "</body></html>\n"
    )
    output = campaign_dir / "artifacts" / "scenario_2_report.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return {
        "id": "queued_batch_to_japanese_html",
        "instruction_times": [first_at, second_at],
        "batch": batch, "events": log.events,
        "artifact": {"path": str(output), "bytes": output.stat().st_size,
                     "sha256": sha256(output.read_bytes()),
                     "doctype": html.startswith("<!DOCTYPE html>"),
                     "lang_ja": 'lang="ja"' in html,
                     "has_japanese": bool(re.search(r"[ぁ-んァ-ン一-龯]", html))},
        "tasks": [task_receipt(state)],
    }


async def scenario_3() -> dict[str, Any]:
    log = ReceiptLog()
    completed: list[str] = []

    async def complete(state: TaskState) -> None:
        completed.append(state.task_id)
        log.add("SYSTEM", "async_result_injected", task_id=state.task_id)

    manager = TaskManager(complete, log)
    interrupted = manager.start("python analyze_logs.py")
    await asyncio.sleep(0.8)
    progress_at_interrupt = interrupted.progress
    interrupt_at = log.add("USER", "user.interrupt", text="取消",
                           task_id=interrupted.task_id,
                           progress=progress_at_interrupt)
    cancel_started = time.perf_counter()
    cancelled = manager.cancel_all()
    await _await_cancelled(interrupted)
    cancel_latency = round(time.perf_counter() - cancel_started, 3)
    cancel_receipt_at = log.add("SYSTEM", "process_cancelled", task_ids=cancelled,
                                cancel_latency_seconds=cancel_latency,
                                returncode=interrupted.returncode)
    recovery = manager.start("python re_run_summary.py")
    recovery_at = log.add("SYSTEM", "runtime_recovered", task_id=recovery.task_id)
    assert recovery._task is not None
    await recovery._task
    return {
        "id": "interrupt_terminates_and_recovers",
        "interrupt_at": interrupt_at, "cancel_receipt_at": cancel_receipt_at,
        "cancel_latency_seconds": cancel_latency,
        "recovery_at": recovery_at, "completed_callbacks": completed,
        "events": log.events,
        "tasks": [task_receipt(interrupted), task_receipt(recovery)],
    }


async def scenario_4(campaign_dir: Path) -> dict[str, Any]:
    log = ReceiptLog()
    completion_queue: asyncio.Queue[TaskState] = asyncio.Queue()

    async def complete(state: TaskState) -> None:
        log.add("SYSTEM", "async_result_injected", task_id=state.task_id)
        await completion_queue.put(state)

    manager = TaskManager(complete, log)
    states = [manager.start(command) for command in (
        "python analyze_fast.py", "python analyze_mid.py", "python analyze_slow.py"
    )]
    first = await asyncio.wait_for(completion_queue.get(), timeout=30)
    query_receipts = []
    cancelled_ids = []
    for state in states:
        if state.task_id == first.task_id or state.status != "running":
            continue
        query_receipts.append({"task_id": state.task_id, "status": state.status,
                               "progress": state.progress,
                               "queried_at": log.add("TOOL", "query_task",
                                                     task_id=state.task_id,
                                                     progress=state.progress)})
        if state.progress <= 50:
            if manager.cancel(state.task_id):
                cancelled_ids.append(state.task_id)
                log.add("TOOL", "cancel_task", task_id=state.task_id,
                        progress=state.progress)
    for state in states:
        await _await_cancelled(state)
    report_rows = [task_receipt(state) for state in states]
    report = {
        "first_completed": first.task_id, "query_receipts": query_receipts,
        "cancelled_ids": cancelled_ids,
        "completed_results": {row["task_id"]: row["result"] for row in report_rows
                              if row["status"] == "completed"},
    }
    output = campaign_dir / "artifacts" / "scenario_4_report.json"
    write_json(output, report)
    return {
        "id": "parallel_progress_threshold_cancellation",
        **report, "events": log.events, "tasks": report_rows,
        "artifact": {"path": str(output), "bytes": output.stat().st_size,
                     "sha256": sha256(output.read_bytes())},
    }


def real_task(receipt: dict[str, Any]) -> bool:
    executable = receipt.get("executable", {})
    common = (
        receipt.get("pid") is not None
        and executable.get("mode") == "real_subprocess"
        and executable.get("shell") is False
        and len(executable.get("worker_sha256", "")) == 64
        and len(executable.get("input_sha256", "")) == 64
        and len(executable.get("argv_sha256", "")) == 64
    )
    if receipt.get("status") == "completed":
        return common and receipt.get("returncode") == 0 \
            and len(receipt.get("stdout_sha256", "")) == 64 \
            and isinstance(receipt.get("result"), dict)
    if receipt.get("status") == "cancelled":
        return common and receipt.get("returncode") not in {None, 0} \
            and executable.get("cancelled") is True
    return False


def derive_acceptance(scenarios: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    by_id = {row["id"]: row for row in scenarios}
    one = by_id.get("async_command_and_immediate_question", {})
    two = by_id.get("queued_batch_to_japanese_html", {})
    three = by_id.get("interrupt_terminates_and_recovers", {})
    four = by_id.get("parallel_progress_threshold_cancellation", {})
    all_tasks = [task for scenario in scenarios for task in scenario.get("tasks", [])]
    q = four.get("query_receipts", [])
    q_by_id = {row["task_id"]: row for row in q}
    tasks4 = {row["task_id"]: row for row in four.get("tasks", [])}
    gates = {
        "exact_four_scenarios": len(scenarios) == 4 and len(by_id) == 4,
        "real_subprocess_receipts_only": bool(all_tasks) and all(real_task(row) for row in all_tasks),
        "scenario_1_nonblocking_and_immediate_response": (
            one.get("placeholder_latency_seconds", 1) < 0.1
            and one.get("time_answer_at", 999) < one.get("completion_event_at", -1)
            and one.get("tasks", [{}])[0].get("elapsed_seconds", 0) >= 3
            and one.get("tasks", [{}])[0].get("status") == "completed"
        ),
        "scenario_2_deferred_events_batched_once": (
            len(two.get("batch", [])) == 3
            and two.get("batch", [{}])[0].get("type") == "async.result"
            and [row.get("type") for row in two.get("batch", [])[1:]]
                == ["user.input", "user.input"]
            and len([event for event in two.get("events", [])
                     if event.get("event") == "batch_appended"]) == 1
        ),
        "scenario_2_japanese_html_artifact": all([
            two.get("artifact", {}).get("doctype"), two.get("artifact", {}).get("lang_ja"),
            two.get("artifact", {}).get("has_japanese"),
            two.get("artifact", {}).get("bytes", 0) > 100,
            len(two.get("artifact", {}).get("sha256", "")) == 64,
        ]),
        "scenario_3_os_process_cancelled_then_recovered": (
            len(three.get("tasks", [])) == 2
            and three["tasks"][0].get("status") == "cancelled"
            and three["tasks"][0].get("progress", 100) < 100
            and three["tasks"][0].get("returncode") not in {None, 0}
            and three["tasks"][1].get("status") == "completed"
            and three.get("cancel_receipt_at", 0) >= three.get("interrupt_at", 999)
            and three.get("recovery_at", 0) >= three.get("cancel_receipt_at", 999)
        ),
        "scenario_4_exact_rates_and_fast_first": (
            four.get("first_completed") == "T1"
            and [row.get("executable", {}).get("rate_percent_per_logical_second")
                 for row in four.get("tasks", [])] == [3.0, 2.0, 1.0]
        ),
        "scenario_4_query_once_and_cancel_only_under_threshold": (
            len(q) == len(q_by_id) == 2
            and set(q_by_id) == {"T2", "T3"}
            and q_by_id["T2"]["progress"] > 50
            and q_by_id["T3"]["progress"] <= 50
            and four.get("cancelled_ids") == ["T3"]
            and tasks4.get("T2", {}).get("status") == "completed"
            and tasks4.get("T3", {}).get("status") == "cancelled"
        ),
        "scenario_4_integrated_report_hashed": (
            set(four.get("completed_results", {})) == {"T1", "T2"}
            and four.get("artifact", {}).get("bytes", 0) > 100
            and len(four.get("artifact", {}).get("sha256", "")) == 64
        ),
    }
    return {"status": "passed" if all(gates.values()) else "failed", "gates": gates,
            "protocol_sha256": sha256(canonical_json(protocol))}


def manifest(campaign_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(campaign_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            data = path.read_bytes()
            files.append({"path": str(path.relative_to(campaign_dir)),
                          "bytes": len(data), "sha256": sha256(data)})
    return {"generated_at": datetime.now(UTC).isoformat(), "files": files}


async def run(campaign_id: str | None, tick_real: float) -> Path:
    if tick_real <= 0:
        raise ValueError("tick-real must be positive")
    tasks.TICK_REAL = tick_real
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    campaign_id = campaign_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    campaign_dir = VALIDATION_ROOT / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=False)
    write_json(campaign_dir / "protocol.json", protocol)
    started = time.perf_counter()
    scenarios = [await scenario_1(), await scenario_2(campaign_dir),
                 await scenario_3(), await scenario_4(campaign_dir)]
    for scenario in scenarios:
        write_json(campaign_dir / "scenarios" / f"{scenario['id']}.json", scenario)
    acceptance = derive_acceptance(scenarios, protocol)
    summary = {"experiment": "4-6", "campaign_id": campaign_id,
               "generated_at": datetime.now(UTC).isoformat(),
               "tick_real_seconds": tick_real,
               "elapsed_seconds": round(time.perf_counter() - started, 3),
               "scenario_status": {row["id"]: "recorded" for row in scenarios},
               "acceptance": acceptance, "status": acceptance["status"]}
    write_json(campaign_dir / "summary.json", summary)
    write_json(campaign_dir / "manifest.json", manifest(campaign_dir))
    return campaign_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id")
    parser.add_argument("--tick-real", type=float, default=0.15)
    args = parser.parse_args()
    print(asyncio.run(run(args.campaign_id, args.tick_real)))


if __name__ == "__main__":
    main()
