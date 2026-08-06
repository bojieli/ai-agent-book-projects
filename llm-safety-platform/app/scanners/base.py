"""Scanner SPI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.policy.binding import ScannerSpec


@dataclass
class ScanContext:
    tenant_id: str
    request_id: str
    vault: Any
    spec: ScannerSpec
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    scanner_id: str
    decision: str
    risk_score: float
    reasons: list[str] = field(default_factory=list)
    redacted_text: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scanner_id": self.scanner_id,
            "decision": self.decision,
            "risk_score": self.risk_score,
            "reasons": list(self.reasons),
        }


class Scanner(Protocol):
    id: str
    layer: str  # L1 | L2 | L3

    def scan(self, text: str, ctx: ScanContext) -> ScanResult: ...
