#!/usr/bin/env python3
"""Run Experiment 4-4 through the collaboration MCP stdio server."""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import os
import re
import select
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
SERVER = HERE / "src" / "main.py"
VALIDATION = HERE / "validation" / "experiment_4_4"
CREDENTIAL = re.compile(r"\b(?:sk|gh[opusr])-[A-Za-z0-9_-]{12,}\b")
SENSITIVE_ENV_NAMES = {
    "ANTHROPIC_API_KEY",
    "KIMI_API_KEY",
    "MOONSHOT_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "SENDGRID_API_KEY",
    "SMTP_PASSWORD",
    "SMTP_USERNAME",
    "SMTP_FROM_EMAIL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_DEFAULT_CHAT_ID",
    "SLACK_WEBHOOK_URL",
    "DISCORD_WEBHOOK_URL",
    "HITL_ADMIN_EMAIL",
    "HITL_WEBHOOK_URL",
}
DELIVERY_GATES = {
    "real_email_notification",
    "real_im_notification",
    "real_slack_notification",
}
SYNTHETIC_PRIVACY_CANARY = "PRIVATE-MARKER-MUST-BE-FILTERED"


def parse_human_decision(value: str) -> tuple[bool, str]:
    """Parse one explicit APPROVE/REJECT line from a live human operator."""
    match = re.fullmatch(r"\s*(APPROVE|REJECT)(?:\s*:\s*(.*))?\s*", value, re.I)
    if not match:
        raise ValueError("decision must be APPROVE or REJECT, optionally followed by ': notes'")
    approved = match.group(1).upper() == "APPROVE"
    notes = (match.group(2) or "").strip()
    return approved, notes or "No additional notes supplied by the live human operator."


def _readline_before_timeout(stream: Any, timeout_seconds: float) -> str:
    """Read one byte stream line while ensuring the worker exits by its deadline."""
    descriptor = stream.fileno()
    encoding = getattr(stream, "encoding", None) or "utf-8"
    deadline = time.monotonic() + timeout_seconds
    data = bytearray()
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        readable, _, _ = select.select([descriptor], [], [], remaining)
        if not readable:
            raise TimeoutError
        chunk = os.read(descriptor, 1)
        if not chunk:
            return data.decode(encoding, errors="replace")
        data.extend(chunk)
        if chunk == b"\n":
            return data.decode(encoding, errors="replace")


async def read_human_decision_line(stream: Any, timeout_seconds: float) -> str:
    """Read a live decision without leaving a permanently blocked stdin worker."""
    try:
        return await asyncio.to_thread(
            _readline_before_timeout,
            stream,
            timeout_seconds,
        )
    except TimeoutError as exc:
        raise RuntimeError(
            f"live human decision input timed out after {timeout_seconds} seconds"
        ) from exc


def remaining_before_deadline(deadline: float, *, now: float | None = None) -> float:
    """Return a positive remaining duration for a shared approval deadline."""
    remaining = deadline - (time.monotonic() if now is None else now)
    if remaining <= 0:
        raise RuntimeError("live human decision input timed out before presentation")
    return remaining


def notification_readiness(env: dict[str, str]) -> dict[str, bool]:
    """Report whether all inputs for each real notification gate are present."""
    email_service = bool(
        env.get("SENDGRID_API_KEY") and env.get("SMTP_FROM_EMAIL")
    ) or bool(
        env.get("SMTP_USERNAME") and env.get("SMTP_PASSWORD")
    )
    return {
        "email": bool(email_service and env.get("HITL_ADMIN_EMAIL")),
        "telegram": bool(
            env.get("TELEGRAM_BOT_TOKEN") and env.get("TELEGRAM_DEFAULT_CHAT_ID")
        ),
        "slack": bool(env.get("SLACK_WEBHOOK_URL")),
    }


