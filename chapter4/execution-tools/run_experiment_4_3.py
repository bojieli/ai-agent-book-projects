#!/usr/bin/env python3
"""Run the manuscript-scope Experiment 4-3 campaign over real MCP stdio."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "experiment_protocol.json"
SERVER = HERE / "server.py"
VALIDATION = HERE / "validation" / "experiment_4_3"
CREDENTIAL = re.compile(r"\b(?:sk|gh[opusr])-[A-Za-z0-9_-]{12,}\b")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n"
    if CREDENTIAL.search(text):
        raise ValueError(f"credential-shaped string in {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unwrap(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if structured:
        return structured
    texts = [getattr(item, "text", None) for item in getattr(result, "content", [])]
    texts = [item for item in texts if item]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]
    return texts


async def run(
    campaign_id: str,
    android_container: str,
    github_head_branch: str,
    github_base_branch: str,
) -> Path:
    run_dir = VALIDATION / campaign_id
    run_dir.mkdir(parents=True, exist_ok=False)
    workspace = run_dir / "workspace"
    workspace.mkdir()
    outside = run_dir / "outside-witness.txt"
    outside.write_text("MUST-NOT-CHANGE\n", encoding="utf-8")
    outside_before = sha(outside)
    write_json(run_dir / "protocol.json", json.loads(PROTOCOL.read_text(encoding="utf-8")))

    env = os.environ.copy()
    if env.get("KIMI_API_KEY") or env.get("MOONSHOT_API_KEY"):
        review_provider = "kimi"
        review_model = "kimi-k3"
    else:
        review_provider = "openrouter"
        review_model = "openai/gpt-4.1-mini"
    env.update({
        "WORKSPACE_DIR": str(workspace),
        "REQUIRE_APPROVAL_FOR_DANGEROUS_OPS": "true",
        "AUTO_VERIFY_CODE": "true",
        "AUTO_SUMMARIZE_COMPLEX_OUTPUT": "false",
        "EXECUTION_LLM_RECEIPT_PATH": str(run_dir / "llm_receipts.checkpoint.json"),
        "PROVIDER": review_provider,
        "MODEL": review_model,
        "ANDROID_WORLD_CONTAINER": android_container,
    })
    parameters = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)
    receipts: list[dict[str, Any]] = []

    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            schemas = [tool.model_dump(by_alias=True, exclude_none=True, mode="json") for tool in listed.tools]
            write_json(run_dir / "catalog.json", {
                "transport": "mcp-stdio", "server_name": initialized.serverInfo.name,
                "server_version": initialized.serverInfo.version, "schemas": schemas,
                "schema_sha256": hashlib.sha256(json.dumps(schemas, sort_keys=True).encode()).hexdigest(),
            })

            async def call(case: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
                started = time.perf_counter()
                try:
                    result = await session.call_tool(tool, arguments=arguments)
                    payload = unwrap(result)
                    is_error = bool(getattr(result, "isError", False) or getattr(result, "is_error", False))
                except Exception as exc:
                    payload, is_error = {"success": False, "error": f"{type(exc).__name__}: {exc}"}, True
                row = {
                    "case": case, "tool": tool, "arguments": arguments,
                    "transport": "mcp-stdio", "mcp_result_is_error": is_error,
                    "payload": payload,
                    "latency_seconds": round(time.perf_counter() - started, 3),
                }
                receipts.append(row)
                write_json(run_dir / "receipts" / f"{len(receipts):02d}_{case}.json", row)
                return row

            await call("python_valid_write", "file_write", {
                "path": "valid.py", "content": "def add(a, b):\n    return a + b\n", "overwrite": True})
            await call("python_invalid_rejected", "file_write", {
                "path": "invalid.py", "content": "def broken(:\n    pass\n", "overwrite": True})
            await call("javascript_valid_write", "file_write", {
                "path": "valid.js", "content": "const answer = 42;\nconsole.log(answer);\n", "overwrite": True})
            await call("javascript_invalid_rejected", "file_write", {
                "path": "invalid.js", "content": "const broken = ;\n", "overwrite": True})
            await call("verified_edit", "file_edit", {
                "path": "valid.py", "search": "a + b", "replace": "a - b"})
            await call("path_escape_rejected", "file_write", {
                "path": "../../escape.py", "content": "print('escape')\n", "overwrite": True})
            await call("terminal_safe", "virtual_terminal", {"command": "pwd && printf SAFE", "timeout": 10})
            await call("terminal_timeout", "virtual_terminal", {"command": "sleep 2", "timeout": 1})
            await call("terminal_danger_rejected", "virtual_terminal", {
                "command": "rm -rf ./should-never-execute", "timeout": 10})
            await call("python_docker_sandbox", "code_interpreter", {
                "language": "python", "timeout": 30,
                "code": "import os, json\nprint(json.dumps({'root': os.listdir('/'), 'network_proxy': os.environ.get('HTTPS_PROXY')}))\n"})
            await call("python_network_denied", "code_interpreter", {
                "language": "python", "timeout": 30,
                "code": "import urllib.request\ntry:\n print(urllib.request.urlopen('https://example.com', timeout=3).status)\nexcept Exception as e:\n print(type(e).__name__, str(e))\n"})
            await call("long_output_persisted", "code_interpreter", {
                "language": "python", "timeout": 30,
                "code": "for i in range(260): print(f'LINE-{i:03d}')\n"})
            await call("excel_formula_screenshot", "excel_create_with_formula_and_screenshot", {
                "output_path": "invoice.xlsx", "rows": [
                    {"item": "Compute", "quantity": 2, "unit_price": 12.5},
                    {"item": "Storage", "quantity": 3, "unit_price": 7.0}]})
            await call("real_webhook", "webhook_post", {
                "url": "https://postman-echo.com/post",
                "payload": {"experiment": "4-3", "marker": "REAL-WEBHOOK-RECEIPT"}})
            await call("real_browser", "browser_navigate", {
                "url": "https://example.com", "screenshot_path": "browser-example.png"})
            await call("calendar_preflight", "google_calendar_add", {
                "summary": "Experiment 4-3", "start_time": "2026-08-01T10:00:00+00:00",
                "end_time": "2026-08-01T10:30:00+00:00"})
            await call("github_pr_preflight", "github_create_pr", {
                "repo_name": "bojieli/ai-agent-book",
                "title": "feat(ch4): build Experiment 4-3 GUI environments",
                "body": "Experiment 4-3 evidence: real Android and X11 Computer Use execution.",
                "head_branch": github_head_branch, "base_branch": github_base_branch})
            await call("real_virtual_desktop", "virtual_desktop_execute", {
                "url": "https://example.com", "screenshot_path": "computer-use-example.png",
                "expected_title": "Example Domain"})
            await call("real_virtual_mobile", "virtual_mobile_execute", {
                "container_name": android_container, "screenshot_path": "android-wifi-settings.png"})
            await call("desktop_mobile_capabilities", "environment_capabilities", {})

    by_case = {row["case"]: row["payload"] for row in receipts}
    llm_path = run_dir / "llm_receipts.checkpoint.json"
    llm_receipts = json.loads(llm_path.read_text(encoding="utf-8")) if llm_path.is_file() else []
    write_json(run_dir / "llm_receipts.json", llm_receipts)
    long_path = by_case.get("long_output_persisted", {}).get("stdout_file")
    long_file = Path(long_path) if long_path else None
    retained_long_file = run_dir / "artifacts" / "long_output.full.txt"
    if long_file and long_file.is_file():
        retained_long_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(long_file, retained_long_file)
        long_evidence = {
            "path": str(retained_long_file.relative_to(run_dir)),
            "bytes": retained_long_file.stat().st_size,
            "sha256": sha(retained_long_file),
            "source_temp_path_sha256": hashlib.sha256(str(long_file).encode()).hexdigest(),
        }
    else:
        long_evidence = None
    caps = by_case.get("desktop_mobile_capabilities", {})
    gates = {
        "real_mcp_catalog_and_calls": len(schemas) >= 12 and len(receipts) == 20,
        "python_and_javascript_linter": (
            by_case["python_valid_write"].get("verification") == "passed"
            and by_case["javascript_valid_write"].get("verification") == "passed"
            and by_case["python_invalid_rejected"].get("success") is False
            and by_case["javascript_invalid_rejected"].get("success") is False),
        "file_edit_verified_and_escape_rejected": (
            by_case["verified_edit"].get("success") is True
            and by_case["path_escape_rejected"].get("success") is False
            and outside_before == sha(outside)),
        "terminal_timeout_and_llm_danger_review": (
            by_case["terminal_safe"].get("success") is True
            and by_case["terminal_timeout"].get("success") is False
            and by_case["terminal_danger_rejected"].get("success") is False
            and any(row.get("purpose") == "dangerous_operation_review"
                    and row.get("response", {}).get("id") and row.get("usage", {}).get("total_tokens")
                    and row.get("latency_seconds") is not None for row in llm_receipts)),
        "real_python_container_sandbox": (
            by_case["python_docker_sandbox"].get("success") is True
            and by_case["python_docker_sandbox"].get("sandbox", {}).get("kind") == "docker"
            and by_case["python_network_denied"].get("success") is True
            and "URLError" in by_case["python_network_denied"].get("stdout", "")),
        "long_output_truncated_and_persisted": bool(
            long_evidence and "省略" in by_case["long_output_persisted"].get("stdout", "")),
        "real_excel_formula_and_screenshot": by_case["excel_formula_screenshot"].get("success") is True,
        "real_webhook": by_case["real_webhook"].get("success") is True,
        "real_browser": by_case["real_browser"].get("success") is True,
        "real_calendar_mutation": by_case["calendar_preflight"].get("success") is True,
        "real_github_pr_mutation": by_case["github_pr_preflight"].get("success") is True,
        "real_email_mutation": False,
        "real_virtual_desktop_session": bool(
            by_case["real_virtual_desktop"].get("success") is True
            and by_case["real_virtual_desktop"].get("expected_title_matched") is True
            and by_case["real_virtual_desktop"].get("screenshot", {}).get("sha256")),
        "real_virtual_mobile_session": bool(
            by_case["real_virtual_mobile"].get("success") is True
            and by_case["real_virtual_mobile"].get("settings_activity")
            and by_case["real_virtual_mobile"].get("screenshot", {}).get("sha256")
            and caps.get("android_active_devices")),
        "credential_free_usage_latency_receipts": bool(llm_receipts) and all(
            row.get("response", {}).get("id") and row.get("usage", {}).get("total_tokens") is not None
            and row.get("latency_seconds") is not None for row in llm_receipts),
    }
    core_names = [name for name in gates if name not in {
        "real_calendar_mutation", "real_github_pr_mutation", "real_email_mutation",
        "real_virtual_desktop_session", "real_virtual_mobile_session"}]
    status = "passed" if all(gates.values()) else (
        "blocked" if all(gates[name] for name in core_names) else "failed")
    summary = {
        "experiment": "4-3", "campaign_id": campaign_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status, "official_complete": status == "passed",
        "gates": gates, "long_output_full_file": long_evidence,
        "blockers": [name for name, value in gates.items() if not value],
        "receipt_count": len(receipts), "llm_call_count": len(llm_receipts),
    }
    write_json(run_dir / "summary.json", summary)
    files = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append({"path": str(path.relative_to(run_dir)), "bytes": path.stat().st_size,
                          "sha256": sha(path)})
    manifest = {"experiment": "4-3", "campaign_id": campaign_id,
                "status": status, "official_complete": status == "passed", "files": files}
    write_json(run_dir / "manifest.json", manifest)
    write_json(VALIDATION / "latest.json", {
        "experiment": "4-3", "campaign_id": campaign_id, "status": status,
        "official_complete": status == "passed",
        "manifest": str((run_dir / "manifest.json").relative_to(HERE)),
        "manifest_sha256": sha(run_dir / "manifest.json")})
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-id", default=datetime.now(timezone.utc).strftime("real_mcp_%Y%m%dT%H%M%SZ"))
    parser.add_argument("--android-container", default=os.getenv("ANDROID_WORLD_CONTAINER", "exp4-3-android"))
    parser.add_argument("--github-head-branch", default="nonexistent-exp4-3")
    parser.add_argument("--github-base-branch", default="main")
    args = parser.parse_args()
    path = asyncio.run(run(
        args.campaign_id, args.android_container,
        args.github_head_branch, args.github_base_branch,
    ))
    print(path)
    status = json.loads((path / "summary.json").read_text(encoding="utf-8"))["status"]
    return 0 if status in {"passed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
