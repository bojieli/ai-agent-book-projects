"""从用户纠正的 before/after 对中提炼候选规则（实验 8-9 双路径之一）。

确定性路径：预置模式库 + 规则引擎。对每个反馈对，检测 before 中命中、
after 中被消除的模式；用户纠正原话中的关键词可作为辅助证据。同一模式在
多条反馈中出现时聚合成一条候选规则，记录全部 source_ids。

LLM 路径：把一批反馈对交给模型归纳规则，要求返回符合 schema 的 JSON，
证据回执由调用方保存。LLM 只能产出候选（status=candidate），是否合并、
激活由模型外部的 skill_manager 与 judge 决定（可信根隔离）。

规则 schema：id / name / definition / detector / bad_example / good_example /
scope / source_ids / status。
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

from llm_client import chat
from rules_engine import EMOJI_PATTERN, run_detector

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

# 预置模式库：覆盖书中最常见的八类「AI 味」。
# keywords 用于把用户纠正原话映射到模式；rewrite_hint 供确定性改写路径使用。
PATTERN_LIBRARY: Dict[str, Dict[str, Any]] = {
    "dash-density": {
        "name": "破折号使用过多",
        "definition": "频繁用破折号（——）串联句子、代替正常的停顿和连接，一段里出现三处以上，是典型的 AI 腔。",
        "detector": {"type": "density", "pattern": "——", "min_occurrences": 3, "threshold": 6},
        "keywords": ["破折号", "——"],
        "rewrite_hint": "把多数破折号改成逗号或句号，或直接拆成两句；一处必要的补充说明可以保留。",
    },
    "not-but": {
        "name": "「不是……而是……」句式滥用",
        "definition": "同一篇里连用两处以上「不是 X，而是 Y」的对仗句式。单独一次真实对比不算违规。",
        "detector": {"type": "regex", "pattern": r"不是[^。！？；：\n]{0,30}?而是", "min_occurrences": 2},
        "keywords": ["不是", "而是"],
        "rewrite_hint": "保留真正有对比意义的一处，其余改成直接陈述「它是什么」。",
    },
    "parallelism": {
        "name": "排比堆砌",
        "definition": "连续三个以上结构高度相似的分句（同开头或同结尾），读起来像口号。",
        "detector": {"type": "structure", "kind": "parallelism", "min_run": 3},
        "keywords": ["排比", "对仗"],
        "rewrite_hint": "把排比拆开，用长短不一的句子各说一件事；保留最多两句对仗。",
    },
    "lets-start": {
        "name": "「让我们」口号式开头",
        "definition": "连续用「让我们」领起句子，像动员演讲而不是在写文案。",
        "detector": {"type": "regex", "pattern": "让我们", "min_occurrences": 2},
        "keywords": ["让我们", "口号"],
        "rewrite_hint": "删掉口号句，直接陈述事实或发出一次具体邀请。",
    },
    "template-sequence": {
        "name": "「首先/其次/最后」模板序列",
        "definition": "堆叠「首先、其次、再次、然后、最后、总而言之」等连接词，把文案写成公文提纲。",
        "detector": {
            "type": "regex",
            "pattern": "首先|其次|再次|然后|接下来|最后|总而言之|综上所述|总的来说",
            "min_occurrences": 3,
        },
        "keywords": ["首先", "其次", "模板", "八股"],
        "rewrite_hint": "去掉连接词标签，让句子按自然顺序衔接；两处的「首先/其次」可以接受。",
    },
    "emoji-density": {
        "name": "emoji 泛滥",
        "definition": "一段文案里 emoji 出现三次以上，或密度超过每千字 5 个；正式稿件应基本不用。",
        "detector": {"type": "density", "pattern": EMOJI_PATTERN, "min_occurrences": 3, "threshold": 5},
        "keywords": ["emoji", "表情"],
        "rewrite_hint": "正式稿件全部删掉；生活化随笔最多保留一两个。",
    },
    "era-opening": {
        "name": "「在……的今天/时代」开头",
        "definition": "用「在……的今天」「在这个……的时代」「在……的当下」这类空泛宏大开头的套话。",
        "detector": {
            "type": "regex",
            "pattern": r"在[^，。！？；\n]{2,24}?(?:的今天|的时代|的当下|的时代背景下)",
            "min_occurrences": 1,
        },
        "keywords": ["在今天", "的时代", "开头"],
        "rewrite_hint": "删掉宏大开头，第一句直接说具体的事。",
    },
    "hollow-metaphor": {
        "name": "空洞比喻与假拟人",
        "definition": "用「仿佛一位智者」「宛如一盏明灯」这类不传递任何具体信息的比喻和拟人抒情。",
        "detector": {
            "type": "llm",
            "judge_prompt": (
                "判断下面这段文字是否包含空洞比喻或假拟人：即用「仿佛/宛如/犹如/如同 + "
                "智者/明灯/灯塔/导师/守护者/屏障」等意象抒情，但不传递具体事实。"
                "只回答 JSON：{\"hit\": true/false, \"evidence\": \"命中的片段或空字符串\"}。"
            ),
        },
        "keywords": ["仿佛", "宛如", "比喻", "拟人", "抒情", "明灯", "灯塔", "智者"],
        "rewrite_hint": "删掉比喻，改写为可验证的具体事实、数据或体验描述。",
    },
}

# 空洞比喻在提炼阶段的确定性探针（仅用于找证据，真正的检测走 judge）。
_METAPHOR_PROBE = re.compile(r"仿佛|宛如|犹如|如同")


def load_pairs(path: Path | None = None) -> List[Dict[str, Any]]:
    return json.loads((path or DATA_DIR / "feedback_pairs.json").read_text(encoding="utf-8"))


def _pattern_hit(text: str, key: str, spec: Dict[str, Any]) -> bool:
    """before 是否呈现该模式；llm 类规则用确定性探针找证据。"""
    if spec["detector"]["type"] == "llm":
        return bool(_METAPHOR_PROBE.search(text))
    return bool(run_detector(text, spec["detector"]))


def extract_deterministic(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """确定性提炼：before 命中且 after 消除的模式聚合成候选规则。"""
    matched: Dict[str, Dict[str, Any]] = {}
    for pair in pairs:
        for key, spec in PATTERN_LIBRARY.items():
            hit_before = _pattern_hit(pair["before"], key, spec)
            if not hit_before:
                continue
            eliminated = not _pattern_hit(pair["after"], key, spec)
            keyword_support = any(kw in pair.get("correction", "") for kw in spec["keywords"])
            if not (eliminated or keyword_support):
                continue
            entry = matched.setdefault(key, {"source_ids": [], "scenes": set(), "first_pair": pair})
            entry["source_ids"].append(pair["id"])
            entry["scenes"].add(pair["scene"])

    candidates = []
    for key, entry in matched.items():
        spec = PATTERN_LIBRARY[key]
        first = entry["first_pair"]
        candidates.append({
            "id": f"rule-{key}",
            "name": spec["name"],
            "definition": spec["definition"],
            "detector": dict(spec["detector"]),
            "bad_example": first["before"],
            "good_example": first["after"],
            "rewrite_hint": spec["rewrite_hint"],
            "scope": sorted(entry["scenes"]),
            "source_ids": entry["source_ids"],
            "status": "candidate",
        })
    return candidates


_LLM_EXTRACT_PROMPT = """你是写作规范的提炼助手。下面是用户纠正 AI 生成文案的 before/after 对。
请归纳出可检查的规则，每条规则必须能落地为确定性检测或校准过的 LLM judge。

