"""Real API Coding Agent used by the Experiment 9-6 campaign."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Dict

from openai import OpenAI

from evolution import candidate_from_source


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _client(provider: str) -> tuple[OpenAI, dict[str, Any]]:
    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is required")
        base = "https://openrouter.ai/api/v1"
        return OpenAI(api_key=key, base_url=base), {
            "provider": provider, "endpoint": base + "/chat/completions", "credential_env": "OPENROUTER_API_KEY"
        }
    if provider == "ark":
        key = os.getenv("ARK_API_KEY")
        if not key:
            raise RuntimeError("ARK_API_KEY is required")
        base = "https://ark.cn-beijing.volces.com/api/v3"
        return OpenAI(api_key=key, base_url=base), {
            "provider": provider, "endpoint": base + "/chat/completions", "credential_env": "ARK_API_KEY"
        }
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required")
    return OpenAI(api_key=key), {
        "provider": provider, "endpoint": "https://api.openai.com/v1/chat/completions", "credential_env": "OPENAI_API_KEY"
    }


def generate_with_openai(
    stable_source: str,
    diagnosis: Dict[str, Any],
    model: str | None = None,
    *,
    provider: str = "openrouter",
    seed: int = 8501,
    rejected_history: list[dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    client, backend = _client(provider)
    selected_model = model or (
        os.getenv("ARK_MODEL", "doubao-seed-1-6-250615") if provider == "ark"
        else ("openai/gpt-4o-mini" if provider == "openrouter" else "gpt-4o-mini")
    )
    prompt = f"""You are the Coding Agent in a controlled self-modification pipeline.

Modify only the supplied retry-policy module. Preserve both public function
signatures and retry behavior for temporary failures. Permanent failures
(retryable=false or a listed permanent code) must not be retried and must open
the circuit on the first occurrence. Update VERSION to a candidate version.
Do not import modules, access files, or alter validation/release logic.

Before the source, predict the intended impact. Return JSON only:
{{"impact_prediction": {{"non_retryable_calls": {{"before": "up to 4", "after": 1}},
"temporary_timeout_recovery_rate": {{"before": 1.0, "after": 1.0}}}},
"source": "the complete Python module"}}

Failure diagnosis:
{json.dumps(diagnosis, ensure_ascii=False, indent=2)}

Previously rejected candidates (do not repeat their failure):
{json.dumps(rejected_history or [], ensure_ascii=False, indent=2)}

Stable module:
{stable_source}
"""
    request = {
        "model": selected_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": seed,
        "max_tokens": 1400,
        "response_format": {"type": "json_object"},
    }
    started = time.perf_counter()
    response = client.chat.completions.create(**request)
    elapsed = time.perf_counter() - started
    raw = response.model_dump(mode="json", exclude_none=True)
    payload = _extract_json(response.choices[0].message.content or "")
    source = str(payload.get("source", ""))
    if not source.endswith("\n"):
        source += "\n"
    usage = raw.get("usage") or {}
    cost = usage.get("cost")
    receipt = {
        "backend": {**backend, "model": selected_model, "credential_value_recorded": False},
        "request": request,
        "response": raw,
        "request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
        "response_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
        "elapsed_seconds": round(elapsed, 6),
        "usage": {
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "provider_reported_cost_usd": float(cost) if cost is not None else None,
            "cost_qualification": (
                "provider-native usage.cost" if cost is not None
                else "provider did not expose monetary cost; no price was guessed"
            ),
        },
    }
    return candidate_from_source(
        stable_source,
        source,
        impact_prediction=payload.get("impact_prediction") or {},
        generator_metadata={
            "generator": "real_llm_coding_agent", "model": selected_model,
            "provider": provider, "seed": seed, "api_calls": 1, "receipt": receipt,
        },
    )
