"""Run a visual Browser Use trajectory through an open-model API endpoint."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import ConfigError, ModelEndpoint, resolve_endpoint
from evidence import retain_step_screenshots, write_json, write_manifest

DEFAULT_TASK = (
    "Open Google, search for San Francisco weather today, and report the "
    "temperature and conditions. Do not sign in or change any external data."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_run_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("runs") / f"open-model-{stamp}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--max-steps", type=int, default=25)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and print the redacted endpoint configuration without importing browser-use or calling an API",
    )
    args = parser.parse_args()
    if args.max_steps < 1:
        parser.error("--max-steps must be positive")
    return args


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def scrub_secret(text: str, secret: str) -> str:
    return text.replace(secret, "<redacted>") if secret else text


def scrub_value(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return scrub_secret(value, secret)
    if isinstance(value, list):
        return [scrub_value(item, secret) for item in value]
    if isinstance(value, dict):
        return {key: scrub_value(item, secret) for key, item in value.items()}
    return value


def public_preflight(endpoint: ModelEndpoint, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "api": endpoint.public_dict(),
        "task": args.task,
        "max_steps": args.max_steps,
        "headless": args.headless,
        "record_video": args.record_video,
        "requirements": {
            "image_input": True,
            "structured_actions": True,
            "browser_execution": True,
        },
    }


async def run(args: argparse.Namespace, endpoint: ModelEndpoint) -> int:
    try:
        import httpx
        from browser_use import Agent, BrowserSession, ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "browser-use is not installed; run `python -m pip install -r requirements.txt`"
        ) from exc

    run_dir = (args.output_dir or default_run_dir()).expanduser().resolve()
    if run_dir.exists() and any(run_dir.iterdir()):
        raise RuntimeError(f"output directory is not empty: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = utc_now()
    write_json(run_dir / "preflight.json", public_preflight(endpoint, args))
    api_receipts: list[dict[str, Any]] = []

    async def record_request(request: httpx.Request) -> None:
        body = await request.aread()
        requested_model = None
        try:
            requested_model = json.loads(body).get("model")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            pass
        api_receipts.append(
            {
                "kind": "request",
                "at": utc_now(),
                "method": request.method,
                "url": str(request.url),
                "requested_model": requested_model,
                "body_bytes": len(body),
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "authorization_retained": False,
            }
        )

    async def record_response(response: httpx.Response) -> None:
        body = await response.aread()
        try:
            parsed_body: Any = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed_body = {"non_json_body": body.decode("utf-8", errors="replace")}
        api_receipts.append(
            {
                "kind": "response",
                "at": utc_now(),
                "url": str(response.request.url),
                "status_code": response.status_code,
                "body": scrub_value(parsed_body, endpoint.api_key),
                "authorization_retained": False,
            }
        )

    http_client = httpx.AsyncClient(event_hooks={"request": [record_request], "response": [record_response]})
    llm = ChatOpenAI(
        model=endpoint.model,
        api_key=endpoint.api_key,
        base_url=endpoint.base_url,
        temperature=0.0,
        frequency_penalty=0.0,
        add_schema_to_system_prompt=endpoint.schema_mode == "prompt",
        dont_force_structured_output=endpoint.schema_mode == "prompt",
        max_retries=2,
        http_client=http_client,
    )
    browser = BrowserSession(
        headless=args.headless,
        downloads_path=run_dir / "downloads",
        record_video_dir=(run_dir / "video") if args.record_video else None,
    )
    agent = Agent(
        task=args.task,
        llm=llm,
        browser_session=browser,
        use_vision=True,
        max_actions_per_step=1,
        use_judge=False,
        file_system_path=str(run_dir / "agent-files"),
    )

    history = None
    failure: Exception | None = None
    try:
        history = await agent.run(max_steps=args.max_steps)
    except Exception as exc:  # noqa: BLE001 - retain arbitrary provider/browser failure evidence
        failure = exc
    finally:
        try:
            await browser.kill()
        except Exception as close_exc:  # noqa: BLE001 - cleanup failures belong in the run receipt
            if failure is None:
                failure = close_exc
        try:
            await http_client.aclose()
        except Exception as close_exc:  # noqa: BLE001 - cleanup failures belong in the run receipt
            if failure is None:
                failure = close_exc

    write_json(run_dir / "api-receipts.json", api_receipts)

    if history is not None:
        retained_history, screenshots = retain_step_screenshots(history.model_dump(), run_dir)
        write_json(run_dir / "history.json", retained_history)
        write_json(run_dir / "screenshots.json", screenshots)
        provider_models = sorted(
            {
                item["body"]["model"]
                for item in api_receipts
                if item.get("kind") == "response"
                and isinstance(item.get("body"), dict)
                and isinstance(item["body"].get("model"), str)
            }
        )
        summary = {
            "schema_version": 1,
            "experiment": "9-6/9-7-open-model-arm",
            "acceptance_scope": "provider-portable-computer-use-trajectory",
            "status": "complete" if history.is_done() else "incomplete",
            "started_at": started_at,
            "ended_at": utc_now(),
            "api": endpoint.public_dict(),
            "provider_models_reported": provider_models,
            "browser_use_version": importlib.metadata.version("browser-use"),
            "task": args.task,
            "max_steps": args.max_steps,
            "steps_executed": len(history),
            "agent_reported_success": history.is_successful(),
            "final_result": history.final_result(),
            "urls": history.urls(),
            "errors": history.errors(),
            "screenshots_retained": sum(1 for item in screenshots if item["path"]),
            "credential_retained": False,
            "qualification": "This is a separate open-model arm, not an Anthropic-equivalent result.",
        }
        write_json(run_dir / "summary.json", summary)

    if failure is not None:
        message = scrub_secret(str(failure), endpoint.api_key)
        trace = scrub_secret("".join(traceback.format_exception(failure)), endpoint.api_key)
        write_json(
            run_dir / "failure.json",
            {
                "status": "failed",
                "ended_at": utc_now(),
                "error_type": type(failure).__name__,
                "message": message,
                "traceback": trace,
                "credential_retained": False,
            },
        )

    write_manifest(
        run_dir,
        {
            "experiment": "9-6/9-7-open-model-arm",
            "created_at": utc_now(),
            "api": endpoint.public_dict(),
            "credential_retained": False,
        },
    )
    print(json.dumps({"run_dir": str(run_dir), "failed": failure is not None}, ensure_ascii=False))
    if failure is not None:
        return 1
    return 0 if history is not None and history.is_done() else 1


def main() -> int:
    load_dotenv_if_available()
    args = parse_args()
    try:
        endpoint = resolve_endpoint(os.environ)
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    if args.dry_run:
        print(json.dumps(public_preflight(endpoint, args), ensure_ascii=False, indent=2))
        return 0
    return asyncio.run(run(args, endpoint))


if __name__ == "__main__":
    raise SystemExit(main())