def human_decision_accepted(
    human_decision: dict[str, Any] | None,
    mcp_result: dict[str, Any],
) -> bool:
    """Return whether MCP accepted the live decision for the same request."""
    return bool(
        human_decision
        and mcp_result.get("success") is True
        and mcp_result.get("timeout") is not True
        and mcp_result.get("approved") is human_decision.get("approved")
        and mcp_result.get("request_id") == human_decision.get("request_id")
    )


def publication_is_authorized(
    human_decision: dict[str, Any] | None,
    mcp_result: dict[str, Any],
) -> bool:
    """Return whether an accepted live decision explicitly approved publication."""
    return bool(
        human_decision_accepted(human_decision, mcp_result)
        and human_decision.get("approved") is True
    )


def classify_status(gates: dict[str, bool], *, interactive_human: bool) -> str:
    """Classify a run while reserving ``blocked`` for unavailable external gates."""
    if all(gates.values()):
        return "passed"
    exempt_gates = set(DELIVERY_GATES)
    if not interactive_human:
        exempt_gates.add("real_human_decision")
    core_gates = (value for name, value in gates.items() if name not in exempt_gates)
    return "blocked" if all(core_gates) else "failed"


def redact_material(value: Any, sensitive_values: tuple[str, ...]) -> Any:
    """Remove credentials and private delivery identifiers from retained evidence."""
    if isinstance(value, dict):
        return {key: redact_material(item, sensitive_values) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_material(item, sensitive_values) for item in value]
    if isinstance(value, str):
        redacted = value
        for sensitive in sensitive_values:
            redacted = redacted.replace(sensitive, "[REDACTED]")
        return redacted
    return value


def retain_human_decision(
    human_decision: dict[str, Any],
    mcp_result: dict[str, Any],
    sensitive_values: tuple[str, ...],
) -> dict[str, Any]:
    """Build a redacted decision record without changing the in-memory decision."""
    return redact_material(
        {**human_decision, "mcp_result": mcp_result},
        sensitive_values,
    )


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


