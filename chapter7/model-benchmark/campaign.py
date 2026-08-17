#!/usr/bin/env python3
"""Full Experiment 7-10 campaign runner.

This is the long-form, resumable experiment described by the book.  It stores
every real request in SQLite so a 168-hour availability campaign or a large
100-request workload matrix can be resumed without losing completed cells.
There is deliberately no synthetic fallback in this runner; ``demo.py --mock``
remains a separate educational check and can never populate this database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from openai import OpenAI


HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "campaign_config.json"
DEFAULT_DB = HERE / "results" / "campaign.sqlite3"
PROMPT_SCHEMA_VERSION = "experiment-7-10-standard-workload-v2"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def execution_config_fingerprint(config: dict[str, Any]) -> str:
    """Bind request semantics while permitting price/reference-only re-analysis."""
    providers = []
    for raw in config["providers"]:
        providers.append({
            key: value
            for key, value in raw.items()
            if key != "pricing"
        })
    payload = {
        "prompt_schema_version": PROMPT_SCHEMA_VERSION,
        "providers": providers,
        "workload": config["workload"],
        "availability": config["availability"],
        "rate_limit": config["rate_limit"],
        "agent_cost": config["agent_cost"],
    }
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reference_token_count(text: str) -> int:
    import tiktoken

    return len(tiktoken.get_encoding("cl100k_base").encode(text))


@dataclass(frozen=True)
class Price:
    """Authoritative native-currency price and optional dated USD conversion.

    Keeping the provider's published currency is deliberate.  A CNY price must
    never be placed in a field labelled USD merely to make the analysis run.
    Non-USD prices become comparable in USD only when the configuration also
    pins a dated conversion rate and its source.
    """

    input_per_million: float | None = None
    cached_input_per_million: float | None = None
    output_per_million: float | None = None
    currency: str | None = None
    source_url: str | None = None
    as_of: str | None = None
    usd_per_currency_unit: float | None = None
    fx_source_url: str | None = None
    fx_as_of: str | None = None
    status: str = "unresolved"
    blocker: str | None = None

    @property
    def native_rates_complete(self) -> bool:
        return all(
            value is not None
            for value in (
                self.input_per_million,
                self.cached_input_per_million,
                self.output_per_million,
            )
        ) and bool(self.currency and self.source_url and self.as_of)

    @property
    def usd_conversion_complete(self) -> bool:
        if not self.native_rates_complete:
            return False
        if self.currency == "USD":
            return True
        return (
            self.usd_per_currency_unit is not None
            and self.usd_per_currency_unit > 0
            and bool(self.fx_source_url and self.fx_as_of)
        )


@dataclass(frozen=True)
class Provider:
    name: str
    model: str
    api_key_env: str
    base_url: str = ""
    protocol: str = "openai"
    thinking_budget_tokens: int = 0
    model_family: str | None = None
    access_class: str | None = None
    extra_body: dict[str, Any] | None = None
    max_output_field: str = "max_tokens"
    pricing: Price = field(default_factory=Price)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Provider":
        pricing = Price(**data.pop("pricing", {}))
        return cls(**data, pricing=pricing)

    def api_key(self) -> str:
        key = os.getenv(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"{self.name} requires {self.api_key_env}")
        return key

    def client(self) -> OpenAI:
        if self.protocol == "openai":
            return OpenAI(
                api_key=self.api_key(),
                base_url=self.base_url or None,
                timeout=300,
                max_retries=0,
            )
        if self.protocol == "anthropic":
            from anthropic import Anthropic

            return Anthropic(api_key=self.api_key(), timeout=300, max_retries=0)
        if self.protocol == "gemini":
            from google import genai

            return genai.Client(api_key=self.api_key())
        raise ValueError(f"Unsupported provider protocol: {self.protocol}")


@dataclass
class Observation:
    campaign_id: str
    phase: str
    cell_id: str
    provider: str
    model: str
    scheduled_at_utc: str | None
    started_at_utc: str
    ended_at_utc: str
    target_context_tokens: int
    target_output_tokens: int
    concurrency: int
    request_index: int
    ok: bool
    status_code: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    ttft_s: float | None = None
    e2e_s: float | None = None
    thinking_ttft_s: float | None = None
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    visible_output_tokens: int = 0
    reasoning_tokens: int = 0
    prompt_sha256: str | None = None
    output_sha256: str | None = None
    output_text: str | None = None
    finish_reason: str | None = None
    request_id: str | None = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    cell_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    scheduled_at_utc TEXT,
    started_at_utc TEXT NOT NULL,
    ended_at_utc TEXT NOT NULL,
    target_context_tokens INTEGER NOT NULL,
    target_output_tokens INTEGER NOT NULL,
    concurrency INTEGER NOT NULL,
    request_index INTEGER NOT NULL,
    ok INTEGER NOT NULL,
    status_code INTEGER,
    error_type TEXT,
    error_message TEXT,
    ttft_s REAL,
    e2e_s REAL,
    thinking_ttft_s REAL,
    input_tokens INTEGER NOT NULL,
    cached_input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    visible_output_tokens INTEGER NOT NULL DEFAULT 0,
    reasoning_tokens INTEGER NOT NULL,
    prompt_sha256 TEXT,
    output_sha256 TEXT,
    output_text TEXT,
    finish_reason TEXT,
    request_id TEXT
);
CREATE INDEX IF NOT EXISTS observations_grouping
ON observations(campaign_id, phase, provider, model);
CREATE INDEX IF NOT EXISTS observations_probe_time
ON observations(campaign_id, phase, provider, scheduled_at_utc);

CREATE TABLE IF NOT EXISTS batches (
    batch_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    target_context_tokens INTEGER NOT NULL,
    target_output_tokens INTEGER NOT NULL,
    concurrency INTEGER NOT NULL,
    requested INTEGER NOT NULL,
    succeeded INTEGER NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    wall_s REAL NOT NULL,
    started_at_utc TEXT NOT NULL,
    ended_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campaign_metadata (
    campaign_id TEXT PRIMARY KEY,
    execution_config_fingerprint TEXT NOT NULL,
    prompt_schema_version TEXT NOT NULL,
    config_json TEXT NOT NULL,
    created_at_utc TEXT NOT NULL
);
"""


class CampaignStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.connection.executescript(SCHEMA)
        existing = {
            row[1] for row in self.connection.execute("PRAGMA table_info(observations)")
        }
        migrations = {
            "visible_output_tokens": "INTEGER NOT NULL DEFAULT 0",
            "prompt_sha256": "TEXT",
            "output_text": "TEXT",
        }
        for name, declaration in migrations.items():
            if name not in existing:
                self.connection.execute(
                    f"ALTER TABLE observations ADD COLUMN {name} {declaration}"
                )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def has(self, cell_id: str) -> bool:
        with self.lock:
            row = self.connection.execute(
                "SELECT 1 FROM observations WHERE cell_id = ?", (cell_id,)
            ).fetchone()
        return row is not None

    def bind_campaign(self, campaign_id: str, config: dict[str, Any]) -> str:
        fingerprint = execution_config_fingerprint(config)
        encoded = json.dumps(config, sort_keys=True, ensure_ascii=False)
        with self.lock:
            row = self.connection.execute(
                "SELECT execution_config_fingerprint FROM campaign_metadata WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()
            if row and row[0] != fingerprint:
                raise RuntimeError(
                    f"campaign '{campaign_id}' is bound to execution fingerprint {row[0]}, "
                    f"not {fingerprint}; use a new campaign id or the original execution config"
                )
            self.connection.execute(
                """
                INSERT OR IGNORE INTO campaign_metadata
                (campaign_id, execution_config_fingerprint, prompt_schema_version, config_json, created_at_utc)
                VALUES (?, ?, ?, ?, ?)
                """,
                (campaign_id, fingerprint, PROMPT_SCHEMA_VERSION, encoded, utc_now()),
            )
            self.connection.commit()
        return fingerprint

    def add(self, observation: Observation) -> None:
        payload = asdict(observation)
        payload["ok"] = int(observation.ok)
        columns = ", ".join(payload)
        placeholders = ", ".join("?" for _ in payload)
        with self.lock:
            self.connection.execute(
                f"INSERT OR IGNORE INTO observations ({columns}) VALUES ({placeholders})",
                tuple(payload.values()),
            )
            self.connection.commit()

    def add_batch(self, payload: dict[str, Any]) -> None:
        columns = ", ".join(payload)
        placeholders = ", ".join("?" for _ in payload)
        with self.lock:
            self.connection.execute(
                f"""
                INSERT INTO batches ({columns}) VALUES ({placeholders})
                ON CONFLICT(batch_id) DO UPDATE SET
                    requested = batches.requested + excluded.requested,
                    succeeded = batches.succeeded + excluded.succeeded,
                    input_tokens = batches.input_tokens + excluded.input_tokens,
                    output_tokens = batches.output_tokens + excluded.output_tokens,
                    wall_s = batches.wall_s + excluded.wall_s,
                    ended_at_utc = excluded.ended_at_utc
                """,
                tuple(payload.values()),
            )
            self.connection.commit()


class PromptFactory:
    """Build deterministic content with a measured tokenizer length."""

    def __init__(self):
        try:
            import tiktoken

            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:  # pragma: no cover - dependency error is actionable
            raise RuntimeError("Install tiktoken from requirements.txt") from exc

    def build(self, target_tokens: int, output_tokens: int) -> str:
        instruction = (
            "You are running a controlled throughput benchmark. Read all context. "
            f"Return exactly {output_tokens} tokens of plain analytical prose; do not use markdown. "
            "End with the marker BENCHMARK_DONE.\n\n"
        )
        end = "\n\nQuestion: Explain how stable context prefixes affect an Agent system."
        fixed = self.encoding.encode(instruction + end)
        if target_tokens < len(fixed) + 16:
            raise ValueError(
                f"target context {target_tokens} is too small; need at least {len(fixed) + 16}"
            )
        filler_id = self.encoding.encode(" measurement")[0]
        token_ids = self.encoding.encode(instruction)
        token_ids.extend([filler_id] * (target_tokens - len(fixed)))
        token_ids.extend(self.encoding.encode(end))
        text = self.encoding.decode(token_ids)
        # Token boundaries can merge at concatenation points. Correct until the
        # content length is exact for the declared reference tokenizer.
        for _ in range(8):
            actual = len(self.encoding.encode(text))
            if actual == target_tokens:
                return text
            if actual < target_tokens:
                text += self.encoding.decode([filler_id] * (target_tokens - actual))
            else:
                ids = self.encoding.encode(text)
                text = self.encoding.decode(ids[:target_tokens])
        actual = len(self.encoding.encode(text))
        if actual != target_tokens:
            raise RuntimeError(f"could not create exact {target_tokens}-token prompt (got {actual})")
        return text


def int_attr(value: Any, name: str) -> int:
    return int(getattr(value, name, 0) or 0) if value is not None else 0


def error_details(exc: Exception) -> tuple[int | None, str, str]:
    status = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status is None and response is not None:
        status = getattr(response, "status_code", None)
    message = str(exc)
    lower = message.casefold()
    if any(tag in lower for tag in ("insufficient_quota", "insufficient balance", "billing")):
        category = "quota_or_balance"
    elif status == 429 or "rate limit" in lower or "rate_limit" in lower:
        category = "rate_limit"
    elif status in {401, 403}:
        category = "authentication"
    elif status is not None and status >= 500:
        category = "provider_5xx"
    elif "timeout" in lower:
        category = "timeout"
    elif "connection" in lower or "network" in lower:
        category = "network"
    else:
        category = type(exc).__name__
    # Provider messages sometimes echo request metadata. Keep a bounded record.
    return status, category, message[:1000]


def measure_stream(
    provider: Provider,
    *,
    campaign_id: str,
    phase: str,
    cell_id: str,
    prompt: str,
    target_context_tokens: int,
    target_output_tokens: int,
    concurrency: int,
    request_index: int,
    scheduled_at_utc: str | None = None,
    client: Any | None = None,
) -> Observation:
    if provider.protocol == "anthropic":
        return measure_anthropic(
            provider,
            campaign_id=campaign_id,
            phase=phase,
            cell_id=cell_id,
            prompt=prompt,
            target_context_tokens=target_context_tokens,
            target_output_tokens=target_output_tokens,
            concurrency=concurrency,
            request_index=request_index,
            scheduled_at_utc=scheduled_at_utc,
            client=client,
        )
    if provider.protocol == "gemini":
        return measure_gemini(
            provider,
            campaign_id=campaign_id,
            phase=phase,
            cell_id=cell_id,
            prompt=prompt,
            target_context_tokens=target_context_tokens,
            target_output_tokens=target_output_tokens,
            concurrency=concurrency,
            request_index=request_index,
            scheduled_at_utc=scheduled_at_utc,
            client=client,
        )
    if provider.protocol != "openai":
        raise ValueError(f"Unsupported provider protocol: {provider.protocol}")
    started_wall = utc_now()
    started = time.perf_counter()
    first_content: float | None = None
    first_reasoning: float | None = None
    content: list[str] = []
    usage = None
    finish_reason = None
    request_id = None
    try:
        request: dict[str, Any] = dict(
            model=provider.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1 if any(tag in provider.model.casefold() for tag in ("kimi-", "gpt-5")) else 0,
            stream=True,
            stream_options={"include_usage": True},
            timeout=300,
        )
        request[provider.max_output_field] = target_output_tokens + provider.thinking_budget_tokens
        if provider.extra_body:
            request["extra_body"] = provider.extra_body
        stream = (client or provider.client()).chat.completions.create(**request)
        for chunk in stream:
            request_id = request_id or getattr(chunk, "id", None)
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            for choice in getattr(chunk, "choices", []) or []:
                finish_reason = getattr(choice, "finish_reason", None) or finish_reason
                delta = getattr(choice, "delta", None)
                reasoning = getattr(delta, "reasoning_content", None) if delta else None
                if reasoning and first_reasoning is None:
                    first_reasoning = time.perf_counter()
                piece = getattr(delta, "content", None) if delta else None
                if piece:
                    if first_content is None:
                        first_content = time.perf_counter()
                    content.append(piece)
        ended = time.perf_counter()
        if first_content is None:
            raise RuntimeError("empty response: no content token")
        prompt_details = getattr(usage, "prompt_tokens_details", None)
        completion_details = getattr(usage, "completion_tokens_details", None)
        text = "".join(content)
        reasoning_tokens = int_attr(completion_details, "reasoning_tokens")
        billed_output_tokens = int_attr(usage, "completion_tokens")
        return Observation(
            campaign_id=campaign_id,
            phase=phase,
            cell_id=cell_id,
            provider=provider.name,
            model=provider.model,
            scheduled_at_utc=scheduled_at_utc,
            started_at_utc=started_wall,
            ended_at_utc=utc_now(),
            target_context_tokens=target_context_tokens,
            target_output_tokens=target_output_tokens,
            concurrency=concurrency,
            request_index=request_index,
            ok=True,
            ttft_s=first_content - started,
            e2e_s=ended - started,
            thinking_ttft_s=(first_reasoning - started) if first_reasoning else None,
            input_tokens=int_attr(usage, "prompt_tokens"),
            cached_input_tokens=int_attr(prompt_details, "cached_tokens"),
            output_tokens=billed_output_tokens,
            visible_output_tokens=(
                max(0, billed_output_tokens - reasoning_tokens)
                if billed_output_tokens else reference_token_count(text)
            ),
            reasoning_tokens=reasoning_tokens,
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            output_sha256=hashlib.sha256(text.encode()).hexdigest(),
            output_text=text,
            finish_reason=finish_reason,
            request_id=request_id,
        )
    except Exception as exc:
        ended = time.perf_counter()
        status, error_type, message = error_details(exc)
        return Observation(
            campaign_id=campaign_id,
            phase=phase,
            cell_id=cell_id,
            provider=provider.name,
            model=provider.model,
            scheduled_at_utc=scheduled_at_utc,
            started_at_utc=started_wall,
            ended_at_utc=utc_now(),
            target_context_tokens=target_context_tokens,
            target_output_tokens=target_output_tokens,
            concurrency=concurrency,
            request_index=request_index,
            ok=False,
            status_code=status,
            error_type=error_type,
            error_message=message,
            e2e_s=ended - started,
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        )


def _failed_observation(
    provider: Provider,
    exc: Exception,
    *,
    campaign_id: str,
    phase: str,
    cell_id: str,
    scheduled_at_utc: str | None,
    started_at_utc: str,
    started: float,
    target_context_tokens: int,
    target_output_tokens: int,
    concurrency: int,
    request_index: int,
    prompt: str,
) -> Observation:
    status, error_type, message = error_details(exc)
    return Observation(
        campaign_id=campaign_id,
        phase=phase,
        cell_id=cell_id,
        provider=provider.name,
        model=provider.model,
        scheduled_at_utc=scheduled_at_utc,
        started_at_utc=started_at_utc,
        ended_at_utc=utc_now(),
        target_context_tokens=target_context_tokens,
        target_output_tokens=target_output_tokens,
        concurrency=concurrency,
        request_index=request_index,
        ok=False,
        status_code=status,
        error_type=error_type,
        error_message=message,
        e2e_s=time.perf_counter() - started,
        prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
    )


def measure_anthropic(
    provider: Provider,
    *,
    campaign_id: str,
    phase: str,
    cell_id: str,
    prompt: str,
    target_context_tokens: int,
    target_output_tokens: int,
    concurrency: int,
    request_index: int,
    scheduled_at_utc: str | None = None,
    client: Any | None = None,
) -> Observation:
    """Measure Anthropic's native streaming Messages API."""

    started_at = utc_now()
    started = time.perf_counter()
    first_content: float | None = None
    first_reasoning: float | None = None
    content: list[str] = []
    try:
        kwargs: dict[str, Any] = {
            "model": provider.model,
            "max_tokens": target_output_tokens + provider.thinking_budget_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if provider.thinking_budget_tokens:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": provider.thinking_budget_tokens,
            }
        else:
            kwargs["temperature"] = 0
        with (client or provider.client()).messages.stream(**kwargs) as stream:
            for event in stream:
                if getattr(event, "type", "") != "content_block_delta":
                    continue
                delta = getattr(event, "delta", None)
                delta_type = getattr(delta, "type", "")
                if delta_type == "thinking_delta" and first_reasoning is None:
                    first_reasoning = time.perf_counter()
                if delta_type == "text_delta" and getattr(delta, "text", ""):
                    if first_content is None:
                        first_content = time.perf_counter()
                    content.append(delta.text)
            final = stream.get_final_message()
        ended = time.perf_counter()
        if first_content is None:
            raise RuntimeError("empty response: no content token")
        usage = getattr(final, "usage", None)
        cached = int_attr(usage, "cache_read_input_tokens")
        reasoning_tokens = 0
        for block in getattr(final, "content", []) or []:
            if getattr(block, "type", "") == "thinking":
                # Native usage does not currently split thinking tokens. This
                # length is intentionally not estimated; latency is still exact.
                reasoning_tokens = int_attr(usage, "thinking_tokens")
        text = "".join(content)
        return Observation(
            campaign_id=campaign_id, phase=phase, cell_id=cell_id,
            provider=provider.name, model=provider.model,
            scheduled_at_utc=scheduled_at_utc, started_at_utc=started_at,
            ended_at_utc=utc_now(), target_context_tokens=target_context_tokens,
            target_output_tokens=target_output_tokens, concurrency=concurrency,
            request_index=request_index, ok=True,
            ttft_s=first_content - started, e2e_s=ended - started,
            thinking_ttft_s=(first_reasoning - started) if first_reasoning else None,
            input_tokens=int_attr(usage, "input_tokens") + int_attr(usage, "cache_creation_input_tokens") + cached,
            cached_input_tokens=cached,
            output_tokens=int_attr(usage, "output_tokens"),
            visible_output_tokens=reference_token_count(text),
            reasoning_tokens=reasoning_tokens,
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            output_sha256=hashlib.sha256(text.encode()).hexdigest(),
            output_text=text,
            finish_reason=str(getattr(final, "stop_reason", "") or ""),
            request_id=str(getattr(final, "id", "") or ""),
        )
    except Exception as exc:
        return _failed_observation(
            provider, exc, campaign_id=campaign_id, phase=phase, cell_id=cell_id,
            scheduled_at_utc=scheduled_at_utc, started_at_utc=started_at, started=started,
            target_context_tokens=target_context_tokens, target_output_tokens=target_output_tokens,
            concurrency=concurrency, request_index=request_index, prompt=prompt,
        )


def measure_gemini(
    provider: Provider,
    *,
    campaign_id: str,
    phase: str,
    cell_id: str,
    prompt: str,
    target_context_tokens: int,
    target_output_tokens: int,
    concurrency: int,
    request_index: int,
    scheduled_at_utc: str | None = None,
    client: Any | None = None,
) -> Observation:
    """Measure Google's native Gemini streaming API, including thought usage."""

    from google.genai import types

    started_at = utc_now()
    started = time.perf_counter()
    first_content: float | None = None
    first_reasoning: float | None = None
    content: list[str] = []
    usage = None
    finish_reason = None
    try:
        config: dict[str, Any] = {
            "max_output_tokens": target_output_tokens + provider.thinking_budget_tokens,
            "temperature": 0,
        }
        if provider.thinking_budget_tokens:
            config["thinking_config"] = types.ThinkingConfig(
                thinking_budget=provider.thinking_budget_tokens,
                include_thoughts=True,
            )
        active_client = client or provider.client()
        stream = active_client.models.generate_content_stream(
            model=provider.model,
            contents=prompt,
            config=types.GenerateContentConfig(**config),
        )
        for chunk in stream:
            usage = getattr(chunk, "usage_metadata", None) or usage
            candidates = getattr(chunk, "candidates", None) or []
            for candidate in candidates:
                finish_reason = getattr(candidate, "finish_reason", None) or finish_reason
                candidate_content = getattr(candidate, "content", None)
                for part in getattr(candidate_content, "parts", []) or []:
                    text = getattr(part, "text", None)
                    if not text:
                        continue
                    if getattr(part, "thought", False):
                        if first_reasoning is None:
                            first_reasoning = time.perf_counter()
                    else:
                        if first_content is None:
                            first_content = time.perf_counter()
                        content.append(text)
        ended = time.perf_counter()
        if first_content is None:
            raise RuntimeError("empty response: no content token")
        text = "".join(content)
        return Observation(
            campaign_id=campaign_id, phase=phase, cell_id=cell_id,
            provider=provider.name, model=provider.model,
            scheduled_at_utc=scheduled_at_utc, started_at_utc=started_at,
            ended_at_utc=utc_now(), target_context_tokens=target_context_tokens,
            target_output_tokens=target_output_tokens, concurrency=concurrency,
            request_index=request_index, ok=True,
            ttft_s=first_content - started, e2e_s=ended - started,
            thinking_ttft_s=(first_reasoning - started) if first_reasoning else None,
            input_tokens=int_attr(usage, "prompt_token_count"),
            cached_input_tokens=int_attr(usage, "cached_content_token_count"),
            output_tokens=int_attr(usage, "candidates_token_count") + int_attr(usage, "thoughts_token_count"),
            visible_output_tokens=int_attr(usage, "candidates_token_count"),
            reasoning_tokens=int_attr(usage, "thoughts_token_count"),
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            output_sha256=hashlib.sha256(text.encode()).hexdigest(),
            output_text=text,
            finish_reason=str(finish_reason or ""),
        )
    except Exception as exc:
        return _failed_observation(
            provider, exc, campaign_id=campaign_id, phase=phase, cell_id=cell_id,
            scheduled_at_utc=scheduled_at_utc, started_at_utc=started_at, started=started,
            target_context_tokens=target_context_tokens, target_output_tokens=target_output_tokens,
            concurrency=concurrency, request_index=request_index, prompt=prompt,
        )


def cell_id(*parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def run_batch(
    store: CampaignStore,
    provider: Provider,
    prompt_factory: PromptFactory,
    *,
    campaign_id: str,
    phase: str,
    context_tokens: int,
    output_tokens: int,
    requests: int,
    concurrency: int,
    slot: str = "",
) -> list[Observation]:
    prompt = prompt_factory.build(context_tokens, output_tokens)
    jobs: list[tuple[int, str]] = []
    for index in range(requests):
        identity = cell_id(
            campaign_id, phase, provider.name, provider.model,
            context_tokens, output_tokens, concurrency, slot, index,
        )
        if not store.has(identity):
            jobs.append((index, identity))
    if not jobs:
        return []
    started_at = utc_now()
    started = time.perf_counter()
    observations: list[Observation] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = {
            pool.submit(
                measure_stream,
                provider,
                campaign_id=campaign_id,
                phase=phase,
                cell_id=identity,
                prompt=prompt,
                target_context_tokens=context_tokens,
                target_output_tokens=output_tokens,
                concurrency=concurrency,
                request_index=index,
                scheduled_at_utc=slot or None,
            ): identity
            for index, identity in jobs
        }
        for future in as_completed(futures):
            observation = future.result()
            store.add(observation)
            observations.append(observation)
            state = "ok" if observation.ok else f"failed:{observation.error_type}"
            print(
                f"[{phase}] {provider.name} context={context_tokens} output={output_tokens} "
                f"c={concurrency} request={observation.request_index}: {state}",
                flush=True,
            )
    wall_s = time.perf_counter() - started
    batch_identity = cell_id(
        "batch", campaign_id, phase, provider.name, context_tokens,
        output_tokens, concurrency, slot,
    )
    store.add_batch({
        "batch_id": batch_identity,
        "campaign_id": campaign_id,
        "phase": phase,
        "provider": provider.name,
        "model": provider.model,
        "target_context_tokens": context_tokens,
        "target_output_tokens": output_tokens,
        "concurrency": concurrency,
        "requested": len(observations),
        "succeeded": sum(item.ok for item in observations),
        "input_tokens": sum(item.input_tokens for item in observations),
        "output_tokens": sum(item.output_tokens for item in observations),
        "wall_s": wall_s,
        "started_at_utc": started_at,
        "ended_at_utc": utc_now(),
    })
    return observations


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return expand_env(json.load(handle))


def providers_from_config(config: dict[str, Any], names: set[str] | None) -> list[Provider]:
    providers = []
    for raw in config["providers"]:
        provider = Provider.from_dict(dict(raw))
        if names and provider.name not in names:
            continue
        provider.api_key()  # fail before beginning an expensive campaign
        providers.append(provider)
    if not providers:
        raise RuntimeError("No provider selected")
    return providers


def run_workloads(
    store: CampaignStore,
    providers: Sequence[Provider],
    factory: PromptFactory,
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    workload = config["workload"]
    contexts = args.context_tokens or workload["context_tokens"]
    outputs = args.output_tokens or workload["output_tokens"]
    requests = args.requests if args.requests is not None else workload["requests_per_cell"]
    concurrency = args.concurrency or workload["concurrency"]
    if not args.smoke and requests < 100:
        raise RuntimeError("Official workload requires at least 100 requests per cell; use --smoke for smaller runs")
    for provider in providers:
        for context in contexts:
            for output in outputs:
                run_batch(
                    store, provider, factory,
                    campaign_id=args.campaign_id,
                    phase="workload",
                    context_tokens=context,
                    output_tokens=output,
                    requests=requests,
                    concurrency=concurrency,
                )


def run_rate_limit(
    store: CampaignStore,
    providers: Sequence[Provider],
    factory: PromptFactory,
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    rate = config["rate_limit"]
    levels = args.concurrency_levels or rate["concurrency_levels"]
    requests = args.requests if args.requests is not None else rate["requests_per_level"]
    for provider in providers:
        for concurrency in levels:
            run_batch(
                store, provider, factory,
                campaign_id=args.campaign_id,
                phase="rate_limit",
                context_tokens=rate["context_tokens"],
                output_tokens=rate["output_tokens"],
                requests=requests,
                concurrency=concurrency,
            )


def probe_slots(duration_hours: float, interval_seconds: float) -> Iterator[tuple[int, str]]:
    total = max(1, int(duration_hours * 3600 / interval_seconds) + 1)
    start_wall = time.time()
    start_monotonic = time.monotonic()
    for index in range(total):
        target_monotonic = start_monotonic + index * interval_seconds
        delay = target_monotonic - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        scheduled = datetime.fromtimestamp(
            start_wall + index * interval_seconds, timezone.utc
        ).isoformat(timespec="seconds")
        yield index, scheduled


def run_probes(
    store: CampaignStore,
    providers: Sequence[Provider],
    factory: PromptFactory,
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    probe = config["availability"]
    duration = args.duration_hours if args.duration_hours is not None else probe["duration_hours"]
    interval = args.interval_seconds if args.interval_seconds is not None else probe["interval_seconds"]
    if not args.smoke and duration < 168:
        raise RuntimeError("Official availability campaign must run for at least 168 hours; use --smoke for a short probe")
    for _, scheduled in probe_slots(duration, interval):
        for provider in providers:
            run_batch(
                store, provider, factory,
                campaign_id=args.campaign_id,
                phase="availability",
                context_tokens=probe["context_tokens"],
                output_tokens=probe["output_tokens"],
                requests=probe.get("requests_per_probe", 1),
                concurrency=1,
                slot=scheduled,
            )


def run_cost_trace(
    store: CampaignStore,
    providers: Sequence[Provider],
    factory: PromptFactory,
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    cost = config["agent_cost"]
    rounds = cost["rounds"]
    # Increasing prefixes approximate a real multi-round Agent trajectory while
    # keeping the initial prefix byte-identical so provider prompt caching can
    # be observed in reported cached token usage.
    for provider in providers:
        for round_index in range(rounds):
            context = cost["initial_context_tokens"] + round_index * cost["tokens_added_per_round"]
            run_batch(
                store, provider, factory,
                campaign_id=args.campaign_id,
                phase="agent_cost",
                context_tokens=context,
                output_tokens=cost["output_tokens"],
                requests=1,
                concurrency=1,
                slot=f"round-{round_index + 1}",
            )


def comma_ints(raw: str) -> list[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values or any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return values


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Full, resumable Experiment 7-10 campaign")
    result.add_argument("phase", choices=["workload", "availability", "rate-limit", "agent-cost", "all"])
    result.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result.add_argument("--db", type=Path, default=DEFAULT_DB)
    result.add_argument("--campaign-id", default="experiment-7-10")
    result.add_argument("--provider", action="append", dest="providers", help="Provider display name; repeatable")
    result.add_argument("--requests", type=int)
    result.add_argument("--concurrency", type=int)
    result.add_argument("--context-tokens", type=comma_ints)
    result.add_argument("--output-tokens", type=comma_ints)
    result.add_argument("--concurrency-levels", type=comma_ints)
    result.add_argument("--duration-hours", type=float)
    result.add_argument("--interval-seconds", type=float)
    result.add_argument(
        "--smoke", action="store_true",
        help="Permit deliberately small validation runs; records remain labelled by their actual scope",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    if args.requests is not None and args.requests <= 0:
        raise SystemExit("--requests must be positive")
    config = load_config(args.config)
    selected = set(args.providers or []) or None
    providers = providers_from_config(config, selected)
    store = CampaignStore(args.db)
    fingerprint = store.bind_campaign(args.campaign_id, config)
    print(f"Campaign execution fingerprint: {fingerprint}")
    factory = PromptFactory()
    try:
        phases = (
            ["workload", "rate-limit", "agent-cost", "availability"]
            if args.phase == "all" else [args.phase]
        )
        for phase in phases:
            if phase == "workload":
                run_workloads(store, providers, factory, config, args)
            elif phase == "rate-limit":
                run_rate_limit(store, providers, factory, config, args)
            elif phase == "agent-cost":
                run_cost_trace(store, providers, factory, config, args)
            else:
                run_probes(store, providers, factory, config, args)
    finally:
        store.close()
    print(f"Campaign data saved to {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
