#!/usr/bin/env python3
"""Run the exact Chapter 4 Experiment 4-7 contract.

Unlike the original mechanism demo, this runner:

* obtains 126 complete schemas from the perception MCP server via stdio;
* uses exactly local Ollama ``qwen3:4b`` for both groups;
* asserts that the control catalog exceeds 50K measured tokens;
* executes the selected tools through MCP against real APIs/local processes;
* stores compact canonical receipts, a gzipped schema catalog, and hashes.

The experiment measures *tool-selection* accuracy.  The orchestrator supplies
task constants (AAPL, transformer, openai/openai-python) and resolves dependent
arguments (the three arXiv IDs and visualization code) after the model selects
the correct capability.  This keeps external execution safe and repeatable
without substituting a mock result for a tool call.
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import tiktoken
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
CHAPTER4 = HERE.parent
REPO = CHAPTER4.parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"
MCP_SERVER = CHAPTER4 / "perception-tools" / "src" / "main.py"
VALIDATION_ROOT = HERE / "validation" / "experiment_4_7"

MODEL = "qwen3:4b"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_OPTIONS = {"temperature": 0, "num_ctx": 131072, "num_predict": 1400}
BASE_TOOL_NAMES = {"web_search", "code_interpreter"}
DISCOVERY_TOP_K = 5

TOOL_PROVENANCE = {
    "yfinance_quote": {"backend": "yahoo-finance-yfinance", "origin": "live-api"},
    "stock_price": {"backend": "query1.finance.yahoo.com", "origin": "live-api"},
    "finance_market_summary": {"backend": "yahoo-finance-yfinance", "origin": "live-api"},
    "web_search": {"backend": "html.duckduckgo.com", "origin": "live-api"},
    "search_news": {"backend": "html.duckduckgo.com", "origin": "live-api"},
    "arxiv_search": {"backend": "export.arxiv.org", "origin": "live-api"},
    "arxiv_download": {"backend": "export.arxiv.org", "origin": "live-api"},
    "github_list_contributors": {"backend": "api.github.com", "origin": "live-api"},
    "code_interpreter": {"backend": "python-isolated-subprocess", "origin": "local-process"},
}
SIMULATION_PATTERN = re.compile(
    r"\b(mock(?:ed)?|placeholder|synthetic|simulat(?:ed|ion))\b", re.IGNORECASE
)

STOCK_TOOLS = {"yfinance_quote", "stock_price", "finance_market_summary"}
NEWS_TOOLS = {"web_search", "search_news"}
ARXIV_SEARCH_TOOLS = {"arxiv_search"}
ARXIV_DOWNLOAD_TOOLS = {"arxiv_download"}
GITHUB_TOOLS = {"github_list_contributors"}
CODE_TOOLS = {"code_interpreter"}

TASKS = [
    {
        "id": "apple_stock_news",
        "prompt": "Query Apple's latest stock price and search related current news to explain the movement.",
        "slots": [STOCK_TOOLS, NEWS_TOOLS],
    },
    {
        "id": "transformer_arxiv_download",
        "prompt": "Find the latest transformer papers on arXiv and download the top three PDFs.",
        "slots": [ARXIV_SEARCH_TOOLS, ARXIV_DOWNLOAD_TOOLS],
    },
    {
        "id": "github_contributors_visualization",
        "prompt": "Analyze contributor statistics for openai/openai-python and generate a visualization report.",
        "slots": [GITHUB_TOOLS, CODE_TOOLS],
    },
]

DISCOVER_SCHEMA = {
    "name": "discover_tools",
    "description": (
        "Describe one missing capability in natural language. The runtime performs semantic "
        "retrieval over the perception MCP catalog and appends five complete matching schemas "
        "to conversation history. Call it separately for distinct domains."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {"need": {"type": "string"}},
        "required": ["need"],
    },
}

TREATMENT_GUIDANCE = """
The two base tools are deliberately insufficient for authoritative,
domain-specific retrieval. Never use generic web_search or code_interpreter as
a substitute for a missing specialist merely because a search snippet mentions
the desired value. A structured market quote, repository metadata, academic
search, and file download each require an appropriate specialist discovered at
the moment that capability gap arises. A task can contain multiple distinct
gaps; call discover_tools separately for each one, while continuing to use
web_search for general current-news context and code_interpreter for local
computation after the required source data has been obtained.
""".strip()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8")


def schema_dict(tool) -> dict[str, Any]:
    return tool.model_dump(by_alias=True, exclude_none=True, mode="json")


def render_schemas(schemas: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(schema, ensure_ascii=False, indent=2) for schema in schemas)


def count_tokens(text: str) -> int:
    return len(tiktoken.get_encoding("o200k_base").encode(text))


def extract_json(text: str) -> Any:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("model response did not contain valid JSON")


async def ollama_chat(messages: list[dict[str, str]], *, timeout: float = 900.0) -> dict[str, Any]:
    request = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": OLLAMA_OPTIONS,
        "keep_alive": "30m",
    }
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{OLLAMA_URL}/api/chat", json=request)
        response.raise_for_status()
        payload = response.json()
    return {
        "response_model": payload.get("model"),
        "created_at": payload.get("created_at"),
        "done": payload.get("done"),
        "done_reason": payload.get("done_reason"),
        "content": payload.get("message", {}).get("content", ""),
        "thinking": payload.get("message", {}).get("thinking", ""),
        "prompt_eval_count": payload.get("prompt_eval_count"),
        "eval_count": payload.get("eval_count"),
        "total_duration_ns": payload.get("total_duration"),
        "latency_seconds": round(time.perf_counter() - started, 3),
        "request_hash": sha256_bytes(canonical_json(request).encode()),
    }


class LocalEmbeddingIndex:
    """Semantic index using the locally cached all-MiniLM-L6-v2 encoder.

    This avoids an external embeddings quota and still uses a real dense
    sentence-embedding model.  ``local_files_only`` makes the campaign fail
    closed rather than silently downloading or switching models.
    """

    def __init__(self, schemas: list[dict[str, Any]], cache_dir: Path):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.schemas = schemas
        self.by_name = {schema["name"]: schema for schema in schemas}
        self.texts = [self._text(schema) for schema in schemas]
        self.model = "sentence-transformers/all-MiniLM-L6-v2"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model, local_files_only=True)
        self.encoder = AutoModel.from_pretrained(self.model, local_files_only=True).to("cpu").eval()
        self.torch = torch
        signature = sha256_bytes(canonical_json(self.texts).encode())[:20]
        self.cache_path = cache_dir / f"embeddings-all-MiniLM-L6-v2-{signature}.json"
        if self.cache_path.exists():
            cached = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self.vectors = cached["vectors"]
        else:
            self.vectors = self._embed(self.texts)
            write_json(self.cache_path, {
                "model": self.model,
                "backend": "local-transformers-mean-pooling",
                "local_files_only": True,
                "signature": signature,
                "texts_sha256": sha256_bytes(canonical_json(self.texts).encode()),
                "vectors": self.vectors,
            })

    def receipt(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "backend": "local-transformers-mean-pooling",
            "device": "cpu",
            "local_files_only": True,
            "catalog_text_count": len(self.texts),
            "texts_sha256": sha256_bytes(canonical_json(self.texts).encode()),
            "cache_path": str(self.cache_path),
            "cache_sha256": sha256_bytes(self.cache_path.read_bytes()),
            "vector_count": len(self.vectors),
            "vector_dimensions": len(self.vectors[0]) if self.vectors else 0,
        }

    @staticmethod
    def _text(schema: dict[str, Any]) -> str:
        summary = (schema.get("description") or "").split("\n\n", 1)[0]
        return f"{schema['name']}: {summary}"

    def _embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 32):
            batch = texts[start:start + 32]
            encoded = self.tokenizer(batch, padding=True, truncation=True,
                                     max_length=256, return_tensors="pt")
            with self.torch.no_grad():
                hidden = self.encoder(**encoded).last_hidden_state
                mask = encoded["attention_mask"].unsqueeze(-1).expand(hidden.size()).float()
                pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
                pooled = self.torch.nn.functional.normalize(pooled, p=2, dim=1)
            vectors.extend(pooled.cpu().tolist())
        return vectors

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        ln = sum(a * a for a in left) ** 0.5
        rn = sum(b * b for b in right) ** 0.5
        return dot / (ln * rn + 1e-12)

    def search(self, need: str, top_k: int = DISCOVERY_TOP_K) -> list[dict[str, Any]]:
        query_vector = self._embed([need])[0]
        ranked = sorted(
            ((self._cosine(query_vector, vector), schema)
             for vector, schema in zip(self.vectors, self.schemas)
             if schema["name"] not in BASE_TOOL_NAMES),
            key=lambda pair: pair[0], reverse=True,
        )[:top_k]
        return [{"score": round(score, 6), "schema": schema} for score, schema in ranked]


_AGENT_PROTOCOL = """
Work one step at a time. Every response must be exactly one JSON object with no
markdown. Choose one of these actions:

