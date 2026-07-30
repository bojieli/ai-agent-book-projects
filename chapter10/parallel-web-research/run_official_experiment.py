#!/usr/bin/env python3
"""Run Experiment 10-6 with provenance-complete real-provider receipts."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from agents import BrowserPool, Coordinator, WorkerAgent, run_sequential
from message_bus import MessageBus
from sources import TARGET, Website, load_sites


ROOT = Path(__file__).resolve().parent
SOURCE_FILES = [
    "run_official_experiment.py",
    "demo.py",
    "agents.py",
    "llm.py",
    "message_bus.py",
    "sources.py",
    "cascade-stress.example.json",
]
SECRET_ENV_NAMES = (
    "ARK_API_KEY",
    "MOONSHOT_API_KEY",
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
        self.browser: List[Dict[str, Any]] = []
        self.llm: List[Dict[str, Any]] = []
        self.bus: List[Dict[str, Any]] = []

    def record_browser(self, receipt: dict) -> None:
        item = dict(receipt)
        body = item.get("rendered_body_text", "")
        item["rendered_body_bytes"] = len(body.encode("utf-8"))
        item["rendered_body_sha256"] = sha256_bytes(body.encode("utf-8"))
        item["captured_at"] = utc_now()
        self.browser.append(item)

    def record_llm(self, receipt: dict) -> None:
        item = dict(receipt)
        request = item.get("request")
        response = item.get("response")
        if request is not None:
            item["request_sha256"] = sha256_bytes(canonical_bytes(request))
        if response is not None:
            item["response_sha256"] = sha256_bytes(canonical_bytes(response))
        item["captured_at"] = utc_now()
        self.llm.append(item)

    def record_bus(self, phase: str, bus: MessageBus) -> None:
        for env in bus.history:
            self.bus.append({
                "phase": phase,
                "sender_id": env.sender_id,
                "target": env.target,
                "type": env.type,
                "payload": env.payload,
                "sequence": env.seq,
                "relative_seconds": round(env.ts, 6),
            })


async def run_parallel_phase(
    sites: List[Website],
    target: str,
    timeout: float,
    phase: str,
    recorder: ReceiptRecorder,
) -> Dict[str, Any]:
    pool = BrowserPool(headless=True)
    await pool.start()
    browser_version = pool.browser.version if pool.browser else None
    try:
        bus = MessageBus(verbose=False)
        coordinator = Coordinator(bus, target)
        for index, site in enumerate(sites):
            coordinator.add_worker(WorkerAgent(
                f"agent-{index:02d}",
                site,
                bus,
                target,
                pool,
                timeout,
                browser_receipt_sink=recorder.record_browser,
                llm_receipt_sink=recorder.record_llm,
                run_phase=phase,
            ))
        result = await coordinator.run()
        recorder.record_bus(phase, bus)
    finally:
        await pool.close()
    return {
        "result": result,
        "contexts_created": pool.contexts_created,
        "contexts_closed": pool.contexts_closed,
        "chromium_version": browser_version,
    }


async def run_serial_phase(
    sites: List[Website],
    target: str,
    timeout: float,
    recorder: ReceiptRecorder,
) -> Dict[str, Any]:
    pool = BrowserPool(headless=True)
    await pool.start()
    browser_version = pool.browser.version if pool.browser else None
    try:
        result = await run_sequential(
            sites,
            target,
            pool,
            timeout,
            browser_receipt_sink=recorder.record_browser,
            llm_receipt_sink=recorder.record_llm,
            run_phase="default_serial",
        )
    finally:
        await pool.close()
    return {
        "result": result,
        "contexts_created": pool.contexts_created,
        "contexts_closed": pool.contexts_closed,
        "chromium_version": browser_version,
    }


def gate(status: bool, **details: Any) -> Dict[str, Any]:
    return {"status": "pass" if status else "fail", **details}


def find_credential_hits(payloads: Iterable[bytes]) -> Dict[str, int]:
    blobs = list(payloads)
    actual_secret_hits = 0
    for name in SECRET_ENV_NAMES:
        secret = os.getenv(name, "").encode("utf-8")
        if len(secret) >= 8:
            actual_secret_hits += sum(blob.count(secret) for blob in blobs)

    generic_patterns = (
        re.compile(rb'(?i)"(?:api[_-]?key|authorization)"\s*:\s*"(?!<redacted>|null|")[^"]+"'),
        re.compile(rb'(?i)bearer\s+[a-z0-9._~+/=-]{16,}'),
    )
    pattern_hits = sum(len(pattern.findall(blob)) for pattern in generic_patterns for blob in blobs)
    return {"actual_secret_hits": actual_secret_hits, "credential_pattern_hits": pattern_hits}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=TARGET)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--run-id", help="immutable validation/runs directory name")
    parser.add_argument("--output-root", default=str(ROOT / "validation" / "runs"))
    return parser.parse_args()


async def main(args: argparse.Namespace) -> int:
    run_id = args.run_id or f"exp10-6-real-receipts-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    run_dir = Path(args.output_root).resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    started_monotonic = time.monotonic()

    source_hashes = {
        path: sha256_file(ROOT / path)
        for path in SOURCE_FILES
    }
    default_sites = load_sites(None)
    cascade_sites = load_sites(str(ROOT / "cascade-stress.example.json"))
    recorder = ReceiptRecorder()

    default_parallel = await run_parallel_phase(
        default_sites, args.target, args.timeout, "default_parallel", recorder
    )
    default_serial = await run_serial_phase(
        default_sites, args.target, args.timeout, recorder
    )
    cascade = await run_parallel_phase(
        cascade_sites, args.target, args.timeout, "cascade_stress", recorder
    )

    browser_path = run_dir / "browser_receipts.json"
    llm_path = run_dir / "llm_receipts.json"
    bus_path = run_dir / "message_bus_receipts.json"
    write_json(browser_path, {"schema_version": 1, "receipts": recorder.browser})
    write_json(llm_path, {"schema_version": 1, "receipts": recorder.llm})
    write_json(bus_path, {"schema_version": 1, "receipts": recorder.bus})

    parallel_result = default_parallel["result"]
    serial_result = default_serial["result"]
    cascade_result = cascade["result"]
    speedup = (
        round(serial_result["seconds"] / parallel_result["parallel_seconds"], 3)
        if parallel_result["parallel_seconds"]
        else None
    )
    successful_llm = [r for r in recorder.llm if r["kind"] == "llm_chat_completion"]
    phases_with_browser_receipts = sorted({r["phase"] for r in recorder.browser})
    phases_with_llm_receipts = sorted({r["context"]["phase"] for r in successful_llm})
    cascade_expected_acks = set(cascade_result["expected_loser_acks"])
    cascade_actual_acks = set(cascade_result["acks"])

    credential_scan = find_credential_hits(
        [browser_path.read_bytes(), llm_path.read_bytes(), bus_path.read_bytes()]
    )
    gates = {
        "ten_real_default_sites": gate(
            len(default_sites) == 10 and all(s.url.startswith("https://") for s in default_sites),
            count=len(default_sites),
        ),
        "same_sites_parallel_and_serial": gate(
            serial_result["visited"] == len(default_sites),
            configured_count=len(default_sites),
            serial_visited=serial_result["visited"],
        ),
        "default_target_found_both_modes": gate(
            parallel_result["outcome"] == "found"
            and any(item.get("profile", {}).get("found") for item in serial_result["results"]),
            parallel_winner=parallel_result["winner"],
        ),
        "default_resources_closed": gate(
            default_parallel["contexts_created"] == default_parallel["contexts_closed"] == len(default_sites)
            and default_serial["contexts_created"] == default_serial["contexts_closed"] == len(default_sites),
            parallel_created=default_parallel["contexts_created"],
            parallel_closed=default_parallel["contexts_closed"],
            serial_created=default_serial["contexts_created"],
            serial_closed=default_serial["contexts_closed"],
        ),
        "measured_parallel_speedup": gate(speedup is not None and speedup > 1, speedup=speedup),
        "raw_browser_receipts": gate(
            len(recorder.browser) >= len(default_sites)
            and {"default_parallel", "default_serial", "cascade_stress"}.issubset(phases_with_browser_receipts),
            count=len(recorder.browser),
            phases=phases_with_browser_receipts,
        ),
        "raw_llm_provider_receipts": gate(
            len(successful_llm) >= 3
            and all(r.get("response_id") and r.get("response") for r in successful_llm)
            and {"default_parallel", "default_serial", "cascade_stress"}.issubset(phases_with_llm_receipts),
            successful_count=len(successful_llm),
            response_ids=[r.get("response_id") for r in successful_llm],
            phases=phases_with_llm_receipts,
        ),
        "single_cascade_settlement": gate(
            cascade_result["winner"] is not None
            and cascade_result["terminate_broadcasts"] == 1
            and not cascade_result["duplicate_hits"],
            winner=cascade_result["winner"],
            terminate_broadcasts=cascade_result["terminate_broadcasts"],
            duplicate_hits=cascade_result["duplicate_hits"],
        ),
        "cascade_loser_acknowledgements": gate(
            cascade_expected_acks == cascade_actual_acks
            and not cascade_result["missing_loser_acks"],
            expected=sorted(cascade_expected_acks),
            actual=sorted(cascade_actual_acks),
        ),
        "cascade_resources_closed": gate(
            cascade["contexts_created"] == cascade["contexts_closed"] == len(cascade_sites),
            created=cascade["contexts_created"],
            closed=cascade["contexts_closed"],
        ),
        "runtime_source_hashes": gate(
            len(source_hashes) == len(SOURCE_FILES)
            and all(len(value) == 64 for value in source_hashes.values()),
            count=len(source_hashes),
        ),
        "credential_free_artifacts": gate(
            credential_scan["actual_secret_hits"] == 0
            and credential_scan["credential_pattern_hits"] == 0,
            **credential_scan,
        ),
    }
    overall_status = "pass" if all(item["status"] == "pass" for item in gates.values()) else "incomplete"

    evidence = {
        "schema_version": 2,
        "experiment": "10-6",
        "run_id": run_id,
        "run_type": "real_parallel_serial_and_cascade_with_raw_receipts",
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
        "target": args.target,
        "git_commit": git_commit(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "playwright": importlib.metadata.version("playwright"),
            "parallel_chromium": default_parallel["chromium_version"],
            "serial_chromium": default_serial["chromium_version"],
            "cascade_chromium": cascade["chromium_version"],
        },
        "inputs": {
            "default_sites": [site.__dict__ for site in default_sites],
            "cascade_sites": [site.__dict__ for site in cascade_sites],
            "timeout_seconds": args.timeout,
        },
        "default_parallel": default_parallel,
        "default_serial": default_serial,
        "measured_speedup": speedup,
        "cascade_stress": cascade,
        "receipt_counts": {
            "browser": len(recorder.browser),
            "llm_all_attempts": len(recorder.llm),
            "llm_successful": len(successful_llm),
            "message_bus": len(recorder.bus),
        },
        "gates": gates,
        "overall_status": overall_status,
    }
    evidence_path = run_dir / "evidence.json"
    write_json(evidence_path, evidence)

    artifact_paths = [evidence_path, browser_path, llm_path, bus_path]
    manifest = {
        "schema_version": 1,
        "experiment": "10-6",
        "run_id": run_id,
        "generated_at": utc_now(),
        "git_commit": evidence["git_commit"],
        "runtime_source_sha256": source_hashes,
        "input_sha256": {
            "default_sites_canonical_json": sha256_bytes(canonical_bytes(evidence["inputs"]["default_sites"])),
            "cascade_sites_canonical_json": sha256_bytes(canonical_bytes(evidence["inputs"]["cascade_sites"])),
        },
        "artifact_sha256": {
            path.name: sha256_file(path)
            for path in artifact_paths
        },
        "acceptance": {
            "overall_status": overall_status,
            "passed_gates": sum(item["status"] == "pass" for item in gates.values()),
            "total_gates": len(gates),
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
        "passed_gates": manifest["acceptance"]["passed_gates"],
        "total_gates": manifest["acceptance"]["total_gates"],
        "measured_speedup": speedup,
        "receipt_counts": evidence["receipt_counts"],
    }, ensure_ascii=False, indent=2))
    return 0 if overall_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parse_args())))
