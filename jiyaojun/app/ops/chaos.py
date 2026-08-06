"""Fault injection drills (Phase 4) — connector timeout / 5xx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChaosProxy:
    inner: Any
    fail_next: int = 0
    timeout_next: int = 0

    @property
    def id(self) -> str:
        return self.inner.id

    @property
    def production_effect(self) -> str:
        return self.inner.production_effect

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return self.inner.mcp_tool_descriptor()

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.timeout_next > 0:
            self.timeout_next -= 1
            raise TimeoutError("injected connector timeout")
        if self.fail_next > 0:
            self.fail_next -= 1
            raise RuntimeError("injected 5xx")
        return self.inner.execute(args)