1. {"action":"discover_tools","need":"one missing capability"}
   Use only when discover_tools is currently available and you lack a suitable
   specialist. Discover one capability at the moment the gap arises; do not
   pre-enumerate all future needs.
2. {"action":"call_tool","tool":"exact_name","query":"primary subject","options":{}}
   Call exactly one currently available tool. Prefer a specialist to generic
   web search. The runtime will return a real observation before your next turn.
3. {"action":"finish","answer":"evidence-grounded answer"}
   Finish only after every requested subtask has a successful observation.

For the arXiv task, one arxiv_download action after arxiv_search downloads the
three returned IDs. For visualization, call github_list_contributors before
code_interpreter. Never invent a result or call an undiscovered tool.
""".strip()


def parse_action(response: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = extract_json(response["content"])
        if not isinstance(parsed, dict):
            raise ValueError("action must be a JSON object")
        kind = parsed.get("action")
        # Tolerate the common ReAct spelling while keeping one-action semantics.
        if not kind and parsed.get("tool"):
            kind = "finish" if parsed["tool"] == "finish" else "call_tool"
        if kind == "discover_tools":
            need = str(parsed.get("need", "")).strip()
            if not need:
                raise ValueError("discover_tools requires a non-empty need")
            return {"action": kind, "need": need}, None
        if kind == "call_tool":
            name = str(parsed.get("tool", "")).strip()
            if not name:
                raise ValueError("call_tool requires tool")
            options = parsed.get("options")
            if not isinstance(options, dict):
                options = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}
            return {"action": kind, "tool": name,
                    "query": str(parsed.get("query", options.pop("query", ""))),
                    "options": options}, None
        if kind == "finish":
            return {"action": kind, "answer": str(parsed.get("answer", ""))}, None
        raise ValueError(f"unknown action {kind!r}")
    except Exception as exc:
        return None, str(exc)


def grade_plan(task: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    names = [action["tool"] for action in actions]
    slot_hits = [sorted(set(names) & slot) for slot in task["slots"]]
    return {
        "selected_tools": names,
        "slot_hits": slot_hits,
        "accuracy": sum(bool(hit) for hit in slot_hits) / len(slot_hits),
        "all_required_capabilities_selected": all(slot_hits),
    }


def parse_payload(result) -> dict[str, Any]:
    texts = [getattr(item, "text", "") for item in result.content]
    if not texts:
        return {"success": False, "error": "MCP result had no text content"}
    try:
        payload = json.loads(texts[0])
        # Static perception tools use ActionResponse(message=...), while the
        # expanded tools use data. Normalize both without changing raw fields.
        if isinstance(payload, dict) and "data" not in payload and "message" in payload:
            payload["data"] = payload["message"]
        return payload
    except json.JSONDecodeError:
        return {"success": False, "error": "MCP result was not JSON", "raw": texts[0][:2000]}


def simulation_markers(value: Any) -> list[str]:
    """Record suspicious evidence markers instead of assuming results are real."""
    return sorted({match.group(1).lower()
                   for match in SIMULATION_PATTERN.finditer(canonical_json(value))})


def substantive_payload(tool_name: str, payload: dict[str, Any]) -> bool:
    """Require task evidence, not merely a backend's success boolean."""
    data = payload.get("data")
    if tool_name in {"yfinance_quote", "stock_price"}:
        return isinstance(data, dict) and data.get("current_price") is not None
    if tool_name == "finance_market_summary":
        return isinstance(data, dict) and bool(data.get("history"))
    if tool_name == "web_search":
        return isinstance(data, dict) and data.get("count", 0) > 0 \
            and bool(data.get("results"))
    if tool_name == "search_news":
        return isinstance(data, list) and bool(data) and all(
            isinstance(row, dict) and row.get("title") and row.get("url") for row in data
        )
    if tool_name == "arxiv_search":
        return isinstance(data, dict) and data.get("count", 0) >= 3 \
            and len(data.get("papers", [])) >= 3
    if tool_name == "arxiv_download":
        if not isinstance(data, dict) or data.get("file_size", 0) <= 1000:
            return False
        path = Path(str(data.get("file_path", "")))
        return path.is_file() and path.read_bytes()[:5] == b"%PDF-"
    if tool_name == "github_list_contributors":
        return isinstance(data, list) and bool(data) and all(
            isinstance(row, dict) and row.get("login")
            and isinstance(row.get("contributions"), int) for row in data
        )
    if tool_name == "code_interpreter":
        return isinstance(data, dict) and data.get("returncode") == 0
    return data is not None


