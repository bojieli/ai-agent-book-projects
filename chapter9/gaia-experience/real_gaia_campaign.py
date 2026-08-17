#!/usr/bin/env python3
"""Real GAIA learning/transfer campaign for manuscript Experiment 9-2.

This runner uses actual GAIA validation questions, externally scores answers
against the published references, extracts cross-run experience with a real
LLM, and reruns a disjoint transfer split under all three manuscript controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import string
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from openai import OpenAI

from experience_documents import ExperienceDocument


ROOT = Path(__file__).resolve().parent
BACKENDS = {
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
    "moonshot": ("MOONSHOT_API_KEY", "https://api.moonshot.cn/v1", "kimi-k3"),
    "ark": ("ARK_API_KEY", "https://ark.cn-beijing.volces.com/api/v3", "doubao-seed-1-6-250615"),
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini"),
}

# Six learning tasks deliberately include an impaired partial and failure arm.
# The four transfer task IDs are disjoint and never shown during extraction.
LEARNING_SPECS = [
    ("a0068077-79f4-461a-adfe-75c1a4148545", "verified"),
    ("bda648d7-d618-4883-88f4-3466eabd860e", "verified"),
    ("cf106601-ab4f-4af9-b045-5295fe67b37d", "verified"),
    ("5a0c1adf-205e-4841-a666-7c3ef95def9d", "verified"),
    ("a0c07678-e491-4bbc-8f0b-07405144218f", "partial_first_component"),
    ("840bfca7-4f7b-481a-8794-c560c340185d", "no_search_control"),
]
TRANSFER_IDS = [
    "8e867cd7-cff9-4e6c-867a-ff5ddc2550be",
    "11af4e1a-5f45-467d-9aeb-46f4bb0bf034",
    "d0633230-7067-47a9-9dbf-ee11e0a2cdd6",
    "e29834fd-413a-455c-a33e-c3915b07401c",
]

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the live web for evidence relevant to a GAIA question.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}


def _dump(value: Any) -> Any:
    return value.model_dump(mode="json", exclude_none=True) if hasattr(value, "model_dump") else value


def normalize_str(value: str, *, remove_punct: bool = True) -> str:
    value = re.sub(r"\s", "", str(value)).lower()
    if remove_punct:
        value = value.translate(str.maketrans("", "", string.punctuation))
    return value


def _number(value: str) -> float | None:
    try:
        return float(str(value).replace("$", "").replace("%", "").replace(",", ""))
    except ValueError:
        return None


def gaia_component_score(answer: str, ground_truth: str) -> dict[str, Any]:
    """AWorld-compatible exact score plus auditable partial list credit.

    `official_exact` is the authoritative GAIA/AWorld result. `component_score`
    only distinguishes partial list answers for the manuscript's three-state
    learning analysis; it never changes the official exact result.
    """
    gt_number = _number(ground_truth)
    if gt_number is not None:
        exact = _number(answer) == gt_number
        return {"official_exact": exact, "component_score": 1.0 if exact else 0.0, "matched_components": int(exact), "total_components": 1}
    delimiters = [",", ";"]
    if any(char in ground_truth for char in delimiters):
        gt = [part.strip() for part in re.split(r"[,;]", ground_truth)]
        predicted = [part.strip() for part in re.split(r"[,;]", answer)]
        matches = 0
        for index, expected in enumerate(gt):
            if index >= len(predicted):
                continue
            pnum, enum = _number(predicted[index]), _number(expected)
            matches += int((pnum == enum) if enum is not None else (normalize_str(predicted[index], remove_punct=False) == normalize_str(expected, remove_punct=False)))
        exact = len(predicted) == len(gt) and matches == len(gt)
        return {"official_exact": exact, "component_score": round(matches / len(gt), 6), "matched_components": matches, "total_components": len(gt)}
    exact = normalize_str(answer) == normalize_str(ground_truth)
    return {"official_exact": exact, "component_score": 1.0 if exact else 0.0, "matched_components": int(exact), "total_components": 1}


def outcome_label(score: float) -> str:
    if score == 1.0:
        return "success"
    if score > 0:
        return "partial"
    return "failure"


class CampaignClient:
    def __init__(self, provider: str, model: str | None):
        key_env, base_url, default_model = BACKENDS[provider]
        key = os.getenv(key_env)
        if not key:
            raise RuntimeError(f"{key_env} is required")
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            raise RuntimeError("TAVILY_API_KEY is required for live GAIA web trajectories")
        self.provider = provider
        self.model = model or default_model
        self.key_env = key_env
        self.base_url = base_url
        self.tavily_key = tavily_key
        self.client = OpenAI(api_key=key, base_url=base_url)
        self.api_turns: list[dict[str, Any]] = []

    def complete(self, kind: str, **kwargs: Any):
        request = {"model": self.model, **kwargs}
        started = time.time()
        response = self.client.chat.completions.create(**request)
        self.api_turns.append({
            "kind": kind,
            "provider": self.provider,
            "endpoint": f"{self.base_url}/chat/completions",
            "request": _dump(request),
            "response": _dump(response),
            "elapsed_seconds": round(time.time() - started, 6),
        })
        return response

    def search(self, query: str) -> dict[str, Any]:
        public_request = {"query": query, "search_depth": "basic", "max_results": 5, "include_raw_content": False}
        started = time.time()
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": self.tavily_key, **public_request},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        self.api_turns.append({
            "kind": "live_web_search",
            "provider": "tavily",
            "endpoint": "https://api.tavily.com/search",
            "request": public_request,
            "response": payload,
            "elapsed_seconds": round(time.time() - started, 6),
            "credential_value_recorded": False,
        })
        return payload

    def usage(self) -> dict[str, Any]:
        prompt = completion = total = searches = 0
        cost = 0.0
        cost_count = 0
        for turn in self.api_turns:
            if turn["kind"] == "live_web_search":
                searches += 1
                continue
            usage = turn.get("response", {}).get("usage") or {}
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
            "live_tavily_searches": searches,
            "tavily_basic_search_credits": searches,
            "provider_reported_llm_cost_usd": round(cost, 9) if cost_count else None,
            "llm_cost_qualification": "provider-native usage.cost" if cost_count else "provider did not expose monetary cost; no price was guessed",
            "tavily_usd_cost": None,
            "tavily_cost_qualification": "search credits counted; plan-specific USD price is not inferable from API receipts",
        }


def _assistant(message: Any) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            {"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}}
            for call in (message.tool_calls or [])
        ],
    }


def _parse_final(content: str) -> tuple[str, str]:
    try:
        payload = json.loads(content)
        return str(payload.get("final_answer", "")).strip(), str(payload.get("reason", "")).strip()
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"<FINAL>(.*?)</FINAL>", content, re.I | re.S)
        return (match.group(1).strip() if match else content.strip()), "unstructured response"


def run_gaia_task(
    task: dict[str, Any], client: CampaignClient, *, mode: str,
    experience_text: str = "", intervention: str = "verified", max_searches: int = 3,
) -> dict[str, Any]:
    instruction = """You are solving a GAIA validation question. Use live web search when evidence is needed.
