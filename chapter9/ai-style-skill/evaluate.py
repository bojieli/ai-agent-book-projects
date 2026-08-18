"""用外部人工标注的 boundary/retention 集评估 active 规则。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from judge import JudgeFn, llm_judge, score_text
from llm_client import default_model

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"


def load_eval_texts(path: Path | None = None) -> Dict[str, List[Dict[str, Any]]]:
    return json.loads((path or DATA_DIR / "eval_texts.json").read_text(encoding="utf-8"))


def _expected_rule_ids(item: Dict[str, Any], rules: List[Dict[str, Any]]) -> set[str]:
    """把人工标注的反馈来源映射到本次动态提炼出的规则 id。"""
    expected_sources = set(item.get("expected_sources", []))
    return {
        rule["id"]
        for rule in rules
        if expected_sources & set(rule.get("source_ids", []))
    }


def evaluate_rules(
    rules: List[Dict[str, Any]],
    eval_texts: Dict[str, List[Dict[str, Any]]],
    judge_fn: JudgeFn,
) -> Dict[str, Any]:
    """在保留集上逐段调用一次 LLM judge，不使用词表或正则探针。"""
    rule_ids = [rule["id"] for rule in rules]
    tp = {rule_id: 0 for rule_id in rule_ids}
    fp = {rule_id: 0 for rule_id in rule_ids}
    fn = {rule_id: 0 for rule_id in rule_ids}

    boundary_details = []
    detected = 0
    for item in eval_texts.get("boundary", []):
        expected = _expected_rule_ids(item, rules)
        fired = set(score_text(item["text"], rules, judge_fn, text_id=item["id"]))
        matched = expected & fired
        boundary_details.append({
            "id": item["id"],
            "expected_sources": item.get("expected_sources", []),
            "expected": sorted(expected),
            "fired": sorted(fired),
        })
        if matched:
            detected += 1
        for rule_id in rule_ids:
            if rule_id in fired and rule_id in expected:
                tp[rule_id] += 1
            elif rule_id in fired:
                fp[rule_id] += 1
            elif rule_id in expected:
                fn[rule_id] += 1

    retention_details = []
    harmed = 0
    for item in eval_texts.get("retention", []):
        fired = score_text(item["text"], rules, judge_fn, text_id=item["id"])
        retention_details.append({"id": item["id"], "fired": sorted(fired)})
        if fired:
            harmed += 1
            for rule_id in fired:
                fp[rule_id] += 1

    per_rule = {}
    for rule_id in rule_ids:
        precision = tp[rule_id] / (tp[rule_id] + fp[rule_id]) if tp[rule_id] + fp[rule_id] else 1.0
        recall = tp[rule_id] / (tp[rule_id] + fn[rule_id]) if tp[rule_id] + fn[rule_id] else 1.0
        per_rule[rule_id] = {
            "tp": tp[rule_id],
            "fp": fp[rule_id],
            "fn": fn[rule_id],
            "precision": round(precision, 3),
            "recall": round(recall, 3),
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default="openai")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    rules_path = ROOT / "skill" / "rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    judge_fn = llm_judge(provider=args.provider, model=args.model)
    metrics = evaluate_rules(rules, load_eval_texts(), judge_fn)
    report = {
        "provider": args.provider,
        "model": args.model or default_model(args.provider),
        **metrics,
    }
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
