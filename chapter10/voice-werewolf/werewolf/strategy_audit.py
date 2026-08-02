"""Post-game, evidence-based acceptance audit for role strategy."""

from __future__ import annotations

import json
import os


REQUIRED_CRITERIA = (
    "werewolf_concealment",
    "seer_timing_and_evidence",
    "villager_logical_reasoning",
    "role_consistency",
)
VALID_STATUSES = {"pass", "fail", "insufficient"}


def validate_strategy_result(result):
    """Turn a model grade into a strict, machine-checkable acceptance record."""
    errors = []
    criteria = result.get("criteria")
    if not isinstance(criteria, dict):
        criteria = {}
        errors.append("criteria must be an object")
    for name in REQUIRED_CRITERIA:
        item = criteria.get(name)
        if not isinstance(item, dict):
            errors.append(f"missing criterion object: {name}")
            continue
        status = item.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"invalid status for {name}: {status!r}")
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            errors.append(f"criterion lacks quoted evidence: {name}")
    claimed = result.get("overall_pass")
    computed_pass = not errors and all(
        criteria[name].get("status") == "pass" for name in REQUIRED_CRITERIA
    )
    result["model_overall_pass_claim"] = claimed
    result["schema_valid"] = not errors
    result["validation_errors"] = errors
    result["overall_pass"] = computed_pass
    return result


def strategy_acceptance_passes(result):
    return bool(
        isinstance(result, dict)
        and result.get("schema_valid") is True
        and result.get("overall_pass") is True
    )


def _backends():
    from openai import OpenAI
    from .agent import _to_openrouter_model
    options = {"timeout": float(os.getenv("WEREWOLF_LLM_TIMEOUT", "45")), "max_retries": 1}
    out = []
    if os.getenv("ARK_API_KEY"):
        out.append((OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3", **options), os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"), "ark"))
    if os.getenv("MOONSHOT_API_KEY"):
        out.append((OpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url="https://api.moonshot.cn/v1", **options), os.getenv("MOONSHOT_MODEL", "kimi-k3"), "moonshot"))
    if os.getenv("OPENAI_API_KEY"):
        out.append((OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.getenv("OPENAI_BASE_URL") or None, **options), os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "openai"))
    if os.getenv("OPENROUTER_API_KEY"):
        model = _to_openrouter_model(os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))
        out.append((OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            **options,
        ), model, "openrouter"))
    return out


def evaluate_strategy(judge):
    roles = {p.name: p.role.value for p in judge.players}
    payload = {
        "roles": roles,
        "actions": judge.action_history,
        "criteria": {
            "werewolf_concealment": "Wolf public speech plausibly hides identity and does not expose teammates.",
            "seer_timing_and_evidence": "Seer reveals investigation at an appropriate time and reports only known results.",
            "villager_logical_reasoning": "Villager suspicion cites public speech/voting behavior rather than random guesses.",
            "role_consistency": "AI actions and public speech are consistent with role capabilities and goals.",
        },
        "instruction": (
            "Grade each criterion using only status pass/fail/insufficient and short, "
            "quoted action evidence. Do not infer unlogged behavior. Return exactly one "
            "JSON object shaped as {\"criteria\": {\"werewolf_concealment\": "
            "{\"status\": \"pass|fail|insufficient\", \"evidence\": \"quote\"}, "
            "\"seer_timing_and_evidence\": {...}, \"villager_logical_reasoning\": "
            "{...}, \"role_consistency\": {...}}, \"overall_pass\": true|false}. "
            "Use the key status, never grade, and include all four named criteria."
        ),
    }
    last = None
    attempts = []
    for client, model, provider in _backends():
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                response_format={"type": "json_object"},
            )
            if "kimi-k3" in model:
                kwargs.update(temperature=1, max_tokens=4096)
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or "{}"
            raw_result = json.loads(content)
            # Validation annotates its input. Keep a distinct credential-free raw
            # result in the attempt record so attaching attempts to the accepted
            # result cannot create a self-referential JSON structure.
            result = json.loads(content)
            result["provider"] = provider
            result["model"] = model
            checked = validate_strategy_result(result)
            usage = getattr(response, "usage", None)
            usage = usage.model_dump() if hasattr(usage, "model_dump") else usage
            attempts.append({
                "provider": provider,
                "model": model,
                "response_id": getattr(response, "id", None),
                "provider_reported_model": getattr(response, "model", None),
                "usage": usage,
                "schema_valid": checked["schema_valid"],
                "validation_errors": checked["validation_errors"],
                "raw_result": raw_result,
            })
            if checked["schema_valid"]:
                checked["judge_attempts"] = attempts
                return checked
            last = ValueError(
                f"{provider} strategy judge returned an invalid schema: "
                + "; ".join(checked["validation_errors"])
            )
            print(f"[策略审计] {provider} 模式无效，尝试下一端点")
        except Exception as exc:
            last = exc
            attempts.append({
                "provider": provider,
                "model": model,
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            })
            print(f"[策略审计] {provider} 失败：{type(exc).__name__}，尝试下一端点")
    failure = RuntimeError("没有可用的真实 LLM 端点完成有效的策略验收")
    failure.judge_attempts = attempts
    raise failure from last
