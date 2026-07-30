"""Shared evidence helpers for the Chapter 3 experiment campaigns.

The helpers deliberately never read or serialize credential values.  Provider
keys are supplied directly to SDK clients by each campaign; receipts contain
only the provider name, endpoint, model, request payload, raw response, usage,
and latency needed to reproduce/audit the experiment.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id(prefix: str = "run") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{prefix}-{uuid.uuid4().hex[:8]}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path | str) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonable(value: Any) -> Any:
    """Convert SDK/Pydantic/dataclass-ish values to JSON-compatible data."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if hasattr(value, "model_dump"):
        return jsonable(value.model_dump(mode="json"))
    if hasattr(value, "to_dict"):
        return jsonable(value.to_dict())
    if hasattr(value, "__dict__"):
        return jsonable(vars(value))
    return str(value)


def runtime_provenance() -> Dict[str, Any]:
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        revision = None
    return {
        "captured_at": utc_now(),
        "git_revision": revision,
        "python": sys.version,
        "platform": platform.platform(),
        "credential_presence": {
            name: bool(os.getenv(name))
            for name in (
                "ARK_API_KEY",
                "MOONSHOT_API_KEY",
                "OPENAI_API_KEY",
                "GEMINI_API_KEY",
                "SILICONFLOW_API_KEY",
            )
        },
    }


class ChatRecorder:
    """Thin OpenAI-compatible chat wrapper that retains credential-free calls."""

    def __init__(self, client: Any, provider: str, endpoint: str):
        self.client = client
        self.provider = provider
        self.endpoint = endpoint.rstrip("/")
        self.calls: list[Dict[str, Any]] = []

    def create(self, *, purpose: str, **request: Any) -> Any:
        started_at = utc_now()
        start = time.perf_counter()
        try:
            response = self.client.chat.completions.create(**request)
        except Exception as exc:
            self.calls.append(
                {
                    "purpose": purpose,
                    "provider": self.provider,
                    "endpoint": self.endpoint,
                    "started_at": started_at,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 3),
                    "request": jsonable(request),
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
            raise
        elapsed = round((time.perf_counter() - start) * 1000, 3)
        raw = jsonable(response)
        call = {
            "purpose": purpose,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "started_at": started_at,
            "latency_ms": elapsed,
            "request": jsonable(request),
            "response": raw,
            "usage": raw.get("usage") if isinstance(raw, dict) else None,
            "response_model": raw.get("model") if isinstance(raw, dict) else None,
            "response_id": raw.get("id") if isinstance(raw, dict) else None,
        }
        self.calls.append(call)
        return response


def write_campaign_evidence(
    project_dir: Path | str,
    experiment: str,
    evidence: Mapping[str, Any],
    receipts: Iterable[Mapping[str, Any]] = (),
    *,
    input_paths: Iterable[Path | str] = (),
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write immutable run artifacts plus ``validation/latest.json``.

    ``latest.json`` is the canonical compact pointer.  It contains hashes for
    the detailed evidence, raw credential-free receipts, and all declared
    inputs.  It is written last, so a partial campaign can never look current.
    """
    project_dir = Path(project_dir).resolve()
    run_id = run_id or make_run_id(experiment.replace("-", "_"))
    run_dir = project_dir / "validation" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    evidence_path = run_dir / "evidence.json"
    receipts_path = run_dir / "receipts.json"
    evidence_payload = {
        "schema_version": "chapter3-evidence-v1",
        "experiment": experiment,
        "run_id": run_id,
        "provenance": runtime_provenance(),
        **jsonable(dict(evidence)),
    }
    evidence_path.write_text(
        json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    receipts_path.write_text(
        json.dumps(list(receipts), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    inputs = []
    for raw_path in input_paths:
        path = Path(raw_path).resolve()
        inputs.append(
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )

    artifact_hashes = {
        "evidence.json": sha256_file(evidence_path),
        "receipts.json": sha256_file(receipts_path),
    }
    manifest = {
        "schema_version": "chapter3-evidence-v1",
        "experiment": experiment,
        "run_id": run_id,
        "created_at": utc_now(),
        "status": evidence_payload.get("status", "unknown"),
        "run_dir": str(run_dir),
        "artifacts": artifact_hashes,
        "inputs": inputs,
        "summary": evidence_payload.get("summary", {}),
        "acceptance": evidence_payload.get("acceptance", {}),
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest["artifacts"]["manifest.json"] = sha256_file(manifest_path)

    latest_path = project_dir / "validation" / "latest.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
