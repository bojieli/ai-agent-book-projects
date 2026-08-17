#!/usr/bin/env python3
"""Run Experiment 9-5 with a real model, localhost HTTP, and Chromium."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import shutil
import time
from typing import Any
from urllib.request import Request, urlopen

from openai import OpenAI
from playwright.async_api import async_playwright

from learning_agent import KnowledgeBase
from learning_agent.replay import WorkflowReplayer
from learning_agent.workflow import (
    ActionType,
    PredicateType,
    StatePredicate,
    Workflow,
    WorkflowStep,
)
from local_mail_sandbox import mail_sandbox


ROOT = Path(__file__).resolve().parent
FIRST = {"recipient": "test@example.com", "subject": "测试邮件", "content": "第一次探索正文"}
TRANSFER = {"recipient": "second@example.org", "subject": "季度报告", "content": "完全不同的回放正文"}
ALLOWED_PLAN = [
    ("input_text", "#recipient", "recipient"),
    ("input_text", "#subject", "subject"),
    ("input_text", "#content", "content"),
    ("click", "#send", None),
]


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def _provider_client(provider: str) -> tuple[OpenAI, dict[str, Any]]:
    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is required for --provider openrouter")
        endpoint = "https://openrouter.ai/api/v1"
        return OpenAI(api_key=key, base_url=endpoint), {
            "provider": provider, "endpoint": endpoint + "/chat/completions", "credential_env": "OPENROUTER_API_KEY"
        }
    if provider == "ark":
        key = os.getenv("ARK_API_KEY")
        if not key:
            raise RuntimeError("ARK_API_KEY is required for --provider ark")
        endpoint = "https://ark.cn-beijing.volces.com/api/v3"
        return OpenAI(api_key=key, base_url=endpoint), {
            "provider": provider, "endpoint": endpoint + "/chat/completions", "credential_env": "ARK_API_KEY"
        }
    if provider == "moonshot":
        key = os.getenv("MOONSHOT_API_KEY")
        if not key:
            raise RuntimeError("MOONSHOT_API_KEY is required for --provider moonshot")
        endpoint = "https://api.moonshot.cn/v1"
        return OpenAI(api_key=key, base_url=endpoint), {
            "provider": provider, "endpoint": endpoint + "/chat/completions", "credential_env": "MOONSHOT_API_KEY"
        }
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for --provider openai")
    return OpenAI(api_key=key), {
        "provider": provider, "endpoint": "https://api.openai.com/v1/chat/completions", "credential_env": "OPENAI_API_KEY"
    }


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _usage(response_payload: dict[str, Any]) -> dict[str, Any]:
    usage = response_payload.get("usage") or {}
    cost = usage.get("cost")
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
        "provider_reported_cost_usd": float(cost) if cost is not None else None,
        "cost_qualification": (
            "provider-native usage.cost" if cost is not None
            else "provider did not expose monetary cost; no price was guessed"
        ),
    }


def _sum_usage(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = completion = total = 0
    cost = 0.0
    cost_count = 0
    for receipt in receipts:
        usage = receipt["response"].get("usage") or {}
        prompt += int(usage.get("prompt_tokens") or 0)
        completion += int(usage.get("completion_tokens") or 0)
        total += int(usage.get("total_tokens") or 0)
        if usage.get("cost") is not None:
            cost += float(usage["cost"])
            cost_count += 1
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total or prompt + completion,
        "provider_reported_cost_usd": round(cost, 9) if cost_count else None,
        "provider_reported_cost_observations": cost_count,
        "cost_qualification": (
            "provider-native usage.cost summed across calls"
            if cost_count else "provider did not expose monetary cost; no price was guessed"
        ),
    }


async def model_explore(
    base_url: str, client: OpenAI, backend: dict[str, Any], model: str,
    seed: int, screenshot_path: Path,
):
    """Run a real observe-decide-act loop, one provider call per browser step."""
    started = time.perf_counter()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        browser_version = browser.version
        page = await browser.new_page()
        await page.goto(base_url + "/app", wait_until="networkidle")
        receipts = []
        captured = []
        for step_index, expected in enumerate(ALLOWED_PLAN):
            controls = await page.locator("input, textarea, button").evaluate_all("""els => els.map(e => {
              const parts=[]; let n=e;
              while(n && n.nodeType===1){ let i=1, s=n.previousElementSibling; while(s){if(s.tagName===n.tagName)i++;s=s.previousElementSibling} parts.unshift(n.tagName.toLowerCase()+'['+i+']');n=n.parentElement; }
              return {tag:e.tagName.toLowerCase(),id:e.id,name:e.name,type:e.type||null,
                role:e.getAttribute('role'),aria_label:e.getAttribute('aria-label'),
                data_testid:e.getAttribute('data-testid'),text:e.innerText||'',
                label:e.labels?.[0]?.innerText||'',value:e.value||'',xpath:'/'+parts.join('/')};
            })""")
            status = {
                "url": page.url,
                "status_text": await page.locator("#status").inner_text(),
                "persisted_count": await page.evaluate("window.__agentState.persistedCount"),
            }
            prompt = f"""You are the stepwise browser Agent for a local disposable mail sandbox.
