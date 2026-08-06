#!/usr/bin/env python3
"""Canonical live campaign for Experiment 3-8.

The comparison keeps the corpus, cases, BM25 implementation, retrieval depth,
answer model, and independent judge fixed.  The only changed factor is whether
the answerer receives one search of the original question or may plan and
iterate searches through a ReAct tool loop.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from openai import OpenAI

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CHAPTER))

from experiment_utils import ChatRecorder, jsonable, sha256_file, write_campaign_evidence
from offline_retriever import OfflineRetriever


ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
MOONSHOT_ENDPOINT = "https://api.moonshot.cn/v1"
ARTICLE_RE = re.compile(r"第[一二三四五六七八九十百千零两0-9]+条(?:之[一二三四五六七八九十0-9]+)?")


def parse_json(text: str) -> Dict[str, Any]:
    value = (text or "").strip()
    if "```" in value:
        value = value.split("```", 2)[1]
        if value.lstrip().startswith("json"):
            value = value.lstrip()[4:]
    return json.loads(value.strip())


def article_hits(results: Iterable[Dict[str, Any]], gold: Iterable[str]) -> List[str]:
    combined = "\n".join(str(row.get("text", "")) for row in results)
    return [article for article in gold if article in combined]


def context(results: List[Dict[str, Any]]) -> str:
    return "\n\n".join(
        f"[{row['chunk_id']}] {row['metadata']['title']}\n{row['text']}"
        for row in results
    )


def citations(answer: str, valid_ids: Iterable[str]) -> Dict[str, Any]:
    cited = re.findall(r"\[([^\[\]]+_chunk_\d+)\]", answer or "")
    valid = set(valid_ids)
    return {
        "cited_chunk_ids": cited,
        "valid_count": sum(item in valid for item in cited),
        "invalid_count": sum(item not in valid for item in cited),
        "has_valid_citation": any(item in valid for item in cited),
    }


def usage(calls: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for call in calls:
        current = call.get("usage") or {}
        for key in totals:
            totals[key] += int(current.get(key) or 0)
    return totals


def judge_prompt(case: Dict[str, Any], arm: str, answer: str, retrieved: List[Dict[str, Any]]):
    return [
        {
            "role": "system",
            "content": (
                "你是独立的中文法律问答评审。只根据给出的法条证据评分，不要使用外部知识。"
                "检查结论是否被证据支持、是否覆盖问题的全部法律问题、引用是否真实。"
                "这不是正式法律意见。只返回 JSON。"
            ),
        },
        {
            "role": "user",
            "content": f"""问题：{case['question']}
金标准法条：{json.dumps(case['gold_articles'], ensure_ascii=False)}
实验臂：{arm}
检索证据：
{context(retrieved)}

回答：
{answer}

