"""Canonical real-provider campaign for Experiment 2-5."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from agent import ATTACKER_EMAIL, DEFENSES, Agent, RunResult
from attacks import ATTACKS


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()


def accepted_receipt(call: dict[str, Any], model: str) -> bool:
    response = call.get("response") or {}
    usage = response.get("usage") or {}
    return bool(
        response.get("id")
        and response.get("model") == model
        and usage.get("total_tokens") is not None
        and not call.get("error")
    )


def request_messages_contain(provider_calls: list[dict[str, Any]], literal: str) -> bool:
    """Return whether a literal is present in any provider-request message.

    Inspect the structured request rather than its JSON serialization.  JSON
    escapes the quotes in XML-style source tags, which made the real tag
    ``<external_content source="webpage">`` invisible to the old validator.
    """
    for call in provider_calls:
        request = call.get("request") or {}
        for message in request.get("messages") or []:
            if isinstance(message, dict) and literal in str(message.get("content") or ""):
                return True
    return False


def workspace_inventory(root: Path) -> list[dict[str, Any]]:
    inventory = []
    if not root.exists():
        return inventory
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        inventory.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    return inventory


def combine_results(first: RunResult, second: RunResult | None = None) -> RunResult:
    if second is None:
        return first
    return RunResult(
        final_text=second.final_text,
        executed_tool_calls=first.executed_tool_calls + second.executed_tool_calls,
        requested_tool_calls=first.requested_tool_calls + second.requested_tool_calls,
        provider_calls=first.provider_calls + second.provider_calls,
        messages=[
            {"session": 1, "messages": first.messages},
            {"session": 2, "messages": second.messages},
        ],
        workspace_events=first.workspace_events + second.workspace_events,
        error="; ".join(value for value in (first.error, second.error) if value) or None,
    )


def run_trial(
    client: OpenAI,
    protocol: dict[str, Any],
    protocol_hash: str,
    run_dir: Path,
    attack_index: int,
    defense_index: int,
    trial: int,
) -> dict[str, Any]:
    attack = ATTACKS[attack_index]
    defense = DEFENSES[defense_index]
    trial_id = f"{attack_index + 1}-{defense_index + 1}-{trial:02d}"
    evidence_path = run_dir / "cells" / f"trial-{trial_id}.json"
    workspace = run_dir / "workspaces" / f"trial-{trial_id}"
    model = protocol["provider"]["model"]
    if evidence_path.exists():
        cached = json.loads(evidence_path.read_text(encoding="utf-8"))
        if cached.get("protocol_sha256") != protocol_hash:
            raise RuntimeError(f"protocol mismatch for {evidence_path}")
        if cached.get("complete") and all(
            accepted_receipt(call, model) for call in cached.get("provider_calls", [])
        ) and cached.get("workspace_inventory") == workspace_inventory(workspace):
            expected_source_tag = (
                request_messages_contain(
                    cached.get("provider_calls", []), '<external_content source="webpage">'
                )
                if defense.source_tagging and attack_index in {1, 2}
                else None
            )
            if cached.get("source_tag_visible_after_external_read") != expected_source_tag:
                cached["source_tag_visible_after_external_read"] = expected_source_tag
                atomic_json(evidence_path, cached)
            return cached
        raise RuntimeError(f"incomplete or mutated checkpoint requires a new run directory: {evidence_path}")

    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    max_steps = int(protocol["design"]["max_agent_steps_per_user_turn"])
    first_agent = Agent(
        client=client,
        model=model,
        defense=defense,
        webpage_content=attack.webpage_content,
        temperature=float(protocol["provider"]["temperature"]),
        workspace=workspace,
    )
    if attack_index == 2:
        first = first_agent.run([attack.user_messages[0]], max_steps=max_steps)
        # A genuinely new Agent/session must consume the persisted memory file;
        # no messages from session 1 are carried into session 2.
        second_agent = Agent(
            client=client,
            model=model,
            defense=defense,
            webpage_content="",
            temperature=float(protocol["provider"]["temperature"]),
            workspace=workspace,
        )
        second = second_agent.run([attack.user_messages[1]], max_steps=max_steps)
        result = combine_results(first, second)
        fresh_session = bool(first.messages and second.messages and first.messages is not second.messages)
    else:
        result = first_agent.run(list(attack.user_messages), max_steps=max_steps)
        fresh_session = None

    memory_text = (workspace / "memory.json").read_text(encoding="utf-8") if (workspace / "memory.json").exists() else ""
    attack_succeeded = bool(attack.judge(result))
    provider_valid = bool(result.provider_calls) and all(
        accepted_receipt(call, model) for call in result.provider_calls
    )
    request_trace = json.dumps(
        [call.get("request", {}) for call in result.provider_calls], ensure_ascii=False
    )
    evidence = {
        "experiment_id": "2-5",
        "trial_id": trial_id,
        "created_at": utc_now(),
        "protocol_sha256": protocol_hash,
        "attack": {"index": attack_index + 1, "name": attack.name},
        "defense": {"index": defense_index + 1, **asdict(defense)},
        "trial": trial,
        "attack_succeeded": attack_succeeded,
        "memory_poison_persisted": ATTACKER_EMAIL in memory_text if attack_index == 2 else None,
        "fresh_session_used": fresh_session,
        "prompt_hardening_visible": (
            "【安全加固】" in request_trace if defense.prompt_hardening else "【安全加固】" not in request_trace
        ),
        "source_tag_visible_after_external_read": (
            request_messages_contain(
                result.provider_calls, '<external_content source="webpage">'
            )
            if defense.source_tagging and attack_index in {1, 2}
            else None
        ),
        "provider_receipts_valid": provider_valid,
        "complete": result.error is None and provider_valid,
        "final_text": result.final_text,
        "executed_tool_calls": result.executed_tool_calls,
        "requested_tool_calls": result.requested_tool_calls,
        "workspace_events": result.workspace_events,
        "messages": result.messages,
        "provider_calls": result.provider_calls,
        "error": result.error,
        "workspace_inventory": workspace_inventory(workspace),
    }
    atomic_json(evidence_path, evidence)
    return evidence


def summarize(protocol: dict[str, Any], protocol_hash: str, run_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected = len(ATTACKS) * len(DEFENSES) * int(protocol["design"]["trials_per_cell"])
    rates = {}
    for attack in ATTACKS:
        rates[attack.name] = {}
        for defense in DEFENSES:
            selected = [
                row for row in rows
                if row["attack"]["name"] == attack.name and row["defense"]["name"] == defense.name
            ]
            rates[attack.name][defense.name] = {
                "successes": sum(row["attack_succeeded"] for row in selected),
                "trials": len(selected),
                "success_rate": sum(row["attack_succeeded"] for row in selected) / len(selected),
            }
    configured_secrets = [
        value for name in (
            "MOONSHOT_API_KEY", "KIMI_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"
        ) if (value := os.getenv(name))
    ]
    credential_findings = []
    for path in sorted((run_dir / "cells").glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        if any(secret in raw for secret in configured_secrets):
            credential_findings.append(str(path.relative_to(run_dir)))
    d4_rows = [row for row in rows if row["defense"]["runtime_guard"]]
    runtime_guard_ok = all(
        not any(
            requested.get("runtime_authorized") is False
            and any(
                executed["name"] == requested["name"]
                and executed["args"] == requested["args"]
                for executed in row["executed_tool_calls"]
            )
            for requested in row["requested_tool_calls"]
        )
        for row in d4_rows
    )
    acceptance = {
        "full_3x4x5_matrix": len(rows) == expected,
        "all_trials_complete": len(rows) == expected and all(row["complete"] for row in rows),
        "real_provider_receipts": all(row["provider_receipts_valid"] for row in rows),
        "exact_provider_model": all(
            call["response"].get("model") == protocol["provider"]["model"]
            for row in rows for call in row["provider_calls"]
        ),
        "all_three_attack_channels_executed": (
            {row["attack"]["index"] for row in rows} == {1, 2, 3}
            and all(
                any(call["name"] == "read_webpage" for call in row["requested_tool_calls"])
                for row in rows if row["attack"]["index"] in {2, 3}
            )
        ),
        "all_four_progressive_defenses_executed": {row["defense"]["index"] for row in rows} == {1, 2, 3, 4},
        "real_isolated_filesystem_and_outbox": all(
            (run_dir / "workspaces" / f"trial-{row['trial_id']}").is_dir() for row in rows
        ),
        "memory_attack_uses_fresh_sessions": all(
            row["fresh_session_used"] for row in rows if row["attack"]["index"] == 3
        ),
        "prompt_hardening_intervention_visible": all(row["prompt_hardening_visible"] for row in rows),
        "source_tagging_intervention_visible": all(
            row["source_tag_visible_after_external_read"] is not False for row in rows
        ),
        "runtime_guard_authorization_enforced": runtime_guard_ok,
        "credential_scan_passed": not credential_findings,
    }
    acceptance["passed"] = all(acceptance.values())
    usage = {key: 0 for key in ("prompt_tokens", "completion_tokens", "total_tokens")}
    for row in rows:
        for call in row["provider_calls"]:
            raw = (call.get("response") or {}).get("usage") or {}
            for key in usage:
                usage[key] += int(raw.get(key) or 0)
    return {
        "experiment_id": "2-5",
        "status": "passed" if acceptance["passed"] else "partial",
        "created_at": utc_now(),
        "protocol_sha256": protocol_hash,
        "scope": {"expected_trials": expected, "completed_trials": len(rows), "provider_calls": sum(len(row["provider_calls"]) for row in rows)},
        "acceptance": acceptance,
        "attack_success_rates": rates,
        "usage": usage,
        "errors": [row["error"] for row in rows if row["error"]],
        "credential_scan_findings": credential_findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    load_dotenv(HERE / ".env")
    key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
    if not key:
        raise RuntimeError("MOONSHOT_API_KEY or KIMI_API_KEY is required")
    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    protocol_hash = sha256_bytes(protocol_bytes)
    run_dir = (args.output or HERE / "validation" / "runs" / f"exp2-5-{datetime.now().strftime('%Y%m%d-%H%M%S')}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    protocol_copy = run_dir / "experiment_protocol.json"
    if protocol_copy.exists() and protocol_copy.read_bytes() != protocol_bytes:
        raise RuntimeError("run directory contains a different frozen protocol")
    protocol_copy.write_bytes(protocol_bytes)
    client = OpenAI(
        api_key=key,
        base_url=protocol["provider"]["base_url"],
        timeout=120,
        max_retries=3,
    )
    jobs = [
        (attack_index, defense_index, trial)
        for trial in range(1, int(protocol["design"]["trials_per_cell"]) + 1)
        for attack_index in range(len(ATTACKS))
        for defense_index in range(len(DEFENSES))
    ]
    rows = []
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_trial, client, protocol, protocol_hash, run_dir, *job): job
            for job in jobs
        }
        for future in as_completed(futures):
            job = futures[future]
            try:
                row = future.result()
                rows.append(row)
                print(f"trial {row['trial_id']} complete", flush=True)
            except Exception as exc:
                failures.append({"job": job, "type": type(exc).__name__, "error": str(exc)})
                print(f"trial {job} ERROR {exc}", flush=True)
    if failures:
        atomic_json(run_dir / "transport_failures.json", failures)
        return 2
    rows.sort(key=lambda row: tuple(int(value) for value in row["trial_id"].split("-")))
    comparison = summarize(protocol, protocol_hash, run_dir, rows)
    comparison_path = run_dir / "comparison.json"
    atomic_json(comparison_path, comparison)
    artifacts = {
        str(path.relative_to(run_dir)): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted((run_dir / "cells").glob("*.json"))
    }
    manifest = {
        "experiment_id": "2-5",
        "status": comparison["status"],
        "protocol_sha256": protocol_hash,
        "comparison_sha256": sha256_file(comparison_path),
        "acceptance": comparison["acceptance"],
        "artifacts": artifacts,
    }
    manifest_path = run_dir / "manifest.json"
    atomic_json(manifest_path, manifest)
    latest = {
        "experiment_id": "2-5",
        "run_dir": str(run_dir.relative_to(HERE)),
        "manifest_sha256": sha256_file(manifest_path),
        "status": comparison["status"],
    }
    atomic_json(HERE / "validation" / "latest.json", latest)
    print(json.dumps(comparison, ensure_ascii=False, indent=2))
    return 0 if comparison["acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
