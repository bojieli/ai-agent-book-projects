"""Credential-free raw provider receipts for staged system-prompt add-on."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


class RecordingCompletions:
    def __init__(self, owner: "RecordingClient", inner: Any) -> None:
        self.owner = owner
        self.inner = inner

    def create(self, **kwargs: Any) -> Any:
        call_index = len(self.owner.receipts) + 1
        started = time.perf_counter()
        record = {
            "schema_version": "1.0",
            "call_index": call_index,
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "provider": self.owner.provider,
            "base_url": self.owner.base_url,
            "context": dict(self.owner.context),
            "request": _jsonable(kwargs),
            "response": None,
            "error": None,
        }
        try:
            response = self.inner.create(**kwargs)
            record["response"] = _jsonable(response)
            return response
        except Exception as exc:
            record["error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
            raise
        finally:
            record["duration_s"] = round(time.perf_counter() - started, 3)
            path = self.owner.receipt_dir / f"call_{call_index:03d}.json"
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            record["receipt_path"] = str(path)
            self.owner.receipts.append(record)


class RecordingChat:
    def __init__(self, owner: "RecordingClient", inner: Any) -> None:
        self.completions = RecordingCompletions(owner, inner.completions)


class RecordingClient:
    """Small OpenAI-client proxy that persists each real request and response."""

    def __init__(self, inner: Any, receipt_dir: Path, *, provider: str, base_url: str) -> None:
        self.receipt_dir = receipt_dir
        self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.provider = provider
        self.base_url = base_url
        self.context: dict[str, Any] = {}
        self.receipts: list[dict[str, Any]] = []
        self.chat = RecordingChat(self, inner.chat)

    def set_context(self, **context: Any) -> None:
        self.context = context

    def usage(self) -> dict[str, int]:
        totals = {
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "requests": 0,
        }
        for receipt in self.receipts:
            response = receipt.get("response") or {}
            usage = response.get("usage") or {}
            details = usage.get("prompt_tokens_details") or {}
            if usage:
                totals["requests"] += 1
            totals["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
            totals["cached_prompt_tokens"] += int(details.get("cached_tokens") or 0)
            totals["completion_tokens"] += int(usage.get("completion_tokens") or 0)
        return totals
