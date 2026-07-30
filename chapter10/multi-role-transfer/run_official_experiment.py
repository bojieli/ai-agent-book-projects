#!/usr/bin/env python3
"""Run Experiment 10-2 with raw Moonshot/Tavily receipts and source hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from openai import OpenAI

from demo import COMPOSITE_TASK, save_evidence
from orchestrator import MultiRoleOrchestrator


ROOT = Path(__file__).resolve().parent
BASE_URL = "https://api.moonshot.cn/v1"
SOURCE_FILES = [
    "run_official_experiment.py",
    "demo.py",
    "orchestrator.py",
    "roles.py",
    "tools.py",
]
SECRET_ENV_NAMES = (
    "MOONSHOT_API_KEY",
    "TAVILY_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class ReceiptRecorder:
    def __init__(self) -> None:
        self.provider: List[Dict[str, Any]] = []
        self.tavily: List[Dict[str, Any]] = []

    def record_provider(self, receipt: dict) -> None:
        item = dict(receipt)
        item["request_sha256"] = sha256_bytes(canonical_bytes(item["request"]))
        item["response_sha256"] = sha256_bytes(canonical_bytes(item["response"]))
        item["captured_at"] = utc_now()
        self.provider.append(item)

    def record_tavily(self, receipt: dict) -> None:
        item = dict(receipt)
        item["request_sha256"] = sha256_bytes(canonical_bytes(item["request"]))
        raw = item["response"]["raw_body"].encode("utf-8")
        item["raw_response_bytes"] = len(raw)
        item["raw_response_sha256"] = sha256_bytes(raw)
        item["captured_at"] = utc_now()
        self.tavily.append(item)


def find_credential_hits(payloads: Iterable[bytes]) -> Dict[str, int]:
    blobs = list(payloads)
    actual_secret_hits = 0
    for name in SECRET_ENV_NAMES:
        secret = os.getenv(name, "").encode("utf-8")
        if len(secret) >= 8:
            actual_secret_hits += sum(blob.count(secret) for blob in blobs)
    patterns = (
        re.compile(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|")[^"]+"'),
        re.compile(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}'),
    )
    pattern_hits = sum(len(pattern.findall(blob)) for pattern in patterns for blob in blobs)
    return {"actual_secret_hits": actual_secret_hits, "credential_pattern_hits": pattern_hits}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--run-id", help="immutable validation/runs directory name")
    parser.add_argument("--output-root", default=str(ROOT / "validation" / "runs"))
    return parser.parse_args()


def main(args: argparse.Namespace) -> int:
    moonshot_key = os.getenv("MOONSHOT_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not moonshot_key or not tavily_key:
        missing = [
            name
            for name, value in (("MOONSHOT_API_KEY", moonshot_key), ("TAVILY_API_KEY", tavily_key))
            if not value
        ]
        raise RuntimeError(f"official run requires configured credentials: {', '.join(missing)}")

    run_id = args.run_id or f"exp10-2-kimi-tavily-receipts-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    run_dir = Path(args.output_root).resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    source_hashes = {name: sha256_file(ROOT / name) for name in SOURCE_FILES}
    started = time.monotonic()
    started_at = utc_now()
    recorder = ReceiptRecorder()

    client = OpenAI(api_key=moonshot_key, base_url=BASE_URL)
    orchestrator = MultiRoleOrchestrator(
        client=client,
        model=args.model,
        max_steps=args.max_steps,
        verbose=False,
        start_role="triage",
        provider_receipt_sink=recorder.record_provider,
        tool_receipt_sink=recorder.record_tavily,
    )
    final = orchestrator.run(COMPOSITE_TASK)

    evidence_path = run_dir / "evidence.json"
    evidence = save_evidence(
        evidence_path,
        orchestrator,
        final,
        model=args.model,
        base_url=BASE_URL,
        task=COMPOSITE_TASK,
    )
    provider_path = run_dir / "moonshot_receipts.json"
    tavily_path = run_dir / "tavily_receipts.json"
    write_json(provider_path, {"schema_version": 1, "receipts": recorder.provider})
    write_json(tavily_path, {"schema_version": 1, "receipts": recorder.tavily})

    credential_scan = find_credential_hits(
        [evidence_path.read_bytes(), provider_path.read_bytes(), tavily_path.read_bytes()]
    )
    behavior_gates = evidence["acceptance_gates"]
    response_ids = [item.get("response_id") for item in recorder.provider]
    receipt_gates = {
        "moonshot_raw_receipts_for_every_api_call": (
            len(recorder.provider) == len(orchestrator.api_calls) > 0
            and all(item.get("request") and item.get("response") for item in recorder.provider)
        ),
        "unique_moonshot_response_ids": (
            all(response_ids) and len(set(response_ids)) == len(response_ids)
        ),
        "raw_tavily_receipt_retained": (
            len(recorder.tavily) >= 1
            and all(item["response"]["http_status"] == 200 for item in recorder.tavily)
            and all(item["response"]["raw_body"] for item in recorder.tavily)
        ),
        "tavily_request_credentials_removed": all(
            "api_key" not in item["request"]["body"] for item in recorder.tavily
        ),
        "runtime_source_hashes_captured": (
            len(source_hashes) == len(SOURCE_FILES)
            and all(len(value) == 64 for value in source_hashes.values())
        ),
        "credential_free_artifacts": (
            credential_scan["actual_secret_hits"] == 0
            and credential_scan["credential_pattern_hits"] == 0
        ),
    }
    all_gates = {**behavior_gates, **receipt_gates}
    overall_status = "pass" if all(all_gates.values()) else "incomplete"

    acceptance = {
        "schema_version": 1,
        "experiment": "10-2",
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "git_commit": git_commit(),
        "model": args.model,
        "base_url": BASE_URL,
        "behavior_gates": behavior_gates,
        "provenance_gates": receipt_gates,
        "response_ids": response_ids,
        "receipt_counts": {
            "moonshot": len(recorder.provider),
            "tavily": len(recorder.tavily),
        },
        "credential_scan": credential_scan,
        "runtime_source_sha256": source_hashes,
        "pre_acceptance_artifact_sha256": {
            evidence_path.name: sha256_file(evidence_path),
            provider_path.name: sha256_file(provider_path),
            tavily_path.name: sha256_file(tavily_path),
        },
        "passed_gates": sum(all_gates.values()),
        "total_gates": len(all_gates),
        "overall_status": overall_status,
    }
    acceptance_path = run_dir / "acceptance.json"
    write_json(acceptance_path, acceptance)

    manifest = {
        "schema_version": 1,
        "experiment": "10-2",
        "run_id": run_id,
        "generated_at": utc_now(),
        "git_commit": acceptance["git_commit"],
        "runtime_source_sha256": source_hashes,
        "artifact_sha256": {
            path.name: sha256_file(path)
            for path in (evidence_path, provider_path, tavily_path, acceptance_path)
        },
        "acceptance": {
            "overall_status": overall_status,
            "passed_gates": acceptance["passed_gates"],
            "total_gates": acceptance["total_gates"],
        },
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)

    latest = ROOT / "validation" / "latest.json"
    write_json(latest, {
        "schema_version": 1,
        "run_id": run_id,
        "run_directory": str(run_dir.relative_to(ROOT)),
        "manifest_sha256": sha256_file(manifest_path),
        "overall_status": overall_status,
    })
    print(json.dumps({
        "run_id": run_id,
        "run_directory": str(run_dir),
        "overall_status": overall_status,
        "passed_gates": acceptance["passed_gates"],
        "total_gates": acceptance["total_gates"],
        "handoff_chain": evidence["handoff_chain"],
        "receipt_counts": acceptance["receipt_counts"],
    }, ensure_ascii=False, indent=2))
    return 0 if overall_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
