"""实验 8-8 的真实 Coding Agent 路径（OpenAI 兼容 API）。

读取失败诊断与稳定版调度器源码，让模型产出候选 confirmation_gate.py。
输出只能写入 validation/<run>/candidates/ 隔离目录；静态检查、回放验证、
发布决定全部由模型外部代码做出。原始请求/响应与用量保存在证据回执中。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any, Dict

from openai import OpenAI

from evolution import candidate_from_gate


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


PROMPT_TEMPLATE = """You are the Coding Agent in a controlled Harness evolution pipeline.

Failure signals (user corrections, thumbs-down, post-hoc audit) show that the
stable tool dispatcher executes irreversible high-risk calls without user
confirmation. Write a NEW Python module named confirmation_gate.py adding a
confirmation gate in front of dispatch. Do NOT modify the stable module; the
harness wires your module in. Do not alter validation/release logic.

The module MUST define exactly these callables:
- requires_confirmation(tool_name, args=None) -> bool
- issue_confirmation(tool_name, args=None) -> str
  (a one-time token bound to this exact tool name and full args)
- dispatch(tool_name, args=None, *, execute, confirm_token=None) -> dict

dispatch behavior contract (execute is injected by the harness; never call
real tools yourself):
- low-risk call: return {{"status": "executed", "confirmed": false, "result": execute(tool_name, args)}}
- high-risk call without token: return {{"status": "pending_confirmation", "reason": ...}} and NEVER call execute
- high-risk call with a valid unused token for THIS tool+args: consume the
  token, then return {{"status": "executed", "confirmed": true, "result": execute(tool_name, args)}}
- invalid, already-used, or mismatched token: return {{"status": "rejected", "reason": ...}} and NEVER call execute

High-risk rules (tool name + argument patterns):
- delete_file (any path)
- git_push with force=true
- sql_query containing DROP TABLE / TRUNCATE, or DELETE ... without WHERE
- run_shell with destructive patterns (rm -rf, mkfs, shutdown, dd if=)
Everything else is low-risk and must NOT be suspended.

Only import from: hashlib, hmac, json, re, secrets, string. No file, network,
or subprocess access. Set VERSION = "1.1.0-candidate".

Before the source, predict the intended impact. Return JSON only:
{{"impact_prediction": {{"unconfirmed_high_risk_executions": {{"after": 0}},
"low_risk_calls_suspended": {{"after": 0}}}},
"source": "the complete Python module"}}

Failure diagnosis:
{diagnosis}

Previously rejected candidates (do not repeat their failure):
{rejected_history}

Stable module (read-only context; do not modify):
{stable_source}
"""


def generate_with_openai(
    stable_source: str,
    diagnosis: Dict[str, Any],
    model: str | None = None,
    *,
    provider: str = "ark",
    seed: int = 8801,
    rejected_history: list[dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    client, backend = _client(provider)
    selected_model = model or (
        os.getenv("ARK_MODEL", "doubao-seed-1-6-250615") if provider == "ark"
        else ("openai/gpt-4o-mini" if provider == "openrouter" else "gpt-4o-mini")
    )
    prompt = PROMPT_TEMPLATE.format(
        diagnosis=json.dumps(diagnosis, ensure_ascii=False, indent=2),
        rejected_history=json.dumps(rejected_history or [], ensure_ascii=False, indent=2),
        stable_source=stable_source,
    )
    request = {
        "model": selected_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "seed": seed,
        "max_tokens": 2400,
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
    return candidate_from_gate(
        source,
        impact_prediction=payload.get("impact_prediction") or {},
        generator_metadata={
            "generator": "real_llm_coding_agent", "model": selected_model,
            "provider": provider, "seed": seed, "api_calls": 1, "receipt": receipt,
        },
    )
