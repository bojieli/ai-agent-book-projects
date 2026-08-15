#!/usr/bin/env python3
"""Exploratory backend probes for Experiment 6-11 readiness (2026-07-31).

Probes candidate substitutions with minimal real calls (1-line embed, 1-token
chat, tiny rerank) and records sanitized, credential-free receipts. Secrets are
read from the environment only; every recorded error string is scrubbed of any
environment-held credential before being written.
"""

import json
import os
import time
from pathlib import Path

import requests
from openai import OpenAI

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "candidate_backend_probes_20260731.json"

KEY_ENVS = [
    "KIMI_API_KEY", "MOONSHOT_API_KEY", "ARK_API_KEY", "DASHSCOPE_API_KEY",
    "SILICONFLOW_API_KEY", "MISTRAL_API_KEY", "GEMINI_API_KEY",
    "OPENROUTER_API_KEY", "OPENAI_API_KEY",
]


def scrub(text: str) -> str:
    for env in KEY_ENVS:
        secret = os.getenv(env, "")
        if secret:
            text = text.replace(secret, "<redacted>")
    return text[:1500]


def embed_probe(name, base_url, key_env, model, **extra):
    row = {"component": "embedding", "name": name, "model": model,
           "base_url": base_url, "key_env": key_env,
           "key_present": bool(os.getenv(key_env, ""))}
    started = time.perf_counter()
    try:
        client = OpenAI(api_key=os.environ[key_env], base_url=base_url, timeout=60)
        kwargs = {"model": model, "input": ["user memory retrieval backend probe"]}
        kwargs.update(extra)
        resp = client.embeddings.create(**kwargs)
        row.update(status="ok", dimensions=len(resp.data[0].embedding),
                   latency_ms=round((time.perf_counter() - started) * 1000, 1),
                   usage=resp.usage.model_dump() if resp.usage else None)
    except Exception as exc:  # noqa: BLE001 - receipts must capture any failure
        row.update(status="error", latency_ms=round((time.perf_counter() - started) * 1000, 1),
                   error=scrub(f"{type(exc).__name__}: {exc}"))
    return row


def chat_probe(name, base_url, key_env, model, max_tokens=1, **extra):
    row = {"component": "chat", "name": name, "model": model,
           "base_url": base_url, "key_env": key_env,
           "key_present": bool(os.getenv(key_env, ""))}
    started = time.perf_counter()
    try:
        client = OpenAI(api_key=os.environ[key_env], base_url=base_url, timeout=60)
        kwargs = {"model": model,
                  "messages": [{"role": "user", "content": "Reply exactly OK"}],
                  "max_tokens": max_tokens}
        kwargs.update(extra)
        resp = client.chat.completions.create(**kwargs)
        row.update(status="ok", content=(resp.choices[0].message.content or "")[:40],
                   latency_ms=round((time.perf_counter() - started) * 1000, 1),
                   usage=resp.usage.model_dump() if resp.usage else None)
    except Exception as exc:  # noqa: BLE001
        row.update(status="error", latency_ms=round((time.perf_counter() - started) * 1000, 1),
                   error=scrub(f"{type(exc).__name__}: {exc}"))
    return row


def http_probe(name, method, url, key_env, payload=None):
    row = {"component": "http", "name": name, "url": url, "key_env": key_env,
           "key_present": bool(os.getenv(key_env, ""))}
    started = time.perf_counter()
    try:
        headers = {"Authorization": f"Bearer {os.environ[key_env]}",
                   "Content-Type": "application/json"}
        resp = requests.request(method, url, headers=headers, json=payload, timeout=60)
        row.update(status="ok" if resp.ok else "error", http_status=resp.status_code,
                   latency_ms=round((time.perf_counter() - started) * 1000, 1),
                   body=scrub(resp.text))
    except Exception as exc:  # noqa: BLE001
        row.update(status="error", latency_ms=round((time.perf_counter() - started) * 1000, 1),
                   error=scrub(f"{type(exc).__name__}: {exc}"))
    return row


