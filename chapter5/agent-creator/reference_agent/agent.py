"""A small production-shaped OpenAI-compatible Agent loop.

The creator preserves this loop in template mode and only specializes the
system prompt, tool schemas, and domain tool implementation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from domain_tools import execute_tool


ROOT = Path(__file__).resolve().parent


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class GeneratedAgent:
    def __init__(self, *, model: str | None = None, client: Any | None = None):
        self.model = model or os.getenv("OPENAI_MODEL") or os.getenv(
            "OPENROUTER_MODEL", "openai/gpt-5.6-luna"
        )
        use_router = bool(os.getenv("OPENROUTER_API_KEY")) and (
            "/" in self.model
            or os.getenv("AGENT_PROVIDER", "auto").casefold() in {"auto", "openrouter"}
        )
        api_key = os.getenv("OPENROUTER_API_KEY") if use_router else os.getenv("OPENAI_API_KEY")
        base_url = "https://openrouter.ai/api/v1" if use_router else os.getenv("OPENAI_BASE_URL")
        if client is None and not api_key:
            raise RuntimeError("Set OPENAI_API_KEY or OPENROUTER_API_KEY")
        self.client = client or OpenAI(api_key=api_key, base_url=base_url)
        self.system_prompt = (ROOT / "system_prompt.md").read_text(encoding="utf-8")
        self.tools = _load_json(ROOT / "tools.json")["tools"]

    @staticmethod
    def _assistant_message(message: Any) -> dict[str, Any]:
        result: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in message.tool_calls
            ]
        return result

    def run(
        self,
        task: str,
        *,
        history: list[dict[str, Any]] | None = None,
        max_iterations: int = 12,
    ) -> dict[str, Any]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            *(history or []),
            {"role": "user", "content": task},
        ]
        trace: list[dict[str, Any]] = []
        usage_totals = {
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "requests": 0,
        }
        for iteration in range(1, max_iterations + 1):
            kwargs = dict(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )
            if any(tag in self.model.casefold() for tag in ("kimi-", "gpt-5")):
                kwargs["temperature"] = 1
            else:
                kwargs["temperature"] = 0
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            messages.append(self._assistant_message(message))
            usage = getattr(response, "usage", None)
            prompt_details = getattr(usage, "prompt_tokens_details", None)
            usage_totals["prompt_tokens"] += getattr(usage, "prompt_tokens", 0) or 0
            usage_totals["cached_prompt_tokens"] += (
                getattr(prompt_details, "cached_tokens", 0) or 0
            )
            usage_totals["completion_tokens"] += (
                getattr(usage, "completion_tokens", 0) or 0
            )
            usage_totals["requests"] += 1
            trace.append({
                "iteration": iteration,
                "content": message.content or "",
                "tool_calls": len(message.tool_calls or []),
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
            })
            if not message.tool_calls:
                return {
                    "ok": True,
                    "answer": message.content or "",
                    "iterations": iteration,
                    "trace": trace,
                    "messages": messages,
                    "usage": usage_totals,
                }
            for call in message.tool_calls:
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                    result = execute_tool(call.function.name, arguments)
                except Exception as exc:  # tool failures must return to the model
                    result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        return {
            "ok": False,
            "answer": "",
            "iterations": max_iterations,
            "trace": trace,
            "messages": messages,
            "usage": usage_totals,
            "error": "maximum iterations reached",
        }
