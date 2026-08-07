"""Exact GPT-5.6 Responses API agent for Experiment 1-3.

The previous companion sent Responses-style hosted tools to Chat Completions
through a proxy and then reported an empty ``tool_calls`` list.  This module
uses the actual ``/v1/responses`` protocol and preserves its typed output items
(``web_search_call``, ``code_interpreter_call``, messages, and citations).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Literal, Optional

import requests

logger = logging.getLogger(__name__)


class GPT5NativeAgent:
    """GPT-5.6 Sol with OpenAI-hosted web search and Python tools."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-5.6-sol",
    ):
        if not api_key:
            raise ValueError("An API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider = (
            "openai" if self.base_url == "https://api.openai.com/v1" else
            "openrouter" if "openrouter.ai" in self.base_url else
            "dashscope" if "dashscope" in self.base_url else
            "custom"
        )
        self.conversation_history: List[Dict[str, Any]] = []
        self.system_prompt = self._create_system_prompt()
        self.previous_response_id: Optional[str] = None
        self.api_turns: List[Dict[str, Any]] = []

    @staticmethod
    def _create_system_prompt() -> str:
        return """You are a deep-research assistant. 你是一名深度研究助手。

Hard rule / 硬性规则: when the user's research request leaves material
preferences ambiguous — for example which data source to use or which
technical indicators to compute — ask a concise clarifying question FIRST
(for example “您偏好使用哪个数据源？需要分析哪些技术指标？”), and do NOT
call any tool until the user answers.
当用户的研究请求没有明确数据来源或具体分析指标时，必须先向用户提问澄清，
在用户回答之前不要调用任何工具。

After clarification, use hosted web search for current facts and cite
sources, and use the hosted Python/code-interpreter tool for quantitative
analysis; do not claim a calculation was run unless the response contains a
completed code_interpreter_call.
澄清之后：使用 web_search 获取最新事实并引用来源链接；所有定量计算必须通过
code_interpreter 实际执行，不得口算或声称运行了代码。"""

    def _tools(self) -> List[Dict[str, Any]]:
        if self.provider == "dashscope":
            # Exact structures from the Alibaba Model Studio Responses API guides.
            return [{"type": "web_search"}, {"type": "code_interpreter"}]
        # Exact structures from the official OpenAI Responses API guides.
        return [
            {"type": "web_search", "search_context_size": "medium"},
            {
                "type": "code_interpreter",
                "container": {"type": "auto", "memory_limit": "4g"},
            },
        ]

    def _build_responses_request(
        self,
        input_text: str,
        *,
        use_tools: bool = True,
        tool_choice: Literal["auto", "none", "required"] = "auto",
        reasoning_effort: str = "low",
        verbosity: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        background: bool = False,
    ) -> Dict[str, Any]:
        if self.provider != "dashscope":
            if reasoning_effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
                raise ValueError("Unsupported GPT-5.6 reasoning effort")
            if verbosity not in {None, "low", "medium", "high"}:
                raise ValueError("verbosity must be low, medium, or high")
        request: Dict[str, Any] = {
            "model": self.model,
            "instructions": self.system_prompt,
            "input": input_text,
        }
        if self.provider == "dashscope":
            # DashScope runs thinking natively and has no reasoning.effort or
            # text.verbosity knobs; its gateway also drops non-streaming
            # requests that stay silent for ~60s, so streaming is mandatory.
            request["stream"] = True
        else:
            request["reasoning"] = {"effort": reasoning_effort}
            request["background"] = background
            request["store"] = True
            if verbosity:
                request["text"] = {"verbosity": verbosity}
        if max_output_tokens:
            request["max_output_tokens"] = max_output_tokens
        if use_tools:
            request["tools"] = self._tools()
            request["tool_choice"] = tool_choice
        if self.previous_response_id:
            request["previous_response_id"] = self.previous_response_id
        return request

    @staticmethod
    def _output_text(response: Dict[str, Any]) -> str:
        chunks: List[str] = []
        for item in response.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                if isinstance(content, dict) and content.get("type") == "output_text" and content.get("text"):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()

    @staticmethod
    def _tool_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            item
            for item in response.get("output") or []
            if isinstance(item, dict)
            and item.get("type") in {
                "web_search_call",
                "code_interpreter_call",
                "hosted_tool_call",
            }
        ]

    @staticmethod
    def _citations(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        citations = []
        for item in response.get("output") or []:
            if not isinstance(item, dict):
                continue
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                for annotation in content.get("annotations") or []:
                    if isinstance(annotation, dict) and annotation.get("type") in {
                        "url_citation",
                        "container_file_citation",
                    }:
                        citations.append(annotation)
            # DashScope reports sources on the web_search_call item itself
            # instead of url_citation annotations; normalize them here.
            if item.get("type") == "web_search_call":
                action = item.get("action")
                if isinstance(action, dict):
                    for source in action.get("sources") or []:
                        url = source if isinstance(source, str) else (source.get("url") if isinstance(source, dict) else None)
                        if url:
                            citations.append(
                                {"type": "url_citation", "url": url}
                            )
        return citations

    def _post_responses(
        self, request: Dict[str, Any]
    ) -> tuple[int, Dict[str, Any], Optional[Dict[str, int]]]:
        """Send one Responses request and return (status, body, stream_events).

        DashScope requires streaming; the final ``response.completed`` event
        carries the same response object the non-streaming API returns, so both
        paths converge on an identical shape.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if not request.get("stream"):
            http_response = requests.post(
                f"{self.base_url}/responses",
                headers=headers,
                json=request,
                timeout=900,
            )
            try:
                return http_response.status_code, http_response.json(), None
            except ValueError:
                return http_response.status_code, {"raw_text": http_response.text}, None

        event_counts: Dict[str, int] = {}
        final_response: Optional[Dict[str, Any]] = None
        with requests.post(
            f"{self.base_url}/responses",
            headers=headers,
            json=request,
            stream=True,
            timeout=900,
        ) as http_response:
            status_code = http_response.status_code
            if not http_response.ok:
                return status_code, {"raw_text": http_response.text}, event_counts
            for line in http_response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except ValueError:
                    continue
                event_type = event.get("type") or "unknown"
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
                if event_type in {"response.completed", "response.failed"}:
                    final_response = event.get("response")
        if final_response is None:
            return status_code, {"error": {"type": "stream_incomplete",
                                           "message": "stream ended without response.completed"}}, event_counts
        return status_code, final_response, event_counts

    def process_request(
        self,
        user_request: str,
        use_tools: bool = True,
        tool_choice: Literal["auto", "none", "required"] = "auto",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        reasoning_effort: str = "low",
        verbosity: Optional[str] = None,
        dry_run: bool = False,
        background: bool = False,
    ) -> Dict[str, Any]:
        """Create one Responses API turn and retain its complete trace.

        ``temperature`` remains in the signature for legacy callers, but is not
        sent: GPT-5.6 reasoning requests use ``reasoning.effort`` instead.
        """
        request = self._build_responses_request(
            user_request,
            use_tools=use_tools,
            tool_choice=tool_choice,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            max_output_tokens=max_tokens,
            background=background,
        )
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "request": request,
                "response": None,
                "tool_calls": [],
                "model": self.model,
                "provider": self.provider,
            }

        started = time.monotonic()
        try:
            status_code, response, stream_events = self._post_responses(request)
            elapsed = round(time.monotonic() - started, 6)
            turn = {
                "request": json.loads(json.dumps(request, ensure_ascii=False)),
                "http_status": status_code,
                "response": response,
                "elapsed_seconds": elapsed,
            }
            if stream_events:
                turn["stream_event_counts"] = stream_events
            self.api_turns.append(turn)
            if status_code >= 400 or response.get("error"):
                error = response.get("error") or {
                    "type": "http_error",
                    "message": response.get("raw_text") or json.dumps(response)[:500],
                }
                return {
                    "success": False,
                    "error": error,
                    "response": None,
                    "request": request,
                    "raw_response": response,
                    "tool_calls": [],
                    "citations": [],
                    "usage": response.get("usage") or {},
                    "model": self.model,
                    "provider": self.provider,
                    "base_url": self.base_url,
                    "elapsed_seconds": elapsed,
                }

            self.previous_response_id = response.get("id")
            text = self._output_text(response)
            self.conversation_history.extend(
                [
                    {"role": "user", "content": user_request},
                    {"role": "assistant", "content": text},
                ]
            )
            return {
                "success": response.get("status") == "completed" and bool(text),
                "error": response.get("error"),
                "response": text,
                "request": request,
                "raw_response": response,
                "output_items": response.get("output") or [],
                "tool_calls": self._tool_items(response),
                "citations": self._citations(response),
                "usage": response.get("usage") or {},
                "model": response.get("model") or self.model,
                "requested_model": self.model,
                "provider": self.provider,
                "base_url": self.base_url,
                "response_id": response.get("id"),
                "status": response.get("status"),
                "elapsed_seconds": elapsed,
                "temperature_omitted_for_reasoning_model": temperature is not None,
            }
        except Exception as exc:
            elapsed = round(time.monotonic() - started, 6)
            self.api_turns.append(
                {
                    "request": request,
                    "elapsed_seconds": elapsed,
                    "error": {"class": type(exc).__name__, "message": str(exc)},
                }
            )
            return {
                "success": False,
                "error": {"class": type(exc).__name__, "message": str(exc)},
                "response": None,
                "request": request,
                "tool_calls": [],
                "citations": [],
                "model": self.model,
                "provider": self.provider,
                "base_url": self.base_url,
                "elapsed_seconds": elapsed,
            }

    def search_and_analyze(
        self, topic: str, analysis_code: Optional[str] = None
    ) -> Dict[str, Any]:
        code_requirement = (
            f"Run this supplied Python in the hosted tool and inspect its output:\n{analysis_code}"
            if analysis_code
            else "Use the hosted Python tool for all quantitative processing."
        )
        return self.process_request(
            f"Research current information about {topic}. {code_requirement} "
            "Cite web sources and distinguish searched facts from computed results.",
            use_tools=True,
            reasoning_effort="medium",
        )

    def clear_history(self) -> None:
        self.conversation_history = []
        self.previous_response_id = None
        self.api_turns = []

    def get_history(self) -> List[Dict[str, Any]]:
        return json.loads(json.dumps(self.conversation_history, ensure_ascii=False))

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt


class GPT5AgentChain:
    """Sequential Responses turns linked with ``previous_response_id``."""

    def __init__(self, agent: GPT5NativeAgent):
        self.agent = agent
        self.chain_results: List[Dict[str, Any]] = []

    def add_step(self, request: str, **kwargs: Any) -> "GPT5AgentChain":
        self.chain_results.append(
            {"request": request, "result": self.agent.process_request(request, **kwargs)}
        )
        return self

    def execute(self) -> List[Dict[str, Any]]:
        return self.chain_results

    def clear(self) -> None:
        self.chain_results = []