def mcp_receipt(tool_name: str, result, payload: dict[str, Any],
                *, arguments: dict[str, Any], latency_seconds: float) -> dict[str, Any]:
    configured = TOOL_PROVENANCE.get(tool_name, {})
    payload_backend = payload.get("backend") if isinstance(payload, dict) else None
    configured_backend = configured.get("backend")
    if tool_name == "web_search":
        engine = str(payload.get("metadata", {}).get("search_engine", "")).lower()
        configured_backend = {
            "duckduckgo": "html-or-lite.duckduckgo.com",
            "serper-google": "google.serper.dev",
            "tavily": "api.tavily.com",
        }.get(engine, configured_backend)
    provenance = {
        "backend": configured_backend or payload_backend,
        "origin": configured.get("origin"),
    }
    is_error = bool(getattr(result, "isError", False))
    # Remote bodies are untrusted observations and may legitimately discuss a
    # "simulation" or "mock". Inspect only control-plane provenance/error
    # metadata so content cannot falsely invalidate (or validate) the backend.
    markers = simulation_markers({
        "backend": payload.get("backend"),
        "error_type": payload.get("error_type"),
        "error": payload.get("error"),
        "metadata": payload.get("metadata"),
    })
    substantive = substantive_payload(tool_name, payload)
    return {
        "tool": tool_name,
        "arguments": arguments,
        "transport": "mcp-stdio",
        "mcp_result_is_error": is_error,
        "backend_provenance": provenance,
        "simulation_markers": markers,
        "substantive_observation": substantive,
        "latency_seconds": latency_seconds,
        "payload": payload,
        "success": bool(payload.get("success")) and not is_error and not markers and substantive
                    and bool(provenance["backend"]) and provenance["origin"] in {
                        "live-api", "local-process"
                    },
    }


def compact_tool_data(tool_name: str, payload: dict[str, Any]) -> Any:
    data = payload.get("data")
    if tool_name == "github_list_contributors" and isinstance(data, list):
        return [{"login": row.get("login"), "contributions": row.get("contributions")}
                for row in data[:20]]
    return data


def arxiv_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data", {})
    if isinstance(data, dict) and "message" in data:
        data = data["message"]
    papers = data.get("papers", []) if isinstance(data, dict) else []
    ids = []
    for paper in papers:
        raw = str(paper.get("id") or paper.get("entry_id") or paper.get("pdf_url") or "")
        match = re.search(r"(?:abs/|pdf/)?([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", raw)
        if match:
            ids.append(match.group(1))
    return ids[:3]


def visualization_code(contributors: list[dict[str, Any]], output_path: Path) -> str:
    rows = [(str(row.get("login", "unknown")), int(row.get("contributions") or 0))
            for row in contributors[:10]]
    return f"""import html
rows = {rows!r}
width, height, margin = 900, 500, 70
maximum = max([value for _, value in rows] or [1])
bar_w = max(30, (width - 2 * margin) // max(1, len(rows)))
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{{width}}" height="{{height}}">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<text x="450" y="32" text-anchor="middle" font-size="22">openai/openai-python contributors</text>']
for index, (name, value) in enumerate(rows):
    bar_h = int((height - 150) * value / maximum)
    x = margin + index * bar_w
    y = height - 80 - bar_h
    parts.append(f'<rect x="{{x}}" y="{{y}}" width="{{bar_w - 8}}" height="{{bar_h}}" fill="#4f46e5"/>')
    parts.append(f'<text x="{{x + (bar_w-8)/2}}" y="{{y-5}}" text-anchor="middle" font-size="11">{{value}}</text>')
    parts.append(f'<text x="{{x + (bar_w-8)/2}}" y="{{height-60}}" text-anchor="end" transform="rotate(-35 {{x + (bar_w-8)/2}} {{height-60}})" font-size="10">{{html.escape(name)}}</text>')
parts.append('</svg>')
open({str(output_path)!r}, 'w', encoding='utf-8').write(''.join(parts))
print({str(output_path)!r})
"""


def _task_artifacts(task_dir: Path) -> dict[str, Any]:
    downloaded_paths = sorted((task_dir / "papers").glob("*.pdf")) \
        if (task_dir / "papers").exists() else []
    downloaded = []
    for path in downloaded_paths:
        data = path.read_bytes()
        downloaded.append({
            "path": str(path),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
            "pdf_signature": data.startswith(b"%PDF-"),
        })
    chart = task_dir / "contributors.svg"
    chart_data = chart.read_bytes() if chart.exists() else b""
    return {
        "downloaded_pdfs": downloaded,
        "download_count": len(downloaded),
        "visualization": str(chart) if chart.exists() else None,
        "visualization_bytes": len(chart_data),
        "visualization_sha256": sha256_bytes(chart_data) if chart_data else None,
        "visualization_svg_signature": chart_data.lstrip().startswith(b"<svg") if chart_data else False,
    }


