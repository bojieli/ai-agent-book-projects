#!/usr/bin/env python3
"""Live self-healing parser + browser/Vision campaign for Experiment 5-7."""

from __future__ import annotations

import argparse
import ast
import base64
import datetime as dt
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from PIL import Image
from playwright.sync_api import sync_playwright

from agent import SYSTEM_PROMPT, _build_user_prompt, _extract_code
from engine import LogParserEngine, ParseError, builtin_json_parser
from tester import run_tests


HERE = Path(__file__).resolve().parent
FORMATS = [
    {
        "name": "live_pipe_parser",
        "required": ["timestamp", "level", "module", "step", "message"],
        "script": """import logging, sys
formatter=logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|step=%(step)s|%(message)s', datefmt='%Y-%m-%dT%H:%M:%SZ')
handler=logging.StreamHandler(sys.stdout); handler.setFormatter(formatter)
logger=logging.getLogger('checkout.worker'); logger.handlers=[handler]; logger.setLevel(logging.INFO); logger.propagate=False
logger.info('accepted real request req-81', extra={'step': 1})
logger.warning('retrying payment authorization req-81', extra={'step': 2})
logger.error('authorization exhausted req-81', extra={'step': 3})
""",
    },
    {
        "name": "live_bracket_parser",
        "required": ["timestamp", "level", "tool", "latency_ms", "status", "message"],
        "script": """import datetime, time
events=[('inventory_lookup',34,'ok','stock check completed'),('payment_api',181,'retry','upstream requested retry'),('payment_api',412,'timeout','deadline exceeded')]
for tool,latency,status,message in events:
    started=time.perf_counter(); time.sleep(0.003); observed=max(latency,int((time.perf_counter()-started)*1000))
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds')
    level='ERROR' if status=='timeout' else ('WARNING' if status=='retry' else 'INFO')
    print(f'[{stamp}] ({level}) <tool={tool}> {{latency_ms={observed} status={status}}} :: {message}', flush=True)
""",
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


def backend(provider: str, model: str | None) -> tuple[OpenAI, str, str]:
    choices = {
        "ark": (os.getenv("ARK_API_KEY"), "https://ark.cn-beijing.volces.com/api/v3", model or "doubao-seed-1-6-250615"),
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


def usage(response) -> dict[str, Any]:
    value = response.usage
    return {
        "prompt_tokens": getattr(value, "prompt_tokens", None),
        "completion_tokens": getattr(value, "completion_tokens", None),
        "total_tokens": getattr(value, "total_tokens", None),
        "cached_prompt_tokens": getattr(getattr(value, "prompt_tokens_details", None), "cached_tokens", None),
    }


def assert_safe_parser(source: str) -> None:
    tree = ast.parse(source)
    allowed_imports = {"re", "json", "datetime"}
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not any(node.name == "parse" for node in functions):
        raise ValueError("generated code has no parse function")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] not in allowed_imports for alias in node.names):
                raise ValueError("generated parser imports a disallowed module")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] not in allowed_imports:
            raise ValueError("generated parser imports a disallowed module")
        if isinstance(node, (ast.With, ast.AsyncWith, ast.ClassDef, ast.Global, ast.Nonlocal)):
            raise ValueError(f"generated parser contains disallowed {type(node).__name__}")


def model_parser(
    client: OpenAI,
    model: str,
    definition: dict[str, Any],
    samples: list[str],
    error: str,
    parsers_dir: Path,
) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    receipts = []
    feedback = None
    final_test = None
    path = parsers_dir / f"{definition['name']}.py"
    for attempt in range(1, 4):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(samples, definition["required"], error, feedback)},
        ]
        request = {
            "model": model,
            "messages": messages,
            "temperature": 1 if any(x in model.casefold() for x in ("kimi-k3", "gpt-5", "o1", "o3", "o4")) else 0,
        }
        started = time.monotonic()
        response = client.chat.completions.create(**request)
        choice = response.choices[0]
        receipt = {
            "purpose": f"generate-{definition['name']}-attempt-{attempt}",
            "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "latency_s": round(time.monotonic() - started, 3),
            "request": request,
            "response": {"id": response.id, "model": response.model, "finish_reason": choice.finish_reason, "content": choice.message.content},
            "usage": usage(response),
        }
        receipts.append(receipt)
        if choice.finish_reason == "length":
            feedback = "The provider truncated the previous program. Return a shorter complete parse function."
            continue
        source = _extract_code(choice.message.content or "")
        try:
            assert_safe_parser(source)
            path.write_text(source + "\n", encoding="utf-8")
            fn = LogParserEngine.load_parser_from_file(str(path))
            final_test = run_tests(fn, samples, definition["required"])
            if final_test["passed"]:
                return path, receipts, final_test
            feedback = final_test["report"]
        except Exception as exc:
            feedback = f"{type(exc).__name__}: {exc}"
    raise RuntimeError(f"three real parser attempts failed for {definition['name']}: {feedback}")


