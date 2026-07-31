"""Planning and conversation contracts for Experiment 9-2.

The experiment has two arms which share the same browser WebRTC transport:

* ``direct``: the caller supplies every call parameter.
* ``react``: a text model turns one natural-language task into a call plan and
  explicitly records its observation/action trace.

No PSTN destination is involved.  The person who opens the local page is the
consenting call participant.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any

from openai import OpenAI, OpenAIError

DEFAULT_PLANNER_MODEL = "gpt-4o-mini"


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _required(label: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} is required")
    return cleaned


def direct_plan(
    *,
    callee_name: str,
    goal: str,
    context: str,
    instructions: str,
) -> CallPlan:
    """Build the fixed-parameter control used by the direct arm."""
    callee = _required("callee_name", callee_name)
    return CallPlan(
        mode="direct",
        callee_name=callee,
        goal=_required("goal", goal),
        context=_required("context", context),
        instructions=_required("instructions", instructions),
        opening_line=f"Hello {callee}. I am an AI assistant calling through this browser to help with the requested task.",
        trace=[
            {"stage": "observation", "summary": "Caller supplied all call parameters."},
            {"stage": "action", "summary": "Open a WebRTC voice session with the fixed parameters."},
        ],
    )


def _planner_client() -> tuple[OpenAI, str, str]:
    model = os.getenv("PHONE_PLANNER_MODEL", os.getenv("OPENAI_MODEL", DEFAULT_PLANNER_MODEL))
    provider = os.getenv("PHONE_MODEL_PROVIDER", "auto").lower()
    if os.getenv("OPENROUTER_API_KEY") and provider in {"auto", "openrouter"}:
        routed = model if "/" in model else f"openai/{model}"
        return (
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
                timeout=120,
                max_retries=2,
            ),
            routed,
            "openrouter",
        )
    if os.getenv("OPENAI_API_KEY") and provider in {"auto", "openai"}:
        return (
            OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None, timeout=120, max_retries=2),
            model,
            "openai",
        )
    raise RuntimeError("ReAct planning requires OPENAI_API_KEY or OPENROUTER_API_KEY")


def _json_object(text: str) -> dict[str, Any]:
    value = json.loads(text)
    if not isinstance(value, dict):
        raise TypeError("planner response must be a JSON object")
    return value


def local_react_plan(task: str) -> CallPlan:
    """Dependency-free ReAct planner used when no hosted text model is usable."""
    import re

    lower = task.lower()
    missing: list[str] = []
    if not re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", lower):
        missing.append("exact appointment time")
    if not re.search(r"\b(?:code|confirmation)\s*(?:is|:)?\s*[a-z-]*\d[a-z0-9-]*\b", lower):
        missing.append("confirmation code")
    reason = (
        "The task omits " + " and ".join(missing) + "; collect and confirm them during the call."
        if missing
        else "The task contains the critical fields; repeat them and request confirmation during the call."
    )
    return CallPlan(
        mode="react",
        callee_name="the user",
        goal=task,
        context="The user supplied only this natural-language task; do not infer unstated facts.",
        instructions=(
            "Ask for each missing field, repeat all task-critical details, request explicit confirmation, "
            "then call complete_task with only the confirmed values."
        ),
        opening_line="Hello. I am an AI assistant calling through this browser to complete your requested confirmation.",
        missing_information=missing,
        trace=[
            {"stage": "observation", "summary": task},
            {"stage": "reason", "summary": reason},
            {"stage": "action", "summary": "Open a WebRTC call and collect missing facts from the user."},
        ],
        planner_model="local-react-planner-v1",
    )


def react_plan(task: str, *, client: OpenAI | None = None, model: str | None = None) -> CallPlan:
    """Plan a browser call from a natural-language task.

    The trace contains short decision summaries, not hidden chain-of-thought.
    Missing facts are intentionally converted into questions for the live call
    rather than guessed by the planner.
    """
    task = _required("task", task)
    try:
        if client is None:
            client, resolved_model, provider = _planner_client()
        else:
            resolved_model = model or DEFAULT_PLANNER_MODEL
            provider = "injected"
        active_model = model or resolved_model
        response = client.chat.completions.create(
            model=active_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You plan a voice call from an AI assistant to the user who will open a local browser page. "
                        "Do not invent missing facts. Return JSON with callee_name, goal, context, instructions, "
                        "opening_line, missing_information (array of short strings), and decision_summary. "
                        "The instructions must tell the voice agent to ask for missing task-critical facts, confirm "
                        "them aloud, then call complete_task. Never claim an external booking, payment, or account "
                        "change occurred; this local experiment may only record what the user confirmed."
                    ),
                },
                {"role": "user", "content": task},
            ],
        )
    except (OpenAIError, RuntimeError):
        return local_react_plan(task)
    content = response.choices[0].message.content or "{}"
    data = _json_object(content)
    missing = data.get("missing_information", [])
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        raise ValueError("planner missing_information must be an array of strings")
    decision = _required("decision_summary", str(data.get("decision_summary", "")))
    return CallPlan(
        mode="react",
        callee_name=_required("callee_name", str(data.get("callee_name", ""))),
        goal=_required("goal", str(data.get("goal", ""))),
        context=str(data.get("context") or "No additional context was supplied.").strip(),
        instructions=_required("instructions", str(data.get("instructions", ""))),
        opening_line=_required("opening_line", str(data.get("opening_line", ""))),
        missing_information=[item.strip() for item in missing if item.strip()],
        trace=[
            {"stage": "observation", "summary": task},
            {"stage": "reason", "summary": decision},
            {"stage": "action", "summary": "Open a WebRTC call and collect missing facts from the user."},
        ],
        planner_model=f"{provider}:{active_model}",
    )


def local_conversation_turn(plan: CallPlan, user_text: str) -> dict[str, Any]:
    """Offline-safe completion for an explicit confirmation turn."""
    import re

    time_match = re.search(
        r"\b((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)(?:\s+at)?\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        user_text,
        re.IGNORECASE,
    )
    confirmation_match = re.search(
        r"(?:confirmation(?:\s+code)?|code)\s*(?:is|:)?\s*([A-Za-z0-9][A-Za-z0-9-]{2,})",
        user_text,
        re.IGNORECASE,
    )
    explicitly_confirmed = "confirm" in user_text.lower()
    should_complete = explicitly_confirmed and bool(time_match or confirmation_match)
    appointment_time = time_match.group(1) if time_match else ""
    confirmation = confirmation_match.group(1) if confirmation_match else ""
    if should_complete:
        details = ", ".join(value for value in (appointment_time, confirmation) if value)
        speech = f"Thank you. I saved the details you confirmed: {details}."
    else:
        speech = "Please state the exact time and confirmation code, then explicitly confirm both."
    return {
        "assistant_message": speech,
        "should_complete": should_complete,
        "completion": {
            "result": "The user confirmed a local experiment record.",
            "appointment_time": appointment_time,
            "confirmation_number": confirmation,
            "notes": "No external organization was contacted.",
        },
        "dialogue_model": "local-confirmation-parser",
    }


def conversation_turn(plan: CallPlan, transcript: list[dict[str, str]], user_text: str) -> dict[str, Any]:
    """Generate the next call turn, falling back to the auditable local parser."""
    try:
        client, active_model, provider = _planner_client()
        response = client.chat.completions.create(
            model=os.getenv("PHONE_DIALOGUE_MODEL", active_model),
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You run a short local browser call. Return JSON with assistant_message, should_complete, "
                        "and completion containing result, appointment_time, confirmation_number, notes. Complete "
                        "only after the user explicitly confirms task-critical facts. Never claim an external action. "
                        f"Goal: {plan.goal}. Context: {plan.context}. Instructions: {plan.instructions}"
                    ),
                },
                {"role": "user", "content": json.dumps(transcript + [{"speaker": "user", "text": user_text}])},
            ],
        )
        result = _json_object(response.choices[0].message.content or "{}")
        completion = result.get("completion") or {}
        required = {"result", "appointment_time", "confirmation_number", "notes"}
        if not isinstance(completion, dict) or not required.issubset(completion):
            raise ValueError("dialogue completion object is incomplete")
        result["assistant_message"] = _required("assistant_message", str(result.get("assistant_message", "")))
        result["should_complete"] = bool(result.get("should_complete"))
        result["dialogue_model"] = f"{provider}:{os.getenv('PHONE_DIALOGUE_MODEL', active_model)}"
        return result
    except (AttributeError, KeyError, OpenAIError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
        return local_conversation_turn(plan, user_text)