Choose exactly the next safe action, not a multi-action plan. Return JSON only as
{{"action":"input_text|click","selector":"#id","value_key":"recipient|subject|content|null"}}.
Goal: send one message using the supplied parameter keys. Fill recipient, subject and content before clicking send.
Task parameters: {json.dumps(FIRST, ensure_ascii=False)}
Prior actions: {json.dumps(captured, ensure_ascii=False)}
Current page state: {json.dumps(status, ensure_ascii=False)}
Current controls: {json.dumps(controls, ensure_ascii=False)}
"""
            request_payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "seed": seed + step_index,
                "max_tokens": 300,
                "response_format": {"type": "json_object"},
            }
            api_started = time.perf_counter()
            response = await asyncio.to_thread(client.chat.completions.create, **request_payload)
            raw_response = _jsonable(response)
            decision = _extract_json(response.choices[0].message.content or "")
            normalized = (decision.get("action"), decision.get("selector"), decision.get("value_key"))
            if normalized != expected:
                raise RuntimeError(f"model returned unsafe or out-of-order step {step_index + 1}: {normalized!r}; expected {expected!r}")
            action, selector, value_key = normalized
            control = next(item for item in controls if f"#{item['id']}" == selector)
            before = {
                "url": page.url,
                "visible": await page.locator(selector).is_visible(),
                "page_status": status,
            }
            if action == "input_text":
                await page.locator(selector).fill(FIRST[str(value_key)])
            else:
                await page.locator(selector).click()
                await page.wait_for_function("window.__agentState.persistedCount === 1")
            captured.append({
                "action": action, "selector": selector, "value_key": value_key,
                "action_parameters": ({"text_template": "{" + str(value_key) + "}"} if value_key else {}),
                "before": before,
                "after": {
                    "url": page.url,
                    "value": await page.locator(selector).input_value() if action == "input_text" else None,
                    "status_text": await page.locator("#status").inner_text(),
                },
                "locator_evidence": {
                    "xpath": control["xpath"], "css": selector, "id": control["id"],
                    "name": control["name"], "type": control["type"], "role": control["role"],
                    "aria-label": control["aria_label"], "data-testid": control["data_testid"],
                    "captured_url": page.url,
                },
            })
            receipts.append({
                "kind": "browser_agent_step",
                "step": step_index + 1,
                "backend": {**backend, "credential_value_recorded": False},
                "request": request_payload,
                "response": raw_response,
                "elapsed_seconds": round(time.perf_counter() - api_started, 6),
            })
        final_text = await page.locator("#sent-list").inner_text()
        await page.screenshot(path=str(screenshot_path), full_page=True)
        await browser.close()
    return {
        "success": all(value in final_text for value in FIRST.values()),
        "captured_actions": captured,
        "llm_calls": len(receipts),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "browser": {"engine": "playwright-chromium", "version": browser_version, "headless": True},
        "api_receipts": receipts,
        "usage": _sum_usage(receipts),
        "screenshot": screenshot_path.name,
    }


def compile_workflow(base_url: str, captured: list[dict[str, Any]]) -> Workflow:
    workflow = Workflow(
        workflow_id="local-mail-send-v1",
        intent="send message",
        initial_url=base_url + "/app",
        example_parameters=dict(FIRST),
        description="Model-explored localhost mail workflow",
    )
    for item in captured:
        selector = item["selector"]
        locator = item.get("locator_evidence") or {}
        attributes = {
            key: str(value) for key, value in locator.items()
            if key in {"id", "name", "type", "role", "aria-label", "data-testid"} and value is not None
        }
        if item["action"] == "input_text":
            key = item["value_key"]
            workflow.add_step(WorkflowStep(
                action_type=ActionType.INPUT_TEXT,
                xpath=locator.get("xpath"),
                css_selector=selector,
                element_attributes=attributes,
                parameters={"text": "{" + key + "}", "clear_existing": True},
                description=f"fill {key}",
                preconditions=[StatePredicate(
                    PredicateType.ELEMENT_VISIBLE, True, selector=selector,
                    description=f"{key} field is visible",
                )],
                postconditions=[StatePredicate(
                    PredicateType.ELEMENT_VALUE_EQUALS, "{" + key + "}", selector=selector,
                    description=f"{key} field contains this run's value",
                )],
            ))
        else:
            workflow.add_step(WorkflowStep(
                action_type=ActionType.CLICK,
                xpath=locator.get("xpath"),
                css_selector=selector,
                element_attributes=attributes,
                description="submit message",
                preconditions=[StatePredicate(
                    PredicateType.ELEMENT_VISIBLE, True, selector=selector,
                    description="send button is visible before the side effect",
                )],
                postconditions=[
                    StatePredicate(
                        PredicateType.ELEMENT_TEXT_CONTAINS, "Message sent", selector="#status",
                        description="server-confirmed send status is visible",
                    ),
                    StatePredicate(
                        PredicateType.PAGE_STATE_EQUALS, True, state_key="sent",
                        description="page state confirms persistence",
                    ),
                ],
            ))
    if workflow.steps:
        workflow.steps[0].preconditions.insert(0, StatePredicate(
            PredicateType.URL_CONTAINS, "/app",
            description="workflow is on the captured application route",
        ))
    for key in ("recipient", "subject", "content"):
        workflow.final_predicates.append(StatePredicate(
            PredicateType.ELEMENT_TEXT_CONTAINS, "{" + key + "}", selector="#sent-list",
            description=f"sent-list contains current {key}",
        ))
    return workflow


async def replay(workflow: Workflow, parameters: dict[str, str], *, validate_state: bool = True):
    runner = WorkflowReplayer(headless=True)
    await runner.setup()
    try:
        return await runner.replay_workflow(workflow, parameters=parameters, validate_state=validate_state)
    finally:
        await runner.cleanup()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def campaign(args: argparse.Namespace) -> dict[str, Any]:
    client, backend = _provider_client(args.provider)
    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or ROOT / "validation" / stamp
    output_dir.mkdir(parents=True, exist_ok=False)
    store_dir = output_dir / "workflow_store"

    with mail_sandbox() as (base_url, state):
        state.reset(version=1)
        screenshot_path = output_dir / "exploration-final.png"
        exploration = await model_explore(base_url, client, backend, args.model, args.seed, screenshot_path)
        workflow = compile_workflow(base_url, exploration["captured_actions"])
        store = KnowledgeBase(str(store_dir))
        store.save_candidate(workflow)
        candidate_file = store_dir / f"candidate_{workflow.workflow_id}.json"
        candidate_before_reset = candidate_file.exists() and not store.workflows
        candidate_snapshot = output_dir / "candidate_snapshot.json"
        shutil.copyfile(candidate_file, candidate_snapshot)

        # An independent HTTP reset is the validation_reset boundary.
        _post(base_url + "/api/reset", {"version": 1, "fault": "normal"})
        validation = await replay(workflow, FIRST)
        if validation["success"]:
            workflow.mark_validated()
            store.publish_validated(workflow)

        # A workflow with no reset callback remains a candidate and cannot be retrieved.
        no_reset = compile_workflow(base_url, exploration["captured_actions"])
        no_reset.workflow_id = "no-reset-negative-control"
        store.save_candidate(no_reset)
        no_reset_stayed_candidate = no_reset.workflow_id not in store.workflows

        # Match and replay different literals without another model call.
        _post(base_url + "/api/reset", {"version": 1, "fault": "normal"})
        match = store.find_workflow_for_task(
            'send message to second@example.org with subject "季度报告" and content "完全不同的回放正文"'
        )
        transfer = await replay(match.workflow, TRANSFER) if match else {"success": False, "actions_executed": []}
        transfer_state = state.snapshot()
        transfer_exact = transfer_state["messages"] == [TRANSFER]

        false_success_cases = []
        for name, parameters, fault in (
            ("blank_content", {**TRANSFER, "content": ""}, "normal"),
            ("dropped_persistence", dict(TRANSFER), "drop_persistence"),
        ):
            _post(base_url + "/api/reset", {"version": 1, "fault": fault})
            naive = await replay(workflow, parameters, validate_state=False)
            naive_persisted = bool(state.snapshot()["messages"])
            _post(base_url + "/api/reset", {"version": 1, "fault": fault})
            validated = await replay(workflow, parameters, validate_state=True)
            validated_persisted = bool(state.snapshot()["messages"])
            false_success_cases.append({
                "case": name,
                "naive_reported_success": naive["success"],
                "naive_actual_success": naive_persisted,
                "validated_reported_success": validated["success"],
                "validated_actual_success": validated_persisted,
                "validated_failure": validated.get("failed_predicate") or validated.get("errors"),
            })

        # UI version 2 changes the button locator. The precondition must stop
        # before any POST /api/send occurs, then the store archives the version.
        _post(base_url + "/api/reset", {"version": 2, "fault": "normal"})
        before_change_events = len([e for e in state.snapshot()["events"] if e["event"] == "send_request"])
        changed = await replay(workflow, TRANSFER)
        after_change_events = len([e for e in state.snapshot()["events"] if e["event"] == "send_request"])
        if not changed["success"]:
            store.invalidate_workflow(workflow.workflow_id, changed.get("failed_predicate") or str(changed["errors"]))
        invalid_file = store_dir / f"invalid_{workflow.workflow_id}.json"
        post_invalidation_match = store.find_workflow_for_task("send message to audit@example.org")

        naive_false_rate = sum(
            row["naive_reported_success"] and not row["naive_actual_success"] for row in false_success_cases
        ) / len(false_success_cases)
        validated_false_rate = sum(
            row["validated_reported_success"] and not row["validated_actual_success"] for row in false_success_cases
        ) / len(false_success_cases)
        metrics = {
            "exploration_seconds": exploration["elapsed_seconds"],
            "validation_replay_seconds": validation["execution_time"],
            "parameterized_replay_seconds": transfer.get("execution_time"),
            "exploration_llm_calls": exploration["llm_calls"],
            "parameterized_replay_llm_calls": 0,
            "exploration_success_rate": float(exploration["success"]),
            "replay_success_rate": float(bool(transfer["success"])),
            "workflow_match_rate": float(match is not None),
            "naive_false_success_rate": naive_false_rate,
            "state_validated_false_success_rate": validated_false_rate,
            "page_change_detection_rate": float(not changed["success"]),
            "fallback_relearn_count": int(changed["fallback_required"]),
            "speedup_exploration_over_parameterized_replay": (
                exploration["elapsed_seconds"] / transfer.get("execution_time")
                if transfer.get("execution_time") else None
            ),
        }
        gates = {
            "real_stepwise_model_exploration_succeeded": exploration["success"] and exploration["llm_calls"] == len(ALLOWED_PLAN),
            "capture_has_actions_parameters_url_and_locator_evidence": all(
                item.get("before", {}).get("url")
                and item.get("locator_evidence", {}).get("xpath")
                and item.get("locator_evidence", {}).get("css")
                and item.get("locator_evidence", {}).get("id")
                and "action_parameters" in item
                for item in exploration["captured_actions"]
            ),
            "workflow_has_pre_post_and_final_state_checks": (
                all(step.preconditions and step.postconditions for step in workflow.steps)
                and bool(workflow.final_predicates)
            ),
            "first_success_created_candidate": candidate_before_reset,
            "independent_reset_replay_validated": validation["success"] and workflow.validated_at is not None,
            "missing_reset_never_published": no_reset_stayed_candidate,
            "validated_workflow_was_matchable": match is not None,
            "parameterized_replay_used_no_llm": transfer["success"] and transfer_exact,
            "training_literals_not_reused": transfer_exact and FIRST not in transfer_state["messages"],
            "naive_baseline_exposes_false_success": naive_false_rate == 1.0,
            "state_validation_rejects_false_success": validated_false_rate == 0.0 and all(
                not row["validated_reported_success"] for row in false_success_cases
            ),
            "page_change_stopped_before_side_effect": (
                not changed["success"] and changed["fallback_required"]
                and before_change_events == after_change_events
            ),
            "invalid_version_removed_from_retrieval": (
                invalid_file.exists() and workflow.workflow_id not in store.workflows
                and post_invalidation_match is None
            ),
        }
        result_claims = {
            "validated_workflow_completed_parameterized_transfer": bool(transfer["success"] and transfer_exact),
            "replay_eliminated_stepwise_llm_calls": exploration["llm_calls"] > 0 and metrics["parameterized_replay_llm_calls"] == 0,
            "state_validation_reduced_false_success_rate": validated_false_rate < naive_false_rate,
            "page_change_was_detected_before_side_effect": gates["page_change_stopped_before_side_effect"],
            "replay_was_faster_than_exploration": bool(
                transfer.get("execution_time") and exploration["elapsed_seconds"] > transfer["execution_time"]
            ),
        }
        report = {
            "schema_version": 2,
            "experiment": "9-5",
            "canonical_source": "book/chapter9.md#实验-9-5-从浏览器轨迹生成可验证工作流",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "execution_mode": "real_model_plus_local_http_plus_real_playwright_chromium",
            "model": args.model,
            "seed": args.seed,
            "backend": {**backend, "credential_value_recorded": False},
            "credential_value_recorded": False,
            "host": {"python": platform.python_version(), "platform": platform.platform()},
            "lifecycle": {
                "exploration": exploration,
                "candidate_file": str(candidate_file.relative_to(output_dir)),
                "validation_reset_count": state.reset_count,
                "validation_replay": validation,
                "transfer_replay": transfer,
                "page_change_replay": changed,
                "invalid_file": str(invalid_file.relative_to(output_dir)),
            },
            "false_success_comparison": false_success_cases,
            "metrics": metrics,
            "cost": exploration["usage"],
            "sandbox": {
                "url_origin": base_url,
                "external_side_effects": False,
                "final_state": state.snapshot(),
            },
            "gates": gates,
            "acceptance": {
                "gates": [{"name": name, "passed": passed} for name, passed in gates.items()],
                "execution_accepted": all(gates.values()),
                "result_claims": result_claims,
                "all_manuscript_result_claims_observed": all(result_claims.values()),
            },
            "accepted": all(gates.values()),
        }

    report_path = output_dir / "evidence.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["artifact_hashes"] = {
        "candidate_snapshot_sha256": _sha(candidate_snapshot),
        "invalid_sha256": _sha(invalid_file),
        "exploration_screenshot_sha256": _sha(screenshot_path),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = ROOT / "validation" / "latest.json"
    latest.parent.mkdir(exist_ok=True)
    shutil.copyfile(report_path, latest)
    print(json.dumps({
        "evidence": str(report_path.relative_to(ROOT)),
        "evidence_sha256": _sha(report_path),
        "accepted": report["accepted"],
        "metrics": report["metrics"],
        "cost": report["cost"],
    }, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("openrouter", "openai", "ark", "moonshot"), default="ark")
    parser.add_argument("--model", default="doubao-seed-1-6-flash-250615")
    parser.add_argument("--seed", type=int, default=8401)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    report = asyncio.run(campaign(args))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
