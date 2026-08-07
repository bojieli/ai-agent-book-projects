"""对待评文本按 active 规则打分，并对 llm 类规则做金标集校准。

确定性规则直接跑 rules_engine；llm 类规则走 LLM judge。judge 上线前必须用
data/golden_set.json 校准：judge 判定与人工标注的一致率低于阈值（默认 0.8）
就拒绝激活该规则——呼应第六章「评判者本身也要被评判」。

离线路径用 proxy_judge（确定性探针）演示校准机制；真实验收必须用
llm_judge 走真实 API，证据回执由调用方保存。
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable, Dict, List

from llm_client import chat
from rules_engine import run_detector

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

JudgeFn = Callable[[str], bool]

# 离线代理探针：近似「空洞比喻与假拟人」judge，仅用于教学演示与单元测试。
_PROXY_PROBE = re.compile(
    r"(仿佛|宛如|犹如|如同)[^，。！？\n]{0,16}"
    r"(智者|灯塔|明灯|导师|精灵|使者|守护者|屏障|港湾|星辰)"
)


def proxy_judge(rule: Dict[str, Any]) -> JudgeFn:
    """离线确定性代理 judge。注意：它不是真 LLM，只用于演示校准流程。"""

    def judge(text: str) -> bool:
        return bool(_PROXY_PROBE.search(text))

    return judge


def llm_judge(
    rule: Dict[str, Any],
    *,
    provider: str,
    model: str | None = None,
    seed: int = 8901,
    receipts: List[Dict[str, Any]] | None = None,
) -> JudgeFn:
    """真实 LLM judge：每次判定都是一次真实调用，回执追加进 receipts。"""
    prompt_template = rule["detector"].get("judge_prompt", "")

    def judge(text: str) -> bool:
        content, receipt = chat(
            [{"role": "user", "content": prompt_template + "\n\n待评文本：\n" + text}],
            provider=provider, model=model, seed=seed, max_tokens=300,
        )
        if receipts is not None:
            receipts.append(receipt)
        try:
            payload = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I))
            return bool(payload.get("hit"))
        except (json.JSONDecodeError, AttributeError):
            return False  # judge 输出不可解析时按不命中处理，并保留回执供审计

    return judge


def calibrate(
    rule: Dict[str, Any],
    golden_set: List[Dict[str, Any]],
    judge_fn: JudgeFn,
    *,
    threshold: float = 0.8,
) -> Dict[str, Any]:
    """用金标集校准 judge：一致率达标才允许激活该规则。"""
    cases = []
    agree = 0
    for item in golden_set:
        expected = item.get("labels", {}).get(rule["id"])
        if expected is None:
            continue
        got = judge_fn(item["text"])
        ok = got == expected
        agree += int(ok)
        cases.append({"id": item["id"], "expected": expected, "judged": got, "agree": ok})
    total = len(cases)
    agreement = agree / total if total else 0.0
    return {
        "rule_id": rule["id"],
        "cases": cases,
        "total": total,
        "agree": agree,
        "agreement": agreement,
        "threshold": threshold,
        "decision": "activate" if agreement >= threshold else "reject",
        "note": (
            "judge 与金标集一致率达到阈值，允许上线"
            if agreement >= threshold
            else "一致率低于阈值，拒绝上线该规则——先修 judge 或规则定义"
        ),
    }


def score_text(
    text: str,
    rules: List[Dict[str, Any]],
    llm_judges: Dict[str, JudgeFn] | None = None,
) -> Dict[str, Any]:
    """按 active 规则给文本打分，返回 {rule_id: 命中详情}。"""
    result: Dict[str, Any] = {}
    for rule in rules:
        detector = rule.get("detector", {})
        if detector.get("type") == "llm":
            judge_fn = (llm_judges or {}).get(rule["id"])
            if judge_fn and judge_fn(text):
                result[rule["id"]] = {"verdict": True, "evidence": "judge 判定命中"}
            continue
        hits = run_detector(text, detector)
        if hits:
            result[rule["id"]] = {"hits": hits}
    return result


def load_golden_set(path: Path | None = None) -> List[Dict[str, Any]]:
    return json.loads((path or DATA_DIR / "golden_set.json").read_text(encoding="utf-8"))
