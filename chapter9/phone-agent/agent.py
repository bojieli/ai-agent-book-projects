"""Fail-closed LLM planning and dialogue contracts for Experiment 9-2.

The direct arm receives a fixed call plan.  The ReAct arm asks a real external
OpenAI-compatible provider to observe an incomplete task, identify missing facts,
and choose the browser-call action.  Both arms use the same external model for the
post-ASR dialogue turn.  Provider errors are surfaced; this module has no local
planner, parser, mock, or fallback path.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

DEFAULT_ARK_MODEL = "doubao-seed-1-6-flash-250615"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


@dataclass(frozen=True)
class CallPlan:
    mode: str
    callee_name: str
    goal: str
    context: str
    instructions: str
    opening_line: str
    missing_information: list[str] = field(default_factory=list)
    trace: list[dict[str, str]] = field(default_factory=list)
    planner_model: str | None = None
    planner_receipt: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: str
    base_url: str | None
    model: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} is required")
    return cleaned


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _redact_secrets(value: Any) -> Any:
    """Remove credential values before any provider request/response is retained."""
    serialized = json.dumps(value, ensure_ascii=False)
    for name, secret in os.environ.items():
        if (
            any(marker in name.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
            and len(secret) >= 8
        ):
            serialized = serialized.replace(secret, "[REDACTED]")
    serialized = re.sub(r"\b(?:sk|ak)-[A-Za-z0-9_-]{12,}\b", "[REDACTED]", serialized)
    return json.loads(serialized)


def _provider_config(model: str | None = None) -> ProviderConfig:
    provider = os.getenv("PHONE_MODEL_PROVIDER", "ark").casefold()
    if provider == "ark":
        key = os.getenv("ARK_API_KEY", "")
        if not key:
            raise RuntimeError("PHONE_MODEL_PROVIDER=ark requires ARK_API_KEY")
        return ProviderConfig(
            name="ark",
            api_key=key,
            base_url=os.getenv("ARK_BASE_URL", ARK_BASE_URL),
            model=model or os.getenv("PHONE_PLANNER_MODEL", DEFAULT_ARK_MODEL),
        )
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError("PHONE_MODEL_PROVIDER=openai requires OPENAI_API_KEY")
        return ProviderConfig(
            name="openai",
            api_key=key,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            model=model or os.getenv("PHONE_PLANNER_MODEL", "gpt-4.1-mini"),
        )
    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError("PHONE_MODEL_PROVIDER=openrouter requires OPENROUTER_API_KEY")
        return ProviderConfig(
            name="openrouter",
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
            model=model or os.getenv("PHONE_PLANNER_MODEL", "openai/gpt-4.1-mini"),
        )
    raise RuntimeError("PHONE_MODEL_PROVIDER must be ark, openai, or openrouter")


def _json_object(text: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise TypeError("model response must be a JSON object")
    return value


def _real_json_completion(
    *,
    purpose: str,
    messages: list[dict[str, str]],
    model: str | None = None,
    client: OpenAI | None = None,
    provider_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Make one real completion and retain a credential-free raw receipt."""
    config = _provider_config(model)
    active_client = client or OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=120,
        max_retries=0,
    )
    request = {
        "model": model or config.model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 700,
    }
    sanitized_request = _redact_secrets(request)
    started_at = _now()
    started = time.monotonic()
    response = active_client.chat.completions.create(**request)
    latency = time.monotonic() - started
    finished_at = _now()

    if not response.id:
        raise RuntimeError(f"{purpose} response omitted its provider response ID")
    if not response.choices:
        raise RuntimeError(f"{purpose} response contained no choices")
    choice = response.choices[0]
    content = (choice.message.content or "").strip()
    if not content:
        raise RuntimeError(f"{purpose} response contained no text")
    if not choice.finish_reason:
        raise RuntimeError(f"{purpose} response omitted finish status")
    usage = response.usage.model_dump(exclude_none=True) if response.usage else None
    if not usage or int(usage.get("total_tokens", 0)) <= 0:
        raise RuntimeError(f"{purpose} response omitted token usage")

    raw_response = _redact_secrets(response.model_dump(exclude_none=True))
    parsed = _json_object(content)
    receipt = {
        "schema_version": 1,
        "purpose": purpose,
        "execution": "real_external_llm",
        "provider": provider_name or config.name,
        "requested_model": request["model"],
        "provider_model": response.model,
        "provider_response_id": response.id,
        "finish_reason": choice.finish_reason,
        "usage": usage,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "latency_seconds": round(latency, 6),
        "request": sanitized_request,
        "request_sha256": _sha256_json(sanitized_request),
        "raw_response": raw_response,
        "raw_response_sha256": _sha256_json(raw_response),
        "response_content": content,
        "response_content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "external_request_completed": True,
        "mock": False,
        "probe_only": False,
        "fallback_used": False,
        "credential_fields_retained": False,
    }
    return parsed, receipt


def direct_plan(
    *,
    callee_name: str,
    goal: str,
    context: str,
    instructions: str,
) -> CallPlan:
    """Build the fixed-parameter control without an LLM planning call."""
    callee = _required("callee_name", callee_name)
    return CallPlan(
        mode="direct",
        callee_name=callee,
        goal=_required("goal", goal),
        context=_required("context", context),
        instructions=_required("instructions", instructions),
        opening_line=(
            f"Hello {callee}. Please state the exact appointment time and confirmation code, "
            "then explicitly confirm both."
        ),
        trace=[
            {"stage": "observation", "summary": "Caller supplied all call parameters."},
            {
                "stage": "action",
                "summary": "Open a WebRTC voice session with the fixed parameters.",
            },
        ],
    )


