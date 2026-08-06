"""OpenAI-0.27 compatibility adapter with credential-free call receipts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any


_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{20,}"),
)
_TRANSIENT_ERROR_NAMES = {
    "APIConnectionError",
    "APITimeoutError",
    "RateLimitError",
    "ServiceUnavailableError",
    "Timeout",
}
_MAX_TRANSPORT_ATTEMPTS = 5


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _redact_text(value: str) -> str:
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub("<redacted-credential>", value)
    return value


def _plain(value: Any) -> Any:
    if hasattr(value, "to_dict_recursive"):
        return value.to_dict_recursive()
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_text(str(value))


class ReceiptRecorder:
    """Append crash-tolerant JSONL receipts for one checkpoint."""

    def __init__(self) -> None:
        self._path: Path | None = None
        self._lock = threading.Lock()

    def set_path(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # A checkpoint with no model calls is valid. Materialize its receipt
        # now so the runner can still compress and retain an empty JSONL file.
        path.touch(exist_ok=True)
        self._path = path

    def record(
        self,
        *,
        kind: str,
        request: dict[str, Any],
        started: float,
        response: Any | None = None,
        error: BaseException | None = None,
        transport_retries: list[dict[str, Any]] | None = None,
    ) -> None:
        if self._path is None:
            return
        request_plain = _plain(request)
        response_plain = _plain(response) if response is not None else None
        if kind == "embedding" and isinstance(response_plain, dict):
            compact_data = []
            for row in response_plain.get("data", []):
                vector = row.get("embedding", []) if isinstance(row, dict) else []
                compact_data.append(
                    {
                        "index": row.get("index") if isinstance(row, dict) else None,
                        "object": row.get("object") if isinstance(row, dict) else None,
                        "embedding_dimensions": len(vector),
                        "embedding_sha256": _sha256_json(vector),
                    }
                )
            response_plain["data"] = compact_data
        row = {
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "kind": kind,
            "request": request_plain,
            "request_sha256": _sha256_json(request_plain),
            "response": response_plain,
            "latency_seconds": round(time.perf_counter() - started, 3),
            "success": error is None,
            "transport_retries": transport_retries or [],
            "error": (
                None
                if error is None
                else {
                    "type": type(error).__name__,
                    "message": _redact_text(str(error))[:1000],
                }
            ),
        }
        encoded = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())


RECORDER = ReceiptRecorder()


def install(
    *,
    api_key: str,
    api_base: str,
    chat_model: str,
    embedding_model: str,
    receipt_path: Path,
) -> None:
    """Redirect the upstream GPT-3/GPT-4 calls to compatible current models."""

    import openai

    openai.api_key = api_key
    openai.api_base = api_base
    original_chat_create = openai.ChatCompletion.create
    original_embedding_create = openai.Embedding.create
    request_timeout = float(os.environ.get("GA_PROVIDER_TIMEOUT_SECONDS", "90"))
    RECORDER.set_path(receipt_path)

    def call_with_transient_retries(
        *, kind: str, request: dict[str, Any], function: Any
    ) -> Any:
        started = time.perf_counter()
        retries: list[dict[str, Any]] = []
        for attempt in range(1, _MAX_TRANSPORT_ATTEMPTS + 1):
            try:
                response = function()
            except BaseException as exc:
                transient = type(exc).__name__ in _TRANSIENT_ERROR_NAMES
                if transient and attempt < _MAX_TRANSPORT_ATTEMPTS:
                    retries.append(
                        {
                            "attempt": attempt,
                            "type": type(exc).__name__,
                            "message": _redact_text(str(exc))[:1000],
                        }
                    )
                    time.sleep(min(4.0, 0.5 * (2 ** (attempt - 1))))
                    continue
                RECORDER.record(
                    kind=kind,
                    request=request,
                    started=started,
                    error=exc,
                    transport_retries=retries,
                )
                raise
            RECORDER.record(
                kind=kind,
                request=request,
                started=started,
                response=response,
                transport_retries=retries,
            )
            return response
        raise AssertionError("unreachable provider retry loop")

    def chat_create(**kwargs: Any) -> Any:
        actual = dict(kwargs)
        actual["model"] = chat_model
        actual["enable_thinking"] = False
        actual["request_timeout"] = request_timeout
        request = _plain(actual)
        return call_with_transient_retries(
            kind="chat",
            request=request,
            function=lambda: original_chat_create(**actual),
        )

    def completion_create(**kwargs: Any) -> Any:
        prompt = kwargs.get("prompt", "")
        actual = {
            "model": chat_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 512),
            "top_p": kwargs.get("top_p", 1),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "presence_penalty": kwargs.get("presence_penalty", 0),
            "enable_thinking": False,
            "request_timeout": request_timeout,
        }
        if kwargs.get("stop"):
            actual["stop"] = kwargs["stop"]
        request = _plain(actual)
        response = call_with_transient_retries(
            kind="chat",
            request=request,
            function=lambda: original_chat_create(**actual),
        )
        content = response["choices"][0]["message"]["content"]
        return SimpleNamespace(choices=[SimpleNamespace(text=content)])

    def embedding_create(**kwargs: Any) -> Any:
        actual = dict(kwargs)
        actual["model"] = embedding_model
        actual["dimensions"] = 1024
        actual["request_timeout"] = request_timeout
        request = _plain(actual)
        return call_with_transient_retries(
            kind="embedding",
            request=request,
            function=lambda: original_embedding_create(**actual),
        )

    openai.ChatCompletion.create = staticmethod(chat_create)
    openai.Completion.create = staticmethod(completion_create)
    openai.Embedding.create = staticmethod(embedding_create)
