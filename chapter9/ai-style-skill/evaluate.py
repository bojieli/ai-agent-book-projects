"""评估：逐条规则的精确率/召回率、boundary 检出率、retention 误伤率、规则增长曲线。

离线可完整运行：

    python evaluate.py

增长曲线模拟逐批反馈进入的增量过程：feedback_pairs 分成 3 批顺序处理，
每批提炼候选 → 合并进规则集，记录每批后的规则数。验收口径是「合并后规则数
明显少于原始候选数」——防膨胀靠合并去重，而不是无限追加。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from extract_rules import extract_deterministic, load_pairs
from judge import proxy_judge, score_text
from skill_manager import merge_rules

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"


def load_eval_texts(path: Path | None = None) -> Dict[str, List[Dict[str, Any]]]:
    return json.loads((path or DATA_DIR / "eval_texts.json").read_text(encoding="utf-8"))


def evaluate_rules(
    rules: List[Dict[str, Any]],
    eval_texts: Dict[str, List[Dict[str, Any]]],
    llm_judges: Dict[str, Callable[[str], bool]] | None = None,
) -> Dict[str, Any]:
    """在 boundary/retention 集上评估规则集。"""
    rule_ids = [r["id"] for r in rules]
    tp = {rid: 0 for rid in rule_ids}
    fp = {rid: 0 for rid in rule_ids}
    fn = {rid: 0 for rid in rule_ids}

    boundary_details = []
    detected = 0
    for item in eval_texts.get("boundary", []):
        expected = set(item.get("expected_rules", []))
        fired = set(score_text(item["text"], rules, llm_judges))
        boundary_details.append({
            "id": item["id"], "expected": sorted(expected), "fired": sorted(fired),
        })
        if expected & fired:
            detected += 1
        for rid in rule_ids:
            if rid in fired and rid in expected:
                tp[rid] += 1
            elif rid in fired:
                fp[rid] += 1
            elif rid in expected:
                fn[rid] += 1

    retention_details = []
    harmed = 0
    for item in eval_texts.get("retention", []):
        fired = score_text(item["text"], rules, llm_judges)
        retention_details.append({"id": item["id"], "fired": sorted(fired)})
        if fired:
            harmed += 1
            for rid in fired:
                fp[rid] += 1

    per_rule = {}
    for rid in rule_ids:
        precision = tp[rid] / (tp[rid] + fp[rid]) if tp[rid] + fp[rid] else 1.0
        recall = tp[rid] / (tp[rid] + fn[rid]) if tp[rid] + fn[rid] else 1.0
        per_rule[rid] = {
            "tp": tp[rid], "fp": fp[rid], "fn": fn[rid],
            "precision": round(precision, 3), "recall": round(recall, 3),
        }

    boundary_total = len(eval_texts.get("boundary", []))
    retention_total = len(eval_texts.get("retention", []))
    return {
        "per_rule": per_rule,
        "boundary_detection_rate": detected / boundary_total if boundary_total else 0.0,
        "boundary_detected": detected,
        "boundary_total": boundary_total,
        "retention_harm_rate": harmed / retention_total if retention_total else 0.0,
        "retention_harmed": harmed,
        "retention_total": retention_total,
        "boundary_details": boundary_details,
        "retention_details": retention_details,
    }


def incremental_growth(
    pairs: List[Dict[str, Any]], batches: int = 3
) -> Dict[str, Any]:
    """按批模拟增量反馈：每批提炼候选并合并，记录规则数变化。"""
    rules: List[Dict[str, Any]] = []
    curve = []
    total_candidates = 0
    all_candidates: List[Dict[str, Any]] = []
    for batch_no in range(1, batches + 1):
        batch_pairs = [p for p in pairs if p.get("batch") == batch_no]
        candidates = extract_deterministic(batch_pairs)
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
            "conflicts": len(report["conflicts"]),
            "rule_count": len(rules),
        })
    return {
        "rules": rules,
        "candidates": all_candidates,
        "curve": curve,
        "total_candidates": total_candidates,
        "final_rule_count": len(rules),
    }


def main() -> int:
    pairs = load_pairs()
    eval_texts = load_eval_texts()
    growth = incremental_growth(pairs)
    rules = growth["rules"]
    # llm 类规则离线用代理 judge 参与打分；真实校准见 run_experiment_8_9.py。
    llm_judges = {
        r["id"]: proxy_judge(r) for r in rules if r["detector"].get("type") == "llm"
    }
    metrics = evaluate_rules(rules, eval_texts, llm_judges)
    report = {"growth": growth["curve"], "total_candidates": growth["total_candidates"],
              "final_rule_count": growth["final_rule_count"], **metrics}
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"boundary 检出率：{metrics['boundary_detected']}/{metrics['boundary_total']}"
          f" = {metrics['boundary_detection_rate']:.3f}")
    print(f"retention 误伤率：{metrics['retention_harmed']}/{metrics['retention_total']}"
          f" = {metrics['retention_harm_rate']:.3f}")
    print(f"候选规则 {growth['total_candidates']} 条 → 合并后 {growth['final_rule_count']} 条")
    for row in growth["curve"]:
        print(f"  批次 {row['batch']}：新增候选 {row['new_candidates']}，"
              f"新规则 {len(row['added'])}，合并 {row['merged']}，累计规则 {row['rule_count']}")
    for rid, m in metrics["per_rule"].items():
        print(f"  {rid}: precision={m['precision']:.3f} recall={m['recall']:.3f}"
              f" (tp={m['tp']} fp={m['fp']} fn={m['fn']})")
    for detail in metrics["retention_details"]:
        if detail["fired"]:
            print(f"  [误伤] {detail['id']}: {detail['fired']}")
    for detail in metrics["boundary_details"]:
        if not set(detail["expected"]) & set(detail["fired"]):
            print(f"  [漏检] {detail['id']}: 期望 {detail['expected']}，命中 {detail['fired']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