def react_plan(
    task: str,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    provider_name: str | None = None,
) -> CallPlan:
    """Use a real external LLM to create the ReAct call plan; never fall back."""
    task = _required("task", task)
    data, receipt = _real_json_completion(
        purpose="react_planning",
        client=client,
        model=model,
        provider_name=provider_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "Plan a local browser WebRTC voice call. Observe the user's task, identify every missing "
                    "task-critical fact, reason briefly about what must be collected, and choose the call action. "
                    "Never invent facts. Return only JSON with callee_name, goal, context, instructions, "
                    "opening_line, missing_information (array), and decision_summary. opening_line must ask aloud "
                    "for the missing appointment time and confirmation code. instructions must require the voice "
                    "Agent to repeat the facts, obtain explicit confirmation, and complete_task only with confirmed "
                    "values. This local experiment records a confirmation but performs no external booking."
                ),
            },
            {"role": "user", "content": task},
        ],
    )
    missing = data.get("missing_information")
    if (
        not isinstance(missing, list)
        or not missing
        or not all(isinstance(item, str) and item.strip() for item in missing)
    ):
        raise ValueError("ReAct planner must return a non-empty missing_information string array")
    decision = _required("decision_summary", str(data.get("decision_summary", "")))
    return CallPlan(
        mode="react",
        callee_name=_required("callee_name", str(data.get("callee_name", ""))),
        goal=_required("goal", str(data.get("goal", ""))),
        context=_required("context", str(data.get("context", ""))),
        instructions=_required("instructions", str(data.get("instructions", ""))),
        opening_line=_required("opening_line", str(data.get("opening_line", ""))),
        missing_information=[item.strip() for item in missing],
        trace=[
            {"stage": "observation", "summary": task},
            {"stage": "reason", "summary": decision},
            {
                "stage": "action",
                "summary": "Open a WebRTC call and collect the missing facts by voice.",
            },
        ],
        planner_model=f"{receipt['provider']}:{receipt['provider_model']}",
        planner_receipt=receipt,
    )


def conversation_turn(
    plan: CallPlan,
    transcript: list[dict[str, Any]],
    user_text: str,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    provider_name: str | None = None,
) -> dict[str, Any]:
    """Use the ASR transcript in one real dialogue/completion call; never fall back."""
    user_text = _required("ASR transcript", user_text)
    dialogue_model = model or os.getenv("PHONE_DIALOGUE_MODEL")
    data, receipt = _real_json_completion(
        purpose="post_asr_dialogue",
        client=client,
        model=dialogue_model,
        provider_name=provider_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the voice Agent in a short local browser call. The user text below came only from ASR "
                    "over the browser microphone RTP track. Return only JSON with assistant_message, "
                    "explicit_confirmation_observed (boolean), should_complete (boolean), and completion containing "
                    "result, appointment_time, confirmation_number, notes. If the user states an exact time, a "
                    "confirmation code, and explicitly confirms both, set should_complete=true, normalize obvious "
                    "spoken code words/digits into a concise code, and repeat both details in assistant_message. "
                    "Otherwise ask only for what is missing. Never say booked, arranged, scheduled, or imply an "
                    "external action occurred. For a completed turn, completion.result must be exactly "
                    "'Local confirmation recorded.' and completion.notes must be exactly "
                    "'No external organization was contacted or booking made.' "
                    f"Goal: {plan.goal}\nContext: {plan.context}\nInstructions: {plan.instructions}"
                ),
            },
            {
                "role": "user",
                "content": _canonical_json(
                    {
                        "prior_audio_transcript": transcript,
                        "latest_user_asr_transcript": user_text,
                    }
                ),
            },
        ],
    )
    completion = data.get("completion")
    required = {"result", "appointment_time", "confirmation_number", "notes"}
    if not isinstance(completion, dict) or not required.issubset(completion):
        raise ValueError("dialogue completion object is incomplete")
    assistant_message = _required("assistant_message", str(data.get("assistant_message", "")))
    should_complete = data.get("should_complete") is True
    explicit = data.get("explicit_confirmation_observed") is True
    if should_complete and not explicit:
        raise ValueError("model attempted completion without explicit confirmation")
    if should_complete and (
        not str(completion.get("appointment_time") or "").strip()
        or not str(completion.get("confirmation_number") or "").strip()
    ):
        raise ValueError("model attempted completion without both critical fields")
    if should_complete and (
        str(completion.get("result", "")).strip() != "Local confirmation recorded."
        or str(completion.get("notes", "")).strip()
        != "No external organization was contacted or booking made."
    ):
        raise ValueError(
            "model attempted completion without the required no-external-action boundary"
        )
    return {
        "assistant_message": assistant_message,
        "explicit_confirmation_observed": explicit,
        "should_complete": should_complete,
        "completion": {key: str(completion.get(key, "")).strip() for key in sorted(required)},
        "dialogue_model": f"{receipt['provider']}:{receipt['provider_model']}",
        "llm_receipt": receipt,
    }


__all__ = [
    "CallPlan",
    "conversation_turn",
    "direct_plan",
    "react_plan",
]
