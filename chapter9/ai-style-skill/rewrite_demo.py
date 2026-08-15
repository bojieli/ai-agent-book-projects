"""改写演示：一段 AI 味文本按 Skill 规则改写的 before/after。

确定性路径（离线）：用 rules_engine 定位命中，给出每条规则的预置换写建议，
并展示人工参考改写——不假装自动改写。
LLM 路径（真实）：把 active 规则连同原文交给模型改写，返回 before/after
与证据回执。

    python rewrite_demo.py                # 离线路径
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from llm_client import chat
from rules_engine import run_detector

# 演示用原文：刻意集齐八类 AI 味。
SAMPLE_TEXT = (
    "在这个效率至上的时代，让我们一起重新认识这款笔记工具——它不是简单的记录软件——"
    "而是你的第二大脑。首先，它能自动整理灵感；其次，它让检索快如闪电；"
    "最后，它让分享毫无门槛——仿佛一位永不疲倦的管家。总而言之，让我们从现在开始，"
    "把每一条灵感都安顿好 🚀✨💡。"
)

# 人工参考改写：离线对照用，展示「按规则改完应该长什么样」。
REFERENCE_REWRITE = (
    "这款笔记工具值得再介绍一次。它会自动整理你随手记下的灵感，检索和分享也都很快，"
    "基本不用操心整理。想找一款省心笔记工具的话，现在就可以试试。"
)


def rewrite_deterministic(text: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """确定性路径：定位命中 + 预置换写建议 + 人工参考改写。"""
    suggestions = []
    for rule in rules:
        detector = rule.get("detector", {})
        if detector.get("type") == "llm":
            continue  # llm 类规则离线不做定位，由真实 judge 路径处理
        hits = run_detector(text, detector)
        if hits:
            suggestions.append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "hits": [{"evidence": h["evidence"], "detail": h["detail"]} for h in hits],
                "suggestion": rule.get("rewrite_hint", "按规则定义改写。"),
            })
    return {
        "mode": "deterministic",
        "original": text,
        "suggestions": suggestions,
        "reference_rewrite": REFERENCE_REWRITE,
        "note": "确定性路径只做定位与预置建议，自动改写属于真实 LLM 路径。",
    }


_REWRITE_PROMPT = """你是中文文案改写助手。请按下面的写作规则改写给出的文案，消除所有违规之处，
保持原意，不要增加新事实。只返回 JSON：{{"rewritten": "改写后的全文",
"applied_rules": ["实际应用的规则 id"]}}

写作规则：
{rules}

待改写文案：
{text}
"""


def rewrite_with_llm(
    text: str,
    rules: List[Dict[str, Any]],
    *,
    provider: str,
    model: str | None = None,
    seed: int = 8901,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """真实 LLM 改写路径，返回 (改写结果, 证据回执)。"""
    brief_rules = [
        {"id": r["id"], "name": r["name"], "definition": r["definition"],
         "bad_example": r.get("bad_example", ""), "good_example": r.get("good_example", "")}
        for r in rules
    ]
    content, receipt = chat(
        [{"role": "user", "content": _REWRITE_PROMPT.format(
            rules=json.dumps(brief_rules, ensure_ascii=False, indent=2), text=text)}],
        provider=provider, model=model, seed=seed,
    )
    payload = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I))
    return {
        "mode": "real_llm",
        "original": text,
        "rewritten": payload.get("rewritten", ""),
        "applied_rules": payload.get("applied_rules", []),
    }, receipt


def _load_active_rules() -> List[Dict[str, Any]]:
    import json as _json
    from pathlib import Path

    rules_path = Path(__file__).resolve().parent / "skill" / "rules.json"
    if not rules_path.exists():
        raise SystemExit("请先生成 Skill：python demo.py 或 python run_experiment_8_9.py")
    return _json.loads(rules_path.read_text(encoding="utf-8"))


def main() -> int:
    rules = _load_active_rules()
    result = rewrite_deterministic(SAMPLE_TEXT, rules)
    print("原文：", result["original"])
    print("\n命中与改写建议：")
    for s in result["suggestions"]:
        print(f"- [{s['rule_name']}] {len(s['hits'])} 处命中：{s['suggestion']}")
    print("\n人工参考改写：", result["reference_rewrite"])
    print("\n" + result["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
