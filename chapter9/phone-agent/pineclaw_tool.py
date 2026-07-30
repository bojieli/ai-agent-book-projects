"""Real Pine Voice SDK adapter used by Experiment 9-2.

The default path in this module reaches the real telephone network through the
official ``pine-voice`` package.  Offline behaviour lives in ``test_double.py``
and must be selected explicitly by the caller.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, is_dataclass
from typing import Any

from openai import OpenAI

_DEFAULT_MODEL = "gpt-4o-mini"
_client: OpenAI | None = None
_active_model: str | None = None

AUTHORIZED_NUMBER_ENV = "PINE_AUTHORIZED_TEST_NUMBER"
CONSENT_ENV = "PINE_TEST_CALL_CONSENT"
CONSENT_VALUE = "I_HAVE_EXPLICIT_CONSENT"


def require_authorized_destination(phone_number: str) -> None:
    """Fail closed unless the exact destination was allowlisted with consent.

    A ReAct model or public-number search must never be able to turn a plausible
    phone number into authority to call it. The human operator must separately
    set the exact E.164 destination and the explicit consent acknowledgement.
    """
    authorized = os.getenv(AUTHORIZED_NUMBER_ENV, "").strip()
    consent = os.getenv(CONSENT_ENV, "").strip()
    if not authorized or consent != CONSENT_VALUE:
        raise PermissionError(
            f"Real calls are disabled. Set {AUTHORIZED_NUMBER_ENV} to a consenting E.164 "
            f"destination and {CONSENT_ENV}={CONSENT_VALUE}."
        )
    if phone_number != authorized:
        raise PermissionError("The requested destination is not the explicitly authorized test number")


def _map_openrouter_model(model: str) -> str:
    if "/" in model:
        return model
    return "openai/" + model if model.startswith("gpt-") else model


def _resolve() -> tuple[OpenAI, str]:
    """Resolve the text model used by the outer ReAct agent and extractor."""
    global _client, _active_model
    if _client is not None and _active_model is not None:
        return _client, _active_model
    model = os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)
    if os.getenv("OPENAI_API_KEY"):
        _client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            timeout=120.0,
            max_retries=3,
        )
        _active_model = model
    elif os.getenv("OPENROUTER_API_KEY"):
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            timeout=120.0,
            max_retries=3,
        )
        _active_model = _map_openrouter_model(model)
    else:
        raise RuntimeError("The ReAct agent needs OPENAI_API_KEY or OPENROUTER_API_KEY")
    return _client, _active_model


def _get_client() -> OpenAI:
    return _resolve()[0]


def default_model() -> str:
    return _resolve()[1]


def _plain(value: Any) -> Any:
    """Convert SDK dataclasses/Pydantic objects to JSON-compatible values."""
    if is_dataclass(value):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if hasattr(value, "model_dump"):
        return _plain(value.model_dump())
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _safe_json(text: str) -> dict[str, Any]:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip()).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        value = json.loads(match.group(0)) if match else {}
    return value if isinstance(value, dict) else {}


def extract_call_facts(
    *,
    objective: str,
    transcript: list[dict[str, Any]],
    summary: str = "",
    model: str | None = None,
) -> dict[str, Any]:
    """Extract the acceptance-criteria fields from a completed real call."""
    prompt = (
        "Extract a completed phone call into JSON. Do not invent anything. Return keys "
        "goal_achieved (boolean), key_fields (object containing concrete appointment time, "
        "confirmation number, price, names or other task facts), follow_up_needed (boolean), "
        "follow_up_reason (string), and summary (string).\n"
        f"Objective: {objective}\nProvider summary: {summary}\n"
        f"Transcript: {json.dumps(transcript, ensure_ascii=False)}"
    )
    client, active_model = _resolve()
    response = client.chat.completions.create(
        model=model or active_model,
        messages=[
            {"role": "system", "content": "You are a strict call-record extractor. Output JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    facts = _safe_json(content)
    if not isinstance(facts.get("key_fields"), dict):
        facts["key_fields"] = {}
    return facts


def make_phone_call(
    phone_number: str,
    goal: str,
    context: str = "",
    *,
    callee_name: str = "Requested business",
    instructions: str = "Confirm every task-critical detail before ending the call.",
    caller: str = "communicator",
    voice: str = "female",
    max_duration_minutes: int = 10,
    enable_summary: bool = True,
    extract_facts: bool = True,
    model: str | None = None,
) -> dict[str, Any]:
    """Place and await a real Pine AI phone call via the official SDK.

    ``phone_number`` must be E.164 and in a country supported by Pine Voice.  A
    completed SDK result is normalized into the record consumed by the ReAct
    loop; the transcript and provider call id always remain intact.
    """
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone_number):
        raise ValueError("phone_number must use E.164 form, for example +14155551234")
    require_authorized_destination(phone_number)
    try:
        from pine_voice import PineVoice  # official ``pine-voice`` distribution
    except ImportError as exc:
        raise RuntimeError("Install the official SDK with: pip install pine-voice") from exc

    # PineVoice reads PINE_ACCESS_TOKEN/PINE_USER_ID itself.  Passing explicitly
    # also makes the credential contract clear and permits dependency injection.
    access_token = os.getenv("PINE_ACCESS_TOKEN")
    user_id = os.getenv("PINE_USER_ID")
    if not access_token or not user_id:
        raise RuntimeError("Real calls require PINE_ACCESS_TOKEN and PINE_USER_ID")

    with PineVoice(access_token=access_token, user_id=user_id) as client:
        sdk_result = client.calls.create_and_wait(
            to=phone_number,
            name=callee_name,
            context=context or "No additional background was supplied.",
            objective=goal,
            instructions=instructions,
            caller=caller,
            voice=voice,
            max_duration_minutes=max_duration_minutes,
            enable_summary=enable_summary,
        )

    raw = _plain(sdk_result)
    transcript = raw.get("transcript") or []
    summary = str(raw.get("summary") or "")
    facts = (
        extract_call_facts(
            objective=goal,
            transcript=transcript,
            summary=summary,
            model=model,
        )
        if extract_facts
        else {}
    )
    return {
        "provider": "pine-voice",
        "call_id": str(raw.get("call_id") or ""),
        "phone_number": phone_number,
        "goal": goal,
        "status": str(raw.get("status") or "unknown"),
        "duration_seconds": int(raw.get("duration_seconds") or 0),
        "credits_charged": int(raw.get("credits_charged") or 0),
        "summary": str(facts.get("summary") or summary),
        "goal_achieved": bool(facts.get("goal_achieved", raw.get("status") == "completed")),
        "key_fields": facts.get("key_fields", {}),
        "transcript": transcript,
        "follow_up_needed": bool(facts.get("follow_up_needed", False)),
        "follow_up_reason": str(facts.get("follow_up_reason") or ""),
        "raw_provider_result": raw,
    }
