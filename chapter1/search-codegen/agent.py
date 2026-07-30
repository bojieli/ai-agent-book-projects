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
            "custom"
        )
        self.conversation_history: List[Dict[str, Any]] = []
        self.system_prompt = self._create_system_prompt()
        self.previous_response_id: Optional[str] = None
        self.api_turns: List[Dict[str, Any]] = []

    @staticmethod
    def _create_system_prompt() -> str:
        return """You are a deep-research assistant. Use hosted web search for
current facts and cite sources. Use the hosted Python/code-interpreter tool for
quantitative analysis; do not claim a calculation was run unless the response
contains a completed code_interpreter_call. Ask a concise clarifying question
before research when a material user preference is genuinely ambiguous."""

    @staticmethod
    def _tools() -> List[Dict[str, Any]]:
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
        if reasoning_effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
            raise ValueError("Unsupported GPT-5.6 reasoning effort")
        if verbosity not in {None, "low", "medium", "high"}:
            raise ValueError("verbosity must be low, medium, or high")
        request: Dict[str, Any] = {
            "model": self.model,
            "instructions": self.system_prompt,
            "input": input_text,
            "reasoning": {"effort": reasoning_effort},
            "background": background,
            "store": True,
        }
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
            if item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                if content.get("type") == "output_text" and content.get("text"):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()

    @staticmethod
    def _tool_items(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            item
            for item in response.get("output") or []
            if item.get("type") in {
                "web_search_call",
                "code_interpreter_call",
                "hosted_tool_call",
            }
        ]

    @staticmethod
    def _citations(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        citations = []
        for item in response.get("output") or []:
            for content in item.get("content") or []:
                for annotation in content.get("annotations") or []:
                    if annotation.get("type") in {
                        "url_citation",
                        "container_file_citation",
                    }:
                        citations.append(annotation)
        return citations

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
            http_response = requests.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request,
                timeout=900,
            )
            elapsed = round(time.monotonic() - started, 6)
            try:
                response = http_response.json()
            except ValueError:
                response = {"raw_text": http_response.text}
            turn = {
                "request": json.loads(json.dumps(request, ensure_ascii=False)),
                "http_status": http_response.status_code,
                "response": response,
                "elapsed_seconds": elapsed,
            }
            self.api_turns.append(turn)
            if not http_response.ok or response.get("error"):
                error = response.get("error") or {
                    "type": "http_error",
                    "message": http_response.text,
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
