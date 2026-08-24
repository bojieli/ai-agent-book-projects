"""流式请求，以及在中途把它切断。

三家的增量格式不一样，但对这个实验来说只需要四个东西：思考、正文、工具名、
工具参数的半截 JSON。切断的方式就是读到条件满足就不再读了，连接直接关掉——
和真实的连接中断一样，剩下的内容永远不会到达。
"""

from __future__ import annotations

import json
import os
import time

import requests

from providers import ANTHROPIC, GEMINI, KIMI, _key

REASONING, TEXT, TOOL_ARGS = "reasoning", "text", "tool_args"
BREAK_POINTS = (REASONING, TEXT, TOOL_ARGS)


class Partial(dict):
    """流被切断时手上攒到的东西。"""

    @classmethod
    def new(cls) -> "Partial":
        return cls(reasoning="", text="", tool_name=None, tool_args="", tool_index=None,
                   tool_args_closed=False, truncated=False, finished=False)

    @property
    def has_partial_args(self) -> bool:
        return bool(self.get("tool_name")) and not self.get("tool_args_closed")


def _cut_here(state: Partial, where: str, limits: dict) -> bool:
    if where == REASONING:
        return len(state.get("reasoning") or "") >= limits[REASONING]
    if where == TEXT:
        return len(state.get("text") or "") >= limits[TEXT]
    if state.get("tool_args_closed"):
        # 参数整块到达，流里根本没出现过“半截”，这个断点在这家厂商上不可复现。
        return False
    return bool(state.get("tool_name")) and len(state.get("tool_args") or "") >= limits[TOOL_ARGS]


def stream_until(provider: str, payload: dict, where: str | None,
                 limits: dict | None = None) -> Partial:
    """流式请求。``where`` 为 None 表示读完整条流（作为对照）。"""
    limits = limits or {REASONING: 40, TEXT: 30, TOOL_ARGS: 10}
    state = Partial.new()

    url, headers, body = _stream_request(provider, payload)
    return _read_stream(provider, url, headers, body, where, limits, state)


def _read_stream(provider, url, headers, body, where, limits, state, attempts: int = 3) -> Partial:
    """取流本身也会被掐断，重试几次再放弃——这次中断不是实验要测的那一个。"""
    for attempt in range(attempts):
        try:
            return _read_stream_once(provider, url, headers, body, where, limits, Partial.new())
        except requests.RequestException as e:
            if attempt == attempts - 1:
                raise RuntimeError(f"取流失败：{e}") from e
            time.sleep(6 * (attempt + 1))
    return state


def _read_stream_once(provider, url, headers, body, where, limits, state: Partial) -> Partial:
    with requests.post(url, headers=headers, json=body, stream=True, timeout=180) as r:
        if r.status_code != 200:
            raise RuntimeError(f"{provider} HTTP {r.status_code}: {r.text[:300]}")
        # SSE 响应头常常不写 charset，不显式指定就会按 latin-1 解码，中文直接变乱码。
        r.encoding = "utf-8"

        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                state["finished"] = True
                break
            try:
                event = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            _absorb(provider, event, state)
            if where and _cut_here(state, where, limits):
                # 到这里就当连接断了。真实的中断不会正好停在增量边界上，所以把
                # 手上那一段截到指定字符数，剩下的内容永远收不到。
                field = {REASONING: "reasoning", TEXT: "text", TOOL_ARGS: "tool_args"}[where]
                state[field] = state[field][:limits[where]]
                state["truncated"] = True
                break
        else:
            state["finished"] = True
    return state


def _stream_request(provider: str, payload: dict):
    body = dict(payload)
    if provider == KIMI:
        body["stream"] = True
        return (os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1") + "/chat/completions",
                {"Authorization": f"Bearer {_key('MOONSHOT_API_KEY', 'KIMI_API_KEY')}",
                 "Content-Type": "application/json"}, body)
    if provider == ANTHROPIC:
        body["stream"] = True
        return ("https://api.anthropic.com/v1/messages",
                {"x-api-key": _key("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"}, body)
    model = body.pop("_model")
    return (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse",
            {"x-goog-api-key": _key("GEMINI_API_KEY", "GOOGLE_API_KEY"), "Content-Type": "application/json"}, body)


def _absorb(provider: str, event: dict, state: Partial) -> None:
    if provider == KIMI:
        delta = (event.get("choices") or [{}])[0].get("delta") or {}
        state["reasoning"] += delta.get("reasoning_content") or ""
        state["text"] += delta.get("content") or ""
        for call in delta.get("tool_calls") or []:
            fn = call.get("function") or {}
            index = call.get("index", 0)
            if state["tool_index"] is None:
                state["tool_index"] = index
            if index != state["tool_index"]:
                continue  # 同一轮里的第二个调用，与这次要切断的那个无关
            state["tool_name"] = state["tool_name"] or fn.get("name")
            state["tool_args"] += fn.get("arguments") or ""
        return

    if provider == ANTHROPIC:
        etype = event.get("type")
        if etype == "content_block_start":
            block = event.get("content_block") or {}
            if block.get("type") == "tool_use" and state["tool_index"] is None:
                state["tool_name"] = block.get("name")
                state["tool_index"] = event.get("index")
        elif etype == "content_block_delta":
            d = event.get("delta") or {}
            state["reasoning"] += d.get("thinking") or ""
            state["text"] += d.get("text") or ""
            if d.get("partial_json") and event.get("index") == state["tool_index"]:
                state["tool_args"] += d["partial_json"]
        return

    for part in ((event.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []:
        if part.get("thought"):
            state["reasoning"] += part.get("text") or ""
        elif "functionCall" in part:
            if state["tool_name"]:
                continue  # 只跟第一个调用
            fc = part["functionCall"]
            state["tool_name"] = fc.get("name")
            # Gemini 的流式接口把 functionCall 整块吐出来，不给半截参数。
            state["tool_args"] = json.dumps(fc.get("args") or {}, ensure_ascii=False)
            state["tool_args_closed"] = True
        elif "text" in part:
            state["text"] += part["text"]
