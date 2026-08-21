"""Moonshot Kimi（OpenAI 兼容）聊天 / 视觉调用封装，带留证。

密钥只从环境变量读，绝不写入 receipt 或任何落盘文件。
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time

import requests

from receipts import ReceiptBook, utc_now

MOONSHOT_URL = "https://api.moonshot.cn/v1/chat/completions"
CODEGEN_MODEL = "kimi-k2.5"
VISION_MODEL = "moonshot-v1-8k-vision-preview"


def _sanitize(obj, limit=2000):
    """receipt 中的请求体脱敏：超长字符串（如 base64 图片）替换为哈希摘要。"""
    if isinstance(obj, str):
        if len(obj) > limit:
            return {"_truncated_sha256": hashlib.sha256(obj.encode()).hexdigest(),
                    "_len": len(obj), "_head": obj[:200]}
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v, limit) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v, limit) for v in obj]
    return obj


def kimi_chat(messages, book: ReceiptBook, name: str, model: str = CODEGEN_MODEL,
              max_tokens: int = 8192, temperature: float | None = None) -> tuple[str, dict]:
    started = utc_now()
    t0 = time.time()
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:
        payload["temperature"] = temperature
    try:
        r = requests.post(
            MOONSHOT_URL,
            headers={"Authorization": f"Bearer {os.environ['KIMI_API_KEY']}"},
            json=payload, timeout=600,
        )
        data = r.json()
    except Exception as e:  # 网络/解析失败同样留证
        ended = utc_now()
        book.record(name, provider="moonshot", endpoint=MOONSHOT_URL, model=model,
                    request=_sanitize(payload), response={"error": repr(e)},
                    started_utc=started, ended_utc=ended,
                    latency_ms=int((time.time() - t0) * 1000), status="error")
        raise
    ended = utc_now()
    latency = int((time.time() - t0) * 1000)
    content = None
    if r.ok:
        content = data["choices"][0]["message"]["content"]
    book.record(name, provider="moonshot", endpoint=MOONSHOT_URL, model=model,
                request=_sanitize(payload),
                response={"status_code": r.status_code, "content": content,
                          "usage": data.get("usage"), "error": data.get("error")},
                started_utc=started, ended_utc=ended, latency_ms=latency,
                status="ok" if r.ok else "error")
    if not r.ok:
        raise RuntimeError(f"Kimi 调用失败: {r.status_code} {data.get('error')}")
    return content, data.get("usage") or {}


def image_message_part(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {"type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"}}


def extract_code_block(text: str, lang: str = "python") -> str:
    """从 LLM 回复中提取 ```python 代码块。"""
    marker = f"```{lang}"
    start = text.find(marker)
    if start == -1:
        start = text.find("```")
        if start == -1:
            return text.strip()
        start += 3
    else:
        start += len(marker)
    end = text.find("```", start)
    return text[start:end if end != -1 else None].strip()
