#!/usr/bin/env python3
"""Canonical live campaign for Chapter 5, Experiment 5-9.

The companion demo historically stopped at static HTML inspection and a
constructed submission dictionary.  This campaign deliberately has no such
fallback: a real model writes the form, Chromium executes its JavaScript, a
single browser submit produces the JSON, and a second real model call consumes
that exact browser-produced payload.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

from openai import OpenAI
from playwright.sync_api import sync_playwright

from demo import FORM_SYSTEM_PROMPT, PARSE_SYSTEM_PROMPT, validate_form


HERE = Path(__file__).resolve().parent
REQUEST = "我想订一张去北京的机票"
SUBMISSION = {
    "departure_city": "上海",
    "departure_date": "2026-08-11",
    "trip_type": "round_trip",
    "return_date": "2026-08-18",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def resolve_backend(provider: str, model: str | None) -> tuple[OpenAI, str, str]:
    choices = {
        "ark": (
            os.getenv("ARK_API_KEY"),
            "https://ark.cn-beijing.volces.com/api/v3",
            model or "doubao-seed-1-6-flash-250615",
        ),
        "moonshot": (
            os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY"),
            "https://api.moonshot.cn/v1",
            model or "kimi-k3",
        ),
        "openrouter": (
            os.getenv("OPENROUTER_API_KEY"),
            "https://openrouter.ai/api/v1",
            model or "openai/gpt-5.6-luna",
        ),
        "openai": (
            os.getenv("OPENAI_API_KEY"),
            os.getenv("OPENAI_BASE_URL"),
            model or "gpt-5.6-luna",
        ),
        "gemini": (
            os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            "https://generativelanguage.googleapis.com/v1beta/openai/",
            model or "gemini-2.5-flash",
        ),
    }
    key, base_url, resolved_model = choices[provider]
    if not key:
        raise RuntimeError(f"provider={provider} has no configured credential")
    kwargs: dict[str, Any] = {
        "api_key": key,
        "timeout": 180.0,
        "max_retries": 4,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs), resolved_model, base_url or "https://api.openai.com/v1"


def call(
    client: OpenAI,
    model: str,
    purpose: str,
    messages: list[dict[str, str]],
) -> tuple[str, dict[str, Any]]:
    started = time.monotonic()
    reasoning = any(
        marker in model.casefold()
        for marker in ("kimi-k3", "gpt-5", "o1", "o3", "o4", "reasoner", "thinking")
    )
    request: dict[str, Any] = {"model": model, "messages": messages}
    request["temperature"] = 1 if reasoning else 0
    response = client.chat.completions.create(**request)
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(f"{purpose}: provider response was truncated")
    content = choice.message.content or ""
    usage = response.usage
    receipt = {
        "purpose": purpose,
        "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "latency_s": round(time.monotonic() - started, 3),
        "request": request,
        "response": {
            "id": response.id,
            "model": response.model,
            "finish_reason": choice.finish_reason,
            "content": content,
        },
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "cached_prompt_tokens": getattr(
                getattr(usage, "prompt_tokens_details", None), "cached_tokens", None
            ),
        },
    }
    if not receipt["response"]["id"] or not receipt["usage"]["total_tokens"]:
        raise RuntimeError(f"{purpose}: provider did not return complete receipt metadata")
    return content, receipt


def strip_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:html)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def browser_submit(html: str, screenshot: Path) -> dict[str, Any]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.set_content(html, wait_until="load")
        page.locator("form").evaluate(
            """form => {
              window.__submitCount = 0;
              form.addEventListener('submit', () => { window.__submitCount += 1; }, true);
            }"""
        )
        return_field = page.locator('[name="return_date"]')
        initial_return_visible = return_field.is_visible()
        page.locator('[name="departure_city"]').fill(SUBMISSION["departure_city"])
        page.locator('[name="departure_date"]').fill(SUBMISSION["departure_date"])
        page.locator(
            '[name="trip_type"][value="round_trip"]'
        ).check()
        return_field.wait_for(state="visible")
        return_field.fill(SUBMISSION["return_date"])
        after_round_trip_visible = return_field.is_visible()
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        page.wait_for_function(
            "document.querySelector('#result') && document.querySelector('#result').textContent.trim().length > 0"
        )
        submitted_text = page.locator("#result").text_content() or ""
        submitted = json.loads(submitted_text)
        submit_count = page.evaluate("window.__submitCount")
        screenshot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot), full_page=True)
        browser_version = browser.version
        browser.close()
    return {
        "browser": "Chromium",
        "browser_version": browser_version,
        "initial_return_visible": initial_return_visible,
        "after_round_trip_visible": after_round_trip_visible,
        "submit_count": submit_count,
        "submitted_json": submitted,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider", choices=["ark", "moonshot", "openrouter", "openai", "gemini"], default="ark"
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    started_utc = dt.datetime.now(dt.timezone.utc)
    run_id = args.run_id or started_utc.strftime("%Y%m%dT%H%M%SZ-5_9-live-browser")
    run_dir = HERE / "validation" / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"immutable run already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    client, model, endpoint = resolve_backend(args.provider, args.model)
    receipts: list[dict[str, Any]] = []
    generation_messages = [
        {"role": "system", "content": FORM_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"用户请求：{REQUEST}\n请为其中缺失的信息生成澄清表单。",
        },
    ]

    html = ""
    static_report: dict[str, bool] = {}
    browser_result: dict[str, Any] | None = None
    errors: list[str] = []
    for attempt in range(1, 4):
        text, receipt = call(
            client, model, f"generate-form-attempt-{attempt}", generation_messages
        )
        receipts.append(receipt)
        html = strip_fence(text)
        structural_ok, static_report, _ = validate_form(html)
        if structural_ok:
            try:
                browser_result = browser_submit(html, run_dir / "browser-submitted.png")
                break
            except Exception as exc:
                errors.append(f"browser attempt {attempt}: {type(exc).__name__}: {exc}")
        else:
            errors.append(f"structure attempt {attempt}: {static_report}")
        generation_messages.extend(
            [
                {"role": "assistant", "content": text},
                {
                    "role": "user",
                    "content": (
                        "The form failed executable acceptance. Return a complete corrected HTML. "
                        f"Static checks={static_report}; execution errors={errors[-1:]}"
                    ),
                },
            ]
        )
    if browser_result is None:
        atomic_json(run_dir / "receipts.json", receipts)
        raise RuntimeError(f"live browser acceptance failed after three real generations: {errors}")

    html_path = run_dir / "generated_form.html"
    html_path.write_text(html, encoding="utf-8")
    submitted = browser_result["submitted_json"]
    parse_messages = [
        {"role": "system", "content": PARSE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"原始请求：{REQUEST}\n浏览器表单实际提交的 JSON 数据：\n"
                + json.dumps(submitted, ensure_ascii=False, indent=2)
            ),
        },
    ]
    summary, receipt = call(client, model, "continue-after-browser-submit", parse_messages)
    receipts.append(receipt)
    atomic_json(run_dir / "receipts.json", receipts)

    gates = {
        "live_model_generated_complete_html": bool(
            receipts and "<html" in html.casefold() and "<script" in html.casefold()
        ),
        "all_manuscript_fields_present": all(static_report.values()),
        "real_chromium_executed_javascript": bool(browser_result["browser_version"]),
        "return_date_hidden_before_round_trip": not browser_result["initial_return_visible"],
        "return_date_visible_after_round_trip": browser_result["after_round_trip_visible"],
        "user_submitted_exactly_once": browser_result["submit_count"] == 1,
        "browser_submission_contains_all_values": all(
            submitted.get(key) == value for key, value in SUBMISSION.items()
        ),
        "agent_consumed_exact_browser_payload": parse_messages[-1]["content"].endswith(
            json.dumps(submitted, ensure_ascii=False, indent=2)
        ),
        "agent_continued_booking_task": all(
            marker in summary for marker in ("北京", "上海", "2026-08-11", "2026-08-18")
        ),
        "raw_provider_receipts_complete": all(
            row["response"]["id"] and row["usage"]["total_tokens"] for row in receipts
        ),
        "rendered_browser_screenshot_retained": (run_dir / "browser-submitted.png").is_file(),
    }
    manifest = {
        "schema_version": "1.0",
        "experiment": "5-9",
        "run_id": run_id,
        "started_at_utc": started_utc.isoformat(),
        "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": args.provider,
        "endpoint": endpoint,
        "model": model,
        "temperature": 1 if any(x in model.casefold() for x in ("kimi-k3", "gpt-5")) else 0,
        "source": {
            "manuscript": "book/chapter5.md#实验-5-9",
            "campaign_sha256": sha256(Path(__file__)),
        },
        "input": {"request": REQUEST, "intended_submission": SUBMISSION},
        "static_validation": static_report,
        "browser_execution": browser_result,
        "agent_continuation": summary,
        "usage": {
            "calls": len(receipts),
            "prompt_tokens": sum(r["usage"]["prompt_tokens"] or 0 for r in receipts),
            "completion_tokens": sum(r["usage"]["completion_tokens"] or 0 for r in receipts),
            "total_tokens": sum(r["usage"]["total_tokens"] or 0 for r in receipts),
            "latency_s": round(sum(r["latency_s"] for r in receipts), 3),
        },
        "artifacts": {
            "html": {"path": "generated_form.html", "sha256": sha256(html_path)},
            "screenshot": {
                "path": "browser-submitted.png",
                "sha256": sha256(run_dir / "browser-submitted.png"),
            },
            "receipts": {"path": "receipts.json", "sha256": sha256(run_dir / "receipts.json")},
        },
        "acceptance_gates": gates,
        "official_complete": all(gates.values()),
        "errors_during_repair": errors,
    }
    atomic_json(run_dir / "manifest.json", manifest)
    if manifest["official_complete"]:
        latest = HERE / "validation" / "latest.json"
        shutil.copyfile(run_dir / "manifest.json", latest)
    print(json.dumps({"run_id": run_id, "official_complete": manifest["official_complete"], "gates": gates}, ensure_ascii=False, indent=2))
    if not manifest["official_complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
