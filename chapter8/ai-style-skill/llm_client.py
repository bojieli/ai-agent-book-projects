"""OpenAI 兼容 Chat Completions 客户端：统一证据回执。

约定与 chapter8/self-modifying-agent/llm_generator.py 一致：每次真实调用返回
(content, receipt)，receipt 含原始请求、原始响应、Token 用量、延迟与
请求/响应哈希，不记录凭据值。凭证从环境变量读取，支持 ark / openrouter / openai。
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, List, Tuple

_PROVIDERS = {
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
    "ark": ("ARK_API_KEY", "https://ark.cn-beijing.volces.com/api/v3"),
    "openai": ("OPENAI_API_KEY", None),
}

_DEFAULT_MODELS = {
    "openrouter": "openai/gpt-4o-mini",
    "ark": "doubao-seed-1-6-250615",
    "openai": "gpt-4o-mini",
}


def make_client(provider: str) -> Tuple[Any, Dict[str, Any]]:
    # openai 包只在真实路径才需要，惰性导入保证离线路径零依赖。
    from openai import OpenAI

    if provider not in _PROVIDERS:
        raise ValueError(f"不支持的 provider：{provider}（可选：{sorted(_PROVIDERS)}）")
    env_name, base_url = _PROVIDERS[provider]
    key = os.getenv(env_name)
    if not key:
        raise RuntimeError(f"真实 LLM 路径需要设置环境变量 {env_name}")
    client = OpenAI(api_key=key, base_url=base_url) if base_url else OpenAI(api_key=key)
    backend = {
        "provider": provider,
        "endpoint": (base_url or "https://api.openai.com/v1") + "/chat/completions",
        "credential_env": env_name,
    }
    return client, backend


def default_model(provider: str) -> str:
    if provider == "ark":
        return os.getenv("ARK_MODEL", _DEFAULT_MODELS["ark"])
    return _DEFAULT_MODELS[provider]


def chat(
    messages: List[Dict[str, str]],
    *,
    provider: str,
    model: str | None = None,
    seed: int = 8901,
    max_tokens: int = 5000,
) -> Tuple[str, Dict[str, Any]]:
    """发起一次真实调用，返回 (文本内容, 证据回执)。"""
    client, backend = make_client(provider)
    selected = model or default_model(provider)
    request = {
        "model": selected,
        "messages": messages,
        "temperature": 0,
        "seed": seed,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    started = time.perf_counter()
    response = client.chat.completions.create(**request)
    elapsed = time.perf_counter() - started
    raw = response.model_dump(mode="json", exclude_none=True)
    usage = raw.get("usage") or {}
    cost = usage.get("cost")
    receipt = {
        "backend": {**backend, "model": selected, "credential_value_recorded": False},
        "request": request,
        "response": raw,
        "request_sha256": hashlib.sha256(
            json.dumps(request, sort_keys=True).encode()
        ).hexdigest(),
        "response_sha256": hashlib.sha256(
            json.dumps(raw, sort_keys=True).encode()
        ).hexdigest(),
        "elapsed_seconds": round(elapsed, 6),
        "usage": {
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
            "provider_reported_cost_usd": float(cost) if cost is not None else None,
            "cost_qualification": (
                "provider-native usage.cost"
                if cost is not None
                else "provider did not expose monetary cost; no price was guessed"
            ),
        },
    }
    return response.choices[0].message.content or "", receipt
