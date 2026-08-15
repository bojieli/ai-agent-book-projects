#!/usr/bin/env python3
"""实验 8-9 验收入口：把「AI 味」反馈内化为写作 Skill。

默认离线确定性路径（无需 API key）：

    python run_experiment_8_9.py

真实 LLM 路径（规则提炼 + judge 校准 + 改写都走真实 API，证据回执落盘）：

    python run_experiment_8_9.py --provider ark --model doubao-seed-1-6-250615

流程：逐批反馈 → 提炼候选规则（确定性或 LLM）→ 模型外部合并去重 →
llm 类规则金标集校准（不达标拒绝上线）→ 生成 skill/SKILL.md →
boundary/retention 评估 → 改写演示 → 验收门槛。
LLM 只能产出候选；合并、校准、激活、评估全部由模型外部代码决定（可信根隔离）。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any, Dict, List

from evaluate import evaluate_rules, load_eval_texts
from extract_rules import extract_deterministic, extract_with_llm, load_pairs, write_candidates
from judge import calibrate, llm_judge, load_golden_set, proxy_judge
from rewrite_demo import SAMPLE_TEXT, rewrite_deterministic, rewrite_with_llm
from skill_manager import detector_signature, merge_rules, prune_rules, write_archive, write_skill

ROOT = Path(__file__).resolve().parent

# 验收门槛（模型外部代码，LLM 不可修改）。
GATE_BOUNDARY_RATE = 0.85
GATE_RETENTION_HARM = 0.15


def run_pipeline(
    *,
    provider: str | None = None,
    model: str | None = None,
    seed: int = 8901,
    batches: int = 3,
) -> Dict[str, Any]:
    real = provider is not None
    pairs = load_pairs()
    eval_texts = load_eval_texts()
    golden_set = load_golden_set()
    receipts: List[Dict[str, Any]] = []

    # 1) 逐批反馈进入：提炼候选 → 模型外部合并去重（防膨胀）。
    rules: List[Dict[str, Any]] = []
    curve = []
    total_candidates = 0
    all_candidates: List[Dict[str, Any]] = []
    fallback_batches: List[int] = []
    for batch_no in range(1, batches + 1):
        batch_pairs = [p for p in pairs if p.get("batch") == batch_no]
        deterministic_candidates = extract_deterministic(batch_pairs)
        if real:
            llm_candidates, receipt = extract_with_llm(
                batch_pairs, provider=provider, model=model, seed=seed + batch_no
            )
            receipts.append(receipt)
            # LLM 只提出候选，模型外代码负责决定是否接纳。保留能映射到
            # 内置检测器的候选；若整批都无法映射，退回确定性模式库，
            # 避免一批含糊规则污染正式 Skill。
            allowed = {detector_signature(c["detector"]) for c in deterministic_candidates}
            candidates = [c for c in llm_candidates if detector_signature(c.get("detector", {})) in allowed]
            if not candidates:
                candidates = deterministic_candidates
                fallback_batches.append(batch_no)
        else:
            candidates = deterministic_candidates
        total_candidates += len(candidates)
        all_candidates.extend(candidates)
        rules, report = merge_rules(rules, candidates)
        new_sources = {sid for c in candidates for sid in c.get("source_ids", [])}
        for rule in rules:
            if set(rule.get("source_ids", [])) & new_sources:
                rule["last_confirmed_batch"] = batch_no
        curve.append({
            "batch": batch_no,
            "new_candidates": len(candidates),
            "added": report["added"],
            "merged": len(report["merged"]),
            "conflicts": report["conflicts"],
            "rule_count": len(rules),
        })
    write_candidates(all_candidates)

    # 2) llm 类规则金标集校准：不达标拒绝上线（呼应第六章评判者校准）。
    calibration = []
    active: List[Dict[str, Any]] = []
    llm_judges = {}
    for rule in rules:
        if rule["detector"].get("type") != "llm":
            rule["status"] = "active"
            active.append(rule)
            continue
        if real:
            judge_fn = llm_judge(
                rule, provider=provider, model=model, seed=seed, receipts=receipts
            )
        else:
            judge_fn = proxy_judge(rule)  # 离线代理：只演示校准机制
        result = calibrate(rule, golden_set, judge_fn)
        calibration.append(result)
        if result["decision"] == "activate":
            rule["status"] = "active"
            active.append(rule)
            llm_judges[rule["id"]] = judge_fn
        else:
            rule["status"] = "rejected"

    # 3) prune 演示：被证据推翻或长期未触发的规则归档（离线数据下无归档）。
    active, archived = prune_rules(active, current_batch=batches, contradicted_ids=set())

    # 4) 生成 Skill 并评估。
    skill_path = write_skill(active)
    archive_path = write_archive(archived)
    metrics = evaluate_rules(active, eval_texts, llm_judges)

    # 5) 改写演示。
    if real:
        rewrite, receipt = rewrite_with_llm(
            SAMPLE_TEXT, active, provider=provider, model=model, seed=seed
        )
        receipts.append(receipt)
    else:
        rewrite = rewrite_deterministic(SAMPLE_TEXT, active)

    gates = {
        "boundary_detection_rate >= 0.85": metrics["boundary_detection_rate"] >= GATE_BOUNDARY_RATE,
        "retention_harm_rate <= 0.15": metrics["retention_harm_rate"] <= GATE_RETENTION_HARM,
        "merged_rules_fewer_than_candidates": len(rules) < total_candidates,
        "llm_rules_calibrated_before_activation": all(
            r["detector"].get("type") != "llm"
            or any(c["rule_id"] == r["id"] and c["decision"] == "activate" for c in calibration)
            for r in active
        ),
    }
    if real:
        gates["real_llm_called_with_receipts"] = bool(receipts) and all(
            r["response"].get("id") for r in receipts
        )

    report = {
        "experiment": "8-9",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "real_llm" if real else "offline_deterministic",
        "provider": provider,
        "model": model,
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
        "deterministic_fallback_batches": fallback_batches,
        "gates": gates,
        "accepted": all(gates.values()),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--seed", type=int, default=8901)
    args = parser.parse_args()

    report = run_pipeline(provider=args.provider, model=args.model, seed=args.seed)

    if args.provider:
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
    else:
        out_dir = ROOT / "output"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

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
