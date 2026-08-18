"""把 active 规则连同原文交给 LLM 改写，返回 before/after 与证据回执。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from llm_client import chat

# 演示用原文：刻意集齐八类 AI 味。
SAMPLE_TEXT = (
    "在这个效率至上的时代，让我们一起重新认识这款笔记工具——它不是简单的记录软件——"
    "而是你的第二大脑。首先，它能自动整理灵感；其次，它让检索快如闪电；"
    "最后，它让分享毫无门槛——仿佛一位永不疲倦的管家。总而言之，让我们从现在开始，"
    "把每一条灵感都安顿好 🚀✨💡。"
)

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
        raise SystemExit("请先生成 Skill：python demo.py 或 python run_ai_style_skill.py")
    return _json.loads(rules_path.read_text(encoding="utf-8"))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ark", "openrouter", "openai"), default="openai")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    rules = _load_active_rules()
    result, _ = rewrite_with_llm(
        SAMPLE_TEXT, rules, provider=args.provider, model=args.model
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
