"""Run and package the strict real-provider Experiment 10-1 campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from agent import STAGE_PROMPTS, STAGE_TOOLS, StagedAgent
from config import Config
from evidence import RecordingClient


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha256(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def usage_cost(usage: dict, pricing: dict) -> dict:
    prompt = int(usage["prompt_tokens"])
    cached = min(prompt, int(usage["cached_prompt_tokens"]))
    completion = int(usage["completion_tokens"])
    cost = (
        (prompt - cached) * pricing["uncached_input_per_million"]
        + cached * pricing["cached_input_per_million"]
        + completion * pricing["output_per_million"]
    ) / 1_000_000
    return {
        **usage,
        "uncached_prompt_tokens": prompt - cached,
        "total_tokens": prompt + completion,
        "cost": round(cost, 9),
        "currency": pricing["currency"],
        "pricing_as_of": pricing["as_of"],
        "pricing_source_url": pricing["source_url"],
    }


def validate_manifest(manifest: dict) -> list[str]:
    errors = []
    result = manifest["result"]
    transitions = [event["kind"] for event in result["transition_events"]]
    stages = [event["stage"] for event in result["stage_entries"]]
    receipts = manifest["provider_receipts"]
    successful_receipts = [
        receipt for receipt in receipts
        if receipt["response_id"] and receipt["usage_complete"]
    ]
    required = manifest["protocol"]["value"]["required_transitions"]
    cursor = 0
    for name in transitions:
        if cursor < len(required) and name == required[cursor]:
            cursor += 1
    checks = {
        "approved": result["approved"] and result["completion_reason"] == "approved",
        "all_stages": all(stage in stages for stage in ("requirements", "implementation", "review")),
        "transition_sequence": cursor == len(required),
        "rollback": result["revision_count"] >= 1 and stages.count("implementation") >= 2,
        "review_reentry": stages.count("review") >= 2,
        # Failed attempts are retained as evidence instead of being deleted.
        # Every receipt must therefore be either a complete success or an
        # explicitly typed provider error.
        "receipts": bool(successful_receipts) and all(
            (r["response_id"] and r["usage_complete"]) or r.get("error_type")
            for r in receipts
        ),
        "provider": all(r["provider"] == "moonshot" for r in receipts),
        "usage": manifest["usage_and_cost"]["requests"] == len(successful_receipts),
        "tool_evidence": all(
            any(log["action"] == action for log in manifest["execution_logs"])
            for action in ("run_linter", "run_tests", "analyze_complexity", "审查不通过 -> 回退实现")
        ),
        "files": bool(manifest["workspace"]["files"]),
        "credentials_absent": manifest["security"]["credentials_absent_from_receipts"],
    }
    fault_required = manifest["protocol"]["value"].get("review_fault_injection", {}).get(
        "enabled", False
    )
    if fault_required:
        events = manifest.get("review_fault_events") or []
        markers = {event.get("marker") for event in events}
        final_sources = manifest.get("workspace", {}).get("file_contents", {}).values()
        checks["controlled_fault_injected"] = (
            len(events) == 1 and events[0].get("source_changed") is True
        )
        checks["controlled_fault_repaired"] = bool(markers) and all(
            marker and all(marker not in source for source in final_sources)
            for marker in markers
        )
    manifest["acceptance_checks"] = checks
    errors.extend(name for name, ok in checks.items() if not ok)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()

    protocol_raw = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_raw)
    run_id = datetime.now(timezone.utc).strftime("exp10-1-kimi-k3-%Y%m%dT%H%M%SZ")
    run_dir = (args.run_dir or HERE / "runs" / run_id).resolve()
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SystemExit(f"run directory is not empty: {run_dir}")
    receipt_dir = run_dir / "raw_provider_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        raise SystemExit("MOONSHOT_API_KEY is required for the official real-provider campaign")
    Config.API_KEY = api_key
    Config.BASE_URL = protocol["backend"]["base_url"]
    Config.MODEL = protocol["backend"]["model"]
    # Kimi K3 rejects any explicit value other than 1.  Using its supported
    # value avoids manufacturing one failed 400 receipt before every real call.
    Config.TEMPERATURE = 1.0
    inner = OpenAI(api_key=api_key, base_url=Config.BASE_URL)
    client = RecordingClient(
        inner, receipt_dir, provider=protocol["backend"]["provider"], base_url=Config.BASE_URL
    )

    source_files = ["agent.py", "config.py", "tools.py", "simulated_user.py", "evidence.py",
                    "run_official_experiment.py", "experiment_protocol.json"]
    started = time.perf_counter()
    agent = StagedAgent(
        max_revisions=protocol["limits"]["max_revisions"],
        max_total_steps=protocol["limits"]["max_total_steps"],
        verbose=True,
        interactive=False,
        client=client,
        inject_first_review_fault=protocol.get("review_fault_injection", {}).get("enabled", False),
    )
    result = agent.run(protocol["task"])
    duration = round(time.perf_counter() - started, 3)

    receipts = []
    for raw in client.receipts:
        response = raw.get("response") or {}
        usage = response.get("usage") or {}
        receipts.append({
            "call_index": raw["call_index"],
            "path": str(Path(raw["receipt_path"]).relative_to(run_dir)),
            "provider": raw["provider"],
            "stage": raw["context"].get("stage"),
            "step": raw["context"].get("step"),
            "duration_s": raw["duration_s"],
            "response_id": response.get("id"),
            "response_model": response.get("model"),
            "finish_reason": ((response.get("choices") or [{}])[0]).get("finish_reason"),
            "usage_complete": all(usage.get(k) is not None for k in ("prompt_tokens", "completion_tokens")),
            "error_type": (raw.get("error") or {}).get("type"),
            "sha256": sha256(Path(raw["receipt_path"])),
        })

    workspace_files = {}
    for name, content in agent.workspace.files.items():
        out = run_dir / "workspace" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        workspace_files[name] = {"path": str(out.relative_to(run_dir)), "sha256": sha256(out)}

    manifest = {
        "schema_version": "1.0",
        "experiment": "10-1",
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": duration,
        "protocol": {
            "path": "experiment_protocol.json",
            "sha256": hashlib.sha256(protocol_raw).hexdigest(),
            "value": protocol,
        },
        "source_hashes": {name: sha256(HERE / name) for name in source_files},
        "stage_contract": {
            stage: {
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "tools_sha256": json_sha256(STAGE_TOOLS[stage]),
                "tool_names": [tool["function"]["name"] for tool in STAGE_TOOLS[stage]],
            }
            for stage, prompt in STAGE_PROMPTS.items()
        },
        "result": result,
        "execution_logs": agent.logs,
        "history": agent.history,
        "workspace": {
            "requirements": agent.workspace.requirements,
            "review_issues": agent.workspace.review_issues,
            "files": workspace_files,
            # Needed only for validating that the injected canary was actually
            # removed.  The same content is also persisted under workspace/.
            "file_contents": dict(agent.workspace.files),
        },
        "review_fault_events": agent.review_fault_events,
        "provider_receipts": receipts,
        "usage_and_cost": usage_cost(client.usage(), protocol["backend"]["pricing"]),
        "security": {
            "credentials_absent_from_receipts": all(
                api_key not in Path(raw["receipt_path"]).read_text(encoding="utf-8")
                for raw in client.receipts
            )
        },
        "acceptance_checks": {},
        "official_complete": False,
    }
    errors = validate_manifest(manifest)
    manifest["validation_errors"] = errors
    manifest["official_complete"] = not errors
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "manifest": str(manifest_path),
        "official_complete": manifest["official_complete"],
        "validation_errors": errors,
        "usage_and_cost": manifest["usage_and_cost"],
    }, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