Do not use prior knowledge as evidence for dated or obscure facts. Separate discovery from verification,
prefer primary sources, and obey the requested answer format. When ready, return JSON only as
{"final_answer":"exact concise answer", "reason":"brief evidence rationale"}."""
    tools = [SEARCH_TOOL]
    if intervention == "partial_first_component":
        instruction += "\nCONTROL INTERVENTION: return only the first requested list component, even if the question requests two."
    elif intervention == "no_search_control":
        instruction += "\nCONTROL INTERVENTION: answer without any web search."
        tools = []
    if experience_text:
        instruction += "\n\nRetrieved experience (generic strategy only; it contains no held-out answer):\n" + experience_text
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": task["Question"]},
    ]
    trajectory: list[dict[str, Any]] = [{"step": 0, "role": "user", "content": task["Question"]}]
    search_count = 0
    final_content = ""
    while True:
        response = client.complete(
            "gaia_task_agent",
            messages=messages,
            tools=tools or None,
            temperature=0,
            response_format={"type": "json_object"},
        )
        message = response.choices[0].message
        messages.append(_assistant(message))
        trajectory.append({"step": len(trajectory), "role": "assistant", "content": message.content or "", "tool_calls": _assistant(message)["tool_calls"]})
        if not message.tool_calls:
            final_content = message.content or ""
            break
        for call in message.tool_calls:
            if call.function.name != "web_search" or search_count >= max_searches:
                result = {"error": "search_limit_or_unknown_tool"}
            else:
                try:
                    query = json.loads(call.function.arguments or "{}").get("query", "")
                except json.JSONDecodeError:
                    query = ""
                result = client.search(query)
                search_count += 1
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})
            trajectory.append({"step": len(trajectory), "role": "tool", "name": call.function.name, "content": result})
        if search_count >= max_searches:
            tools = []

    answer, rationale = _parse_final(final_content)
    scoring = gaia_component_score(answer, task["Final answer"])
    return {
        "trajectory_id": f"{task['task_id']}::{mode}",
        "gaia_task_id": task["task_id"],
        "gaia_level": task["Level"],
        "task_family": "web_research",
        "capabilities": ["search", "source_verification", "answer_formatting"],
        "question": task["Question"],
        "reference_answer": task["Final answer"],
        "model_answer": answer,
        "answer_rationale": rationale,
        "mode": mode,
        "intervention": intervention,
        "environment_score": scoring["component_score"],
        "official_gaia_exact": scoring["official_exact"],
        "outcome": outcome_label(scoring["component_score"]),
        "score_details": scoring,
        "search_count": search_count,
        "retrieved_experience_characters": len(experience_text),
        "retrieved_experience_estimated_tokens": round(len(experience_text) / 4, 2),
        "trajectory": trajectory,
    }


def extract_cross_trajectory_document(records: list[dict[str, Any]], client: CampaignClient) -> tuple[ExperienceDocument, dict[str, Any]]:
    compact = [{
        "trajectory_id": row["trajectory_id"], "question": row["question"],
        "outcome": row["outcome"], "environment_score": row["environment_score"],
        "search_queries": [step["content"].get("query") for step in row["trajectory"] if step.get("role") == "tool" and isinstance(step.get("content"), dict)],
        "answer_rationale": row["answer_rationale"],
    } for row in records]
    prompt = f"""Compare these externally scored, real GAIA trajectories. Propose reusable experience,
