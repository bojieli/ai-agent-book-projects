"""三家厂商的最小客户端。

刻意不用各家的 SDK：这个实验关心的就是线上的 JSON 长什么样，用 SDK 反而会把
差异藏起来。请求和响应原样保留，跨厂商报错时那份原始响应体就是证据。
"""

from __future__ import annotations

import json
import os
import time

import requests

from neutral_trace import PLAINTEXT, SIGNED, SUMMARY, Reasoning, Step, ToolCall

KIMI = "kimi"
ANTHROPIC = "anthropic"
GEMINI = "gemini"
PROVIDERS = (KIMI, ANTHROPIC, GEMINI)

DEFAULT_MODELS = {
    KIMI: os.getenv("KIMI_MODEL", "kimi-k3"),
    ANTHROPIC: os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
    GEMINI: os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
}


class ProviderError(RuntimeError):
    """厂商返回了非 200。``body`` 是原始响应体，直接作为证据留存。"""

    def __init__(self, provider: str, status: int, body: str):
        super().__init__(f"{provider} HTTP {status}: {body[:300]}")
        self.provider, self.status, self.body = provider, status, body


class InjectedOutage(RuntimeError):
    """人为注入的厂商不可用。真实厂商不会配合我们宕机，所以这一段是模拟的。"""


def _post(url: str, headers: dict, body: dict, timeout: int = 180) -> requests.Response:
    """限流和连接抖动自己重试；其余状态码原样返回，交给调用方判断。"""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
        except requests.RequestException as e:  # 连接被对端掐断、读超时等
            last_error = e
            time.sleep(6 * (attempt + 1))
            continue
        if r.status_code != 429 or attempt == 2:
            return r
        time.sleep(6 * (attempt + 1))
    raise RuntimeError(f"三次尝试都没能连上：{last_error}")


def call(provider: str, payload: dict) -> dict:
    """发一次请求，返回原始 JSON；非 200 抛 :class:`ProviderError`。"""
    if provider == KIMI:
        url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1") + "/chat/completions"
        headers = {"Authorization": f"Bearer {_key('MOONSHOT_API_KEY', 'KIMI_API_KEY')}",
                   "Content-Type": "application/json"}
    elif provider == ANTHROPIC:
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": _key("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01",
                   "Content-Type": "application/json"}
    elif provider == GEMINI:
        model = payload.pop("_model")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"x-goog-api-key": _key("GEMINI_API_KEY", "GOOGLE_API_KEY"), "Content-Type": "application/json"}
    else:
        raise ValueError(provider)

    r = _post(url, headers, payload)
    if r.status_code != 200:
        raise ProviderError(provider, r.status_code, r.text)
    return r.json()


def _key(*names: str) -> str:
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    raise RuntimeError(f"缺少环境变量：{' 或 '.join(names)}")


def capture(provider: str, response: dict) -> Step:
    """把厂商的响应读成中立格式的一步。"""
    if provider == KIMI:
        msg = (response.get("choices") or [{}])[0].get("message") or {}
        reasoning = None
        if msg.get("reasoning_content"):
            # 明文，不附凭证：换一家模型也能原样读懂。
            reasoning = Reasoning(text=msg["reasoning_content"], credential=None,
                                  issuer=KIMI, kind=PLAINTEXT)
        calls = [ToolCall(name=c["function"]["name"],
                          arguments=json.loads(c["function"]["arguments"] or "{}"),
                          call_id=c["id"])
                 for c in msg.get("tool_calls") or []]
        return Step(role="assistant", text=msg.get("content") or None, reasoning=reasoning,
                    tool_calls=calls, issuer=KIMI, native=msg)

    if provider == ANTHROPIC:
        blocks = response.get("content") or []
        think = next((b for b in blocks if b["type"] == "thinking"), None)
        reasoning = None
        if think:
            # 正文是明文，但那份 signature 只对 Anthropic 有效。
            reasoning = Reasoning(text=think.get("thinking"), credential=think.get("signature"),
                                  issuer=ANTHROPIC, kind=SIGNED)
        calls = [ToolCall(name=b["name"], arguments=b.get("input") or {}, call_id=b["id"])
                 for b in blocks if b["type"] == "tool_use"]
        text = "".join(b.get("text", "") for b in blocks if b["type"] == "text") or None
        return Step(role="assistant", text=text, reasoning=reasoning, tool_calls=calls,
                    issuer=ANTHROPIC, native={"content": blocks})

    if provider == GEMINI:
        # 触发长度上限或安全拦截时，候选里可能根本没有 parts。
        candidates = response.get("candidates") or [{}]
        parts = (candidates[0].get("content") or {}).get("parts") or []
        thought = next((p for p in parts if p.get("thought")), None)
        fc = next((p for p in parts if "functionCall" in p), None)
        reasoning = None
        if thought:
            # thought 是摘要，凭证却挂在工具调用那一格上。
            reasoning = Reasoning(text=thought.get("text"),
                                  credential=(fc or {}).get("thoughtSignature"),
                                  issuer=GEMINI, kind=SUMMARY)
        calls = []
        if fc:
            call_obj = fc["functionCall"]
            calls = [ToolCall(name=call_obj["name"], arguments=call_obj.get("args") or {},
                              call_id=call_obj.get("id") or f"{call_obj['name']}_0")]
        text = "".join(p["text"] for p in parts if "text" in p and not p.get("thought")) or None
        return Step(role="assistant", text=text, reasoning=reasoning, tool_calls=calls,
                    issuer=GEMINI, native={"parts": parts})

    raise ValueError(provider)


def usage_of(provider: str, response: dict) -> dict:
    if provider == KIMI:
        u = response.get("usage") or {}
        return {"input": u.get("prompt_tokens"), "output": u.get("completion_tokens")}
    if provider == ANTHROPIC:
        u = response.get("usage") or {}
        return {"input": u.get("input_tokens"), "output": u.get("output_tokens")}
    u = response.get("usageMetadata") or {}
    return {"input": u.get("promptTokenCount"),
            "output": (u.get("candidatesTokenCount") or 0) + (u.get("thoughtsTokenCount") or 0)}