返回 JSON：{{"rules": [{{"id": "rule-<英文短横线命名>", "name": "...", "definition": "...",
"detector": {{"type": "regex 或 density 或 llm", "pattern": "正则（regex/density 必填）",
"min_occurrences": 数字, "threshold": 每千字次数（density 必填）, "judge_prompt": "llm 类型必填"}},
"bad_example": "取自 before 的原文片段", "good_example": "对应的 after 原文片段",
"scope": ["适用场景"], "source_ids": ["支撑的反馈对 id"]}}]}}

要求：规则必须具体到可检查（不要「写得自然」这种空话）；每条规则至少有一条 source_ids；
bad_example / good_example 必须是原文片段，不要自己编。

反馈对：
{pairs}
"""


def extract_with_llm(
    pairs: List[Dict[str, Any]],
    *,
    provider: str,
    model: str | None = None,
    seed: int = 8901,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """LLM 提炼路径：模型归纳候选规则，返回 (候选列表, 证据回执)。"""
    brief = [
        {
            "id": p["id"], "scene": p["scene"],
            "before": p["before"], "after": p["after"], "correction": p["correction"],
        }
        for p in pairs
    ]
    content, receipt = chat(
        [{"role": "user", "content": _LLM_EXTRACT_PROMPT.format(
            pairs=json.dumps(brief, ensure_ascii=False, indent=2))}],
        provider=provider, model=model, seed=seed,
    )
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    payload = json.loads(cleaned)
    candidates = []
    for rule in payload.get("rules", []):
        if not all(k in rule for k in ("id", "name", "definition", "detector", "source_ids")):
            continue  # schema 不完整的候选直接丢弃，由模型外部代码把关
        rule.setdefault("scope", [])
        rule.setdefault("bad_example", "")
        rule.setdefault("good_example", "")
        rule["status"] = "candidate"
        candidates.append(rule)
    return candidates, receipt


def write_candidates(candidates: List[Dict[str, Any]], path: Path | None = None) -> Path:
    out = path or DATA_DIR / "candidate_rules.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