def _finalize_execution(task: dict[str, Any], state: dict[str, Any], task_dir: Path) -> dict[str, Any]:
    artifacts = _task_artifacts(task_dir)
    success_names = {receipt["tool"] for receipt in state["receipts"] if receipt.get("success")}
    completion = all(success_names & slot for slot in task["slots"])
    if task["id"] == "transformer_arxiv_download":
        completion = completion and artifacts["download_count"] == 3 and all(
            row["pdf_signature"] and row["bytes"] > 1000
            for row in artifacts["downloaded_pdfs"]
        )
    if task["id"] == "github_contributors_visualization":
        completion = completion and artifacts["visualization_bytes"] > 100 \
            and artifacts["visualization_svg_signature"]
    return {"receipts": state["receipts"], "artifacts": artifacts,
            "task_complete": bool(completion)}


async def _call_real_tool(session: ClientSession, task: dict[str, Any], action: dict[str, Any],
                          task_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Execute one model-selected capability through MCP and update dependencies."""
    name = action["tool"]
    query = action["query"]
    options = dict(action["options"])
    if name in STOCK_TOOLS:
        query, options = "AAPL", {}
    elif name in NEWS_TOOLS:
        query = "Apple AAPL stock"
        options.update({"num_results": 5, "limit": 5})
    elif name in ARXIV_SEARCH_TOOLS:
        query = "transformer"
        options.update({"max_results": 3, "sort_by": "submittedDate"})
    elif name in GITHUB_TOOLS:
        query, options = "openai/openai-python", {"limit": 10}
    elif name in CODE_TOOLS:
        chart = task_dir / "contributors.svg"
        query = visualization_code(state["contributors"], chart)
        options = {"timeout": 30}

    if name in ARXIV_DOWNLOAD_TOOLS:
        ids = arxiv_ids(state.get("search_payload") or {})
        if len(ids) != 3:
            receipt = {"tool": name, "success": False,
                       "error": f"expected three arXiv IDs, found {len(ids)}"}
            state["receipts"].append(receipt)
            return receipt
        download_dir = task_dir / "papers"
        download_dir.mkdir(parents=True, exist_ok=True)
        group = []
        for paper_id in ids:
            args = {"paper_id": paper_id, "download_dir": str(download_dir)}
            started = time.perf_counter()
            result = await session.call_tool(name, args)
            payload = parse_payload(result)
            receipt = mcp_receipt(
                name, result, payload, arguments=args,
                latency_seconds=round(time.perf_counter() - started, 3),
            )
            receipt["paper_id"] = paper_id
            state["receipts"].append(receipt)
            group.append(receipt)
        return {"tool": name, "success": all(item["success"] for item in group),
                "downloads": [{"paper_id": item["paper_id"], "success": item["success"]}
                              for item in group]}

    if name == "yfinance_quote":
        args = {"symbol": query}
    elif name == "stock_price":
        args = {"symbol": query}
    elif name == "web_search":
        args = {"query": query, "num_results": int(options.get("num_results", 5)),
                "region": str(options.get("region", "wt-wt"))}
    elif name == "arxiv_search":
        args = {"query": query, "max_results": int(options.get("max_results", 3)),
                "sort_by": str(options.get("sort_by", "submittedDate"))}
    else:
        args = {"query": query, "options_json": json.dumps(options, ensure_ascii=False)}
    started = time.perf_counter()
    result = await session.call_tool(name, args)
    payload = parse_payload(result)
    if name in ARXIV_SEARCH_TOOLS:
        state["search_payload"] = payload
    if name in GITHUB_TOOLS:
        compact = compact_tool_data(name, payload)
        state["contributors"] = compact if isinstance(compact, list) else []
    receipt = mcp_receipt(
        name, result, payload, arguments=args,
        latency_seconds=round(time.perf_counter() - started, 3),
    )
    success = receipt["success"]
    if name in CODE_TOOLS and isinstance(payload.get("data"), dict):
        success = success and payload["data"].get("returncode") == 0
        receipt["success"] = success
    state["receipts"].append(receipt)
    return {"tool": name, "success": success, "data": compact_tool_data(name, payload)}


def append_history(messages: list[dict[str, str]], history: list[dict[str, Any]],
                   role: str, content: str, *, turn: int, event: str,
                   available: set[str] | None = None,
                   extra: dict[str, Any] | None = None) -> None:
    """Append one immutable conversation event and a cumulative hash-chain receipt."""
    messages.append({"role": role, "content": content})
    content_hash = sha256_bytes(content.encode())
    prior = history[-1]["chain_sha256"] if history else "0" * 64
    row = {
        "sequence": len(history),
        "turn": turn,
        "role": role,
        "event": event,
        "content_sha256": content_hash,
        "content_tokens": count_tokens(content),
        "available_tools": sorted(available) if available is not None else None,
        "status_bar_present": "[STATUS BAR: available tools =" in content,
        "chain_sha256": sha256_bytes(
            f"{prior}:{role}:{event}:{turn}:{content_hash}".encode()
        ),
    }
    row.update(extra or {})
    history.append(row)


async def run_agent_task(session: ClientSession, schemas: list[dict[str, Any]],
                         index: LocalEmbeddingIndex, strategy: str,
                         task: dict[str, Any], task_dir: Path) -> dict[str, Any]:
    """One genuine multi-turn loop; only initial schema exposure differs by group."""
    by_name = {schema["name"]: schema for schema in schemas}
    all_schema_text = render_schemas(schemas)
    if strategy == "control":
        system = (f"You are Qwen3-4B in the full-schema control. The perception MCP server exposed "
                  f"{len(schemas)} complete tools.\n\n{all_schema_text}\n\n{_AGENT_PROTOCOL}")
        available = set(by_name)
    else:
        base_schemas = [by_name[name] for name in sorted(BASE_TOOL_NAMES)]
        system = ("You are Qwen3-4B in the active-discovery treatment. Initially only the three "
                  "schemas below exist. Discover a specialist only when you encounter that capability "
                  "gap. Previously discovered schema blocks stay at their original history position.\n\n" +
                  TREATMENT_GUIDANCE + "\n\n" +
                  render_schemas(base_schemas + [DISCOVER_SCHEMA]) + "\n\n" + _AGENT_PROTOCOL)
        available = set(BASE_TOOL_NAMES)
    initial_schema_names = sorted(available | ({"discover_tools"} if strategy == "treatment" else set()))
    messages: list[dict[str, str]] = []
    history: list[dict[str, Any]] = []
    append_history(messages, history, "system", system, turn=0,
                   event="initial_system_prompt", available=available,
                   extra={"schema_names": initial_schema_names})
    append_history(
        messages, history, "user",
        f"Task: {task['prompt']}\n[STATUS BAR: available tools = {sorted(available)}]",
        turn=0, event="task_prompt", available=available,
    )
    state: dict[str, Any] = {"receipts": [], "search_payload": None, "contributors": []}
    actions: list[dict[str, Any]] = []
    discoveries: list[dict[str, Any]] = []
    interactions: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    final_answer = ""
    started = time.perf_counter()
    for turn in range(1, 13):
        response = await ollama_chat(messages)
        action, parse_error = parse_action(response)
        interactions.append({"turn": turn, "response": response,
                             "action": action, "parse_error": parse_error})
        append_history(messages, history, "assistant", response["content"], turn=turn,
                       event="model_response", available=available)
        if parse_error or action is None:
            parse_errors.append(parse_error or "unknown parse error")
            append_history(
                messages, history, "user",
                f"Protocol error: {parse_error}. Return exactly one valid JSON action. "
                f"[STATUS BAR: available tools = {sorted(available)}]",
                turn=turn, event="protocol_error", available=available,
            )
            continue
        if action["action"] == "finish":
            completion_probe = _finalize_execution(task, state, task_dir)
            if not completion_probe["task_complete"]:
                successful = {
                    receipt.get("tool")
                    for receipt in state["receipts"]
                    if receipt.get("success") is True
                }
                missing_count = sum(
                    not bool(successful & slot) for slot in task["slots"]
                )
                append_history(
                    messages,
                    history,
                    "user",
                    "Finish rejected: one or more requested subtasks still lack "
                    f"a successful specialist observation or required artifact "
                    f"(missing capability slots: {missing_count}). "
                    "Use discover_tools for each remaining capability gap, then "
                    "execute the discovered specialist before finishing. "
                    f"[STATUS BAR: available tools = {sorted(available)}]",
                    turn=turn,
                    event="premature_finish_rejected",
                    available=available,
                    extra={"missing_capability_slots": missing_count},
                )
                continue
            final_answer = action["answer"]
            break
        if action["action"] == "discover_tools":
            if strategy != "treatment":
                append_history(
                    messages, history, "user",
                    "discover_tools is unavailable in the control; choose a listed tool.",
                    turn=turn, event="control_discovery_error", available=available,
                )
                continue
            hits = index.search(action["need"], DISCOVERY_TOP_K)
            hit_schemas = [hit["schema"] for hit in hits]
            block = render_schemas(hit_schemas)
            names = [schema["name"] for schema in hit_schemas]
            available.update(names)
            discovery = {"turn": turn, "need": action["need"], "top_k": len(hits),
                         "matches": [{"name": hit["schema"]["name"], "score": hit["score"]}
                                     for hit in hits],
                         "schemas_sha256": sha256_bytes(block.encode()),
                         "schema_tokens": count_tokens(block)}
            discoveries.append(discovery)
            # This user-history item remains at this exact turn for all later requests.
            append_history(
                messages, history, "user",
                f"discover_tools returned these {len(hits)} complete MCP schemas:\n{block}\n\n"
                f"[STATUS BAR: available tools = {sorted(available)}]",
                turn=turn, event="schema_injection", available=available,
                extra={"schema_names": names, "schema_count": len(hit_schemas),
                       "schemas_sha256": discovery["schemas_sha256"],
                       "schema_tokens": discovery["schema_tokens"]},
            )
            continue
        name = action["tool"]
        actions.append(action)
        if name not in available:
            state["receipts"].append({"tool": name, "success": False,
                                      "error": "tool was not available at this turn"})
            hint = ("Call discover_tools for this missing capability first."
                    if strategy == "treatment" else "Choose an exact name from the full catalog.")
            append_history(
                messages, history, "user",
                f"Tool error: {name} is unavailable. {hint} "
                f"[STATUS BAR: available tools = {sorted(available)}]",
                turn=turn, event="unavailable_tool", available=available,
            )
            continue
        observation = await _call_real_tool(session, task, action, task_dir, state)
        append_history(
            messages, history, "user",
            "Real MCP observation:\n" +
            json.dumps(observation, ensure_ascii=False, default=str)[:50000] +
            f"\n[STATUS BAR: available tools = {sorted(available)}]",
            turn=turn, event="mcp_observation", available=available,
            extra={"tool": name, "success": bool(observation.get("success"))},
        )
    grade = grade_plan(task, actions)
    execution = _finalize_execution(task, state, task_dir)
    execution["agent_finished"] = bool(final_answer.strip())
    execution["task_complete"] = execution["task_complete"] and execution["agent_finished"]
    return {
        "task": task["id"], "strategy": strategy, "model": MODEL,
        "prompt": task["prompt"], "actions": actions, "parse_errors": parse_errors,
        "discoveries": discoveries, "grade": grade, "execution": execution,
        "final_answer": final_answer, "interactions": interactions,
        "history_receipt": {
            "events": history,
            "event_count": len(history),
            "final_chain_sha256": history[-1]["chain_sha256"],
            "dynamic_schema_injection_tokens": sum(
                row.get("schema_tokens", 0) for row in history
                if row["event"] == "schema_injection"
            ),
        },
        "initial_schema_names": initial_schema_names,
        "catalog_sha256": sha256_bytes(canonical_json(schemas).encode()),
        "runtime": {"name": "ollama", "model": MODEL,
                    "url": OLLAMA_URL, "options": OLLAMA_OPTIONS},
        "system_prompt_sha256": sha256_bytes(system.encode()),
        "system_prompt_tokens": count_tokens(system),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


async def run_group(session: ClientSession, schemas: list[dict[str, Any]],
                    index: LocalEmbeddingIndex, strategy: str,
                    campaign_dir: Path, *, resume: bool = False) -> list[dict[str, Any]]:
    records = []
    for task in TASKS:
        task_dir = campaign_dir / strategy / task["id"]
        task_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = task_dir / "receipt.json"
        if resume and receipt_path.exists():
            record = json.loads(receipt_path.read_text(encoding="utf-8"))
            if (
                record.get("strategy") != strategy
                or record.get("task") != task["id"]
                or record.get("model") != MODEL
            ):
                raise RuntimeError(f"incompatible completed task receipt: {receipt_path}")
            if record.get("execution", {}).get("task_complete") is True:
                records.append(record)
                continue

            # A formal campaign may make one bounded recovery attempt for an
            # incomplete task after a real provider failure. Preserve the
            # entire first attempt (receipt plus any partial artifacts) inside
            # the same campaign before retrying from a clean task directory.
            # Refuse a third attempt rather than silently cycling forever.
            failed_attempts = task_dir / "failed_attempts"
            archive_dir = failed_attempts / "attempt-1"
            if archive_dir.exists():
                raise RuntimeError(
                    f"maximum two real attempts exhausted for incomplete task: {task_dir}"
                )
            archive_dir.mkdir(parents=True)
            for child in list(task_dir.iterdir()):
                if child == failed_attempts:
                    continue
                child.replace(archive_dir / child.name)
        record = await run_agent_task(session, schemas, index, strategy, task, task_dir)
        write_json(receipt_path, record)
        records.append(record)
    return records


def safe_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_strategy = {}
    for strategy in ("control", "treatment"):
        rows = [record for record in records if record["strategy"] == strategy]
        by_strategy[strategy] = {
            "tasks": len(rows),
            "mean_tool_selection_accuracy": (
                sum(row["grade"]["accuracy"] for row in rows) / len(rows) if rows else 0
            ),
            "tasks_with_all_required_capabilities": sum(
                bool(row["grade"]["all_required_capabilities_selected"]) for row in rows
            ),
            "tasks_completed": sum(bool(row["execution"]["task_complete"]) for row in rows),
            "elapsed_seconds": round(sum(row["elapsed_seconds"] for row in rows), 3),
        }
    return by_strategy


def _history_chain_valid(record: dict[str, Any]) -> bool:
    events = record.get("history_receipt", {}).get("events", [])
    prior = "0" * 64
    for sequence, row in enumerate(events):
        if row.get("sequence") != sequence:
            return False
        expected = sha256_bytes(
            f"{prior}:{row.get('role')}:{row.get('event')}:{row.get('turn')}:"
            f"{row.get('content_sha256')}".encode()
        )
        if row.get("chain_sha256") != expected:
            return False
        prior = expected
    return bool(events) and record.get("history_receipt", {}).get(
        "final_chain_sha256"
    ) == prior


def _required_receipts_real(record: dict[str, Any], task: dict[str, Any]) -> bool:
    receipts = record.get("execution", {}).get("receipts", [])

    def valid(receipt: dict[str, Any]) -> bool:
        provenance = receipt.get("backend_provenance", {})
        return (
            receipt.get("success") is True
            and receipt.get("transport") == "mcp-stdio"
            and receipt.get("mcp_result_is_error") is False
            and bool(provenance.get("backend"))
            and provenance.get("origin") in {"live-api", "local-process"}
            and receipt.get("simulation_markers") == []
            and receipt.get("substantive_observation") is True
            and isinstance(receipt.get("payload"), dict)
            and receipt["payload"].get("success") is True
        )

    for slot in task["slots"]:
        if not any(receipt.get("tool") in slot and valid(receipt) for receipt in receipts):
            return False
    if task["id"] == "transformer_arxiv_download":
        downloads = [receipt for receipt in receipts
                     if receipt.get("tool") == "arxiv_download" and valid(receipt)]
        if len(downloads) != 3 or len({row.get("paper_id") for row in downloads}) != 3:
            return False
    return True


def derive_acceptance(records: list[dict[str, Any]], schemas: list[dict[str, Any]],
                      catalog: dict[str, Any], protocol: dict[str, Any],
                      comparison: dict[str, Any],
                      embedding: dict[str, Any]) -> dict[str, Any]:
    """Derive every acceptance claim from durable campaign receipts."""
    task_by_id = {task["id"]: task for task in TASKS}
    expected_pairs = {(strategy, task["id"])
                      for strategy in ("control", "treatment") for task in TASKS}
    actual_pairs = [(row.get("strategy"), row.get("task")) for row in records]
    exact_six = len(actual_pairs) == 6 and set(actual_pairs) == expected_pairs \
        and len(set(actual_pairs)) == len(actual_pairs)
    schema_by_name = {schema["name"]: schema for schema in schemas}
    catalog_hash = sha256_bytes(canonical_json(schemas).encode())

    qwen_receipts = bool(records) and all(
        row.get("model") == MODEL
        and row.get("runtime", {}).get("name") == "ollama"
        and row.get("runtime", {}).get("model") == MODEL
        and bool(row.get("interactions"))
        and all(
            interaction.get("response", {}).get("response_model") == MODEL
            and interaction.get("response", {}).get("done") is True
            and bool(interaction.get("response", {}).get("request_hash"))
            and bool(interaction.get("response", {}).get("content", "").strip())
            for interaction in row.get("interactions", [])
        )
        for row in records
    )

    real_execution = exact_six and all(
        row.get("task") in task_by_id
        and _required_receipts_real(row, task_by_id[row["task"]])
        for row in records
    )
    completed_with_artifacts = exact_six and all(
        row.get("execution", {}).get("task_complete") is True
        and row.get("execution", {}).get("agent_finished") is True
        and bool(row.get("final_answer", "").strip())
        for row in records
    )

    treatment_rows = [row for row in records if row.get("strategy") == "treatment"]
    treatment_discovery = len(treatment_rows) == 3
    dynamic_token_totals = []
    for row in treatment_rows:
        discoveries = row.get("discoveries", [])
        events = [event for event in row.get("history_receipt", {}).get("events", [])
                  if event.get("event") == "schema_injection"]
        dynamic_tokens = row.get("history_receipt", {}).get(
            "dynamic_schema_injection_tokens", -1
        )
        dynamic_token_totals.append(dynamic_tokens)
        if not discoveries or len(events) != len(discoveries) or not _history_chain_valid(row):
            treatment_discovery = False
            continue
        if set(row.get("initial_schema_names", [])) != {
            "web_search", "code_interpreter", "discover_tools"
        }:
            treatment_discovery = False
        cumulative = {"web_search", "code_interpreter"}
        for discovery, event in zip(discoveries, events):
            names = [match.get("name") for match in discovery.get("matches", [])]
            resolved = [schema_by_name.get(name) for name in names]
            if any(schema is None for schema in resolved):
                treatment_discovery = False
                continue
            expected_block = render_schemas(resolved)
            cumulative.update(names)
            conditions = [
                3 <= discovery.get("top_k", 0) <= 5,
                discovery.get("top_k") == len(names),
                event.get("role") == "user",
                event.get("turn") == discovery.get("turn"),
                event.get("schema_names") == names,
                event.get("schema_count") == len(names),
                event.get("schemas_sha256") == sha256_bytes(expected_block.encode()),
                discovery.get("schemas_sha256") == sha256_bytes(expected_block.encode()),
                event.get("schema_tokens") == count_tokens(expected_block),
                discovery.get("schema_tokens") == count_tokens(expected_block),
                event.get("status_bar_present") is True,
                set(event.get("available_tools") or []) == cumulative,
            ]
            if not all(conditions):
                treatment_discovery = False
        if dynamic_tokens != sum(item.get("schema_tokens", 0) for item in discoveries) \
                or dynamic_tokens <= 0:
            treatment_discovery = False

    control_rows = [row for row in records if row.get("strategy") == "control"]
    full_control_catalog = len(control_rows) == 3 and all(
        set(row.get("initial_schema_names", [])) == set(schema_by_name)
        and row.get("system_prompt_tokens", 0) > protocol["minimum_control_schema_tokens"]
        for row in control_rows
    )
    identical_runtime = exact_six and all(
        row.get("catalog_sha256") == catalog_hash
        and row.get("runtime") == records[0].get("runtime")
        and row.get("model") == records[0].get("model") == protocol["model"]
        and row.get("prompt") == next(
            task["prompt"] for task in TASKS if task["id"] == row.get("task")
        )
        for row in records
    )
    comparison_present = set(comparison) == {"control", "treatment"} and all(
        set(comparison[strategy]) >= {
            "tasks", "mean_tool_selection_accuracy",
            "tasks_with_all_required_capabilities", "tasks_completed", "elapsed_seconds"
        } and comparison[strategy]["tasks"] == 3
        for strategy in ("control", "treatment")
    )
    embedding_real = (
        embedding.get("model") == "sentence-transformers/all-MiniLM-L6-v2"
        and embedding.get("backend") == "local-transformers-mean-pooling"
        and embedding.get("local_files_only") is True
        and embedding.get("catalog_text_count") == len(schemas)
        and embedding.get("vector_count") == len(schemas)
        and embedding.get("vector_dimensions", 0) > 0
        and bool(embedding.get("texts_sha256"))
        and bool(embedding.get("cache_sha256"))
    )
    gates = {
        "exact_model_with_qwen_response_receipts": qwen_receipts,
        "catalog_from_mcp_and_hash_matches": (
            catalog.get("transport") == "mcp-stdio"
            and catalog.get("tools_list_received") is True
            and catalog.get("schema_sha256") == catalog_hash
            and catalog.get("tool_count") == len(schemas)
            and catalog.get("unique_tool_count") == len(schema_by_name)
            and all(catalog.get("required_tools_present", {}).values())
            and catalog.get("catalog_gzip_bytes", 0) > 0
            and len(catalog.get("catalog_gzip_sha256", "")) == 64
            and catalog.get("catalog_gzip_content_sha256") == catalog_hash
        ),
        "tool_count_at_least_120": len(schemas) >= protocol["minimum_mcp_tools"],
        "control_over_50k_complete_schema_tokens": (
            catalog.get("schema_tokens_o200k", 0)
            > protocol["minimum_control_schema_tokens"] and full_control_catalog
        ),
        "three_tasks_each_group": exact_six,
        "real_mcp_execution_only": real_execution,
        "all_tasks_completed_with_required_artifacts": completed_with_artifacts,
        "treatment_discovery_history_and_status_verified": treatment_discovery,
        "identical_tasks_model_runtime_and_catalog": identical_runtime,
        "local_embedding_index_receipted": embedding_real,
        "dynamic_schema_injection_tokens_recorded": (
            len(dynamic_token_totals) == 3 and all(value > 0 for value in dynamic_token_totals)
        ),
        "comparison_metrics_present_for_both_arms": comparison_present,
    }
    return {"status": "passed" if all(gates.values()) else "failed", "gates": gates}


def build_manifest(campaign_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(campaign_dir.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        data = path.read_bytes()
        files.append({"path": str(path.relative_to(campaign_dir)), "bytes": len(data),
                      "sha256": sha256_bytes(data)})
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "files": files}


async def run(campaign_id: str | None = None, *, resume: bool = False) -> Path:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    campaign_id = campaign_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    campaign_dir = VALIDATION_ROOT / campaign_id
    if resume:
        if not campaign_dir.is_dir():
            raise RuntimeError(f"resume campaign does not exist: {campaign_dir}")
        summary_path = campaign_dir / "summary.json"
        manifest_path = campaign_dir / "manifest.json"
        if summary_path.exists() or manifest_path.exists():
            if not (summary_path.is_file() and manifest_path.is_file()):
                raise RuntimeError(
                    f"resume campaign has only one final artifact: {campaign_dir}"
                )
            failed_summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if failed_summary.get("status") != "failed":
                raise RuntimeError(f"resume campaign already passed: {campaign_dir}")
            campaign_attempts = campaign_dir / "failed_campaign_attempts"
            attempt_dir = campaign_attempts / "attempt-1"
            if attempt_dir.exists():
                raise RuntimeError(
                    f"maximum two real campaign attempts exhausted: {campaign_dir}"
                )
            attempt_dir.mkdir(parents=True)
            summary_path.replace(attempt_dir / "summary.failed.json")
            manifest_path.replace(attempt_dir / "manifest.failed.json")
        recorded_protocol = json.loads(
            (campaign_dir / "protocol.json").read_text(encoding="utf-8")
        )
        if recorded_protocol != protocol:
            raise RuntimeError("resume protocol differs from the preserved campaign protocol")
    else:
        campaign_dir.mkdir(parents=True, exist_ok=False)
        write_json(campaign_dir / "protocol.json", protocol)

    params = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER)], env=os.environ.copy())
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            initialize = await session.initialize()
            listed = await session.list_tools()
            schemas = [schema_dict(tool) for tool in listed.tools]
            schema_bytes = canonical_json(schemas).encode()
            schema_text = render_schemas(schemas)
            catalog = {
                "transport": "mcp-stdio", "server": str(MCP_SERVER),
                "tools_list_received": True,
                "server_name": initialize.serverInfo.name,
                "server_version": initialize.serverInfo.version,
                "tool_count": len(schemas), "unique_tool_count": len({s["name"] for s in schemas}),
                "schema_tokens_o200k": count_tokens(schema_text),
                "schema_bytes": len(schema_bytes), "schema_sha256": sha256_bytes(schema_bytes),
                "required_tools_present": {
                    name: name in {schema["name"] for schema in schemas}
                    for name in ["web_search", "code_interpreter", "yfinance_quote", "search_news",
                                 "arxiv_search", "arxiv_download", "github_list_contributors"]
                },
            }
            if catalog["tool_count"] < protocol["minimum_mcp_tools"]:
                raise RuntimeError(f"MCP catalog too small: {catalog['tool_count']}")
            if catalog["schema_tokens_o200k"] <= protocol["minimum_control_schema_tokens"]:
                raise RuntimeError(f"control schema prompt too small: {catalog['schema_tokens_o200k']}")
            if not all(catalog["required_tools_present"].values()):
                raise RuntimeError("required task tools missing from MCP catalog")
            gzip_path = campaign_dir / "catalog.schemas.json.gz"
            catalog_receipt_path = campaign_dir / "catalog_receipt.json"
            if resume:
                preserved_catalog = json.loads(catalog_receipt_path.read_text(encoding="utf-8"))
                current_fields = {
                    key: catalog[key]
                    for key in (
                        "transport", "server", "tools_list_received", "server_name",
                        "server_version", "tool_count", "unique_tool_count",
                        "schema_tokens_o200k", "schema_bytes", "schema_sha256",
                        "required_tools_present",
                    )
                }
                if any(preserved_catalog.get(key) != value
                       for key, value in current_fields.items()):
                    raise RuntimeError("resume MCP catalog differs from preserved catalog receipt")
                if (
                    not gzip_path.is_file()
                    or gzip_path.stat().st_size != preserved_catalog.get("catalog_gzip_bytes")
                    or sha256_bytes(gzip_path.read_bytes())
                    != preserved_catalog.get("catalog_gzip_sha256")
                ):
                    raise RuntimeError("resume schema gzip does not match preserved catalog receipt")
                with gzip.open(gzip_path, "rt", encoding="utf-8") as stream:
                    gzip_schemas = json.load(stream)
                if sha256_bytes(canonical_json(gzip_schemas).encode()) != catalog["schema_sha256"]:
                    raise RuntimeError("resume schema gzip content does not match current MCP catalog")
                catalog = preserved_catalog
            else:
                with gzip.open(gzip_path, "wt", encoding="utf-8") as stream:
                    json.dump(schemas, stream, ensure_ascii=False)
                catalog["catalog_gzip_bytes"] = gzip_path.stat().st_size
                catalog["catalog_gzip_sha256"] = sha256_bytes(gzip_path.read_bytes())
                with gzip.open(gzip_path, "rt", encoding="utf-8") as stream:
                    gzip_schemas = json.load(stream)
                catalog["catalog_gzip_content_sha256"] = sha256_bytes(
                    canonical_json(gzip_schemas).encode()
                )
                write_json(catalog_receipt_path, catalog)

            index = await asyncio.to_thread(LocalEmbeddingIndex, schemas, campaign_dir / "index")
            embedding_receipt = index.receipt()
            embedding_receipt_path = campaign_dir / "embedding_receipt.json"
            if resume:
                preserved_embedding = json.loads(
                    embedding_receipt_path.read_text(encoding="utf-8")
                )
                if preserved_embedding != embedding_receipt:
                    raise RuntimeError("resume embedding index differs from preserved receipt")
            else:
                write_json(embedding_receipt_path, embedding_receipt)
            control = await run_group(
                session, schemas, index, "control", campaign_dir, resume=resume
            )
            treatment = await run_group(
                session, schemas, index, "treatment", campaign_dir, resume=resume
            )
            records = control + treatment
            comparison = safe_summary(records)
            acceptance = derive_acceptance(
                records, schemas, catalog, protocol, comparison, embedding_receipt
            )
            summary = {
                "experiment": "4-7", "campaign_id": campaign_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": MODEL, "catalog": catalog,
                "embedding": embedding_receipt,
                "comparison": comparison,
                "dynamic_schema_injection_tokens": {
                    row["task"]: row["history_receipt"]["dynamic_schema_injection_tokens"]
                    for row in treatment
                },
                "acceptance": acceptance,
                "status": acceptance["status"],
            }
            write_json(campaign_dir / "summary.json", summary)
    write_json(campaign_dir / "manifest.json", build_manifest(campaign_dir))
    return campaign_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an interrupted campaign after validating all preserved setup receipts.",
    )
    args = parser.parse_args()
    if args.resume and not args.campaign_id:
        parser.error("--resume requires --campaign-id")
    path = asyncio.run(run(args.campaign_id, resume=args.resume))
    print(path)


if __name__ == "__main__":
    main()
