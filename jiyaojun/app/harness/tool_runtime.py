"""ToolRuntime — only side-effect path (validate / authz / execute / audit)."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class Connector(Protocol):
    id: str
    production_effect: str  # none|draft_only|observe|production

    def execute(self, args: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class ToolCallRecord:
    call_id: str
    tool_id: str
    meeting_id: str
    args: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    production_effect: str
    ts: float = field(default_factory=time.time)


class ToolRuntime:
    def __init__(self) -> None:
        self._tools: dict[str, Connector] = {}
        self.audit: list[ToolCallRecord] = []

    def register(self, connector: Connector) -> None:
        self._tools[connector.id] = connector

    def discover(
        self,
        allowlist: list[str] | None,
        max_effect: str,
        effect_rank: dict[str, int],
    ) -> list[str]:
        allowed = []
        for tid, tool in self._tools.items():
            if allowlist is not None and tid not in allowlist:
                continue
            if effect_rank[tool.production_effect] > effect_rank[max_effect]:
                continue
            allowed.append(tid)
        return allowed

    def call(
        self,
        tool_id: str,
        meeting_id: str,
        args: dict[str, Any],
        *,
        allowlist: list[str] | None,
        max_effect: str,
        effect_rank: dict[str, int],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if allowlist is not None and tool_id not in allowlist:
            raise PermissionError(f"tool not in allowlist: {tool_id}")
        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(f"unknown tool: {tool_id}")
        if effect_rank[tool.production_effect] > effect_rank[max_effect]:
            raise PermissionError(
                f"tool effect {tool.production_effect} exceeds cap {max_effect}"
            )
        payload = dict(args)
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        try:
            result = tool.execute(payload)
            self.audit.append(
                ToolCallRecord(
                    call_id=str(uuid.uuid4()),
                    tool_id=tool_id,
                    meeting_id=meeting_id,
                    args=payload,
                    result=result,
                    error=None,
                    production_effect=tool.production_effect,
                )
            )
            return result
        except Exception as exc:  # noqa: BLE001 — audit then re-raise
            self.audit.append(
                ToolCallRecord(
                    call_id=str(uuid.uuid4()),
                    tool_id=tool_id,
                    meeting_id=meeting_id,
                    args=payload,
                    result=None,
                    error=str(exc),
                    production_effect=tool.production_effect,
                )
            )
            raise


def idem_key(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