def collect_live_logs(run_dir: Path) -> list[dict[str, Any]]:
    collected = []
    for index, definition in enumerate(FORMATS, 1):
        script = run_dir / f"producer-{index}.py"
        script.write_text(definition["script"], encoding="utf-8")
        started = time.monotonic()
        process = subprocess.run(["python", str(script)], capture_output=True, text=True, timeout=30)
        if process.returncode != 0:
            raise RuntimeError(f"live log producer failed: {process.stderr}")
        lines = [line for line in process.stdout.splitlines() if line.strip()]
        raw = run_dir / f"live-format-{index}.log"
        raw.write_text("\n".join(lines) + "\n", encoding="utf-8")
        collected.append({
            **definition, "script_path": script, "raw_path": raw, "lines": lines,
            "producer_latency_s": round(time.monotonic() - started, 4),
        })
    return collected


def visualize(run_dir: Path, parsed: list[dict[str, Any]]) -> tuple[dict[str, Any], Path]:
    keys = sorted({key for row in parsed for key in row})
    rows = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in keys) + "</tr>"
        for row in parsed
    )
    document = f"""<!doctype html><meta charset=utf-8><title>Adaptive log parser</title>
    <style>body{{font-family:system-ui;background:#0b1020;color:#e8eefc;padding:30px}}table{{border-collapse:collapse;width:100%;background:#121a30}}th,td{{border:1px solid #33415f;padding:9px;text-align:left}}th{{color:#79c0ff}}h1{{color:#a5d6ff}}</style>
    <h1>Self-healed live log stream</h1><p>{len(parsed)} runtime records parsed after hot update.</p>
    <table><thead><tr>{''.join(f'<th>{html.escape(key)}</th>' for key in keys)}</tr></thead><tbody>{rows}</tbody></table>"""
    html_path = run_dir / "visualization.html"
    screenshot = run_dir / "visualization.png"
    html_path.write_text(document, encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1800, "height": 1000})
        page.set_content(document, wait_until="load")
        page.screenshot(path=str(screenshot), full_page=True)
        result = {"browser": "Chromium", "version": browser.version, "rows": len(parsed), "columns": keys}
        browser.close()
    return result, screenshot


