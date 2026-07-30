#!/usr/bin/env python3
"""Run Experiment 4-3 through the collaboration MCP stdio server."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
SERVER = HERE / "src" / "main.py"
VALIDATION = HERE / "validation" / "experiment_4_3"
CREDENTIAL = re.compile(r"\b(?:sk|gh[opusr])-[A-Za-z0-9_-]{12,}\b")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n"
    if CREDENTIAL.search(text):
        raise ValueError(f"credential-shaped value in {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_value(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"result"}:
            return parse_value(value["result"])
        return value
    if isinstance(value, str):
        for parser in (json.loads, ast.literal_eval):
            try:
                return parse_value(parser(value))
            except Exception:
                pass
    return value


def unwrap(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if structured:
        return parse_value(structured)
    texts = [getattr(item, "text", None) for item in getattr(result, "content", [])]
    texts = [item for item in texts if item]
    return parse_value(texts[0]) if len(texts) == 1 else [parse_value(item) for item in texts]


async def run(campaign_id: str) -> Path:
    run_dir = VALIDATION / campaign_id
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / "protocol.json",
               json.loads((HERE / "experiment_protocol.json").read_text(encoding="utf-8")))
    env = os.environ.copy()
    env.update({
        "COLLAB_PROVIDER": "moonshot", "OPENAI_MODEL": "kimi-k3",
        "COLLAB_LLM_RECEIPT_PATH": str(run_dir / "llm_receipts.checkpoint.json"),
        "HITL_TIMEOUT_SECONDS": "2", "BROWSER_HEADLESS": "true",
        "TIMER_STORAGE_PATH": str(run_dir / "timers.json"),
        # Prevent placeholder values in the checked-in development .env from
        # being mistaken for configured notification credentials.
        "SENDGRID_API_KEY": "", "SMTP_USERNAME": "", "SMTP_PASSWORD": "",
        "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_DEFAULT_CHAT_ID": "",
        "SLACK_WEBHOOK_URL": "", "DISCORD_WEBHOOK_URL": "",
        "HITL_ADMIN_EMAIL": "", "HITL_WEBHOOK_URL": "",
    })
    parameters = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env, cwd=str(HERE / "src"))
    receipts: list[dict[str, Any]] = []
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            schemas = [tool.model_dump(by_alias=True, exclude_none=True, mode="json") for tool in listed.tools]
            write_json(run_dir / "catalog.json", {
                "transport": "mcp-stdio", "server_name": initialized.serverInfo.name,
                "server_version": initialized.serverInfo.version, "schemas": schemas,
                "schema_sha256": hashlib.sha256(json.dumps(schemas, sort_keys=True).encode()).hexdigest()})

            async def call(case: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
                started = time.perf_counter()
                try:
                    result = await session.call_tool(tool, arguments=arguments)
                    payload = unwrap(result)
                    is_error = bool(getattr(result, "isError", False) or getattr(result, "is_error", False))
                except Exception as exc:
                    payload, is_error = {"success": False, "error": f"{type(exc).__name__}: {exc}"}, True
                row = {"case": case, "tool": tool, "arguments": arguments,
                       "transport": "mcp-stdio", "mcp_result_is_error": is_error,
                       "payload": payload, "latency_seconds": round(time.perf_counter() - started, 3)}
                receipts.append(row)
                write_json(run_dir / "receipts" / f"{len(receipts):02d}_{case}.json", row)
                return row

            parent_context = {
                "customer": "Ada", "request": "Refund an item bought 3 days ago for SGD 80",
                "policy": "Refunds within 7 days and below SGD 100 may be approved",
                "irrelevant_history": ["weather chat", "shipping FAQ", "newsletter"],
                "private_note": "PRIVATE-MARKER-MUST-BE-FILTERED",
            }
            minimal = await call("minimal_sync", "mcp_spawn_subagent", {
                "task": "Decide whether the refund meets the supplied policy and explain.",
                "context_strategy": "minimal", "mode": "sync", "parent_context": parent_context,
                "role": "refund policy specialist", "minimal_slice": ["policy"]})
            generated = await call("llm_generated_sync", "mcp_spawn_subagent", {
                "task": "Decide whether the refund meets the supplied policy and explain.",
                "context_strategy": "llm_generated", "mode": "sync", "parent_context": parent_context,
                "role": "refund policy specialist",
                "business_rules": "Keep customer, request, and policy. Exclude private_note and irrelevant history."})
            minimal_id = minimal["payload"].get("subagent_id")
            await call("multi_turn_message", "mcp_send_message_to_subagent", {
                "subagent_id": minimal_id,
                "message": "Additional fact: the item is unused. Re-evaluate using only supplied facts."})

            asynchronous = await call("async_spawn", "mcp_spawn_subagent", {
                "task": "Return a JSON summary of the number 17 and whether it is prime.",
                "context_strategy": "minimal", "mode": "async", "role": "math specialist"})
            async_id = asynchronous["payload"].get("subagent_id")
            async_status = None
            for attempt in range(80):
                async_status = await call(f"async_status_{attempt + 1}", "mcp_get_subagent_status",
                                          {"subagent_id": async_id})
                if async_status["payload"].get("status") in {"completed", "failed"}:
                    break
                await asyncio.sleep(0.25)

            cancel_spawn = await call("cancel_spawn", "mcp_spawn_subagent", {
                "task": "Write a detailed taxonomy with one thousand entries.",
                "context_strategy": "minimal", "mode": "async", "role": "taxonomy specialist"})
            cancel_id = cancel_spawn["payload"].get("subagent_id")
            await call("cancel_subagent", "mcp_cancel_subagent", {"subagent_id": cancel_id})
            await call("cancelled_status", "mcp_get_subagent_status", {"subagent_id": cancel_id})

            # Concurrent calls exercise a real pending request and an operator
            # response through the admin-facing MCP primitive.
            approval_task = asyncio.create_task(call("hitl_approval", "mcp_request_admin_approval", {
                "request_message": "Approve publishing the Experiment 4-3 result?",
                "context": {"risk": "low", "artifact": "validation-only"},
                "timeout_seconds": 8, "urgent": False}))
            await asyncio.sleep(0.5)
            pending = await call("hitl_pending", "mcp_list_pending_requests", {})
            pending_rows = pending["payload"].get("requests", [])
            request_id = pending_rows[0].get("request_id") if pending_rows else None
            if request_id:
                await call("hitl_operator_response", "mcp_respond_to_request", {
                    "request_id": request_id, "approved": True,
                    "admin_notes": "Approved by the automated validation operator; not a claimed human judgment."})
            approval = await approval_task
            timeout = await call("hitl_timeout", "mcp_request_admin_approval", {
                "request_message": "No operator will answer this timeout probe.",
                "context": {"probe": True}, "timeout_seconds": 1, "urgent": False})

            email = await call("email_notification_preflight", "mcp_send_email", {
                "to_email": "nobody@example.invalid", "subject": "Experiment 4-3",
                "body": "Credential preflight only"})
            telegram = await call("im_notification_preflight", "mcp_send_telegram_message", {
                "message": "Experiment 4-3 credential preflight", "chat_id": "0", "parse_mode": "HTML"})
            slack = await call("slack_notification_preflight", "mcp_send_slack_message", {
                "message": "Experiment 4-3 credential preflight"})

    llm_path = run_dir / "llm_receipts.checkpoint.json"
    llm_receipts = json.loads(llm_path.read_text(encoding="utf-8")) if llm_path.is_file() else []
    write_json(run_dir / "llm_receipts.json", llm_receipts)
    by_case = {row["case"]: row["payload"] for row in receipts}
    required_tools = {"mcp_spawn_subagent", "mcp_send_message_to_subagent",
                      "mcp_cancel_subagent", "mcp_get_subagent_status",
                      "mcp_request_admin_approval", "mcp_request_admin_input",
                      "mcp_send_email", "mcp_send_telegram_message", "mcp_send_slack_message"}
    tool_names = {schema["name"] for schema in schemas}
    gates = {
        "real_mcp_catalog_has_required_primitives": required_tools <= tool_names,
        "two_real_context_strategies_compared": (
            by_case["minimal_sync"].get("success") is True
            and by_case["llm_generated_sync"].get("success") is True
            and by_case["minimal_sync"].get("context_strategy") == "minimal"
            and by_case["llm_generated_sync"].get("context_strategy") == "llm_generated"
            and by_case["llm_generated_sync"].get("prep_tokens", 0) > 0
            and "PRIVATE-MARKER-MUST-BE-FILTERED" not in
                by_case["llm_generated_sync"].get("prepared_context", "")),
        "raw_model_usage_latency_receipts": bool(llm_receipts) and all(
            row.get("response", {}).get("id") and row.get("usage", {}).get("total_tokens") is not None
            and row.get("latency_seconds") is not None for row in llm_receipts),
        "sync_async_message_cancel_status_lifecycle": (
            by_case["multi_turn_message"].get("success") is True
            and async_status is not None and async_status["payload"].get("status") == "completed"
            and by_case["cancel_subagent"].get("success") is True
            and by_case["cancelled_status"].get("status") == "cancelled"),
        "hitl_pending_response_and_conservative_timeout": (
            bool(request_id) and approval["payload"].get("approved") is True
            and timeout["payload"].get("timeout") is True
            and timeout["payload"].get("approved") is False),
        "real_human_decision": False,
        "real_email_notification": email["payload"].get("success") is True,
        "real_im_notification": telegram["payload"].get("success") is True,
        "real_slack_notification": slack["payload"].get("success") is True,
    }
    core = [name for name in gates if name not in {
        "real_human_decision", "real_email_notification", "real_im_notification", "real_slack_notification"}]
    status = "passed" if all(gates.values()) else ("blocked" if all(gates[name] for name in core) else "failed")
    summary = {"experiment": "4-3", "campaign_id": campaign_id,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "status": status, "official_complete": status == "passed", "gates": gates,
               "blockers": [name for name, value in gates.items() if not value],
               "tool_call_count": len(receipts), "model_call_count": len(llm_receipts)}
    write_json(run_dir / "summary.json", summary)
    files = [{"path": str(path.relative_to(run_dir)), "bytes": path.stat().st_size, "sha256": sha(path)}
             for path in sorted(run_dir.rglob("*")) if path.is_file() and path.name != "manifest.json"]
    write_json(run_dir / "manifest.json", {"experiment": "4-3", "campaign_id": campaign_id,
               "status": status, "official_complete": status == "passed", "files": files})
    write_json(VALIDATION / "latest.json", {"experiment": "4-3", "campaign_id": campaign_id,
               "status": status, "official_complete": status == "passed",
               "manifest": str((run_dir / "manifest.json").relative_to(HERE)),
               "manifest_sha256": sha(run_dir / "manifest.json")})
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-id", default=datetime.now(timezone.utc).strftime("real_mcp_%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    path = asyncio.run(run(args.campaign_id))
    print(path)
    return 0 if json.loads((path / "summary.json").read_text())["status"] in {"passed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
