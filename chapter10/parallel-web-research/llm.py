"""Evidence-grounded profile extraction with real configured LLM APIs."""

from __future__ import annotations

import json
import os
import time
from typing import Callable, Dict, Optional


ReceiptSink = Optional[Callable[[Dict[str, object]], None]]


def _backends():
    from openai import AsyncOpenAI

    out = []
    if os.getenv("ARK_API_KEY"):
        out.append((AsyncOpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3"), os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"), "ark"))
    if os.getenv("MOONSHOT_API_KEY"):
        out.append((AsyncOpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url="https://api.moonshot.cn/v1"), os.getenv("MOONSHOT_MODEL", "kimi-k3"), "moonshot"))
    if os.getenv("OPENAI_API_KEY"):
        out.append((AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.getenv("OPENAI_BASE_URL") or None), os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "openai"))
    if os.getenv("OPENROUTER_API_KEY"):
        raw = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        out.append((AsyncOpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1"), raw if "/" in raw else f"openai/{raw}", "openrouter"))
    if not out:
        raise RuntimeError("真实网页内容抽取需要 ARK/MOONSHOT/OPENAI/OPENROUTER 任一 API Key")
    return out


async def extract_profile(
    target: str,
    college: str,
    url: str,
    text: str,
    receipt_sink: ReceiptSink = None,
    call_context: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    """Extract only facts visible in the browser observation.

    The deterministic name-presence gate prevents a model from supplying a profile
    from parametric memory when the page did not actually contain the target.
    """
    if target.casefold() not in text.casefold():
        return {"found": False, "reason": "target name absent from rendered page"}
    clipped = text[:45_000]
    prompt = {
        "target": target,
        "site_college": college,
        "url": url,
        "rendered_page_text": clipped,
        "instruction": (
            "Use only rendered_page_text. Decide whether it contains this exact person's faculty profile. "
            "Return JSON keys found, name, college, position, research, evidence. If the name is only a link/listing, "
            "found may be true but leave unsupported fields empty. evidence must be a short verbatim excerpt."
        ),
    }
    last = None
    for client, model, provider in _backends():
        started = time.monotonic()
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}],
                response_format={"type": "json_object"},
            )
            if "kimi-k3" in model:
                kwargs.update(temperature=1, max_tokens=2048)
            response = await client.chat.completions.create(**kwargs)
            raw_response = response.model_dump(mode="json")
            if receipt_sink:
                receipt_sink({
                    "kind": "llm_chat_completion",
                    "context": dict(call_context or {}),
                    "provider": provider,
                    "request": kwargs,
                    "response": raw_response,
                    "response_id": response.id,
                    "response_model": response.model,
                    "usage": response.usage.model_dump(mode="json") if response.usage else None,
                    "duration_seconds": round(time.monotonic() - started, 3),
                })
            content = response.choices[0].message.content or ""
            if not content.strip():
                raise ValueError("empty model response")
            result = json.loads(content)
            result["provider"] = provider
            result["url"] = url
            return result
        except Exception as exc:
            last = exc
            if receipt_sink:
                receipt_sink({
                    "kind": "llm_chat_completion_error",
                    "context": dict(call_context or {}),
                    "provider": provider,
                    "model": model,
                    "error_type": type(exc).__name__,
                    "duration_seconds": round(time.monotonic() - started, 3),
                })
            print(f"  [extract] {provider} failed: {type(exc).__name__}; trying next endpoint")
    raise RuntimeError("all configured LLM extraction endpoints failed") from last
