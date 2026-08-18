#!/usr/bin/env python3
"""把「AI 味」反馈开放式提炼为规则，并由 LLM judge 校准和评估。

默认使用 OpenAI GPT-5.6 Sol：

    python run_ai_style_skill.py

流程：全量反馈 → LLM 开放式提炼并做语义归并 → 每条规则用独立人工
金标校准 LLM judge → 生成 Skill → boundary/retention 评估 → 改写演示。
代码中不包含预置模式库，也不会用 detector 指纹过滤模型发现的新规律。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any, Dict, List

from evaluate import evaluate_rules, load_eval_texts
from extract_rules import extract_with_llm, load_pairs, write_candidates
from judge import calibrate, llm_judge, load_golden_set
from llm_client import default_model
from rewrite_demo import SAMPLE_TEXT, rewrite_with_llm
from skill_manager import merge_rules, prune_rules, write_archive, write_skill

ROOT = Path(__file__).resolve().parent

# 验收门槛（模型外部代码，LLM 不可修改）。
GATE_BOUNDARY_RATE = 0.85
GATE_RETENTION_HARM = 0.15


def run_pipeline(
    *,
    provider: str = "openai",
    model: str | None = None,
    seed: int = 8901,
    batches: int = 3,
) -> Dict[str, Any]:
    pairs = load_pairs()
    eval_texts = load_eval_texts()
    golden_set = load_golden_set()
    receipts: List[Dict[str, Any]] = []

    # 1) 一次查看全部反馈，避免批次顺序让同一概念被拆分、不同概念被误并。
    candidates, receipt = extract_with_llm(
        pairs,
        provider=provider,
        model=model,
        seed=seed,
    )
    receipts.append(receipt)
    rules, merge_report = merge_rules([], candidates)
    pair_batches = {pair["id"]: pair.get("batch", 1) for pair in pairs}
    for rule in rules:
        rule["last_confirmed_batch"] = max(
            (pair_batches[source] for source in rule.get("source_ids", []) if source in pair_batches),
            default=batches,
        )
    curve = [
        {
            "batch": batch_no,
            "rules_with_evidence": sum(
                any(pair_batches.get(source) == batch_no for source in rule.get("source_ids", []))
                for rule in rules
            ),
            "cumulative_rule_count": sum(
                any(pair_batches.get(source, batches + 1) <= batch_no for source in rule.get("source_ids", []))
                for rule in rules
            ),
        }
        for batch_no in range(1, batches + 1)
    ]
    total_candidates = len(candidates)
    write_candidates(candidates)

    # 2) 所有规则都由同一个批量 LLM judge 校准；无金标或不达标都拒绝上线。
    calibration = []
    active: List[Dict[str, Any]] = []
    judge_fn = llm_judge(
        provider=provider, model=model, seed=seed, receipts=receipts
    )
    for rule in rules:
        result = calibrate(rule, golden_set, judge_fn)
        calibration.append(result)
        if result["decision"] == "activate":
            rule["status"] = "active"
            active.append(rule)
        else:
            rule["status"] = "rejected"

    # 3) prune 演示：被证据推翻或长期未触发的规则归档（离线数据下无归档）。
    active, archived = prune_rules(active, current_batch=batches, contradicted_ids=set())

    # 4) 生成 Skill 并评估。
    skill_path = write_skill(active)
    archive_path = write_archive(archived)
    metrics = evaluate_rules(active, eval_texts, judge_fn)

    # 5) 改写演示。
    rewrite, receipt = rewrite_with_llm(
        SAMPLE_TEXT, active, provider=provider, model=model, seed=seed
    )
    receipts.append(receipt)

    gates = {
        "boundary_detection_rate >= 0.85": metrics["boundary_detection_rate"] >= GATE_BOUNDARY_RATE,
        "retention_harm_rate <= 0.15": metrics["retention_harm_rate"] <= GATE_RETENTION_HARM,
        "corpus_rules_have_unique_ids": (
            len(rules) == total_candidates
            and len({rule["id"] for rule in rules}) == len(rules)
            and not merge_report["merged"]
        ),
        "all_active_rules_use_llm_judge": all(
            rule.get("detector") == {"type": "llm"} for rule in active
        ),
        "all_active_rules_calibrated": all(
            any(c["rule_id"] == rule["id"] and c["decision"] == "activate" for c in calibration)
            for rule in active
        ),
        "out_of_library_cases_detected": all(
            any(detail["expected"] and set(detail["expected"]) & set(detail["fired"])
                for detail in metrics["boundary_details"] if detail["id"] == case_id)
            for case_id in ("b9", "b10", "b11")
        ),
        "real_llm_called_with_receipts": bool(receipts) and all(
            receipt["response"].get("id") for receipt in receipts
        ),
    }

    report = {
        "experiment": "ai-style-skill",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "real_llm_judge",
        "provider": provider,
        "model": model or default_model(provider),
        "growth_curve": curve,
        "total_candidates": total_candidates,
        "final_rule_count": len(rules),
        "active_rules": [r["id"] for r in active],
        "archived_rules": [r["id"] for r in archived],
        "calibration": calibration,
        "skill_path": str(skill_path.relative_to(ROOT)),
        "archive_path": str(archive_path.relative_to(ROOT)) if archive_path else None,
        "metrics": metrics,
        "rewrite_demo": rewrite,
        "raw_api_receipts": receipts,
        "gates": gates,
        "accepted": all(gates.values()),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default="openai")
    parser.add_argument("--model", default=None)
    parser.add_argument("--seed", type=int, default=8901)
    args = parser.parse_args()

    report = run_pipeline(provider=args.provider, model=args.model, seed=args.seed)

    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "validation" / stamp
    out_dir.mkdir(parents=True, exist_ok=False)
    evidence_path = out_dir / "evidence.json"
    evidence_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    canonical = ROOT / "validation" / "latest.json"
    shutil.copyfile(evidence_path, canonical)
    print(f"证据回执：{evidence_path.relative_to(ROOT)}（validation/latest.json 已指向）")

    metrics = report["metrics"]
    print(json.dumps({
        "mode": report["execution_mode"],
        "accepted": report["accepted"],
        "boundary_detection_rate": f"{metrics['boundary_detected']}/{metrics['boundary_total']}",
        "retention_harm_rate": f"{metrics['retention_harmed']}/{metrics['retention_total']}",
        "candidates_to_rules": f"{report['total_candidates']} -> {report['final_rule_count']}",
        "active_rules": report["active_rules"],
        "calibration": [
            {"rule_id": c["rule_id"], "agreement": c["agreement"], "decision": c["decision"]}
            for c in report["calibration"]
        ],
        "gates": report["gates"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
