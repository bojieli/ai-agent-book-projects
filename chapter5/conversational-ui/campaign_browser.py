#!/usr/bin/env python3
"""Live Vite-HMR/browser campaign for Chapter 5, Experiment 5-11."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from openai import OpenAI
from playwright.sync_api import sync_playwright

import agent


HERE = Path(__file__).resolve().parent
ROUNDS = [
    {
        "requirement": "把发送按钮和用户消息气泡的主题色从绿色改成蓝色，必须使用 #2563eb。",
        "kind": "color",
        "expected": "rgb(37, 99, 235)",
    },
    {
        "requirement": "把整个界面的字体换成等宽字体（monospace），保留上一轮蓝色主题。",
        "kind": "font",
        "expected": "monospace",
    },
    {
        "requirement": "把顶部标题改成“我的专属客服”，保留前两轮的蓝色和等宽字体。",
        "kind": "title",
        "expected": "我的专属客服",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_url(url: str, timeout: float = 45.0) -> dict[str, Any] | str:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                body = response.read().decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return body
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(0.25)
    raise TimeoutError(f"server did not become ready: {url}; last={last_error}")


def resolve_backend(provider: str, model: str | None) -> tuple[OpenAI, str, str]:
    choices = {
        "ark": (os.getenv("ARK_API_KEY"), "https://ark.cn-beijing.volces.com/api/v3", model or "doubao-seed-1-6-flash-250615"),
        "moonshot": (os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY"), "https://api.moonshot.cn/v1", model or "kimi-k3"),
        "openrouter": (os.getenv("OPENROUTER_API_KEY"), "https://openrouter.ai/api/v1", model or "openai/gpt-5.6-luna"),
        "openai": (os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_BASE_URL"), model or "gpt-5.6-luna"),
    }
    key, base_url, resolved = choices[provider]
    if not key:
        raise RuntimeError(f"provider={provider} has no configured credential")
    kwargs: dict[str, Any] = {"api_key": key, "timeout": 180.0, "max_retries": 4}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs), resolved, base_url or "https://api.openai.com/v1"


def customize(
    client: OpenAI,
    model: str,
    frontend: Path,
    requirement: str,
    round_number: int,
    receipts: list[dict[str, Any]],
    receipt_checkpoint: Path,
) -> dict[str, Any]:
    sources = {
        relative: (frontend / relative).read_text(encoding="utf-8")
        for relative in agent.EDITABLE_FILES
    }
    blocks = "\n\n".join(f"===== {name} =====\n{content}" for name, content in sources.items())
    feedback = ""
    for attempt in range(1, 4):
        messages = [
            {"role": "system", "content": agent.SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"可编辑文件当前内容：\n\n{blocks}\n\n本轮需求：{requirement}\n"
                "请只返回完成本轮所需的最少文件，并调用 apply_edits；工具参数必须是完整有效的 JSON。"
                + (f"\n上次调用未通过可执行校验：{feedback}\n请修复该错误后重新调用。" if feedback else "")
            )},
        ]
        request = {
            "model": model,
            "messages": messages,
            "tools": [agent.APPLY_EDITS_TOOL],
            "tool_choice": {"type": "function", "function": {"name": "apply_edits"}},
            "temperature": 1 if any(marker in model.casefold() for marker in ("kimi-k3", "gpt-5", "o1", "o3", "o4")) else 0,
            "max_tokens": 8192,
        }
        started = time.monotonic()
        response = client.chat.completions.create(**request)
        choice = response.choices[0]
        message = choice.message
        calls = message.tool_calls or []
        call = calls[0] if calls else None
        usage = response.usage
        receipt = {
            "round": round_number,
            "attempt": attempt,
            "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "latency_s": round(time.monotonic() - started, 3),
            "request": request,
            "response": {
                "id": response.id,
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "message": {
                    "content": message.content,
                    "tool_calls": [] if call is None else [{
                        "id": call.id,
                        "type": call.type,
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }],
                },
            },
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
                "cached_prompt_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
            },
            "accepted": False,
        }
        if not response.id or not receipt["usage"]["total_tokens"]:
            raise RuntimeError("provider omitted required receipt metadata")
        try:
            if choice.finish_reason == "length" or call is None:
                raise RuntimeError("incomplete apply_edits call")
            payload = json.loads(call.function.arguments or "{}")
            if not isinstance(payload, dict):
                raise RuntimeError("apply_edits arguments are not an object")
            files = payload.get("files") or []
            if not files:
                raise RuntimeError("empty edit set")
            for item in files:
                if not isinstance(item, dict) or item.get("path") not in agent.EDITABLE_FILES or not isinstance(item.get("content"), str):
                    raise RuntimeError("invalid/disallowed edit item")
            receipt["accepted"] = True
            receipts.append(receipt)
            atomic_json(receipt_checkpoint, receipts)
            return payload
        except (json.JSONDecodeError, RuntimeError) as exc:
            feedback = f"{type(exc).__name__}: {exc}"
            receipt["validation_error"] = feedback
            receipts.append(receipt)
            atomic_json(receipt_checkpoint, receipts)
    raise RuntimeError(f"round {round_number}: model never returned valid apply_edits arguments: {feedback}")


def copy_app(run_dir: Path, backend_port: int) -> tuple[Path, Path]:
    app = run_dir / "app"
    frontend = app / "frontend"
    backend = app / "backend"
    frontend.mkdir(parents=True)
    backend.mkdir(parents=True)
    for filename in ("index.html", "package.json", "package-lock.json", "vite.config.js"):
        shutil.copyfile(HERE / "frontend" / filename, frontend / filename)
    shutil.copytree(HERE / "frontend" / "src", frontend / "src")
    for relative in agent.EDITABLE_FILES:
        shutil.copyfile(HERE / "baseline" / relative, frontend / relative)
    # Reuse the installed dependency tree without duplicating its disk footprint.
    (frontend / "node_modules").symlink_to(HERE / "frontend" / "node_modules", target_is_directory=True)
    config = (frontend / "vite.config.js").read_text(encoding="utf-8")
    (frontend / "vite.config.js").write_text(config.replace("127.0.0.1:8000", f"127.0.0.1:{backend_port}"), encoding="utf-8")
    shutil.copyfile(HERE / "backend" / "main.py", backend / "main.py")
    return frontend, backend


def browser_value(page, kind: str) -> str:
    if kind == "color":
        return page.locator(".send-button").evaluate("el => getComputedStyle(el).backgroundColor")
    if kind == "font":
        return page.locator("body").evaluate("el => getComputedStyle(el).fontFamily")
    if kind == "title":
        return page.locator(".header-title").inner_text()
    raise ValueError(kind)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["ark", "moonshot", "openrouter", "openai"], default="ark")
    parser.add_argument("--model", default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    started = dt.datetime.now(dt.timezone.utc)
    run_id = args.run_id or started.strftime("%Y%m%dT%H%M%SZ-5_11-hmr")
    run_dir = HERE / "validation" / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"immutable run exists: {run_dir}")
    run_dir.mkdir(parents=True)
    frontend_port, backend_port = free_port(), free_port()
    frontend, backend = copy_app(run_dir, backend_port)
    client, model, endpoint = resolve_backend(args.provider, args.model)

    backend_log = (run_dir / "backend.log").open("w", encoding="utf-8")
    frontend_log = (run_dir / "frontend.log").open("w", encoding="utf-8")
    backend_process = subprocess.Popen(
        ["python", "main.py", "--reload", "--port", str(backend_port), "--log-level", "info"],
        cwd=backend, stdout=backend_log, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(frontend_port), "--strictPort"],
        cwd=frontend, stdout=frontend_log, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )
    receipts: list[dict[str, Any]] = []
    round_records: list[dict[str, Any]] = []
    browser_facts: dict[str, Any] = {}
    build_result: dict[str, Any] = {}
    try:
        backend_health = wait_url(f"http://127.0.0.1:{backend_port}/api/health")
        wait_url(f"http://127.0.0.1:{frontend_port}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1100, "height": 850})
            websocket_events: list[dict[str, Any]] = []
            page.on("websocket", lambda ws: websocket_events.append({"event": "opened", "url": ws.url}))
            navigation_count = 0
            def navigated(_frame):
                nonlocal navigation_count
                navigation_count += 1
            page.on("framenavigated", navigated)
            page.goto(f"http://127.0.0.1:{frontend_port}", wait_until="networkidle")
            chromium_version = browser.version
            page.locator(".composer-input").fill("HMR_STATE_SENTINEL")
            page.locator(".send-button").click()
            page.wait_for_function("[...document.querySelectorAll('.bubble')].some(x => x.textContent.includes('HMR_STATE_SENTINEL'))")
            baseline_navigation_count = navigation_count
            for index, definition in enumerate(ROUNDS, 1):
                before = {relative: (frontend / relative).read_text(encoding="utf-8") for relative in agent.EDITABLE_FILES}
                payload = customize(
                    client, model, frontend, definition["requirement"], index,
                    receipts, run_dir / "receipts.checkpoint.json",
                )
                changed = []
                for item in payload["files"]:
                    target = frontend / item["path"]
                    target.write_text(item["content"], encoding="utf-8")
                    changed.append({"path": item["path"], "before_sha256": hashlib.sha256(before[item["path"]].encode()).hexdigest(), "after_sha256": sha256(target)})
                expected = definition["expected"]
                page.wait_for_function(
                    """([kind, expected]) => {
                      if (kind === 'color') return getComputedStyle(document.querySelector('.send-button')).backgroundColor === expected;
                      if (kind === 'font') return getComputedStyle(document.body).fontFamily.toLowerCase().includes(expected);
                      return document.querySelector('.header-title')?.textContent.trim() === expected;
                    }""",
                    arg=[definition["kind"], expected], timeout=30000,
                )
                observed = browser_value(page, definition["kind"])
                state_retained = page.locator(".chat-window").inner_text().find("HMR_STATE_SENTINEL") >= 0
                screenshot = run_dir / f"round-{index}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                round_records.append({
                    "round": index, "requirement": definition["requirement"], "kind": definition["kind"],
                    "expected": expected, "observed": observed, "changed_files": changed,
                    "chat_state_retained": state_retained, "screenshot": screenshot.name,
                })
            page.screenshot(path=str(run_dir / "final.png"), full_page=True)
            browser_facts = {
                "browser": "Chromium", "version": chromium_version,
                "vite_hmr_websockets": websocket_events,
                "navigation_count_after_initial_load": navigation_count - baseline_navigation_count,
                "sentinel_chat_state_retained": "HMR_STATE_SENTINEL" in page.locator(".chat-window").inner_text(),
                "final_title": page.locator(".header-title").inner_text(),
                "final_color": browser_value(page, "color"),
                "final_font": browser_value(page, "font"),
            }
            browser.close()
        build_started = time.monotonic()
        built = subprocess.run(["npm", "run", "build"], cwd=frontend, capture_output=True, text=True, timeout=180)
        build_result = {
            "returncode": built.returncode,
            "latency_s": round(time.monotonic() - build_started, 3),
            "stdout": built.stdout,
            "stderr": built.stderr,
        }
    finally:
        for process in (frontend_process, backend_process):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in (frontend_process, backend_process):
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        frontend_log.close()
        backend_log.close()

    atomic_json(run_dir / "receipts.json", receipts)
    atomic_json(run_dir / "rounds.json", round_records)
    atomic_json(run_dir / "build.json", build_result)
    gates = {
        "real_react_vite_dev_server": "vite" in (run_dir / "frontend.log").read_text(encoding="utf-8").casefold(),
        "real_fastapi_backend_reload_mode": backend_health == {"status": "ok", "mode": "echo", "model": None} and "reloader process" in (run_dir / "backend.log").read_text(encoding="utf-8").casefold(),
        "real_model_generated_three_sequential_edits": (
            len(round_records) == 3
            and sum(receipt.get("accepted") is True for receipt in receipts) == 3
        ),
        "vite_hmr_websocket_observed": bool(browser_facts["vite_hmr_websockets"]),
        "no_full_page_navigation_during_three_edits": browser_facts["navigation_count_after_initial_load"] == 0,
        "react_chat_state_preserved_across_hmr": browser_facts["sentinel_chat_state_retained"] and all(row["chat_state_retained"] for row in round_records),
        "all_color_font_title_requests_visible": browser_facts["final_color"] == "rgb(37, 99, 235)" and "monospace" in browser_facts["final_font"].casefold() and browser_facts["final_title"] == "我的专属客服",
        "final_vite_build_passed": build_result["returncode"] == 0,
        "raw_provider_receipts_complete": all(r["response"]["id"] and r["usage"]["total_tokens"] for r in receipts),
        "rendered_browser_images_retained": all((run_dir / f"round-{i}.png").is_file() for i in range(1, 4)) and (run_dir / "final.png").is_file(),
    }
    artifacts = {}
    for path in sorted(run_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            artifacts[path.name] = {"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
    for relative in agent.EDITABLE_FILES:
        path = frontend / relative
        artifacts[f"final-source/{relative}"] = {"path": str(path.relative_to(run_dir)), "sha256": sha256(path), "bytes": path.stat().st_size}
    manifest = {
        "schema_version": "1.0", "experiment": "5-11", "run_id": run_id,
        "started_at_utc": started.isoformat(), "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": args.provider, "endpoint": endpoint, "model": model,
        "source": {"manuscript": "book/chapter5.md#实验-5-11", "campaign_sha256": sha256(Path(__file__))},
        "servers": {
            "frontend": {"command": ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(frontend_port), "--strictPort"]},
            "backend": {"command": ["python", "main.py", "--reload", "--port", str(backend_port)], "health": backend_health},
        },
        "rounds": round_records, "browser": browser_facts, "build": build_result,
        "usage": {
            "calls": len(receipts), "prompt_tokens": sum(r["usage"]["prompt_tokens"] or 0 for r in receipts),
            "completion_tokens": sum(r["usage"]["completion_tokens"] or 0 for r in receipts),
            "total_tokens": sum(r["usage"]["total_tokens"] or 0 for r in receipts),
            "latency_s": round(sum(r["latency_s"] for r in receipts), 3),
        },
        "artifacts": artifacts, "acceptance_gates": gates, "official_complete": all(gates.values()),
    }
    atomic_json(run_dir / "manifest.json", manifest)
    (HERE / "validation").mkdir(exist_ok=True)
    if manifest["official_complete"]:
        shutil.copyfile(run_dir / "manifest.json", HERE / "validation" / "latest.json")
    print(json.dumps({"run_id": run_id, "official_complete": manifest["official_complete"], "gates": gates}, ensure_ascii=False, indent=2))
    if not manifest["official_complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