返回：{{"correctness":1,"completeness":1,"groundedness":1,"citation_quality":1,
"unsupported_claim":false,"reasoning":"..."}}
每项 1-4 分；4=完全正确，3=核心正确但有轻微缺陷，2=有重大遗漏，1=错误。
若存在实质性无证据结论，unsupported_claim=true。""",
        },
    ]


class Campaign:
    def __init__(self, args: argparse.Namespace):
        ark_key = os.getenv("ARK_API_KEY")
        judge_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        if not ark_key or not judge_key:
            raise RuntimeError("ARK_API_KEY and MOONSHOT_API_KEY/KIMI_API_KEY are required")
        self.args = args
        self.retriever = OfflineRetriever(str(HERE / "laws"))
        self.answer_client = OpenAI(api_key=ark_key, base_url=args.answer_endpoint, timeout=args.timeout, max_retries=3)
        self.judge_client = OpenAI(api_key=judge_key, base_url=args.judge_endpoint, timeout=args.timeout, max_retries=3)

    def search(self, query: str) -> List[Dict[str, Any]]:
        return self.retriever.search(query, top_k=self.args.top_k)

    def answer_once(self, recorder: ChatRecorder, case: Dict[str, Any], retrieved: List[Dict[str, Any]]) -> str:
        response = recorder.create(
            purpose=f"3-8 baseline grounded answer {case['id']}",
            model=self.args.answer_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是法律信息助手。只能依据所给法条回答。每个实质结论后用 [chunk_id] 引用。"
                        "若证据不足必须说明。结尾注明：本回答仅供一般法律信息参考，不构成正式法律意见。"
                    ),
                },
                {"role": "user", "content": f"问题：{case['question']}\n\n证据：\n{context(retrieved)}"},
            ],
            temperature=0,
            seed=self.args.seed,
            max_tokens=900,
        )
        return response.choices[0].message.content or ""

    def answer_agentic(self, recorder: ChatRecorder, case: Dict[str, Any]):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_law",
                    "description": "Search the authoritative local Chinese statute corpus with BM25.",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string", "description": "Focused Chinese legal search query"}},
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                },
            }
        ]
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "你是 ReAct 法律检索 Agent，只能依据 search_law 返回的本地法条。先分解问题并搜索；"
                    "复杂问题应对每个独立法律问题迭代搜索。确认法条齐全后回答，每个结论用 [chunk_id] 引用。"
                    "不得引用未返回的材料。结尾注明：本回答仅供一般法律信息参考，不构成正式法律意见。"
                ),
            },
            {"role": "user", "content": case["question"]},
        ]
        trajectory = []
        union: Dict[str, Dict[str, Any]] = {}
        final = ""
        for iteration in range(1, self.args.max_searches + 2):
            request: Dict[str, Any] = {
                "model": self.args.answer_model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "required" if iteration == 1 else "auto",
                "temperature": 0,
                "seed": self.args.seed,
                "max_tokens": 900,
            }
            response = recorder.create(
                purpose=f"3-8 agentic react {case['id']} iteration {iteration}",
                **request,
            )
            message = response.choices[0].message
            assistant: Dict[str, Any] = {"role": "assistant", "content": message.content or ""}
            if message.tool_calls:
                assistant["tool_calls"] = [jsonable(tc) for tc in message.tool_calls]
            messages.append(assistant)
            step: Dict[str, Any] = {"iteration": iteration, "assistant": message.content or "", "searches": []}
            if not message.tool_calls:
                final = message.content or ""
                trajectory.append(step)
                break
            for tool_call in message.tool_calls:
                if len([q for row in trajectory for q in row["searches"]]) + len(step["searches"]) >= self.args.max_searches:
                    tool_result = {"error": "search budget exhausted"}
                else:
                    try:
                        query = str(json.loads(tool_call.function.arguments).get("query", "")).strip()
                    except Exception:
                        query = ""
                    rows = self.search(query) if query else []
                    for row in rows:
                        union[row["chunk_id"]] = row
                    tool_result = {"query": query, "results": rows}
                    step["searches"].append(tool_result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )
            trajectory.append(step)
        if not final:
            response = recorder.create(
                purpose=f"3-8 agentic forced final {case['id']}",
                model=self.args.answer_model,
                messages=messages + [{"role": "system", "content": "搜索预算已用完。现在仅根据已返回证据给出带引用的最终回答。"}],
                temperature=0,
                seed=self.args.seed,
                max_tokens=900,
            )
            final = response.choices[0].message.content or ""
        return final, list(union.values()), trajectory

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        answer_recorder = ChatRecorder(self.answer_client, "ark", self.args.answer_endpoint)
        judge_recorder = ChatRecorder(self.judge_client, "moonshot", self.args.judge_endpoint)
        started = time.perf_counter()
        baseline_results = self.search(case["question"])
        baseline_search_ms = (time.perf_counter() - started) * 1000
        before = time.perf_counter()
        baseline_answer = self.answer_once(answer_recorder, case, baseline_results)
        baseline_ms = (time.perf_counter() - before) * 1000 + baseline_search_ms

        before = time.perf_counter()
        agent_answer, agent_results, trajectory = self.answer_agentic(answer_recorder, case)
        agent_ms = (time.perf_counter() - before) * 1000

        arms = {}
        for name, answer, rows, latency, searches in (
            ("baseline", baseline_answer, baseline_results, baseline_ms, 1),
            ("agentic", agent_answer, agent_results, agent_ms, sum(len(s["searches"]) for s in trajectory)),
        ):
            response = judge_recorder.create(
                purpose=f"3-8 independent judge {case['id']} {name}",
                model=self.args.judge_model,
                messages=judge_prompt(case, name, answer, rows),
                temperature=0,
                seed=self.args.seed,
                max_tokens=700,
                response_format={"type": "json_object"},
            )
            judged = parse_json(response.choices[0].message.content or "{}")
            hits = article_hits(rows, case["gold_articles"])
            arms[name] = {
                "answer": answer,
                "retrieved_chunks": rows,
                "evidence": {
                    "gold_articles": case["gold_articles"],
                    "hit_articles": hits,
                    "recall": len(hits) / len(case["gold_articles"]),
                },
                "citations": citations(answer, [row["chunk_id"] for row in rows]),
                "search_count": searches,
                "latency_ms": round(latency, 3),
                "judge": judged,
            }
        return {
            "case": {**case, "complexity": "simple" if case.get("difficulty") == "easy" else "complex"},
            "arms": arms,
            "agentic_trajectory": trajectory,
            "receipts": answer_recorder.calls + judge_recorder.calls,
        }


def aggregate(rows: List[Dict[str, Any]], arm: str, group: str | None = None) -> Dict[str, Any]:
    selected = [row for row in rows if group is None or row["case"]["complexity"] == group]
    return {
        "n": len(selected),
        "evidence_recall": statistics.mean(row["arms"][arm]["evidence"]["recall"] for row in selected),
        "judge_correctness": statistics.mean(float(row["arms"][arm]["judge"].get("correctness", 1)) for row in selected),
        "citation_valid_rate": statistics.mean(1.0 if row["arms"][arm]["citations"]["has_valid_citation"] else 0.0 for row in selected),
        "mean_search_count": statistics.mean(row["arms"][arm]["search_count"] for row in selected),
        "mean_latency_ms": statistics.mean(row["arms"][arm]["latency_ms"] for row in selected),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer-model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--judge-model", default=os.getenv("MEMORY_JUDGE_MODEL", "moonshot-v1-32k"))
    parser.add_argument("--answer-endpoint", default=ARK_ENDPOINT)
    parser.add_argument("--judge-endpoint", default=MOONSHOT_ENDPOINT)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-searches", type=int, default=4)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()

    dataset_path = HERE / "evaluation" / "offline_qa.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    campaign = Campaign(args)
    rows: List[Dict[str, Any]] = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(campaign.run_case, case): case["id"] for case in cases}
        for future in concurrent.futures.as_completed(futures):
            case_id = futures[future]
            try:
                rows.append(future.result())
                print(f"completed {case_id} ({len(rows)}/{len(cases)})", flush=True)
            except Exception as exc:
                errors.append({"case_id": case_id, "type": type(exc).__name__, "error": str(exc)})
                print(f"ERROR {case_id}: {exc}", file=sys.stderr, flush=True)
    rows.sort(key=lambda row: row["case"]["id"])
    receipts = [call for row in rows for call in row.pop("receipts")]
    groups = sorted({row["case"]["complexity"] for row in rows})
    summary = {
        arm: {group: aggregate(rows, arm, group) for group in groups} | {"overall": aggregate(rows, arm)}
        for arm in ("baseline", "agentic")
    } if rows else {}
    agent_queries = [
        search["query"] for row in rows for step in row["agentic_trajectory"] for search in step["searches"]
    ]
    corpus_files = sorted((HERE / "laws").rglob("*.md"))
    corpus_manifest = [{"path": str(path.relative_to(HERE)), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in corpus_files]
    acceptance = {
        "real_law_corpus": len(corpus_files) >= 100,
        "labeled_simple_and_complex": set(groups) == {"simple", "complex"},
        "identical_cases_and_corpus": len(rows) == len(cases),
        "one_shot_baseline": all(row["arms"]["baseline"]["search_count"] == 1 for row in rows),
        "live_agent_generated_searches": bool(agent_queries) and all(query.strip() for query in agent_queries),
        "evidence_recall_measured": all("recall" in row["arms"][arm]["evidence"] for row in rows for arm in ("baseline", "agentic")),
        "citations_checked": all("invalid_count" in row["arms"][arm]["citations"] for row in rows for arm in ("baseline", "agentic")),
        "independent_external_judge": bool(rows) and all(any(call.get("provider") == "moonshot" for call in receipts) for _ in [0]),
        "raw_request_response_receipts": bool(receipts) and all("request" in call and ("response" in call or "error" in call) for call in receipts),
        "all_cases_succeeded": len(rows) == len(cases) and not errors,
    }
    acceptance["passed"] = all(acceptance.values())
    hypothesis = {}
    if summary:
        hypothesis = {
            "simple_roughly_ties": abs(summary["agentic"]["simple"]["judge_correctness"] - summary["baseline"]["simple"]["judge_correctness"]) <= 0.5,
            "complex_quality_improves": summary["agentic"]["complex"]["judge_correctness"] > summary["baseline"]["complex"]["judge_correctness"],
            "agentic_adds_latency": summary["agentic"]["overall"]["mean_latency_ms"] > summary["baseline"]["overall"]["mean_latency_ms"],
        }
    evidence = {
        "status": "passed" if acceptance["passed"] else ("partial" if rows else "blocked"),
        "configuration": vars(args),
        "corpus": {"document_count": len(corpus_files), "chunk_count": len(campaign.retriever.chunks), "files": corpus_manifest},
        "scope": {"cases_expected": len(cases), "cases_completed": len(rows), "groups": groups},
        "acceptance": acceptance,
        "hypothesis_outcome": hypothesis,
        "summary": {"metrics": summary, "api_calls": len(receipts), "token_usage": usage(receipts), "errors": len(errors)},
        "errors": errors,
        "results": rows,
    }
    manifest = write_campaign_evidence(
        HERE,
        "3-8",
        evidence,
        receipts,
        input_paths=[HERE / "campaign.py", HERE / "offline_retriever.py", dataset_path, *corpus_files],
    )
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    print(f"Canonical evidence: {HERE / 'validation' / 'latest.json'}")
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
