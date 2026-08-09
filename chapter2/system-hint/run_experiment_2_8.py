#!/usr/bin/env python3
"""Run the frozen, real Kimi K3 campaign for Chapter 2 Experiment 2-9."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "experiment_protocol.json"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def sandbox_hash(root: Path) -> str:
    entries = []
    if root.exists():
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            entries.append({
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            })
    return sha256_bytes(canonical_json(entries))


def condition_order(suite: str, index: int) -> list[str]:
    if suite == "timestamps":
        return (
            ["timestamps_guided", "timestamps_raw", "disabled"]
            if index % 2 == 0
            else ["disabled", "timestamps_raw", "timestamps_guided"]
        )
    enabled = {
        "tool_counter": "tool_counter",
        "todo_list": "todo_list",
        "detailed_errors": "detailed_errors",
        "system_state": "system_state",
        "combined": "combined",
    }[suite]
    return [enabled, "disabled"] if index % 2 == 0 else ["disabled", enabled]


def case_prompt(suite: str, case: dict[str, Any]) -> str:
    if suite == "timestamps":
        names = list(case["records"])
        return (
            f"Read both records {names[0]} and {names[1]}. Select the record with the later "
            "recorded timestamp and submit its name. Do not guess if a tool can provide evidence."
        )
    if suite == "tool_counter":
        return (
            f"Retrieve the payload for primary resource {case['primary']}. If the primary remains "
            f"unavailable, use fallback {case['fallback']}. Submit the resource that supplied the payload."
        )
    if suite == "todo_list":
        artifacts = ", ".join(case["artifacts"])
        return (
            f"Complete this multi-step delivery. Create exactly these artifacts: {artifacts}. "
            f"Every artifact must contain exactly the token {case['token']}. Verify the work, then "
            "submit the complete artifact list."
        )
    if suite == "detailed_errors":
        return (
            f"Read {case['requested']}. It may have been renamed. Recover the actual document without "
            "inventing its contents, then submit the actual filename and the exact token found inside."
        )
    if suite == "system_state":
        return (
            f"Install package {case['package']} in the simulated host using its OS-native package manager. "
            "Inspect the host if needed, perform the action, and submit the manager and package used."
        )
    names = list(case["records"])
    artifacts = ", ".join(case["artifacts"])
    return (
        "Complete every component of this incident workflow and submit one combined result: "
        f"(1) read records {names[0]} and {names[1]} and select the later one; "
        f"(2) retrieve {case['primary']} or, if unavailable, fallback {case['fallback']}; "
        f"(3) create artifacts {artifacts}, each containing exactly {case['token']}; "
        f"(4) read possibly-renamed document {case['requested']} and recover its exact token; "
        f"(5) install package {case['package']} with the simulated host's native package manager. "
        "Use tools for every factual claim and do not omit a component."
    )


def initialize_sandbox(root: Path, suite: str, case: dict[str, Any]) -> None:
    if root.exists():
        raise FileExistsError(f"refusing to replace existing sandbox: {root}")
    root.mkdir(parents=True)
    state: dict[str, Any] = {"suite": suite, "case_id": case["id"]}
    if suite in {"timestamps", "combined"}:
        state["records"] = case["records"]
        records = root / "records"
        records.mkdir()
        for name in case["records"]:
            (records / f"{name}.txt").write_text(f"payload-for-{name}\n", encoding="utf-8")
    if suite in {"tool_counter", "combined"}:
        state["primary"] = case["primary"]
        state["fallback"] = case["fallback"]
        resources = root / "resources"
        resources.mkdir()
        (resources / f"{case['fallback']}.txt").write_text(
            f"verified-payload-{case['id']}\n", encoding="utf-8"
        )
    if suite in {"todo_list", "combined"}:
        state["token"] = case["token"]
        state["artifacts"] = case["artifacts"]
        (root / "artifacts").mkdir()
    if suite in {"detailed_errors", "combined"}:
        state["requested"] = case["requested"]
        state["actual"] = case["actual"]
        state["document_token"] = case["token"]
        documents = root / "documents"
        documents.mkdir()
        (documents / case["actual"]).write_text(case["token"] + "\n", encoding="utf-8")
    if suite in {"system_state", "combined"}:
        state["system"] = {
            key: case[key] for key in ("os", "shell", "python", "cwd", "manager", "package")
        }
    (root / "initial_state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_state(root: Path) -> dict[str, Any]:
    return json.loads((root / "initial_state.json").read_text(encoding="utf-8"))


def function_tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


def tools_for(suite: str, features: set[str]) -> list[dict]:
    string = lambda description: {"type": "string", "description": description}
    tools: list[dict] = []
    if suite in {"timestamps", "combined"}:
        tools.append(function_tool(
            "read_record", "Read one named record.", {"name": string("Record name")}, ["name"]
        ))
    if suite in {"tool_counter", "combined"}:
        tools.append(function_tool(
            "probe_resource", "Probe a primary or fallback resource.",
            {"name": string("Resource name")}, ["name"]
        ))
    if suite in {"todo_list", "combined"}:
        tools.append(function_tool(
            "write_artifact", "Write exact text to a required sandbox artifact.",
            {"file": string("Required artifact filename"), "content": string("Exact file content")},
            ["file", "content"],
        ))
        if "todo_list" in features:
            tools.extend([
                function_tool(
                    "rewrite_todo_list", "Create or replace the explicit task checklist.",
                    {"items": {"type": "array", "items": {"type": "string"}}}, ["items"],
                ),
                function_tool(
                    "update_todo_status", "Update one checklist item after verifying it.",
                    {"item": string("Exact checklist item"), "status": {
                        "type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]
                    }}, ["item", "status"],
                ),
            ])
    if suite in {"detailed_errors", "combined"}:
        tools.extend([
            function_tool(
                "read_document", "Read one document by filename.",
                {"file": string("Document filename")}, ["file"],
            ),
            function_tool(
                "list_documents", "List available document filenames after a lookup failure.", {}, [],
            ),
        ])
    if suite in {"system_state", "combined"}:
        tools.extend([
            function_tool("inspect_system", "Inspect the simulated host state.", {}, []),
            function_tool(
                "install_package", "Perform a simulated native package-manager install action.",
                {"manager": string("Package manager"), "package": string("Package name")},
                ["manager", "package"],
            ),
        ])
    submit_properties: dict[str, Any] = {}
    required: list[str] = []
    if suite == "timestamps":
        submit_properties = {"selected_record": string("Name of later record")}
        required = ["selected_record"]
    elif suite == "tool_counter":
        submit_properties = {"fallback": string("Resource that supplied the payload")}
        required = ["fallback"]
    elif suite == "todo_list":
        submit_properties = {"artifacts": {"type": "array", "items": {"type": "string"}}}
        required = ["artifacts"]
    elif suite == "detailed_errors":
        submit_properties = {
            "document": string("Actual document filename"), "token": string("Exact recovered token")
        }
        required = ["document", "token"]
    elif suite == "system_state":
        submit_properties = {"manager": string("Manager used"), "package": string("Package installed")}
        required = ["manager", "package"]
    else:
        submit_properties = {
            "selected_record": string("Name of later record"),
            "fallback": string("Resource that supplied payload"),
            "artifacts": {"type": "array", "items": {"type": "string"}},
            "document": string("Actual document filename"),
            "token": string("Exact recovered token"),
            "manager": string("Manager used"),
            "package": string("Package installed"),
        }
        required = list(submit_properties)
    tools.append(function_tool(
        "submit_result", "Submit the final result only after tool-backed verification.",
        submit_properties, required,
    ))
    return tools


def status_message(features: set[str], state: dict, counters: dict, todos: dict) -> str | None:
    sections = []
    if "timestamp_guidance" in features:
        sections.append(
            "TIME GUIDANCE: Treat explicit timestamps as decision evidence. Compare them directly; "
            "raw readings do not help unless you translate them into an action."
        )
    if "tool_counter" in features:
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(counters.items())) or "none"
        sections.append(
            "TOOL COUNTS: " + rendered + ". After repeated failure, diagnose and switch to a viable fallback."
        )
    if "todo_list" in features:
        rendered = "; ".join(f"{name}: {status}" for name, status in todos.items()) or "not created"
        sections.append("TODO LIST: " + rendered + ". Keep every required deliverable visible until verified.")
    if "system_state" in features:
        system = state.get("system", {})
        sections.append(
            "SYSTEM STATE: " + ", ".join(f"{key}={system.get(key)}" for key in (
                "os", "shell", "python", "cwd", "manager"
            ))
        )
    if not sections:
        return None
    return "<agent_status>\n" + "\n".join(sections) + "\n</agent_status>"


def timestamp_wrap(features: set[str], timestamp: str, content: str) -> str:
    return f"[{timestamp}] {content}" if "timestamps" in features else content


def execute_tool(
    root: Path,
    suite: str,
    features: set[str],
    name: str,
    arguments: dict,
    counters: dict[str, int],
    todos: dict[str, str],
) -> tuple[str, bool]:
    state = load_state(root)
    counters[name] = counters.get(name, 0) + 1
    ok = True
    if name == "read_record":
        record = str(arguments.get("name", ""))
        path = root / "records" / f"{record}.txt"
        if not path.is_file() or record not in state.get("records", {}):
            ok, content = False, "Error: record not found"
        else:
            content = path.read_text(encoding="utf-8").strip()
            content = timestamp_wrap(features, state["records"][record], content)
    elif name == "probe_resource":
        resource = str(arguments.get("name", ""))
        if resource == state.get("primary"):
            ok, content = False, "Error: primary resource is temporarily unavailable"
        elif resource == state.get("fallback"):
            content = (root / "resources" / f"{resource}.txt").read_text(encoding="utf-8").strip()
        else:
            ok, content = False, "Error: unknown resource"
    elif name == "write_artifact":
        filename = Path(str(arguments.get("file", ""))).name
        required = state.get("artifacts", [])
        if filename not in required:
            ok, content = False, "Error: filename is outside the required artifact set"
        else:
            (root / "artifacts" / filename).write_text(str(arguments.get("content", "")), encoding="utf-8")
            content = f"Wrote artifacts/{filename}"
    elif name == "rewrite_todo_list":
        todos.clear()
        for item in arguments.get("items", []):
            todos[str(item)] = "pending"
        content = f"TODO list now has {len(todos)} items"
    elif name == "update_todo_status":
        item, status = str(arguments.get("item", "")), str(arguments.get("status", ""))
        if item not in todos:
            ok, content = False, "Error: TODO item not found"
        else:
            todos[item] = status
            content = f"Updated {item} to {status}"
    elif name == "read_document":
        filename = Path(str(arguments.get("file", ""))).name
        path = root / "documents" / filename
        if not path.is_file():
            ok = False
            if "detailed_errors" in features:
                available = sorted(item.name for item in (root / "documents").iterdir())
                content = json.dumps({
                    "error_type": "FileNotFoundError",
                    "description": f"Document {filename!r} does not exist",
                    "arguments": arguments,
                    "stack": "sandbox.read_document -> open",
                    "suggestion": "List the directory and try the renamed file",
                    "available_documents": available,
                })
            else:
                content = "Error: document not found"
        else:
            content = path.read_text(encoding="utf-8").strip()
    elif name == "list_documents":
        if counters.get("read_document", 0) == 0:
            ok, content = False, "Error: first attempt the user-requested document path"
        else:
            content = json.dumps(sorted(item.name for item in (root / "documents").iterdir()))
    elif name == "inspect_system":
        content = json.dumps(state["system"], sort_keys=True)
    elif name == "install_package":
        manager, package = str(arguments.get("manager", "")), str(arguments.get("package", ""))
        expected = state["system"]
        ok = manager == expected["manager"] and package == expected["package"]
        content = "Simulated install succeeded" if ok else "Error: wrong native manager or package"
        if ok:
            (root / "install_action.json").write_text(
                json.dumps({"manager": manager, "package": package}, sort_keys=True), encoding="utf-8"
            )
    elif name == "submit_result":
        content = "Submission recorded"
    else:
        ok, content = False, f"Error: unknown tool {name}"
    if "tool_counter" in features:
        content += f"\nTool call #{counters[name]} for '{name}'."
    return content, ok


def component_scores(suite: str, case: dict, events: list[dict], root: Path) -> dict[str, bool]:
    calls = [(event["name"], event["arguments"], event["ok"]) for event in events]
    submissions = [args for name, args, _ in calls if name == "submit_result"]
    submitted = submissions[-1] if submissions else {}
    scores: dict[str, bool] = {}
    if suite in {"timestamps", "combined"}:
        read_names = {args.get("name") for name, args, ok in calls if name == "read_record" and ok}
        expected = case.get("expected", case.get("expected_record"))
        scores["timestamps"] = set(case["records"]).issubset(read_names) and submitted.get("selected_record") == expected
    if suite in {"tool_counter", "combined"}:
        primary_count = sum(name == "probe_resource" and args.get("name") == case["primary"] for name, args, _ in calls)
        fallback_read = any(
            name == "probe_resource" and args.get("name") == case["fallback"] and ok for name, args, ok in calls
        )
        scores["tool_counter"] = fallback_read and submitted.get("fallback") == case["fallback"] and primary_count <= 3
    if suite in {"todo_list", "combined"}:
        exact_files = all(
            (root / "artifacts" / filename).is_file()
            and (root / "artifacts" / filename).read_text(encoding="utf-8").strip() == case["token"]
            for filename in case["artifacts"]
        )
        scores["todo_list"] = exact_files and set(submitted.get("artifacts", [])) == set(case["artifacts"])
    if suite in {"detailed_errors", "combined"}:
        failed_requested = any(
            name == "read_document" and args.get("file") == case["requested"] and not ok for name, args, ok in calls
        )
        actual_read = any(
            name == "read_document" and args.get("file") == case["actual"] and ok for name, args, ok in calls
        )
        scores["detailed_errors"] = (
            failed_requested and actual_read and submitted.get("document") == case["actual"]
            and submitted.get("token") == case["token"]
        )
    if suite in {"system_state", "combined"}:
        installed = any(
            name == "install_package" and ok and args.get("manager") == case["manager"]
            and args.get("package") == case["package"] for name, args, ok in calls
        )
        scores["system_state"] = installed and submitted.get("manager") == case["manager"]
    return scores


def validate_tool_protocol(messages: list[dict]) -> bool:
    pending: list[str] = []
    for message in messages:
        if pending:
            if message.get("role") != "tool" or message.get("tool_call_id") != pending[0]:
                return False
            pending.pop(0)
            continue
        if message.get("role") == "assistant" and message.get("tool_calls"):
            pending = [call["id"] for call in message["tool_calls"]]
    return not pending


def accepted_receipt(call: dict) -> bool:
    response = call.get("response") or {}
    usage = response.get("usage") or {}
    return bool(response.get("id") and usage.get("total_tokens") is not None)


def validate_completed_evidence(
    evidence: dict, protocol_hash: str, initial_hash: str, root: Path
) -> None:
    if not evidence.get("complete"):
        raise ValueError("evidence is not complete")
    if evidence.get("protocol_sha256") != protocol_hash:
        raise ValueError("protocol hash changed")
    if evidence.get("initial_sandbox_sha256") != initial_hash:
        raise ValueError("initial sandbox hash changed")
    if evidence.get("current_sandbox_sha256") != sandbox_hash(root):
        raise ValueError("sandbox changed after checkpoint")
    if not evidence.get("api_calls") or not all(accepted_receipt(call) for call in evidence["api_calls"]):
        raise ValueError("accepted response ID/usage missing")
    if not validate_tool_protocol(evidence.get("messages", [])):
        raise ValueError("assistant/tool protocol is invalid")


def run_one(
    client: OpenAI,
    protocol: dict,
    protocol_hash: str,
    run_dir: Path,
    suite: str,
    case: dict,
    condition: str,
    case_condition_order: list[str],
    order_position: int,
) -> dict:
    run_id = f"{suite}__{case['id']}__{condition}"
    evidence_path = run_dir / "cases" / f"{run_id}.json"
    sandbox = run_dir / "sandboxes" / run_id
    features = set(protocol["conditions"][condition])
    if not sandbox.exists():
        initialize_sandbox(sandbox, suite, case)
    initial_files = []
    for path in sorted(item for item in sandbox.rglob("*") if item.is_file() and item.name != "install_action.json"):
        if "artifacts" not in path.parts:
            initial_files.append({"path": path.relative_to(sandbox).as_posix(), "sha256": sha256_file(path)})
    initial_hash = sha256_bytes(canonical_json(initial_files))
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        order_metadata_changed = False
        expected_order_fields = {
            "case_condition_order": case_condition_order,
            "order_position": order_position,
        }
        for field, expected in expected_order_fields.items():
            if field not in evidence:
                evidence[field] = expected
                order_metadata_changed = True
            elif evidence[field] != expected:
                raise RuntimeError(f"resume refused for {run_id}: {field} differs from frozen protocol")
        if order_metadata_changed:
            evidence["order_metadata_source"] = "backfilled_from_frozen_protocol"
        if evidence.get("complete"):
            validate_completed_evidence(evidence, protocol_hash, initial_hash, sandbox)
            if order_metadata_changed:
                atomic_json(evidence_path, evidence)
            return evidence
        if evidence.get("protocol_sha256") != protocol_hash or evidence.get("initial_sandbox_sha256") != initial_hash:
            raise RuntimeError(f"resume refused for {run_id}: frozen inputs changed")
        if evidence.get("current_sandbox_sha256") != sandbox_hash(sandbox):
            raise RuntimeError(f"resume refused for {run_id}: sandbox changed")
    else:
        prompt = case_prompt(suite, case)
        if "timestamps" in features:
            prompt = timestamp_wrap(features, "2025-09-19 09:00:00", prompt)
        evidence = {
            "experiment_id": "2-8",
            "run_id": run_id,
            "suite": suite,
            "case_id": case["id"],
            "condition": condition,
            "case_condition_order": case_condition_order,
            "order_position": order_position,
            "features": sorted(features),
            "provider": {
                "name": protocol["provider"]["name"],
                "base_url": protocol["provider"]["base_url"],
                "model": protocol["provider"]["model"],
            },
            "protocol_sha256": protocol_hash,
            "initial_sandbox_sha256": initial_hash,
            "current_sandbox_sha256": sandbox_hash(sandbox),
            "created_at": utc_now(),
            "messages": [
                {"role": "system", "content": (
                    "You are an audited local-sandbox agent. Use the supplied tools to complete the user's "
                    "task. Treat tool output as ground truth, do not invent state, and finish by calling "
                    "submit_result exactly once after verification."
                )},
                {"role": "user", "content": prompt},
            ],
            "api_calls": [],
            "tool_events": [],
            "tool_counters": {},
            "todos": {},
            "complete": False,
        }
        atomic_json(evidence_path, evidence)
    max_turns = protocol["design"]["max_llm_turns"]
    configured_tools = tools_for(suite, features)
    if (
        evidence.get("termination") == "assistant_without_tool_call"
        and evidence.get("messages", [{}])[-1].get("role") == "assistant"
    ):
        evidence["messages"].append({
            "role": "user",
            "content": (
                "The audited task is not complete until you call submit_result. "
                "Use the available evidence, perform any missing verification, and submit now."
            ),
        })
        evidence["termination"] = "assistant_without_tool_call_reprompted"
        atomic_json(evidence_path, evidence)
    while len([call for call in evidence["api_calls"] if call.get("response")]) < max_turns:
        request_messages = copy.deepcopy(evidence["messages"])
        status = status_message(features, load_state(sandbox), evidence["tool_counters"], evidence["todos"])
        if status:
            request_messages.append({"role": "user", "content": status})
        request = {
            "model": protocol["provider"]["model"],
            "messages": request_messages,
            "tools": copy.deepcopy(configured_tools),
            "tool_choice": "auto",
            "temperature": protocol["provider"]["temperature"],
            "max_tokens": protocol["provider"]["max_completion_tokens"],
        }
        started = time.perf_counter()
        receipt: dict[str, Any] = {"requested_at": utc_now(), "request": copy.deepcopy(request)}
        try:
            response = client.chat.completions.create(**request)
        except Exception as exc:
            receipt.update({
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": {"type": type(exc).__name__, "message": str(exc)},
            })
            evidence["api_calls"].append(receipt)
            evidence["current_sandbox_sha256"] = sandbox_hash(sandbox)
            atomic_json(evidence_path, evidence)
            raise
        choice = response.choices[0]
        response_payload = response.model_dump(mode="json")
        receipt.update({
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "response": response_payload,
        })
        evidence["api_calls"].append(receipt)
        assistant = choice.message.model_dump(mode="json", exclude_none=True)
        evidence["messages"].append(assistant)
        evidence["current_sandbox_sha256"] = sandbox_hash(sandbox)
        atomic_json(evidence_path, evidence)
        calls = assistant.get("tool_calls") or []
        if not calls:
            evidence["messages"].append({
                "role": "user",
                "content": (
                    "The audited task is not complete until you call submit_result. "
                    "Use the available evidence, perform any missing verification, and submit now."
                ),
            })
            evidence["termination"] = "assistant_without_tool_call_reprompted"
            atomic_json(evidence_path, evidence)
            continue
        submitted = False
        for call in calls:
            name = call["function"]["name"]
            try:
                arguments = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            content, ok = execute_tool(
                sandbox, suite, features, name, arguments,
                evidence["tool_counters"], evidence["todos"],
            )
            event = {
                "at": utc_now(), "tool_call_id": call["id"], "name": name,
                "arguments": arguments, "content": content, "ok": ok,
                "sandbox_sha256_after": sandbox_hash(sandbox),
            }
            evidence["tool_events"].append(event)
            evidence["messages"].append({
                "role": "tool", "tool_call_id": call["id"], "name": name, "content": content,
            })
            evidence["current_sandbox_sha256"] = sandbox_hash(sandbox)
            atomic_json(evidence_path, evidence)
            submitted = submitted or name == "submit_result"
        if submitted:
            evidence["termination"] = "submit_result"
            break
    scores = component_scores(suite, case, evidence["tool_events"], sandbox)
    evidence["component_scores"] = scores
    evidence["objective_pass"] = all(scores.values())
    evidence["llm_turns"] = len([call for call in evidence["api_calls"] if call.get("response")])
    evidence["tool_protocol_valid"] = validate_tool_protocol(evidence["messages"])
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for call in evidence["api_calls"]:
        raw = (call.get("response") or {}).get("usage") or {}
        for key in usage:
            usage[key] += int(raw.get(key) or 0)
    pricing = protocol["pricing"]
    cost = (
        usage["prompt_tokens"] * pricing["uncached_input_per_million"] / 1_000_000
        + usage["completion_tokens"] * pricing["output_per_million"] / 1_000_000
    )
    evidence["usage"] = usage
    evidence["cost"] = {
        "amount": cost, "currency": "CNY",
        "qualification": "all prompt tokens conservatively priced as uncached",
    }
    successful_receipts = [call for call in evidence["api_calls"] if call.get("response")]
    evidence["provider_receipts_valid"] = bool(successful_receipts) and all(
        accepted_receipt(call) for call in successful_receipts
    )
    evidence["current_sandbox_sha256"] = sandbox_hash(sandbox)
    evidence["complete"] = bool(
        evidence["provider_receipts_valid"] and evidence["tool_protocol_valid"]
        and evidence.get("termination") == "submit_result"
    )
    evidence["finished_at"] = utc_now()
    atomic_json(evidence_path, evidence)
    return evidence


def summarize(protocol: dict, protocol_hash: str, run_dir: Path, rows: list[dict]) -> dict:
    by_key = {(row["suite"], row["case_id"], row["condition"]): row for row in rows}
    contrasts = []
    for contrast in protocol["contrasts"]:
        suite = contrast["suite"]
        cases = protocol["cases"][suite]
        enabled = [by_key[(suite, case["id"], contrast["enabled"])] for case in cases]
        control = [by_key[(suite, case["id"], contrast["control"])] for case in cases]
        enabled_passes = sum(row["objective_pass"] for row in enabled)
        control_passes = sum(row["objective_pass"] for row in control)
        enabled_turns = sum(row["llm_turns"] for row in enabled) / len(enabled)
        control_turns = sum(row["llm_turns"] for row in control) / len(control)

        def primary_probes(rows_for_arm: list[dict]) -> int:
            return sum(
                event["name"] == "probe_resource"
                and event["arguments"].get("name") == case["primary"]
                for row, case in zip(rows_for_arm, cases)
                for event in row["tool_events"]
            ) if suite in {"tool_counter", "combined"} else 0

        def mean_component_score(rows_for_arm: list[dict]) -> float:
            values = [
                sum(row["component_scores"].values()) / len(row["component_scores"])
                for row in rows_for_arm
            ]
            return sum(values) / len(values)

        enabled_primary = primary_probes(enabled)
        control_primary = primary_probes(control)
        enabled_components = mean_component_score(enabled)
        control_components = mean_component_score(control)
        feature = contrast["feature"]
        if feature == "timestamps_raw":
            supported = None
            qualification = "nondirectional caveat; report the observed delta rather than a win/loss"
        elif feature == "tool_counter":
            supported = enabled_passes > control_passes or enabled_primary < control_primary
            qualification = "higher pass count or fewer primary retries"
        elif feature == "todo_list":
            supported = enabled_passes > control_passes and enabled_turns <= control_turns
            qualification = "higher complete-artifact count and no greater mean LLM turns"
        elif feature == "combined":
            supported = enabled_passes > control_passes and enabled_components > control_components
            qualification = "higher overall pass count and mean component score"
        else:
            supported = enabled_passes > control_passes
            qualification = "higher objective pass count"
        contrasts.append({
            **contrast,
            "enabled_passes": enabled_passes,
            "control_passes": control_passes,
            "pass_rate_delta": (enabled_passes - control_passes) / len(enabled),
            "n": len(enabled),
            "enabled_mean_turns": enabled_turns,
            "control_mean_turns": control_turns,
            "enabled_primary_probes": enabled_primary,
            "control_primary_probes": control_primary,
            "enabled_mean_component_score": enabled_components,
            "control_mean_component_score": control_components,
            "hypothesis_supported": supported,
            "hypothesis_qualification": qualification,
        })
    expected_runs = sum(
        len(condition_order(suite, index))
        for suite, cases in protocol["cases"].items()
        for index, _case in enumerate(cases)
    )
    protocol_complete = len(rows) == expected_runs and all(row.get("complete") for row in rows)
    order_valid = all(
        row.get("case_condition_order") == condition_order(
            row["suite"], next(
                index for index, case in enumerate(protocol["cases"][row["suite"]])
                if case["id"] == row["case_id"]
            )
        )
        and row.get("order_position") == row.get("case_condition_order", []).index(row["condition"])
        for row in rows
    )
    model_exact = all(
        (call.get("response") or {}).get("model") == protocol["provider"]["model"]
        for row in rows for call in row["api_calls"] if call.get("response")
    )
    def intervention_is_visible(row: dict) -> bool:
        raw_requests = json.dumps(
            [call.get("request", {}) for call in row["api_calls"]], ensure_ascii=False
        )
        raw_events = json.dumps(row["tool_events"], ensure_ascii=False)
        features = set(row["features"])
        checks = []
        if "timestamps" in features:
            checks.append(bool(re.search(r"\[2025-[0-9]{2}-[0-9]{2} [0-9:]{8}\]", raw_requests + raw_events)))
        if "timestamp_guidance" in features:
            checks.append("TIME GUIDANCE:" in raw_requests)
        if "tool_counter" in features:
            checks.append("TOOL COUNTS:" in raw_requests and "Tool call #" in raw_events)
        if "todo_list" in features:
            checks.append("TODO LIST:" in raw_requests and "rewrite_todo_list" in raw_requests)
        if "detailed_errors" in features:
            # The detailed exception is emitted by the audited tool, so it is
            # evidence in the tool-event/result channel rather than in the
            # request that preceded the failure.  Requiring it in the request
            # incorrectly rejected real runs whose tool protocol was valid.
            raw_trace = raw_requests + raw_events
            error_was_triggered = any(
                event.get("name") == "read_document" and not event.get("ok")
                for event in row["tool_events"]
            )
            checks.append(
                not error_was_triggered
                or ('error_type' in raw_trace and "FileNotFoundError" in raw_trace)
            )
        if "system_state" in features:
            checks.append("SYSTEM STATE:" in raw_requests)
        return all(checks)

    def disabled_is_clean(row: dict) -> bool:
        if row["condition"] != "disabled":
            return True
        raw_requests = json.dumps(
            [call.get("request", {}) for call in row["api_calls"]], ensure_ascii=False
        )
        raw_events = json.dumps(row["tool_events"], ensure_ascii=False)
        forbidden = (
            "<agent_status>", "TIME GUIDANCE:", "TOOL COUNTS:", "TODO LIST:",
            "SYSTEM STATE:", "Tool call #", "FileNotFoundError", "rewrite_todo_list",
            "update_todo_status",
        )
        return not any(item in raw_requests + raw_events for item in forbidden)

    comparison = {
        "experiment_id": "2-8",
        "created_at": utc_now(),
        "protocol_sha256": protocol_hash,
        "provider": protocol["provider"],
        "unique_runs": len(rows),
        "expected_unique_runs": expected_runs,
        "contrasts": contrasts,
        "usage": {
            key: sum(row["usage"][key] for row in rows)
            for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        },
        "cost": {
            "amount": sum(row["cost"]["amount"] for row in rows),
            "currency": "CNY",
            "qualification": "all prompt tokens conservatively priced as uncached",
        },
        "historical_claim_policy": protocol["historical_claim_policy"],
        "acceptance": {
            "all_preregistered_runs_complete": protocol_complete,
            "exact_model_every_response": model_exact,
            "all_tool_protocols_valid": all(row["tool_protocol_valid"] for row in rows),
            "all_provider_receipts_valid": all(row["provider_receipts_valid"] for row in rows),
            "preregistered_arm_order_recorded": order_valid,
            "interventions_visible_and_controls_clean": all(
                intervention_is_visible(row) if row["condition"] != "disabled" else disabled_is_clean(row)
                for row in rows
            ),
            "detailed_error_feature_exercised": any(
                row["condition"] == "detailed_errors"
                and any(
                    event.get("name") == "read_document" and not event.get("ok")
                    and "FileNotFoundError" in str(event.get("content"))
                    for event in row["tool_events"]
                )
                for row in rows
            ),
            "credential_scan_passed": False,
        },
    }
    configured = [value for name in ("MOONSHOT_API_KEY", "KIMI_API_KEY") if (value := os.getenv(name))]
    credential_findings = []
    for path in sorted((run_dir / "cases").glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        if any(secret in raw for secret in configured) or re.search(r"sk-[A-Za-z0-9_-]{16,}", raw):
            credential_findings.append(str(path.relative_to(run_dir)))
    credential_ok = not credential_findings
    comparison["acceptance"]["credential_scan_passed"] = credential_ok
    comparison["credential_scan_findings"] = credential_findings
    comparison["campaign_complete"] = all(comparison["acceptance"].values())
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-workers", type=int, default=5)
    args = parser.parse_args()
    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    protocol_hash = sha256_bytes(protocol_bytes)
    run_dir = args.output.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    protocol_copy = run_dir / "experiment_protocol.json"
    if protocol_copy.exists() and protocol_copy.read_bytes() != protocol_bytes:
        raise RuntimeError("run protocol copy differs from frozen protocol")
    protocol_copy.write_bytes(protocol_bytes)
    key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
    if not key:
        raise RuntimeError("MOONSHOT_API_KEY or KIMI_API_KEY is required")
    client = OpenAI(api_key=key, base_url=protocol["provider"]["base_url"])

    jobs = []
    for suite, cases in protocol["cases"].items():
        for index, case in enumerate(cases):
            jobs.append((suite, case, condition_order(suite, index)))

    rows: list[dict] = []
    failures = []

    def run_case(job):
        suite, case, conditions = job
        completed = []
        for position, condition in enumerate(conditions):
            completed.append(run_one(
                client, protocol, protocol_hash, run_dir, suite, case, condition,
                conditions, position,
            ))
        return completed

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {executor.submit(run_case, job): job for job in jobs}
        for future in as_completed(futures):
            suite, case, _ = futures[future]
            try:
                result = future.result()
                rows.extend(result)
                print(f"[{suite}/{case['id']}] completed {len(result)} conditions", flush=True)
            except Exception as exc:
                failures.append({"suite": suite, "case_id": case["id"], "error": str(exc)})
                print(f"[{suite}/{case['id']}] ERROR {exc}", file=sys.stderr, flush=True)

    if failures:
        atomic_json(run_dir / "transport_failures.json", failures)
        return 2
    comparison = summarize(protocol, protocol_hash, run_dir, rows)
    comparison_path = run_dir / "comparison.json"
    atomic_json(comparison_path, comparison)
    artifacts = {}
    for path in sorted((run_dir / "cases").glob("*.json")):
        artifacts[str(path.relative_to(run_dir))] = sha256_file(path)
    manifest = {
        "experiment_id": "2-8",
        "campaign_complete": comparison["campaign_complete"],
        "protocol_sha256": protocol_hash,
        "comparison_sha256": sha256_file(comparison_path),
        "case_artifacts": artifacts,
    }
    atomic_json(run_dir / "manifest.json", manifest)
    print(json.dumps({**manifest, "acceptance": comparison["acceptance"]}, indent=2))
    return 0 if comparison["campaign_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