def vision_review(client: OpenAI, model: str, image_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    image = Image.open(image_path).convert("RGB")
    buffer = io.BytesIO(); image.save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    prompt = "Inspect this rendered adaptive-log table. Return strict JSON: {\"pass\": bool, \"readable\": bool, \"has_multiple_parsers\": bool, \"observed_columns\": [strings], \"reason\": string}. Pass only if the table is readable, contains multiple parsed rows, and visibly includes both parser identifiers and structured fields."
    request = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}", "detail": "high"}},
        ]}],
        "temperature": 0,
    }
    started = time.monotonic()
    response = client.chat.completions.create(**request)
    choice = response.choices[0]
    text = choice.message.content or ""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"Vision reviewer returned no JSON: {text}")
    judgment = json.loads(match.group(0))
    receipt = {
        "purpose": "vision-review-rendered-parser-table",
        "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "latency_s": round(time.monotonic() - started, 3),
        "request": {
            "model": model,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"sha256": sha256(image_path), "bytes": image_path.stat().st_size}},
            ]}], "temperature": 0,
        },
        "response": {"id": response.id, "model": response.model, "finish_reason": choice.finish_reason, "content": text},
        "usage": usage(response),
    }
    return judgment, receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["ark", "moonshot", "openrouter", "openai"], default="ark")
    parser.add_argument("--model", default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    started = dt.datetime.now(dt.timezone.utc)
    run_id = args.run_id or started.strftime("%Y%m%dT%H%M%SZ-5_7-live")
    run_dir = HERE / "validation" / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"immutable run exists: {run_dir}")
    parsers_dir = run_dir / "parsers"; parsers_dir.mkdir(parents=True)
    live = collect_live_logs(run_dir)
    client, model, endpoint = backend(args.provider, args.model)

    engine = LogParserEngine(); engine.register("builtin_json", builtin_json_parser)
    receipts = []; format_records = []
    for definition in live:
        failures = 0
        for line in definition["lines"]:
            try: engine.parse_line(line)
            except ParseError: failures += 1
        if failures != len(definition["lines"]):
            raise RuntimeError("new format did not trigger the initial parser failure")
        error = str(ParseError(definition["lines"][0]))
        path, calls, test = model_parser(client, model, definition, definition["lines"], error, parsers_dir)
        receipts.extend(calls)
        fn = LogParserEngine.load_parser_from_file(str(path)); engine.register(definition["name"], fn)
        after = [engine.parse_line(line) for line in definition["lines"]]
        format_records.append({
            "name": definition["name"], "raw_log": definition["raw_path"].name,
            "raw_log_sha256": sha256(definition["raw_path"]), "samples": len(definition["lines"]),
            "initial_failures": failures, "required_keys": definition["required"],
            "parser": str(path.relative_to(run_dir)), "parser_sha256": sha256(path),
            "test": test, "parsed_after_hot_update": after,
        })

    restarted = LogParserEngine(); restarted.register("builtin_json", builtin_json_parser)
    loaded = restarted.load_persisted(str(parsers_dir))
    all_lines = [line for definition in live for line in definition["lines"]]
    restarted_rows = [restarted.parse_line(line) for line in all_lines]
    browser, screenshot = visualize(run_dir, restarted_rows)
    judgment, vision_receipt = vision_review(client, model, screenshot)
    receipts.append(vision_receipt)
    atomic_json(run_dir / "receipts.json", receipts)
    atomic_json(run_dir / "evidence.json", {"formats": format_records, "loaded_after_restart": loaded, "rows_after_restart": restarted_rows, "browser": browser, "vision_judgment": judgment})
    gates = {
        "raw_logs_emitted_by_real_runtime_processes": all(item["producer_latency_s"] > 0 and item["raw_path"].is_file() for item in live),
        "initial_system_detected_every_new_format_failure": all(row["initial_failures"] == row["samples"] for row in format_records),
        "real_model_generated_both_parser_modules": len(format_records) == 2 and all(row["parser_sha256"] for row in format_records),
        "generated_code_passed_automatic_tests": all(row["test"]["passed"] for row in format_records),
        "hot_update_parsed_every_failed_sample": all(len(row["parsed_after_hot_update"]) == row["samples"] for row in format_records),
        "persisted_parsers_loaded_after_fresh_engine_restart": set(loaded) == {row["name"] for row in format_records},
        "fresh_engine_parsed_entire_mixed_stream": len(restarted_rows) == len(all_lines),
        "real_chromium_rendered_visualization": bool(browser["version"] and screenshot.is_file()),
        "real_vision_model_approved_rendered_pixels": judgment.get("pass") is True and judgment.get("readable") is True,
        "raw_provider_receipts_complete": all(r["response"]["id"] and r["usage"]["total_tokens"] for r in receipts),
    }
    artifacts = {}
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            artifacts[str(path.relative_to(run_dir))] = {"path": str(path.relative_to(run_dir)), "sha256": sha256(path), "bytes": path.stat().st_size}
    manifest = {
        "schema_version": "1.0", "experiment": "5-7", "run_id": run_id,
        "started_at_utc": started.isoformat(), "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": args.provider, "endpoint": endpoint, "model": model,
        "source": {"manuscript": "book/chapter5.md#实验-5-7", "campaign_sha256": sha256(Path(__file__))},
        "formats": format_records, "browser": browser, "vision_judgment": judgment,
        "usage": {"calls": len(receipts), "prompt_tokens": sum(r["usage"]["prompt_tokens"] or 0 for r in receipts), "completion_tokens": sum(r["usage"]["completion_tokens"] or 0 for r in receipts), "total_tokens": sum(r["usage"]["total_tokens"] or 0 for r in receipts), "latency_s": round(sum(r["latency_s"] for r in receipts), 3)},
        "artifacts": artifacts, "acceptance_gates": gates, "official_complete": all(gates.values()),
    }
    atomic_json(run_dir / "manifest.json", manifest)
    (HERE / "validation").mkdir(exist_ok=True)
    if manifest["official_complete"]:
        shutil.copyfile(run_dir / "manifest.json", HERE / "validation" / "latest.json")
    print(json.dumps({"run_id": run_id, "official_complete": manifest["official_complete"], "gates": gates}, ensure_ascii=False, indent=2))
    if not manifest["official_complete"]: raise SystemExit(2)


if __name__ == "__main__":
    main()
