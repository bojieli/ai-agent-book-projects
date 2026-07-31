"""LLM decision point that may autonomously call ``initiate_phone_call_agent``."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from models import DecisionRecord, FieldSpec

TOOL_NAME = "initiate_phone_call_agent"


def _clients_and_models():
    from openai import AsyncOpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    candidates = []
    if os.getenv("ARK_API_KEY"):
        candidates.append(
            (
                AsyncOpenAI(
                    api_key=os.environ["ARK_API_KEY"],
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                ),
                os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"),
                "Volcengine ARK",
            )
        )
    if os.getenv("MOONSHOT_API_KEY"):
        candidates.append(
            (
                AsyncOpenAI(
                    api_key=os.environ["MOONSHOT_API_KEY"],
                    base_url="https://api.moonshot.cn/v1",
                ),
                os.getenv("MOONSHOT_MODEL", "kimi-k3"),
                "Moonshot",
            )
        )
    if os.getenv("OPENAI_API_KEY"):
        candidates.append(
            (
                AsyncOpenAI(
                    api_key=os.environ["OPENAI_API_KEY"],
                    base_url=os.getenv("OPENAI_BASE_URL") or None,
                ),
                model,
                "OpenAI",
            )
        )
    if os.getenv("OPENROUTER_API_KEY"):
        routed = model if "/" in model else f"openai/{model}"
        candidates.append(
            (
                AsyncOpenAI(
                    api_key=os.environ["OPENROUTER_API_KEY"],
                    base_url="https://openrouter.ai/api/v1",
                ),
                routed,
                "OpenRouter",
            )
        )
    if not candidates:
        raise RuntimeError(
            "需要 MOONSHOT_API_KEY、ARK_API_KEY、OPENAI_API_KEY 或 OPENROUTER_API_KEY"
        )
    return candidates


async def decide_orchestration(
    *,
    page_url: str,
    page_title: str,
    fields: list[FieldSpec],
    known_values: dict[str, str],
    elapsed: float,
    raw_request_path: str | None = None,
    raw_response_path: str | None = None,
) -> DecisionRecord:
    """Let the Computer Use Agent choose whether to initiate a Phone Agent.

    There is intentionally no Python ``if len(fields)`` decision. The model sees the
    browser observation, available context, and an optional tool; ``tool_choice=auto``
    is the experiment's autonomy boundary.
    """

    if bool(raw_request_path) != bool(raw_response_path):
        raise ValueError("raw decision request and response paths must be provided together")
    clients = _clients_and_models()
    visible_fields = [
        {
            "name": f.name,
            "label": f.label,
            "type": f.input_type,
            "required": f.required,
            "format_hint": f.format_hint,
            "options": f.options,
        }
        for f in fields
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": TOOL_NAME,
                "description": (
                    "Start a live Phone Agent when a user must provide many missing pieces of "
                    "structured information conversationally. The Phone Agent asks, confirms, "
                    "validates, and streams each collected field back to the browser Agent."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "purpose": {"type": "string"},
                        "required_info": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "label": {"type": "string"},
                                    "format_hint": {"type": "string"},
                                },
                                "required": ["name", "label"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["purpose", "required_info"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    kwargs = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Computer Use Agent completing a registration request. Inspect "
                    "the real page observation and the information already in context. When you "
                    "need to collect a large amount of structured information and it can be done "
                    "step by step through conversation, consider calling the Phone Agent tool. "
                    "Do not call it for one or two simple missing values. Never invent user data. "
                    "Give only a short decision summary; do not reveal private chain-of-thought."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "request": "帮我在这个网站上完成注册",
                        "page_url": page_url,
                        "page_title": page_title,
                        "form_fields": visible_fields,
                        "known_context_fields": sorted(known_values),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "tools": tools,
        "tool_choice": "auto",
    }
    last_error = None
    for client, model, provider in clients:
        request_started = time.monotonic()
        try:
            response = await client.chat.completions.create(model=model, **kwargs)
            provider_latency_seconds = round(time.monotonic() - request_started, 6)
            break
        except Exception as exc:  # noqa: BLE001 - try the next configured provider
            last_error = exc
            print(f"[自主决策] {provider} 调用失败，尝试下一已配置文本端点：{type(exc).__name__}")
    else:
        raise RuntimeError("所有已配置的文本模型端点均调用失败") from last_error
    if raw_request_path and raw_response_path:
        request_receipt = {
            "schema_version": 1,
            "experiment": "10-5",
            "provider": provider,
            "endpoint": str(client.base_url).rstrip("/"),
            "credential_fields_retained": [],
            "request": {"model": model, **kwargs},
        }
        response_receipt = {
            "schema_version": 1,
            "experiment": "10-5",
            "provider": provider,
            "latency_seconds": provider_latency_seconds,
            "response": response.model_dump(mode="json"),
        }
        for path_value, receipt in (
            (raw_request_path, request_receipt),
            (raw_response_path, response_receipt),
        ):
            path = Path(path_value)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(receipt, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    message = response.choices[0].message
    call = next((c for c in (message.tool_calls or []) if c.function.name == TOOL_NAME), None)
    purpose = ""
    requested: list[FieldSpec] = []
    if call:
        args = json.loads(call.function.arguments)
        purpose = str(args.get("purpose", ""))
        by_name = {f.name: f for f in fields}
        by_label = {f.label.casefold(): f for f in fields}
        for item in args.get("required_info", []):
            candidate = by_name.get(str(item.get("name", ""))) or by_label.get(
                str(item.get("label", "")).casefold()
            )
            if candidate and candidate.name not in known_values and candidate not in requested:
                requested.append(candidate)

    return DecisionRecord(
        page_url=page_url,
        page_title=page_title,
        known_fields=sorted(known_values),
        discovered_fields=fields,
        tool_called=TOOL_NAME if call else None,
        purpose=purpose,
        required_info=requested,
        rationale_summary=(
            message.content or "模型通过工具调用决定启动 Phone Agent"
            if call
            else "模型决定继续当前流程"
        ).strip(),
        model=model,
        monotonic_seconds=round(time.monotonic() - elapsed, 6),
        provider=provider,
        provider_response_id=getattr(response, "id", None),
        provider_usage={
            key: int(value)
            for key, value in {
                "prompt_tokens": getattr(getattr(response, "usage", None), "prompt_tokens", None),
                "completion_tokens": getattr(
                    getattr(response, "usage", None), "completion_tokens", None
                ),
                "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", None),
            }.items()
            if value is not None
        },
    )
