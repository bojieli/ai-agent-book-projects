#!/usr/bin/env python3
"""Run and retain the bounded Experiment 9-6 native Computer Use trajectory.

This harness calls the pinned Anthropic Computer Use Demo's ``sampling_loop``.
It is intended to run inside that Demo's locally built container with a host
evidence directory mounted at ``/evidence``.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from computer_use_demo.loop import APIProvider, sampling_loop
from computer_use_demo.tools import ToolResult


TASK = (
    "Open Google, search for San Francisco weather today, and report the "
    "temperature and conditions. Do not sign in or change any external data."
)
MODEL = "claude-sonnet-4-5-20250929"
TOOL_VERSION = "computer_use_20250124"
ACTION_LIMIT = 25
OUT = Path(os.environ.get("EXP96_EVIDENCE_DIR", "/evidence"))


class ActionLimitReached(RuntimeError):
    """Raised before an action beyond the experiment ceiling executes."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return json_safe(value.model_dump())
    return repr(value)


async def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    OUT.mkdir(parents=True, exist_ok=True)
    screenshots = OUT / "screenshots"
    receipts = OUT / "api_receipts"
    screenshots.mkdir(exist_ok=True)
    receipts.mkdir(exist_ok=True)

    started_at = utc_now()
    api_calls: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    action_by_id: dict[str, dict[str, Any]] = {}
    refused_action: dict[str, Any] | None = None
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": [{"type": "text", "text": TASK}]}
    ]
    termination = "unknown"
    exception: dict[str, Any] | None = None

    def api_response_callback(request: Any, response: Any, error: Any) -> None:
        index = len(api_calls) + 1
        request_body = b""
        try:
            request_body = request.content or b""
        except Exception:
            pass

        response_json = None
        response_status = getattr(response, "status_code", None)
        try:
            response_json = response.json()
        except Exception:
            if isinstance(response, (dict, list)):
                response_json = response

        receipt_name = f"response-{index:02d}.json"
        if response_json is not None:
            (receipts / receipt_name).write_text(
                json.dumps(json_safe(response_json), indent=2, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
        else:
            receipt_name = None

        headers = getattr(response, "headers", {}) or {}
        api_calls.append(
            {
                "index": index,
                "observed_at": utc_now(),
                "request": {
                    "method": getattr(request, "method", None),
                    "url": str(getattr(request, "url", "")),
                    "body_bytes": len(request_body),
                    "body_sha256": sha256_bytes(request_body),
                    "credential_header_present": bool(
                        getattr(request, "headers", {}).get("x-api-key")
                    ),
                },
                "response": {
                    "http_status": response_status,
                    "request_id": headers.get("request-id")
                    or headers.get("x-request-id"),
                    "message_id": (
                        response_json.get("id")
                        if isinstance(response_json, dict)
                        else None
                    ),
                    "model": (
                        response_json.get("model")
                        if isinstance(response_json, dict)
                        else None
                    ),
                    "stop_reason": (
                        response_json.get("stop_reason")
                        if isinstance(response_json, dict)
                        else None
                    ),
                    "usage": (
                        response_json.get("usage")
                        if isinstance(response_json, dict)
                        else None
                    ),
                    "receipt": (
                        f"api_receipts/{receipt_name}" if receipt_name else None
                    ),
                },
                "error_type": type(error).__name__ if error else None,
                "error": str(error) if error else None,
            }
        )

    def output_callback(block: Any) -> None:
        nonlocal refused_action
        value = json_safe(block)
        if not isinstance(value, dict) or value.get("type") != "tool_use":
            return
        if len(actions) >= ACTION_LIMIT:
            refused_action = {
                "tool_use_id": value.get("id"),
                "tool": value.get("name"),
                "input": value.get("input"),
                "executed": False,
                "reason": "action_limit",
            }
            raise ActionLimitReached(
                f"refused action {ACTION_LIMIT + 1}; limit is {ACTION_LIMIT}"
            )
        record = {
            "index": len(actions) + 1,
            "tool_use_id": value.get("id"),
            "tool": value.get("name"),
            "input": value.get("input"),
            "executed": True,
            "result": None,
        }
        actions.append(record)
        action_by_id[str(value.get("id"))] = record

    def tool_output_callback(result: ToolResult, tool_use_id: str) -> None:
        record = action_by_id[tool_use_id]
        image_path = None
        image_sha256 = None
        image_bytes = 0
        if result.base64_image:
            import base64

            raw = base64.b64decode(result.base64_image)
            image_path = f"screenshots/action-{record['index']:02d}.png"
            (OUT / image_path).write_bytes(raw)
            image_sha256 = sha256_bytes(raw)
            image_bytes = len(raw)
        record["result"] = {
            "output": result.output,
            "error": result.error,
            "system": result.system,
            "screenshot": image_path,
            "screenshot_sha256": image_sha256,
            "screenshot_bytes": image_bytes,
        }

    try:
        await sampling_loop(
            model=MODEL,
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix=(
                "This is a bounded, read-only evaluation. Do not sign in, accept "
                "agreements, submit forms, or modify external data. Use the GUI "
                "to perform the requested Google search and ground the final answer "
                "in the visible result. If Google presents a CAPTCHA or other human "
                "verification challenge, do not interact with it and do not ask the "
                "user to solve it. Instead, navigate directly to this reputable, "
                "read-only Open-Meteo current-weather endpoint: "
                "https://api.open-meteo.com/v1/forecast?latitude=37.7749&longitude="
                "-122.4194&current=temperature_2m,weather_code&temperature_unit="
                "fahrenheit&timezone=America%2FLos_Angeles . Read the visible JSON, "
                "interpret its WMO weather code, identify Open-Meteo as the alternate "
                "source, and finish immediately. You have at most 25 actions total: "
                "once a credible current temperature and condition are visible, do "
                "not scroll or explore further; return the final answer."
            ),
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=os.environ["ANTHROPIC_API_KEY"],
            only_n_most_recent_images=3,
            max_tokens=4096,
            tool_version=TOOL_VERSION,
            thinking_budget=None,
            token_efficient_tools_beta=False,
        )
        termination = "model_finished"
    except ActionLimitReached as exc:
        termination = "action_limit"
        exception = {"type": type(exc).__name__, "message": str(exc)}
    except Exception as exc:
        termination = "error"
        exception = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }

    final_texts: list[str] = []
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        for block in message.get("content", []):
            value = json_safe(block)
            if isinstance(value, dict) and value.get("type") == "text":
                final_texts.append(value.get("text", ""))
        if final_texts:
            break

    usage_totals: dict[str, int] = {}
    for call in api_calls:
        usage = call["response"].get("usage") or {}
        for key, value in usage.items():
            if isinstance(value, int):
                usage_totals[key] = usage_totals.get(key, 0) + value

    final_stop_reason = (
        api_calls[-1]["response"].get("stop_reason") if api_calls else None
    )
    record = {
        "schema_version": 1,
        "experiment": "9-6",
        "status": "completed" if termination == "model_finished" else termination,
        "started_at": started_at,
        "finished_at": utc_now(),
        "task": TASK,
        "safety": {
            "read_only": True,
            "sign_in_allowed": False,
            "external_mutation_allowed": False,
        },
        "provider": "Anthropic API",
        "requested_model": MODEL,
        "observed_models": sorted(
            {
                call["response"]["model"]
                for call in api_calls
                if call["response"].get("model")
            }
        ),
        "tool_version": TOOL_VERSION,
        "action_limit": ACTION_LIMIT,
        "actions_executed": len(actions),
        "termination": termination,
        "provider_stop_reason": final_stop_reason,
        "final_answer": "\n".join(reversed(final_texts)).strip(),
        "exception": exception,
        "refused_action": refused_action,
        "usage_totals": usage_totals,
        "api_calls": api_calls,
        "actions": actions,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "source_commit": os.environ.get("EXP96_SOURCE_COMMIT"),
            "dockerfile_sha256": os.environ.get("EXP96_DOCKERFILE_SHA256"),
            "image_id": os.environ.get("EXP96_IMAGE_ID"),
            "base_image_digest": os.environ.get("EXP96_BASE_IMAGE_DIGEST"),
        },
    }
    (OUT / "trajectory.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": record["status"],
                "api_calls": len(api_calls),
                "actions_executed": len(actions),
                "final_stop_reason": final_stop_reason,
                "final_answer": record["final_answer"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if termination == "model_finished" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