not task answers. Return JSON with arrays `candidates`, `pitfalls`, `exceptions`, `applies_when`.
Every candidate must have text and supporting_trajectory_ids. Recommend source verification,
query refinement, or answer-format checks only when at least two independent non-failure
trajectories support it. Failures may support pitfalls but never positive recommendations.

Trajectories:\n{json.dumps(compact, ensure_ascii=False, indent=2)}"""
    response = client.complete(
        "cross_trajectory_extractor",
        messages=[{"role": "user", "content": prompt}], temperature=0,
        response_format={"type": "json_object"},
    )
    try:
        proposed = json.loads(response.choices[0].message.content or "{}")
    except json.JSONDecodeError:
        proposed = {}
    by_id = {row["trajectory_id"]: row for row in records}
    accepted, rejected = [], []
    for candidate in proposed.get("candidates", []):
        supporters = list(dict.fromkeys(candidate.get("supporting_trajectory_ids") or []))
        valid = (
            bool(str(candidate.get("text", "")).strip())
            and len(supporters) >= 2
            and all(identifier in by_id and by_id[identifier]["outcome"] != "failure" for identifier in supporters)
        )
        normalized = {"text": str(candidate.get("text", "")).strip(), "supporting_trajectory_ids": supporters, "accepted": valid}
        (accepted if valid else rejected).append(normalized)
    sources = tuple(f"{row['trajectory_id']} ({row['outcome']}, score={row['environment_score']:.2f})" for row in records)
    document = ExperienceDocument(
        task_family="web_research",
        capabilities=("answer_formatting", "search", "source_verification"),
        applies_when=tuple(str(x) for x in proposed.get("applies_when", [])) or ("GAIA web-research tasks requiring externally verifiable facts",),
        recommended_strategies=tuple(item["text"] for item in accepted),
        common_pitfalls=tuple(str(x) for x in proposed.get("pitfalls", [])),
        exceptions=tuple(str(x) for x in proposed.get("exceptions", [])),
        sources=sources,
        last_validated=datetime.now(timezone.utc).date().isoformat(),
    )
    audit = {"raw_proposal": proposed, "accepted_candidates": accepted, "rejected_candidates": rejected, "minimum_nonfailure_support": 2}
    return document, audit


def single_trajectory_summary(record: dict[str, Any]) -> str:
    queries = [
        step["content"].get("query", "") for step in record["trajectory"]
        if step.get("role") == "tool" and isinstance(step.get("content"), dict)
    ]
    return (
        f"One prior run ({record['trajectory_id']}, outcome={record['outcome']}) used "
        f"these search queries: {queries}. Its evidence rationale was: {record['answer_rationale']}"
    )


def _gate(name: str, passed: bool, evidence: object) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def _git_revision() -> str | None:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return proc.stdout.strip() if proc.returncode == 0 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=tuple(BACKENDS), default="openrouter")
    parser.add_argument("--model")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (ROOT / "gaia-validation.jsonl").read_text(encoding="utf-8").splitlines()]
    by_id = {row["task_id"]: row for row in rows}
    selected = {identifier for identifier, _ in LEARNING_SPECS} | set(TRANSFER_IDS)
    missing = selected - set(by_id)
    if missing:
        raise RuntimeError(f"GAIA task IDs missing from dataset: {sorted(missing)}")
    client = CampaignClient(args.provider, args.model)
    learning = [run_gaia_task(by_id[identifier], client, mode="learning", intervention=intervention) for identifier, intervention in LEARNING_SPECS]
    document, extraction_audit = extract_cross_trajectory_document(learning, client)
    markdown = document.to_markdown()
    successful = [row for row in learning if row["outcome"] == "success"]
    summary_source = successful[0] if successful else learning[0]
    single_summary = single_trajectory_summary(summary_source)

    transfer: dict[str, list[dict[str, Any]]] = {mode: [] for mode in ("no_experience", "single_trajectory_summary", "knowledge_document")}
    for identifier in TRANSFER_IDS:
        task = by_id[identifier]
        transfer["no_experience"].append(run_gaia_task(task, client, mode="no_experience"))
        transfer["single_trajectory_summary"].append(run_gaia_task(task, client, mode="single_trajectory_summary", experience_text=single_summary))
        transfer["knowledge_document"].append(run_gaia_task(task, client, mode="knowledge_document", experience_text=markdown))

    baseline_by_task = {row["gaia_task_id"]: row["official_gaia_exact"] for row in transfer["no_experience"]}
    metrics: dict[str, Any] = {}
    for mode, results in transfer.items():
        total = len(results)
        exact = sum(row["official_gaia_exact"] for row in results)
        negative = sum(bool(baseline_by_task[row["gaia_task_id"]]) and not row["official_gaia_exact"] for row in results)
        metrics[mode] = {
            "successes": exact,
            "tasks": total,
            "transfer_success_rate": round(exact / total, 6),
            "negative_transfer_rate_vs_no_experience": round(negative / total, 6),
            "average_retrieved_characters": round(sum(row["retrieved_experience_characters"] for row in results) / total, 2),
            "average_retrieved_estimated_tokens": round(sum(row["retrieved_experience_estimated_tokens"] for row in results) / total, 2),
        }

    labels = {row["outcome"] for row in learning}
    traceable = all(source.split(" (")[0] in {row["trajectory_id"] for row in learning} for source in document.sources)
    gates = [
        _gate("real_gaia_questions_and_external_reference_scoring", all(row["gaia_task_id"] in by_id and "official_gaia_exact" in row for row in learning + sum(transfer.values(), [])), len(learning) + sum(map(len, transfer.values()))),
        _gate("immutable_full_learning_trajectories_saved", all(row["trajectory"] for row in learning), [row["trajectory_id"] for row in learning]),
        _gate("success_partial_failure_present", labels == {"success", "partial", "failure"}, sorted(labels)),
        _gate("cross_trajectory_llm_extraction_executed", any(turn["kind"] == "cross_trajectory_extractor" for turn in client.api_turns), len(extraction_audit["accepted_candidates"])),
        _gate("every_recommendation_has_two_nonfailure_sources", bool(extraction_audit["accepted_candidates"]) and all(len(item["supporting_trajectory_ids"]) >= 2 for item in extraction_audit["accepted_candidates"]), extraction_audit["accepted_candidates"]),
        _gate("markdown_has_required_sections", all(section in markdown for section in ("## 适用场景", "## 推荐策略", "## 常见误区", "## 例外条件", "## 来源轨迹")), None),
        _gate("formal_conclusions_trace_to_raw_trajectories", traceable, list(document.sources)),
        _gate("learning_and_transfer_splits_disjoint", not ({identifier for identifier, _ in LEARNING_SPECS} & set(TRANSFER_IDS)), {"learning": [x for x, _ in LEARNING_SPECS], "transfer": TRANSFER_IDS}),
        _gate("all_three_controls_run_same_model_and_tasks", all({row["gaia_task_id"] for row in results} == set(TRANSFER_IDS) for results in transfer.values()), {mode: len(rows) for mode, rows in transfer.items()}),
        _gate("transfer_context_and_negative_transfer_reported", all("average_retrieved_estimated_tokens" in value and "negative_transfer_rate_vs_no_experience" in value for value in metrics.values()), metrics),
        _gate("raw_real_api_receipts_saved_without_credentials", bool(client.api_turns), len(client.api_turns)),
    ]
    execution_accepted = all(gate["passed"] for gate in gates)
    result_claims = {
        "knowledge_document_improves_over_no_experience": metrics["knowledge_document"]["transfer_success_rate"] > metrics["no_experience"]["transfer_success_rate"],
        "knowledge_document_improves_over_single_summary": metrics["knowledge_document"]["transfer_success_rate"] > metrics["single_trajectory_summary"]["transfer_success_rate"],
        "knowledge_document_negative_transfer_not_worse_than_single_summary": metrics["knowledge_document"]["negative_transfer_rate_vs_no_experience"] <= metrics["single_trajectory_summary"]["negative_transfer_rate_vs_no_experience"],
    }
    dataset_bytes = (ROOT / "gaia-validation.jsonl").read_bytes()
    evidence = {
        "schema_version": 2,
        "experiment_id": "9-2",
        "canonical_source": "book/chapter9.md#实验-9-2-从-GAIA-轨迹提炼经验知识文档",
        "evidence_mode": "real_gaia_live_web_llm_transfer_campaign",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "provider": client.provider,
        "model": client.model,
        "endpoint": f"{client.base_url}/chat/completions",
        "credential_source_envs": [client.key_env, "TAVILY_API_KEY"],
        "credential_value_recorded": False,
        "repository_revision": _git_revision(),
        "host": {"python": sys.version.split()[0], "platform": platform.platform()},
        "gaia_dataset": {"path": "gaia-validation.jsonl", "sha256": hashlib.sha256(dataset_bytes).hexdigest(), "rows": len(rows), "upstream_runtime": "AWorld scorer semantics reproduced by gaia_component_score.official_exact"},
        "learning_trajectories": learning,
        "cross_trajectory_extraction": extraction_audit,
        "experience_document_markdown": markdown,
        "single_trajectory_summary": single_summary,
        "transfer_runs": transfer,
        "metrics": metrics,
        "usage": client.usage(),
        "api_turns": client.api_turns,
        "acceptance": {
            "gates": gates,
            "execution_accepted": execution_accepted,
            "result_claims": result_claims,
            "all_manuscript_result_claims_observed": all(result_claims.values()),
        },
    }
    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or ROOT / "validation" / stamp
    output_dir.mkdir(parents=True, exist_ok=False)
    payload = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    (output_dir / "evidence.json").write_text(payload, encoding="utf-8")
    (output_dir / "experience-document.md").write_text(markdown, encoding="utf-8")
    (ROOT / "validation").mkdir(exist_ok=True)
    (ROOT / "validation" / "latest.json").write_text(payload, encoding="utf-8")
    print(json.dumps({
        "evidence": str((output_dir / "evidence.json").relative_to(ROOT)),
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "execution_accepted": execution_accepted,
        "all_manuscript_result_claims_observed": all(result_claims.values()),
        "learning_outcomes": {label: sum(row["outcome"] == label for row in learning) for label in ("success", "partial", "failure")},
        "metrics": metrics,
        "usage": evidence["usage"],
    }, ensure_ascii=False, indent=2))
    return 0 if execution_accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
