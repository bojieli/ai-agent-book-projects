"""Experiment 6-14: real Responses WebSocket calls, with replayable evidence.

Only the venue lookup is simulated. Models and transport are never mocked by
this runner. Run `python experiment.py --help`; credentials stay in memory.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import sys
import time
from datetime import datetime, timezone

import websockets
from websockets.asyncio.client import connect

ENDPOINT = "wss://api.openai.com/v1/responses"
ARMS = ("sync", "async", "steer_reasoning", "async_steer", "unsupported_steer")
VENUES = [
    {"id": "A", "cost": 1800, "capacity": 30},
    {"id": "B", "cost": 900, "capacity": 12},
    {"id": "C", "cost": 600, "capacity": 8},
]
INSTRUCTIONS = """You are coordinating a simulated meeting, with no real bookings.
Follow the latest user constraints. Select the cheapest venue with sufficient
capacity and cost no greater than the budget. Never invent a tool result.
For tasks with lookup_venues, call it exactly once as your FIRST action, before
any text. If it is still pending, write a short independent meeting-preparation
checklist starting CHECKLIST: with exactly three practical items; do not choose
a venue or invent the receipt. Do not call the lookup again to check its status.
When its actual result arrives, give the final answer as a JSON object with
keys venue, budget, attendees, receipt, source. Copy receipt from the tool and
set source to demo. You may complete an interim response while awaiting data.
For tasks without tools, inspect the supplied venue table and return a JSON
object with keys venue, budget, attendees, source, plan, with source set to demo
and plan a concise preparation plan. No bookings or external actions.
"""
INITIAL = "Plan a demo meeting. Budget is 2000 and attendees is 20."
UPDATES = [
    {"role": "user", "content": "Update: budget is now 1000. Preserve the meeting task."},
    {"role": "user", "content": "Update: attendees is now 10. Apply both updates together."},
]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_text(response):
    return "".join(
        part.get("text", "")
        for item in response.get("output", []) if item.get("type") == "message"
        for part in item.get("content", []) if part.get("type") == "output_text"
    )


def answer_json(text):
    decoder = json.JSONDecoder()
    found = None
    for i, char in enumerate(text):
        if char == "{":
            try:
                value, _ = decoder.raw_decode(text[i:])
                if isinstance(value, dict) and "venue" in value:
                    found = value
            except ValueError:
                pass
    return found


class Trace:
    def __init__(self, path):
        self.path = path
        self.start = time.monotonic()
        self.rows = []

    def add(self, direction, event):
        row = {"index": len(self.rows), "t_s": round(time.monotonic() - self.start, 6),
               "direction": direction, "event": event}
        self.rows.append(row)
        with self.path.open("a") as out:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row


def judge(rows, arm, requested_model):
    """Judge wire events and task output separately; an ACK alone never passes."""
    server = [r for r in rows if r["direction"] == "server"]
    client = [r for r in rows if r["direction"] == "client"]
    local = [r for r in rows if r["direction"] == "local"]
    typed = lambda rs, t: [r for r in rs if r["event"].get("type") == t]
    created = typed(server, "response.created")
    completed = typed(server, "response.completed")
    terminals = [r for r in server if r["event"].get("type") in
                 {"response.completed", "response.incomplete", "response.failed"}]
    failures = [r for r in server if r["event"].get("type") in
                {"error", "response.failed", "response.steer.failed"}]
    errors = [r["event"] for r in failures] + [r["event"] for r in typed(local, "run.error")]
    models = sorted({r["event"]["response"]["model"] for r in created
                     if r["event"]["response"].get("model")})
    calls = [r for r in typed(server, "response.output_item.done")
             if r["event"].get("item", {}).get("type") == "function_call"]
    starts = typed(local, "tool.started")
    ready = typed(local, "tool.ready")
    submissions = [(r, item) for r in typed(client, "response.create")
                   for item in r["event"].get("input", []) if isinstance(item, dict)
                   and item.get("type") == "function_call_output"]
    steers = typed(client, "response.steer")
    accepted = typed(server, "response.steer.accepted")
    pending = typed(server, "response.steer.pending")
    final_text = output_text(completed[-1]["event"]["response"]) if completed else ""
    answer = answer_json(final_text)
    checks = {}
    metrics = {"returned_models": models, "response_ids": [r["event"]["response"]["id"] for r in created],
               "tool_calls": len(calls), "steer_accepted": len(accepted), "steer_pending": len(pending),
               "errors": errors, "answer": answer}
    if arm == "unsupported_steer":
        checks["explicit_unsupported_error"] = any(
            e.get("type") == "response.steer.failed"
            and e.get("error", {}).get("code") == "steering_not_supported"
            and steers and e.get("steer", {}).get("previous_response_id") == steers[0]["event"]["previous_response_id"]
            for e in errors)
        checks["requested_model_returned"] = bool(models) and all(
            m == requested_model or m.startswith(requested_model + "-") for m in models)
        checks["steer_was_sent"] = len(steers) == 1
        checks["no_runner_error"] = not typed(local, "run.error")
        return {"arm": arm, "passed": all(checks.values()), "checks": checks, "metrics": metrics}

    checks["no_api_or_runner_error"] = not errors
    checks["requested_model_returned"] = bool(models) and all(
        m == requested_model or m.startswith(requested_model + "-") for m in models)
    is_steered = arm in {"steer_reasoning", "async_steer"}
    budget, attendees = (1000, 10) if is_steered else (2000, 20)
    feasible = [v for v in VENUES if v["cost"] <= budget and v["capacity"] >= attendees]
    expected = min(feasible, key=lambda v: v["cost"])["id"]
    checks["latest_constraints_and_selection"] = bool(answer) and all(
        answer.get(k) == v for k, v in {"venue": expected, "budget": budget,
                                      "attendees": attendees, "source": "demo"}.items())
    if arm in {"sync", "async", "async_steer"}:
        checks["one_call_one_execution_one_delivery"] = len(calls) == len(starts) == len(ready) == len(submissions) == 1
        if calls and ready and submissions:
            call = calls[0]["event"]["item"]
            sent, item = submissions[0]
            result = ready[0]["event"]["result"]
            checks["original_call_id_and_actual_result"] = (
                call["call_id"] == starts[0]["event"]["call_id"] == ready[0]["event"]["call_id"] == item["call_id"]
                and json.loads(item["output"]) == result and ready[0]["index"] < sent["index"])
            prior_responses = [r for r in created if r["index"] < sent["index"]]
            checks["result_continues_latest_response"] = bool(prior_responses) and (
                sent["event"]["previous_response_id"] == prior_responses[-1]["event"]["response"]["id"])
            checks["receipt_grounded"] = bool(answer) and answer.get("receipt") == result["receipt"]
            checks["native_async_flag"] = bool(call.get("async", False)) == (arm != "sync")
            progress = [r for r in typed(server, "response.output_text.delta")
                        if calls[0]["index"] < r["index"] < ready[0]["index"]]
            progress_text = "".join(r["event"].get("delta", "") for r in progress)
            metrics["independent_text_while_tool_pending"] = "CHECKLIST:" in progress_text
            metrics["tool_duration_s"] = round(ready[0]["t_s"] - starts[0]["t_s"], 3)
            metrics["first_text_after_call_s"] = round(progress[0]["t_s"] - calls[0]["t_s"], 3) if progress else None
            during_execution = [r for r in progress if r["index"] > starts[0]["index"] and r["event"].get("delta", "").strip()]
            metrics["text_deltas_during_tool_execution"] = len(during_execution)
            interim_answers = [answer_json(output_text(r["event"]["response"]))
                               for r in completed if r["index"] < sent["index"]]
            checks["no_premature_venue_json"] = not any(interim_answers)
            if arm == "sync":
                checks["sync_waits_for_result"] = not progress
            elif arm == "async":
                checks["independent_work_before_result"] = "CHECKLIST:" in progress_text
                checks["generation_overlaps_tool_execution"] = bool(during_execution)
                checks["progress_in_original_response"] = bool(progress) and progress[0]["index"] < terminals[0]["index"]
            else:
                checks["steer_while_tool_pending"] = bool(steers) and starts[0]["index"] < steers[0]["index"] < ready[0]["index"]
        else:
            checks["complete_tool_evidence"] = False
    if is_steered:
        checks["one_steer_with_two_user_updates"] = len(steers) == 1 and steers[0]["event"]["input"] == UPDATES
        checks["accepted_and_successor_observed"] = bool(accepted) and len(created) >= 2
        if steers and created and terminals:
            target = steers[0]["event"]["previous_response_id"]
            parent_end = next((r for r in terminals if r["event"]["response"]["id"] == target), None)
            checks["steer_before_parent_terminal"] = bool(parent_end) and steers[0]["index"] < parent_end["index"]
            metrics["parent_terminal"] = parent_end["event"]["type"] if parent_end else None
            metrics["parent_incomplete_reason"] = (parent_end["event"]["response"].get("incomplete_details") or {}).get("reason") if parent_end else None
            metrics["accepted_latency_s"] = round(accepted[0]["t_s"] - steers[0]["t_s"], 3) if accepted else None
            successors = [r for r in created if r["index"] > steers[0]["index"]]
            if successors:
                checks["successor_continues_steered_parent"] = successors[0]["event"]["response"].get("previous_response_id") == target
                between = [r for r in typed(client, "response.create")
                           if steers[0]["index"] < r["index"] < successors[0]["index"]]
                metrics["automatic_successor"] = not between
                checks["successor_completed"] = any(r["event"]["response"]["id"] == successors[-1]["event"]["response"]["id"] for r in completed)
                if arm == "steer_reasoning":
                    checks["no_manual_restart"] = not between
            else:
                checks["successor_completed"] = False
            if arm == "steer_reasoning":
                reasoning = [r for r in typed(server, "response.output_item.added")
                             if r["event"].get("item", {}).get("type") == "reasoning"]
                checks["reasoning_item_before_steer"] = bool(reasoning) and reasoning[0]["index"] < steers[0]["index"]
        else:
            checks["complete_steering_evidence"] = False
    metrics["elapsed_s"] = rows[-1]["t_s"] if rows else 0
    metrics["usage"] = [r["event"]["response"].get("usage") for r in terminals]
    return {"arm": arm, "passed": all(checks.values()), "checks": checks, "metrics": metrics}


async def run_case(directory, arm, args):
    directory.mkdir(parents=True, exist_ok=False)
    trace = Trace(directory / "events.jsonl")
    model = args.control_model if arm == "unsupported_steer" else args.model
    tool_arm = arm in {"sync", "async", "async_steer"}
    tools = [{"type": "function", "name": "lookup_venues",
              "description": "Read the simulated venue inventory. Source is demo. Call once; the host will deliver its result.",
              "async": arm != "sync", "strict": True,
              "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}}] if tool_arm else []
    settings = {"model": model, "store": False, "instructions": INSTRUCTIONS,
                "reasoning": {"effort": "medium" if not tool_arm else "low"},
                "max_output_tokens": 2400, "tools": tools, "parallel_tool_calls": False}
    initial = INITIAL if tool_arm else INITIAL + " Venue table: " + json.dumps(VENUES) + " Check feasibility, staffing, room setup, and a preparation schedule before answering."
    trace.add("local", {"type": "run.config", "arm": arm, "model": model, "endpoint": ENDPOINT,
                        "tool_delay_s": args.tool_delay, "timeout_s": args.timeout,
                        "started_utc": datetime.now(timezone.utc).isoformat()})
    queue = asyncio.Queue()
    jobs = []
    calls = {}
    ready = {}
    delivered = set()
    latest_id = None
    active = False
    steer_target = None
    steer_committed = False
    pending_required = None
    terminal_response = None
    reader = None

    async def lookup(call):
        trace.add("local", {"type": "tool.started", "call_id": call["call_id"]})
        await asyncio.sleep(args.tool_delay)
        result = {"source": "demo", "venues": VENUES, "receipt": secrets.token_hex(12)}
        trace.add("local", {"type": "tool.ready", "call_id": call["call_id"], "result": result})
        await queue.put(("ready", (call["call_id"], result)))

    try:
        async with asyncio.timeout(args.timeout), connect(
            ENDPOINT, additional_headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
            open_timeout=20, max_size=16 * 1024 * 1024,
        ) as ws:
            async def send(event):
                await ws.send(json.dumps(event))
                trace.add("client", event)

            async def read():
                try:
                    async for raw in ws:
                        event = json.loads(raw)
                        trace.add("server", event)
                        await queue.put(("server", event))
                finally:
                    await queue.put(("closed", None))

            async def steer():
                nonlocal steer_target
                steer_target = latest_id
                await send({"type": "response.steer", "previous_response_id": latest_id, "input": UPDATES})

            reader = asyncio.create_task(read())
            await send({"type": "response.create", **settings, "input": initial})
            while True:
                kind, event = await queue.get()
                if kind == "closed":
                    raise RuntimeError("Connection closed before task completion")
                if kind == "ready":
                    ready[event[0]] = event[1]
                else:
                    typ = event.get("type")
                    if typ in {"error", "response.failed", "response.steer.failed"}:
                        break  # Retained verbatim and judged; no silent fallback.
                    if typ == "response.created":
                        latest_id = event["response"]["id"]
                        active = True
                        if steer_target and latest_id != steer_target:
                            steer_committed = True
                        if arm == "unsupported_steer" and not steer_target:
                            await steer()
                    elif typ == "response.output_item.added":
                        if arm == "steer_reasoning" and not steer_target and event["item"]["type"] == "reasoning":
                            await steer()
                    elif typ == "response.output_item.done" and event["item"]["type"] == "function_call":
                        call = event["item"]
                        if call["name"] != "lookup_venues" or json.loads(call["arguments"]) != {} or calls:
                            raise RuntimeError("Unexpected or duplicate tool call")
                        calls[call["call_id"]] = call
                        jobs.append(asyncio.create_task(lookup(call)))
                        if arm == "async_steer" and not steer_target:
                            # Register/start work before injecting the simulated user event.
                            await asyncio.sleep(0)
                            await steer()
                    elif typ == "response.steer.pending":
                        pending_required = {item["call_id"] for item in event["required_input"]
                                            if item["type"] == "function_call_output"}
                    elif typ in {"response.completed", "response.incomplete"}:
                        terminal_response = event["response"]
                        active = False
                        reason = (terminal_response.get("incomplete_details") or {}).get("reason")
                        if typ == "response.incomplete" and reason != "steered":
                            raise RuntimeError("Unexpected incomplete response: " + str(reason))
                        if not tool_arm and not steer_target:
                            raise RuntimeError("No observable reasoning item before response ended; steering trigger not reproduced")

                # A queued steer owns the continuation. Wait for either its
                # automatic successor or required_input; never race it with create.
                awaiting_steer = steer_target and not steer_committed and pending_required is None
                if not active and latest_id and not awaiting_steer:
                    available = set(ready) - delivered
                    required_ready = pending_required is None or pending_required <= available
                    if available and required_ready:
                        items = [{"type": "function_call_output", "call_id": cid,
                                  "output": json.dumps(ready[cid])} for cid in sorted(available)]
                        await send({"type": "response.create", **settings,
                                    "previous_response_id": latest_id, "input": items,
                                    "tool_choice": "none"})
                        delivered.update(available)
                        pending_required = None
                        active = True
                    elif terminal_response and (not tool_arm or (calls and set(calls) == delivered)):
                        if not steer_target or steer_committed:
                            break
    except Exception as exc:
        trace.add("local", {"type": "run.error", "class": type(exc).__name__, "message": str(exc)})
    finally:
        for task in [reader, *jobs]:
            if task:
                task.cancel()
        await asyncio.gather(*(t for t in [reader, *jobs] if t), return_exceptions=True)
    result = judge(trace.rows, arm, model)
    write_json(directory / "acceptance.json", result)
    return result


def replay(run_dir):
    manifest = json.loads((run_dir / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        if digest(run_dir / name) != expected:
            raise ValueError("Evidence hash mismatch: " + name)
    verdicts = []
    for case in manifest["cases"]:
        rows = [json.loads(line) for line in (run_dir / case["name"] / "events.jsonl").read_text().splitlines()]
        actual = judge(rows, case["arm"], case["model"])
        saved = json.loads((run_dir / case["name"] / "acceptance.json").read_text())
        if actual != saved:
            raise ValueError("Judgment changed: " + case["name"])
        if actual["passed"] != case["passed"]:
            raise ValueError("Manifest verdict mismatch: " + case["name"])
        verdicts.append(actual["passed"])
    if all(verdicts) != manifest["all_passed"]:
        raise ValueError("Manifest aggregate verdict mismatch")
    print(json.dumps({"replay_verified": True, "cases": len(manifest["cases"]),
                      "all_passed": manifest["all_passed"]}, indent=2))


async def main(args):
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your environment before running.")
    run_dir = args.out or Path(__file__).parent / "validation" / "runs" / datetime.now(timezone.utc).strftime("exp6-14-%Y%m%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=False)
    source_dir = run_dir / "source"
    source_dir.mkdir()
    for name in ("experiment.py", "requirements.txt", "test_judging.py"):
        (source_dir / name).write_bytes(Path(__file__).with_name(name).read_bytes())
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(), "endpoint": ENDPOINT,
                "python": platform.python_version(), "websockets": websockets.__version__,
                "cases": [], "all_passed": False, "sha256": {}}
    for repeat in range(1, args.repeats + 1):
        for arm in args.arms:
            name = f"{repeat:02d}-{arm}"
            result = await run_case(run_dir / name, arm, args)
            manifest["cases"].append({"name": name, "arm": arm,
                "model": args.control_model if arm == "unsupported_steer" else args.model,
                "passed": result["passed"]})
            write_json(run_dir / "manifest.json", manifest)
            print(json.dumps({"case": name, "passed": result["passed"],
                              "failed_checks": [k for k, v in result["checks"].items() if not v],
                              "error_codes": [e.get("error", {}).get("code", e.get("class"))
                                              for e in result["metrics"]["errors"]]}, ensure_ascii=False), flush=True)
    manifest["all_passed"] = all(c["passed"] for c in manifest["cases"])
    manifest["sha256"] = {str(p.relative_to(run_dir)): digest(p)
                          for p in sorted(run_dir.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(run_dir / "manifest.json", manifest)
    print("Evidence:", run_dir, flush=True)
    return 0 if manifest["all_passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-6-astra")
    parser.add_argument("--control-model", default="gpt-5.6-sol")
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--tool-delay", type=float, default=8.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--replay", type=Path, help="Verify hashes and rejudge saved wire events, without API calls")
    args = parser.parse_args()
    if args.replay:
        replay(args.replay)
    else:
        if args.repeats < 1 or args.tool_delay <= 0 or args.timeout <= 0:
            parser.error("repeats, tool-delay and timeout must be positive")
        sys.exit(asyncio.run(main(args)))
