"""Hash-chain audit + SIEM sink SPI (log|http|file) + Prometheus metrics."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.config import settings
from app.observability.ledger import AuditLedger

_log = logging.getLogger("llm_safety.siem")


class HashChainLedger(AuditLedger):
    """In-process hash chain. Desensitized rebuild = **single-writer** only.

    Multi-replica production must use Postgres advisory lock or a dedicated
    audit-chain writer partition — concurrent writers will fork the chain.
    """

    def __init__(self) -> None:
        super().__init__()
        self._prev = "GENESIS"
        self._lock = threading.Lock()
        self.chain: list[dict[str, Any]] = []

    def write(self, decision: dict[str, Any]) -> None:
        from app.observability.audit_lock import audit_chain_lock

        with audit_chain_lock(None):
            with self._lock:
                base = {k: v for k, v in decision.items() if k not in ("chain_hash", "prev_chain_hash")}
                payload = json.dumps(base, sort_keys=True, ensure_ascii=False)
                chain_hash = hashlib.sha256((self._prev + payload).encode("utf-8")).hexdigest()
                decision["prev_chain_hash"] = self._prev
                decision["chain_hash"] = chain_hash
                self._prev = chain_hash
                self.chain.append(dict(decision))
                super().write(decision)


class SIEMBackend(ABC):
    name: str

    @abstractmethod
    def send(self, event: dict[str, Any]) -> None: ...


class LogSIEMBackend(SIEMBackend):
    name = "log"

    def send(self, event: dict[str, Any]) -> None:
        _log.info("siem_event %s", json.dumps(event, ensure_ascii=False))


class HttpSIEMBackend(SIEMBackend):
    name = "http"

    def __init__(self, url: str | None = None) -> None:
        self.url = (url or settings.siem_webhook_url or os.getenv("SAFETY_SIEM_HTTP_URL", "")).strip()

    def send(self, event: dict[str, Any]) -> None:
        if not self.url:
            return
        data = json.dumps(event, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)  # noqa: S310


class FileSIEMBackend(SIEMBackend):
    name = "file"

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(
            path or os.getenv("SAFETY_SIEM_FILE_PATH", "data/siem_events.jsonl")
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def send(self, event: dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False) + "\n"
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)


def build_siem_backend(name: str | None = None) -> SIEMBackend:
    key = (name or os.getenv("SAFETY_SIEM_SINK", "log")).strip().lower()
    if key == "http":
        return HttpSIEMBackend()
    if key == "file":
        return FileSIEMBackend()
    return LogSIEMBackend()


class SIEMSink:
    """Emits hash-chain-enriched audit events to configured sink(s)."""

    def __init__(self, backend: SIEMBackend | None = None) -> None:
        self.buffer: list[dict[str, Any]] = []
        self.backend = backend or build_siem_backend()
        self.failures: int = 0
        # Optional dual-write to http when webhook set and primary is log/file
        self._http_extra: HttpSIEMBackend | None = None
        if settings.siem_webhook_url and self.backend.name != "http":
            self._http_extra = HttpSIEMBackend(settings.siem_webhook_url)

    def emit(self, event: dict[str, Any]) -> None:
        # Enrich with chain fields when present on decision payloads
        enriched = dict(event)
        enriched.setdefault("source", "llm-safety-platform")
        chain_hash = event.get("chain_hash")
        prev_hash = event.get("prev_chain_hash")
        if chain_hash:
            enriched["chain_hash"] = chain_hash
            enriched["prev_chain_hash"] = prev_hash or ""
            enriched["audit_integrity"] = "hash_chain"
        self.buffer.append(enriched)
        try:
            self.backend.send(enriched)
        except Exception:  # noqa: BLE001
            self.failures += 1
        if self._http_extra is not None:
            try:
                self._http_extra.send(enriched)
            except Exception:  # noqa: BLE001
                self.failures += 1

    def as_syslog(self, event: dict[str, Any]) -> str:
        return f"<134>1 - llm-safety - - - - {json.dumps(event, ensure_ascii=False)}"


class MetricsRegistry:
    def __init__(self) -> None:
        self.counters: dict[str, float] = {}
        self._lock = threading.Lock()

    def inc(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self.counters[name] = self.counters.get(name, 0.0) + value

    def render_prometheus(self) -> str:
        lines = [
            "# HELP llm_safety_requests_total Gateway decisions",
            "# TYPE llm_safety_requests_total counter",
        ]
        with self._lock:
            for k, v in sorted(self.counters.items()):
                lines.append(f"{k} {v}")
        return "\n".join(lines) + "\n"


metrics = MetricsRegistry()
siem = SIEMSink()