async def run(
    campaign_id: str,
    *,
    interactive_human: bool = False,
    human_timeout_seconds: int = 14_400,
    real_notifications: bool = False,
) -> Path:
    if interactive_human and human_timeout_seconds <= 0:
        raise ValueError("human_timeout_seconds must be positive")
    env = os.environ.copy()
    readiness = notification_readiness(env)
    if real_notifications and not all(readiness.values()):
        missing = ", ".join(name for name, ready in readiness.items() if not ready)
        raise RuntimeError(f"real notification configuration is incomplete: {missing}")

    run_dir = VALIDATION / campaign_id
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / "protocol.json",
               json.loads((HERE / "experiment_protocol.json").read_text(encoding="utf-8")))
    env.update({
        "COLLAB_PROVIDER": "moonshot", "OPENAI_MODEL": "kimi-k3",
        "COLLAB_LLM_RECEIPT_PATH": str(run_dir / "llm_receipts.checkpoint.json"),
        "HITL_TIMEOUT_SECONDS": "2", "BROWSER_HEADLESS": "true",
        "TIMER_STORAGE_PATH": str(run_dir / "timers.json"),
    })
    if not real_notifications:
        # Prevent placeholder values in the checked-in development .env from
        # being mistaken for configured notification credentials or causing
        # accidental delivery during the default credential-free campaign.
        env.update({
            "SENDGRID_API_KEY": "", "SMTP_USERNAME": "", "SMTP_PASSWORD": "",
            "SMTP_FROM_EMAIL": "", "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_DEFAULT_CHAT_ID": "", "SLACK_WEBHOOK_URL": "",
            "DISCORD_WEBHOOK_URL": "", "HITL_ADMIN_EMAIL": "",
            "HITL_WEBHOOK_URL": "",
        })
    sensitive_values = tuple(
        value for name in SENSITIVE_ENV_NAMES if (value := env.get(name))
    )
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
                row = {"case": case, "tool": tool,
                       "arguments": redact_material(arguments, sensitive_values),
                       "transport": "mcp-stdio", "mcp_result_is_error": is_error,
                       "payload": redact_material(payload, sensitive_values),
                       "latency_seconds": round(time.perf_counter() - started, 3)}
                receipts.append(row)
                write_json(run_dir / "receipts" / f"{len(receipts):02d}_{case}.json", row)
                return row

            parent_context = {
                "customer": "Ada", "request": "Refund an item bought 3 days ago for SGD 80",
                "policy": "Refunds within 7 days and below SGD 100 may be approved",
                "irrelevant_history": ["weather chat", "shipping FAQ", "newsletter"],
                # This is a non-secret canary retained in the input receipt so
                # the filtered handoff can be checked independently.
                "private_note": SYNTHETIC_PRIVACY_CANARY,
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

            # Concurrent calls exercise a real pending request and a response
            # through the admin-facing MCP primitive. The default path retains
            # the historical automated validation operator. --interactive-human
            # instead blocks on one live APPROVE/REJECT line from stdin.
            approval_message = "Approve publishing the Experiment 4-4 result?"
            approval_context = {
                "risk": "low",
                "artifact": "validation-only",
                "consequence": "An approval authorizes publishing this run in a GitHub pull request; a rejection keeps it local.",
            }
            approval_deadline = (
                time.monotonic() + human_timeout_seconds
                if interactive_human else None
            )
            approval_task = asyncio.create_task(call("hitl_approval", "mcp_request_admin_approval", {
                "request_message": approval_message,
                "context": approval_context,
                "timeout_seconds": human_timeout_seconds if interactive_human else 8,
                "urgent": False}))
            await asyncio.sleep(0.5)
            pending = await call("hitl_pending", "mcp_list_pending_requests", {})
            pending_rows = pending["payload"].get("requests", [])
            request_id = pending_rows[0].get("request_id") if pending_rows else None
            human_decision = None
            if request_id:
                if interactive_human:
                    assert approval_deadline is not None
                    presented_at = datetime.now(timezone.utc).isoformat()
                    print("HITL_REQUEST=" + json.dumps({
                        "request_id": request_id,
                        "message": approval_message,
                        "context": approval_context,
                        "reply_format": "APPROVE[: notes] or REJECT[: notes]",
                    }, ensure_ascii=False), flush=True)
                    try:
                        raw_decision = await read_human_decision_line(
                            sys.stdin,
                            remaining_before_deadline(approval_deadline),
                        )
                    except RuntimeError:
                        if not approval_task.done():
                            approval_task.cancel()
                        await asyncio.gather(approval_task, return_exceptions=True)
                        raise
                    if not raw_decision:
                        raise RuntimeError("live human decision input closed before a response")
                    approved, notes = parse_human_decision(raw_decision)
                    human_decision = {
                        "request_id": request_id,
                        "decision": "approved" if approved else "rejected",
                        "approved": approved,
                        "admin_notes": notes,
                        "presented_at": presented_at,
                        "responded_at": datetime.now(timezone.utc).isoformat(),
                        "timeout_seconds": human_timeout_seconds,
                        "operator_channel": "live-user-chat-forwarded-verbatim-to-runner-stdin",
                        "attestation": (
                            "The active repository user supplied this decision during the run; "
                            "the runner did not synthesize or default it."
                        ),
                    }
                    await call("hitl_human_response", "mcp_respond_to_request", {
                        "request_id": request_id, "approved": approved,
                        "admin_notes": notes})
                else:
                    await call("hitl_operator_response", "mcp_respond_to_request", {
                        "request_id": request_id, "approved": True,
                        "admin_notes": "Approved by the automated validation operator; not a claimed human judgment."})
            approval = await approval_task
            if human_decision is not None:
                write_json(
                    run_dir / "human_decision.json",
                    retain_human_decision(
                        human_decision,
                        approval["payload"],
                        sensitive_values,
                    ),
                )
            timeout = await call("hitl_timeout", "mcp_request_admin_approval", {
                "request_message": "No operator will answer this timeout probe.",
                "context": {"probe": True}, "timeout_seconds": 1, "urgent": False})

            email = await call("email_notification_preflight", "mcp_send_email", {
                "to_email": env.get("HITL_ADMIN_EMAIL") if real_notifications else "nobody@example.invalid",
                "subject": "Experiment 4-4",
                "body": "Real Experiment 4-4 notification" if real_notifications else "Credential preflight only"})
            telegram_arguments = {
                "message": "Real Experiment 4-4 notification" if real_notifications else "Experiment 4-4 credential preflight",
                "parse_mode": "HTML",
            }
            if not real_notifications:
                telegram_arguments["chat_id"] = "0"
            telegram = await call("im_notification_preflight", "mcp_send_telegram_message",
                                  telegram_arguments)
            slack = await call("slack_notification_preflight", "mcp_send_slack_message", {
                "message": "Real Experiment 4-4 notification" if real_notifications else "Experiment 4-4 credential preflight"})

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
            and SYNTHETIC_PRIVACY_CANARY not in
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
            bool(request_id) and approval["payload"].get("success") is True
            and approval["payload"].get("timeout") is not True
            and timeout["payload"].get("timeout") is True
            and timeout["payload"].get("approved") is False),
        "real_human_decision": human_decision_accepted(
            human_decision, approval["payload"]
        ),
        "real_email_notification": email["payload"].get("success") is True,
        "real_im_notification": telegram["payload"].get("success") is True,
        "real_slack_notification": slack["payload"].get("success") is True,
    }
    status = classify_status(gates, interactive_human=interactive_human)
    summary = {"experiment": "4-4", "campaign_id": campaign_id,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "status": status, "official_complete": status == "passed", "gates": gates,
               "blockers": [name for name, value in gates.items() if not value],
               "tool_call_count": len(receipts), "model_call_count": len(llm_receipts),
               "interactive_human": interactive_human,
               "human_timeout_seconds": human_timeout_seconds if interactive_human else None,
               "publication_authorized": publication_is_authorized(
                   human_decision, approval["payload"]
               ),
               "real_notifications_enabled": real_notifications,
               "notification_readiness": readiness}
    write_json(run_dir / "summary.json", summary)
    files = [{"path": str(path.relative_to(run_dir)), "bytes": path.stat().st_size, "sha256": sha(path)}
             for path in sorted(run_dir.rglob("*")) if path.is_file() and path.name != "manifest.json"]
    write_json(run_dir / "manifest.json", {"experiment": "4-4", "campaign_id": campaign_id,
               "status": status, "official_complete": status == "passed", "files": files})
    write_json(VALIDATION / "latest.json", {"experiment": "4-4", "campaign_id": campaign_id,
               "status": status, "official_complete": status == "passed",
               "manifest": str((run_dir / "manifest.json").relative_to(HERE)),
               "manifest_sha256": sha(run_dir / "manifest.json")})
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-id", default=datetime.now(timezone.utc).strftime("real_mcp_%Y%m%dT%H%M%SZ"))
    parser.add_argument(
        "--interactive-human", action="store_true",
        help="wait for a live APPROVE/REJECT line on stdin and retain it as the human decision",
    )
    parser.add_argument(
        "--human-timeout-seconds", type=int, default=14_400,
        help="maximum live-response window for --interactive-human (default: 14400)",
    )
    parser.add_argument(
        "--real-notifications", action="store_true",
        help="use configured email, Telegram, and Slack delivery instead of credential-free preflights",
    )
    args = parser.parse_args()
    path = asyncio.run(run(
        args.campaign_id,
        interactive_human=args.interactive_human,
        human_timeout_seconds=args.human_timeout_seconds,
        real_notifications=args.real_notifications,
    ))
    print(path)
    return 0 if json.loads((path / "summary.json").read_text())["status"] in {"passed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