def main():
    results = []

    # --- SiliconFlow: reproduce and diagnose the 401 -------------------------
    results.append(embed_probe(
        "siliconflow-bge-m3", "https://api.siliconflow.cn/v1",
        "SILICONFLOW_API_KEY", "BAAI/bge-m3"))
    results.append(http_probe(
        "siliconflow-rerank-v2-m3", "POST", "https://api.siliconflow.cn/v1/rerank",
        "SILICONFLOW_API_KEY",
        {"model": "BAAI/bge-reranker-v2-m3", "query": "checking account",
         "documents": ["checking account number 123", "weather"], "top_n": 2,
         "return_documents": False}))
    # Account-level diagnosis: is the key itself dead or just the model/balance?
    results.append(http_probe(
        "siliconflow-user-info", "GET", "https://api.siliconflow.cn/v1/user/info",
        "SILICONFLOW_API_KEY"))

    # --- OpenAI direct: confirm quota state ----------------------------------
    results.append(embed_probe(
        "openai-text-embedding-3-small", "https://api.openai.com/v1",
        "OPENAI_API_KEY", "text-embedding-3-small"))

    # --- OpenRouter: OpenAI embedding pass-through + BGE-M3 availability -----
    results.append(embed_probe(
        "openrouter-openai-text-embedding-3-small", "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY", "openai/text-embedding-3-small"))
    results.append(embed_probe(
        "openrouter-baai-bge-m3", "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY", "BAAI/bge-m3"))

    # --- ARK/Doubao: try public model-name embedding access ------------------
    for model in ("doubao-embedding-large-text-250515",
                  "doubao-embedding-large-text-240915",
                  "doubao-embedding-text-240715"):
        results.append(embed_probe(
            f"ark-{model}", "https://ark.cn-beijing.volces.com/api/v3",
            "ARK_API_KEY", model))

    # --- DashScope (Alibaba): documented substitutes -------------------------
    results.append(embed_probe(
        "dashscope-text-embedding-v4", "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "DASHSCOPE_API_KEY", "text-embedding-v4"))
    results.append(http_probe(
        "dashscope-gte-rerank-v2", "POST",
        "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
        "DASHSCOPE_API_KEY",
        {"model": "gte-rerank-v2",
         "input": {"query": "checking account",
                   "documents": ["checking account number 123", "weather"]},
         "parameters": {"top_n": 2, "return_documents": False}}))

    # --- Known-good controls --------------------------------------------------
    results.append(embed_probe(
        "mistral-embed", "https://api.mistral.ai/v1",
        "MISTRAL_API_KEY", "mistral-embed"))
    results.append(chat_probe(
        "kimi-k2.5", "https://api.moonshot.cn/v1", "KIMI_API_KEY", "kimi-k2.5",
        max_tokens=16, extra_body={"thinking": {"type": "disabled"}}, temperature=0.6))
    results.append(chat_probe(
        "doubao-seed-1-6-250615", "https://ark.cn-beijing.volces.com/api/v3",
        "ARK_API_KEY", "doubao-seed-1-6-250615", max_tokens=16))

    # --- Gemini embedding (last-resort fallback) ------------------------------
    results.append(embed_probe(
        "gemini-embedding-001", "https://generativelanguage.googleapis.com/v1beta/openai/",
        "GEMINI_API_KEY", "gemini-embedding-001"))

    payload = {
        "schema_version": "1.0",
        "purpose": "Experiment 6-11 readiness substitution probes",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "credentials_redacted": True,
        "probes": results,
        "summary": {
            "ok": sum(r["status"] == "ok" for r in results),
            "error": sum(r["status"] == "error" for r in results),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in results:
        print(f"{row['status']:5s} {row['name']}")
    print(json.dumps(payload["summary"]))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
