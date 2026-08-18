"""用一个外部 LLM judge 校准并评估所有候选写作规则。

规则本身来自开放式提炼，不携带正则或预置模式。judge 根据规则定义、正反例与
作用域作语义判定。每条规则必须先在独立人工金标上达到一致率门槛，之后才可激活。
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Tuple

from llm_client import chat

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

Verdicts = Dict[Tuple[str, str], Dict[str, Any]]
JudgeFn = Callable[[List[Dict[str, Any]], List[Dict[str, str]]], Verdicts]

_JUDGE_PROMPT = """你是独立的中文写作质量评判者。请逐一判断每段待评文本是否命中每条规则。
严格依据规则的定义、适用范围和正反例：相似词语本身不等于命中，只有规则所描述的滥用
确实出现才判 true。不要因为文本来自评估集而猜标签。

必须为每个 text_id 与 rule_id 的组合返回一项。只返回 JSON：
{{"verdicts": [{{"text_id": "...", "rule_id": "...", "hit": true,
"evidence": "命中时摘录最短证据；未命中时为空字符串"}}]}}

规则：
{rules}

待评文本：
{texts}
"""


def _strip_json_fence(content: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)


def llm_judge(
    *,
    provider: str,
    model: str | None = None,
    seed: int = 8901,
    receipts: List[Dict[str, Any]] | None = None,
) -> JudgeFn:
    """创建批量 LLM judge；一次调用可判定多条规则或多段文本。"""

    def judge(rules: List[Dict[str, Any]], texts: List[Dict[str, str]]) -> Verdicts:
        brief_rules = [
            {
                "id": rule["id"],
                "name": rule["name"],
                "definition": rule["definition"],
                "bad_example": rule.get("bad_example", ""),
                "good_example": rule.get("good_example", ""),
                "scope": rule.get("scope", []),
            }
            for rule in rules
        ]
        content, receipt = chat(
            [{
                "role": "user",
                "content": _JUDGE_PROMPT.format(
                    rules=json.dumps(brief_rules, ensure_ascii=False, indent=2),
                    texts=json.dumps(texts, ensure_ascii=False, indent=2),
                ),
            }],
            provider=provider,
            model=model,
            seed=seed,
            # Responses API 的 max_output_tokens 也覆盖 reasoning tokens；小上限会让
            # JSON 在中途被截断。给 reasoning 与每个 verdict 都留出明确余量。
            max_tokens=max(2000, 1000 + len(rules) * len(texts) * 120),
        )
        if receipts is not None:
            receipts.append(receipt)

        expected = {(rule["id"], text["id"]) for rule in rules for text in texts}
        try:
            payload = json.loads(_strip_json_fence(content))
        except (json.JSONDecodeError, AttributeError):
            return {
                key: {"hit": False, "evidence": "", "parse_error": True}
                for key in expected
            }

        verdicts: Verdicts = {}
        for item in payload.get("verdicts", []):
            key = (str(item.get("rule_id", "")), str(item.get("text_id", "")))
            if key not in expected or not isinstance(item.get("hit"), bool):
                continue
            verdicts[key] = {
                "hit": item["hit"],
                "evidence": str(item.get("evidence", "")),
            }
        for key in expected - set(verdicts):
            verdicts[key] = {"hit": False, "evidence": "", "missing": True}
        return verdicts

    return judge


def _calibration_cases(
    rule: Dict[str, Any], golden_set: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    sources = set(rule.get("source_ids", []))
    cases = []
    for item in golden_set:
        matching = [
            label["expected"]
            for label in item.get("labels", [])
            if sources & set(label.get("source_ids", []))
        ]
        if not matching:
            continue
        if len(set(matching)) != 1:
            raise ValueError(f"金标 {item['id']} 对规则 {rule['id']} 给出了冲突标签")
        cases.append({"id": item["id"], "text": item["text"], "expected": matching[0]})
    return cases


def calibrate(
    rule: Dict[str, Any],
    golden_set: List[Dict[str, Any]],
    judge_fn: JudgeFn,
    *,
    threshold: float = 0.8,
) -> Dict[str, Any]:
    """用与候选来源关联的独立人工金标校准一条规则。"""
    labeled = _calibration_cases(rule, golden_set)
    texts = [{"id": item["id"], "text": item["text"]} for item in labeled]
    verdicts = judge_fn([rule], texts) if texts else {}
    cases = []
    agree = 0
    for item in labeled:
        verdict = verdicts.get((rule["id"], item["id"]), {"hit": False, "missing": True})
        got = bool(verdict["hit"])
        ok = got == item["expected"] and not verdict.get("missing") and not verdict.get("parse_error")
        agree += int(ok)
        cases.append({
            "id": item["id"],
            "expected": item["expected"],
            "judged": got,
            "evidence": verdict.get("evidence", ""),
            "missing": bool(verdict.get("missing")),
            "parse_error": bool(verdict.get("parse_error")),
            "agree": ok,
        })
    total = len(cases)
    agreement = agree / total if total else 0.0
    decision = "activate" if total and agreement >= threshold else "reject"
    return {
        "rule_id": rule["id"],
        "cases": cases,
        "total": total,
        "agree": agree,
        "agreement": agreement,
        "threshold": threshold,
        "decision": decision,
        "note": (
            "judge 与独立人工金标的一致率达到阈值，允许上线"
            if decision == "activate"
            else "金标覆盖不足或一致率低于阈值，拒绝上线该规则"
        ),
    }


def score_text(
    text: str,
    rules: List[Dict[str, Any]],
    judge_fn: JudgeFn,
    *,
    text_id: str = "target",
) -> Dict[str, Any]:
    """用 LLM judge 对全部 active 规则一次性打分。"""
    if not rules:
        return {}
    verdicts = judge_fn(rules, [{"id": text_id, "text": text}])
    result: Dict[str, Any] = {}
    for rule in rules:
        verdict = verdicts.get((rule["id"], text_id), {})
        if verdict.get("hit"):
            result[rule["id"]] = {
                "verdict": True,
                "evidence": verdict.get("evidence", ""),
            }
    return result


def load_golden_set(path: Path | None = None) -> List[Dict[str, Any]]:
    return json.loads((path or DATA_DIR / "golden_set.json").read_text(encoding="utf-8"))
