"""Build and validate SafetyDecision envelopes."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED = {
    "decision_id",
    "request_id",
    "tenant_id",
    "app_id",
    "policy_binding_id",
    "policy_version",
    "risk_tier",
    "layer",
    "decision",
    "reason_codes",
    "scanner_results",
    "content_hash",
    "retention",
    "latency_ms",
    "created_at",
}

SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "llm-safety-platform"
    / "samples"
    / "safety_decision.schema.json"
)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_decision(
    *,
    request_id: str,
    tenant_id: str,
    app_id: str,
    policy_binding_id: str,
    policy_version: int,
    risk_tier: str,
    layer: str,
    decision: str,
    reason_codes: list[str],
    scanner_results: list[dict[str, Any]],
    source_text: str,
    retention: str,
    latency_ms: float,
) -> dict[str, Any]:
    env = {
        "decision_id": str(uuid.uuid4()),
        "request_id": request_id,
        "tenant_id": tenant_id,
        "app_id": app_id,
        "policy_binding_id": policy_binding_id,
        "policy_version": policy_version,
        "risk_tier": risk_tier,
        "layer": layer,
        "decision": decision,
        "reason_codes": reason_codes,
        "scanner_results": scanner_results,
        "content_hash": content_hash(source_text),
        "retention": retention,
        "latency_ms": latency_ms,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    validate_envelope(env)
    return env


def validate_envelope(env: dict[str, Any]) -> None:
    missing = REQUIRED - set(env)
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")
    if env["decision"] not in (
        "allow",
        "redact",
        "block",
        "confirm_only",
        "alert_only",
    ):
        raise ValueError("bad decision")
    if env["risk_tier"] not in ("low", "medium", "high", "critical"):
        raise ValueError("bad risk_tier")
    # lightweight schema presence check
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"schema missing: {SCHEMA_PATH}")
    # ensure schema is valid JSON
    json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
