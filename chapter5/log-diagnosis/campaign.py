"""Acceptance campaign for Experiment 5-8 using live HTTP, an LLM, and GitHub MCP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parent
VALIDATION = ROOT / "validation"
ARCHITECTURE = """# Live diagnosis experiment architecture

The orchestrator calls a local HTTP order service. Refund flows MUST call
`verify_refund_eligibility` before `process_refund`. Inventory origin calls
have a 250 ms client deadline; on timeout the orchestrator MUST call the same
`check_stock` operation through the degraded cache route and finish normally.
Every trajectory turn records its measured HTTP latency and raw response.
"""
PRD = """# Live diagnosis experiment PRD

- R1 (P0): Every refund must call `verify_refund_eligibility` before
  `process_refund`; a refund without the check is a policy violation.
- R2 (P1): `check_stock` must complete within 250 ms. On origin timeout the
  orchestrator must use the degraded cache route; it must not simply fail.
- R3 (P1): Regression cases must cite the source trajectory ID and the exact
  observed turn where the violation is visible.
"""

INVENTORY_DEADLINE_SECONDS = 0.250
INVENTORY_ORIGIN_HEDGE_SECONDS = 0.100


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if re.search(r"\b(?:sk|gh[opusr])-[A-Za-z0-9_-]{12,}\b", text):
        raise ValueError(f"credential-shaped value in {path}")
    path.write_text(text, encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@dataclass
class Backend:
    provider: str
    model: str
    endpoint: str
    client: OpenAI
    receipt_checkpoint: Path | None = None


def _backend(provider: str) -> Backend:
    if provider == "ark":
        key = os.environ.get("ARK_API_KEY")
        endpoint = os.environ.get("ARK_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3"
        model = os.environ.get("ARK_MODEL") or "doubao-seed-1-6-250615"
    elif provider == "moonshot":
        key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
        endpoint = os.environ.get("MOONSHOT_BASE_URL") or "https://api.moonshot.cn/v1"
        model = os.environ.get("KIMI_MODEL") or "kimi-k3"
    else:
        key = os.environ.get("OPENAI_API_KEY")
        endpoint = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        model = os.environ.get("OPENAI_MODEL") or "gpt-5.6-luna"
    if not key:
        raise RuntimeError(f"missing credential for {provider}")
    return Backend(
        provider,
        model,
        endpoint,
        OpenAI(api_key=key, base_url=endpoint, timeout=180, max_retries=0),
    )


def _json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("response is not an object")
    return value


def _llm_call(
    backend: Backend,
    messages: list[dict[str, str]],
    purpose: str,
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    started = time.perf_counter()
    request = {
        "model": backend.model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    try:
        response = backend.client.chat.completions.create(**request)
    except Exception as exc:
        receipts.append(
            {
                "purpose": purpose,
                "provider": backend.provider,
                "endpoint": backend.endpoint,
                "request": request,
                "latency_s": round(time.perf_counter() - started, 3),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        if backend.receipt_checkpoint is not None:
            _write_json(backend.receipt_checkpoint, {"calls": receipts})
        raise
    usage = response.usage
    content = response.choices[0].message.content or ""
    receipt = {
        "purpose": purpose,
        "provider": backend.provider,
        "endpoint": backend.endpoint,
        "request": request,
        "latency_s": round(time.perf_counter() - started, 3),
        "response": {
            "id": response.id,
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason,
            "content": content,
        },
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        },
    }
    receipts.append(receipt)
    if backend.receipt_checkpoint is not None:
        _write_json(backend.receipt_checkpoint, {"calls": receipts})
    return _json_object(content)


def _http_call(
    base: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: float = 2.0,
) -> dict[str, Any]:
    raw = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        base + path,
        data=raw,
        method=method,
        headers={"content-type": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_raw = response.read()
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            return {
                "method": method,
                "path": path,
                "request": body,
                "http_status": response.status,
                "status": "success",
                "latency_ms": elapsed,
                "response": json.loads(response_raw),
            }
    except Exception as exc:
        return {
            "method": method,
            "path": path,
            "request": body,
            "http_status": getattr(exc, "code", None),
            "status": "error",
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }


def _trajectory(
    base: str,
    task_input: dict[str, Any],
    source_id: str,
    *,
    inject_regressions: bool = False,
) -> dict[str, Any]:
    """Run the HTTP orchestrator and return its measured trajectory.

    Correct behavior is the default.  The acceptance campaign can explicitly
    inject the historical issue #502 behavior to prove generated regression
    tests fail before the fix and pass against the production policy.
    """
    turns: list[dict[str, Any]] = []

    def call(tool: str, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        observed = _http_call(base, method, path, **kwargs)
        turns.append({"index": len(turns), "role": "tool", "module": "http_order_system", "tool": tool, **observed})
        return observed

    intent = task_input["intent"]
    order_id = task_input["order_id"]
    turns.append({"index": 0, "role": "user", "content": json.dumps(task_input, ensure_ascii=False)})
    call("query_order", "GET", f"/orders/{order_id}")
    final_status = "success"
    if intent == "refund":
        if inject_regressions:
            call("process_refund", "POST", "/refund/process", body={"order_id": order_id})
        else:
            eligibility = call(
                "verify_refund_eligibility",
                "POST",
                "/refund/eligibility",
                body={"order_id": order_id},
            )
            eligibility_response = eligibility.get("response")
            eligible = (
                eligibility["status"] == "success"
                and isinstance(eligibility_response, dict)
                and eligibility_response.get("eligible") is True
            )
            if eligible:
                refund = call(
                    "process_refund",
                    "POST",
                    "/refund/process",
                    body={"order_id": order_id},
                )
                if refund["status"] != "success":
                    final_status = "failed"
            else:
                final_status = "failed"
    elif intent == "order_status":
        # Hedge the origin request early enough to leave time for the cache
        # fallback inside the end-to-end 250 ms inventory deadline.
        inventory_started = time.perf_counter()
        origin_timeout = (
            INVENTORY_DEADLINE_SECONDS + 0.100
            if inject_regressions
            else INVENTORY_ORIGIN_HEDGE_SECONDS
        )
        origin = call(
            "check_stock", "GET", f"/inventory/{task_input['sku']}", timeout=origin_timeout
        )
        if origin["status"] == "error":
            if inject_regressions:
                final_status = "failed"
            else:
                elapsed = time.perf_counter() - inventory_started
                remaining = max(0.001, INVENTORY_DEADLINE_SECONDS - elapsed)
                degraded = call(
                    "check_stock",
                    "GET",
                    f"/inventory/{task_input['sku']}?degraded=1",
                    timeout=remaining,
                )
                if degraded["status"] != "success":
                    final_status = "failed"
    call("notify_user", "POST", "/notifications", body={"status": final_status})
    implementation = "buggy" if inject_regressions else "fixed"
    return {
        "trajectory_id": f"{source_id}::{implementation}",
        "source_trajectory_id": source_id,
        "implementation": implementation,
        "task_input": task_input,
        "final_status": final_status,
        "turns": turns,
    }


def _tool_turns(trajectory: dict[str, Any], tool: str) -> list[dict[str, Any]]:
    return [turn for turn in trajectory["turns"] if turn.get("tool") == tool]


def _evaluate(assertion: dict[str, Any], trajectory: dict[str, Any]) -> tuple[bool, str]:
    kind = assertion.get("type")
    params = assertion.get("params") or {}
    if kind == "step_present":
        tool = str(params.get("tool") or "")
        count = len(_tool_turns(trajectory, tool))
        return count > 0, f"{tool} calls={count}"
    if kind == "latency_under":
        tool = str(params.get("tool") or "")
        threshold = float(params.get("threshold_ms"))
        calls = _tool_turns(trajectory, tool)
        # A timed-out attempt is part of the operation and therefore counts.
        worst = max((float(turn["latency_ms"]) for turn in calls), default=float("inf"))
        return worst < threshold, f"{tool} max_latency_ms={worst:.3f}, threshold_ms={threshold:.3f}"
    if kind == "final_status_is":
        wanted = str(params.get("value") or "")
        actual = str(trajectory.get("final_status") or "")
        return actual == wanted, f"final_status={actual}, expected={wanted}"
    return False, f"unsupported assertion type: {kind}"


def _validate_diagnosis(payload: dict[str, Any], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    problems = payload.get("problems")
    if not isinstance(problems, list) or len(problems) < 2:
        raise ValueError("diagnosis must contain at least two evidence-backed problems")
    refs: set[str] = set()
    for problem in problems:
        if not isinstance(problem, dict):
            raise ValueError("problem is not an object")
        refs.add(str(problem.get("prd_ref")))
        tids = problem.get("trajectory_ids")
        turns = problem.get("focus_turns")
        if not isinstance(tids, list) or not tids or not all(tid in sources for tid in tids):
            raise ValueError(
                "problem contains an unknown trajectory reference; trajectory_ids must use only "
                + json.dumps(sorted(sources))
                + " (the source_trajectory_id values, without the ::buggy suffix)"
            )
        if not isinstance(turns, list) or not turns or not all(isinstance(value, int) for value in turns):
            raise ValueError("problem lacks concrete focus turns")
        if not all(
            any(0 <= value < len(sources[tid]["turns"]) for tid in tids)
            for value in turns
        ):
            raise ValueError("problem focus_turns contain indexes absent from every cited trajectory")
    if not {"R1", "R2"}.issubset(refs):
        raise ValueError(f"diagnosis did not cover both observed PRD violations: {sorted(refs)}")
    return problems


def _validate_tests(payload: dict[str, Any], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    tests = payload.get("test_cases")
    if not isinstance(tests, list) or len(tests) < 2:
        raise ValueError("at least two regression tests are required")
    kinds: set[str] = set()
    for test in tests:
        if not isinstance(test, dict) or test.get("trajectory_id") not in sources:
            raise ValueError("test has an unknown trajectory ID")
        focus = test.get("focus_turn")
        if not isinstance(focus, int) or not (0 <= focus < len(sources[test["trajectory_id"]]["turns"])):
            raise ValueError("test focus_turn is not an observed source turn")
        assertion = test.get("assertion")
        if not isinstance(assertion, dict) or assertion.get("type") not in {"step_present", "latency_under", "final_status_is"}:
            raise ValueError("test assertion is not executable by the frozen DSL")
        kinds.add(assertion["type"])
    if "step_present" not in kinds or "latency_under" not in kinds:
        raise ValueError("tests must cover both the missing prerequisite and latency violations")
    return tests


def _mcp_create_issue(title: str, body: str, repo: str, token: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    import asyncio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    owner, sep, name = repo.partition("/")
    if not sep:
        raise ValueError("repository must be owner/name")
    request = {
        "method": "create",
        "owner": owner,
        "repo": name,
        "title": title,
        "body": body,
    }
    params = StdioServerParameters(
        command="github-mcp-server",
        args=["stdio", "--toolsets=issues"],
        env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": token},
    )

    async def run() -> tuple[dict[str, Any], str]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = [tool.name for tool in tools.tools]
                if "issue_write" not in names:
                    raise RuntimeError("official GitHub MCP server did not expose issue_write")
                result = await session.call_tool("issue_write", request)
                text = "".join(getattr(item, "text", "") for item in result.content)
                return {"is_error": bool(result.isError), "content": text}, "github-mcp-server stdio"

    response, transport = asyncio.run(run())
    if response["is_error"]:
        raise RuntimeError(f"GitHub MCP create_issue failed: {response['content']}")
    match = re.search(r"https://github\.com/[^\s\"']+/issues/\d+", response["content"])
    if not match:
        raise RuntimeError(f"GitHub MCP response lacks issue URL: {response['content']}")
    return request, response, match.group(0)


def run(provider: str, run_id: str, repo: str) -> dict[str, Any]:
    run_dir = VALIDATION / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(run_dir)
    run_dir.mkdir(parents=True)
    (run_dir / "architecture.md").write_text(ARCHITECTURE, encoding="utf-8")
    (run_dir / "PRD.md").write_text(PRD, encoding="utf-8")
    shutil.copy2(ROOT / "http_service.py", run_dir / "http_service.py")

    port = _free_port()
    service_log = (run_dir / "service.stdout.jsonl").open("w", encoding="utf-8")
    service_err = (run_dir / "service.stderr.log").open("w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-u", str(ROOT / "http_service.py"), "--port", str(port)],
        stdout=service_log,
        stderr=service_err,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            health = _http_call(base, "GET", "/health", timeout=0.2)
            if health["status"] == "success":
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("local HTTP service did not become healthy")

        source_tasks = {
            "HTTP-RF-001": {"intent": "refund", "order_id": "ORD-58-A"},
            "HTTP-INV-001": {"intent": "order_status", "order_id": "ORD-58-B", "sku": "SKU-42"},
        }
        sources = {
            tid: _trajectory(base, task, tid, inject_regressions=True)
            for tid, task in source_tasks.items()
        }
        with (run_dir / "production_trajectories.jsonl").open("w", encoding="utf-8") as handle:
            for trajectory in sources.values():
                handle.write(json.dumps(trajectory, ensure_ascii=False) + "\n")

        backend = _backend(provider)
        receipts: list[dict[str, Any]] = []
        backend.receipt_checkpoint = run_dir / "provider_receipts.checkpoint.json"
        diagnosis_prompt = f"""Architecture:\n{ARCHITECTURE}\n\nPRD:\n{PRD}\n\nObserved production trajectories:\n{json.dumps(list(sources.values()), ensure_ascii=False, indent=2)}\n\nDiagnose only evidenced violations. Return JSON {{\"problems\":[...]}}. Each problem must contain title, priority, module, description, suggestion, prd_ref, trajectory_ids, focus_turns, and suggested_assignee. focus_turns must cite exact integer indexes in the supplied trajectories.

The ONLY allowed trajectory_ids strings are the exact source_trajectory_id values {json.dumps(sorted(sources))}. Do not copy the implementation-specific trajectory_id values ending in ::buggy. For R1 cite HTTP-RF-001 and exact visible turn indexes; for R2 cite HTTP-INV-001 and exact visible turn indexes."""
        problems: list[dict[str, Any]] | None = None
        diagnosis_error = ""
        for attempt in range(1, 4):
            payload = _llm_call(
                backend,
                [
                    {"role": "system", "content": "You are a production Agent diagnostician. Return one JSON object only and never invent evidence."},
                    {"role": "user", "content": diagnosis_prompt + (f"\n\nPrior validation error: {diagnosis_error}" if diagnosis_error else "")},
                ],
                f"diagnosis_attempt_{attempt}",
                receipts,
            )
            try:
                problems = _validate_diagnosis(payload, sources)
                break
            except ValueError as exc:
                diagnosis_error = str(exc)
        if problems is None:
            raise RuntimeError(f"model diagnosis never passed evidence gates: {diagnosis_error}")
        _write_json(run_dir / "diagnosis.json", {"problems": problems})

        test_prompt = f"""PRD:\n{PRD}\n\nModel-diagnosed problems:\n{json.dumps(problems, ensure_ascii=False, indent=2)}\n\nCreate executable regression tests. Return JSON {{\"test_cases\":[...]}}. Each test needs test_id, trajectory_id, focus_turn, description, and assertion. Allowed assertions only:\n- {{\"type\":\"step_present\",\"params\":{{\"tool\":\"...\"}}}}\n- {{\"type\":\"latency_under\",\"params\":{{\"tool\":\"...\",\"threshold_ms\":250}}}}\n- {{\"type\":\"final_status_is\",\"params\":{{\"value\":\"success\"}}}}\nTests must cite exact source trajectory IDs and turns. Cover both R1 and R2, expressing the correct fixed behavior.

The ONLY allowed trajectory_id strings are {json.dumps(sorted(sources))}; use HTTP-RF-001 for the refund prerequisite assertion and HTTP-INV-001 for the inventory latency assertion. Do not append ::buggy."""
        tests: list[dict[str, Any]] | None = None
        replay_records: list[dict[str, Any]] = []
        feedback = ""
        for attempt in range(1, 4):
            payload = _llm_call(
                backend,
                [
                    {"role": "system", "content": "You are a regression-test engineer. Return one JSON object only."},
                    {"role": "user", "content": test_prompt + (f"\n\nPrior executable validation feedback:\n{feedback}" if feedback else "")},
                ],
                f"regression_generation_attempt_{attempt}",
                receipts,
            )
            try:
                candidate = _validate_tests(payload, sources)
                observed: list[dict[str, Any]] = []
                for test in candidate:
                    source_id = test["trajectory_id"]
                    task = sources[source_id]["task_input"]
                    buggy_traj = _trajectory(
                        base, task, source_id, inject_regressions=True
                    )
                    fixed_traj = _trajectory(base, task, source_id)
                    buggy_passed, buggy_detail = _evaluate(test["assertion"], buggy_traj)
                    fixed_passed, fixed_detail = _evaluate(test["assertion"], fixed_traj)
                    observed.append(
                        {
                            "test": test,
                            "buggy": {"passed": buggy_passed, "detail": buggy_detail, "trajectory": buggy_traj},
                            "fixed": {"passed": fixed_passed, "detail": fixed_detail, "trajectory": fixed_traj},
                        }
                    )
                replay_records = observed
                if not all(not item["buggy"]["passed"] and item["fixed"]["passed"] for item in observed):
                    raise ValueError(
                        "every generated test must reproduce on buggy and pass on fixed: "
                        + json.dumps(
                            [
                                {
                                    "test_id": item["test"].get("test_id"),
                                    "buggy": item["buggy"]["detail"],
                                    "buggy_passed": item["buggy"]["passed"],
                                    "fixed": item["fixed"]["detail"],
                                    "fixed_passed": item["fixed"]["passed"],
                                }
                                for item in observed
                            ],
                            ensure_ascii=False,
                        )
                    )
                tests = candidate
                break
            except ValueError as exc:
                feedback = str(exc)
        if tests is None:
            raise RuntimeError(f"model-generated tests never passed live replay: {feedback}")
        _write_json(run_dir / "regression_tests.json", {"test_cases": tests})
        _write_json(run_dir / "live_replays.json", {"results": replay_records})
        _write_json(run_dir / "provider_receipts.json", {"calls": receipts})

        issue_title = f"[Experiment 5-8][auto-diagnosis] Live HTTP regression findings ({run_id})"
        issue_body = (
            "This issue was created automatically by the Chapter 5 Experiment 5-8 acceptance campaign.\n\n"
            "## Evidence-backed diagnosis\n\n"
            + "\n".join(
                f"- **{p['priority']} {p['title']}** ({p['prd_ref']}): {p['description']} "
                f"Trajectories: {', '.join(p['trajectory_ids'])}; turns: {p['focus_turns']}."
                for p in problems
            )
            + "\n\n## Generated regression tests\n\n"
            + "\n".join(
                f"- `{t['test_id']}` cites `{t['trajectory_id']}` turn {t['focus_turn']}: "
                f"`{json.dumps(t['assertion'], ensure_ascii=False)}`"
                for t in tests
            )
            + "\n\nThe campaign replayed each test against the live buggy and fixed HTTP orchestrators: "
            "all tests failed on buggy behavior and passed on fixed behavior."
        )
        token = subprocess.run(
            ["gh", "auth", "token"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        ).stdout.strip()
        mcp_request, mcp_response, issue_url = _mcp_create_issue(issue_title, issue_body, repo, token)
        _write_json(
            run_dir / "github_mcp_receipt.json",
            {
                "server": "official github/github-mcp-server",
                "transport": "stdio",
                "tool": "issue_write(method=create)",
                "request": mcp_request,
                "response": mcp_response,
                "issue_url": issue_url,
                "credential_free": True,
            },
        )

        gates = {
            "real_local_http_trajectories": len(sources) == 2 and all(t["turns"] for t in sources.values()),
            "measured_latency_and_raw_http": all(
                all("latency_ms" in turn and ("response" in turn or "error" in turn) for turn in trajectory["turns"] if turn.get("role") == "tool")
                for trajectory in sources.values()
            ),
            "live_model_diagnosis": bool(problems) and bool(receipts),
            "diagnosis_references_trajectories_and_turns": all(p.get("trajectory_ids") and p.get("focus_turns") for p in problems),
            "live_model_generated_executable_tests": bool(tests),
            "buggy_failures_reproduced": all(not item["buggy"]["passed"] for item in replay_records),
            "fixed_system_passes": all(item["fixed"]["passed"] for item in replay_records),
            "official_github_mcp_issue_created": issue_url.startswith(f"https://github.com/{repo}/issues/"),
            "raw_provider_receipts_complete": all(
                receipt.get("response")
                and receipt.get("usage", {}).get("prompt_tokens") is not None
                and receipt.get("usage", {}).get("completion_tokens") is not None
                and receipt.get("latency_s") is not None
                for receipt in receipts
            ),
        }
        official_complete = all(gates.values())
        process.terminate()
        process.wait(timeout=5)
        service_log.close()
        service_err.close()
        artifacts = {
            str(path.relative_to(run_dir)): {"sha256": _sha(path), "bytes": path.stat().st_size}
            for path in sorted(run_dir.rglob("*"))
            if path.is_file()
        }
        manifest = {
            "schema_version": "1.0",
            "experiment": "5-8",
            "run_id": run_id,
            "generated_at_utc": _utc(),
            "provider": backend.provider,
            "model": backend.model,
            "service": {"kind": "real local HTTP subprocess", "base_url": base, "pid": process.pid},
            "source_trajectory_ids": sorted(sources),
            "model_call_count": len(receipts),
            "github_issue_url": issue_url,
            "gates": gates,
            "artifacts": artifacts,
            "official_complete": official_complete,
        }
        _write_json(run_dir / "manifest.json", manifest)
        if not official_complete:
            raise RuntimeError("Experiment 5-8 gates failed")
        latest = {
            "experiment": "5-8",
            "run_id": run_id,
            "manifest": str((run_dir / "manifest.json").relative_to(ROOT)),
            "manifest_sha256": _sha(run_dir / "manifest.json"),
            "official_complete": True,
        }
        _write_json(VALIDATION / "latest.json", latest)
        return manifest
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if not service_log.closed:
            service_log.close()
        if not service_err.closed:
            service_err.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("ark", "moonshot", "openai"), default="ark")
    parser.add_argument("--repo", default="bojieli/ai-agent-book")
    parser.add_argument("--run-id", default=f"exp5-8-live-http-mcp-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    args = parser.parse_args()
    print(json.dumps(run(args.provider, args.run_id, args.repo), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
