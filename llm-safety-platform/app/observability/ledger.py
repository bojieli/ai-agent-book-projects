"""Audit ledger for SafetyDecision envelopes."""

from __future__ import annotations

from typing import Any


class AuditLedger:
    def __init__(self) -> None:
        self._by_request: dict[str, dict[str, Any]] = {}

    def write(self, decision: dict[str, Any]) -> None:
        rid = decision["request_id"]
        self._by_request[rid] = decision

    def get(self, request_id: str) -> dict[str, Any] | None:
        return self._by_request.get(request_id)
