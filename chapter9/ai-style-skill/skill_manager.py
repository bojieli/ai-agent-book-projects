"""Skill 的增量维护：合并、去重、冲突检测、prune 与 SKILL.md 生成。

防膨胀原则：新候选与现有规则 detector 签名相同（同类型同模式）时合并来源，
而不是无限追加；阈值等参数不一致时报冲突并由模型外部代码决定保留哪一边。
长期未被新证据确认、或被评估证据推翻的规则归档到 skill/archive/，不再进入
SKILL.md。所有合并/激活/归档决定都发生在这里，不交给生成候选的模型。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / "skill"

# detector 参数中参与冲突检测的字段。
_TUNABLE_KEYS = ("threshold", "min_occurrences", "min_run")


def detector_signature(detector: Dict[str, Any]) -> Tuple:
    """规则的「指纹」：同指纹的规则视为同一条，合并而非追加。"""
    dtype = detector.get("type")
    if dtype == "structure":
        return (dtype, detector.get("kind"))
    if dtype == "llm":
        return (dtype,)
    return (dtype, detector.get("pattern"))


def merge_rules(
    existing: List[Dict[str, Any]], candidates: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """把候选规则合并进现有规则集，返回 (规则集, 合并报告)。"""
    rules = [dict(rule) for rule in existing]
    report: Dict[str, Any] = {"added": [], "merged": [], "conflicts": []}
    for cand in candidates:
        sig = detector_signature(cand.get("detector", {}))
        match = next(
            (r for r in rules if detector_signature(r.get("detector", {})) == sig), None
        )
        if match is None:
            rules.append(cand)
            report["added"].append(cand["id"])
            continue
        # 去重合并：并集来源与作用域，保留已有范例。
        match["source_ids"] = sorted(set(match.get("source_ids", [])) | set(cand.get("source_ids", [])))
        match["scope"] = sorted(set(match.get("scope", [])) | set(cand.get("scope", [])))
        report["merged"].append(cand["id"])
        # 冲突检测：同指纹但可调参数矛盾（如两条破折号规则阈值不同）。
        for key in _TUNABLE_KEYS:
            old = match["detector"].get(key)
            new = cand["detector"].get(key)
            if old is not None and new is not None and old != new:
                report["conflicts"].append({
                    "rule_id": match["id"],
                    "parameter": key,
                    "existing_value": old,
                    "candidate_value": new,
                    "resolution": "保留现有值，冲突记录在案，需人工或更多证据裁决",
                })
    return rules, report


def prune_rules(
    rules: List[Dict[str, Any]],
    *,
    current_batch: int,
    idle_batches: int = 2,
    contradicted_ids: Set[str] | None = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """把长期未被新证据确认、或被证据推翻的规则归档，返回 (存活, 归档)。"""
    contradicted = contradicted_ids or set()
    active, archived = [], []
    for rule in rules:
        last = rule.get("last_confirmed_batch", current_batch)
        reason = None
        if rule["id"] in contradicted:
            reason = "被评估证据推翻（误伤率过高或与金标集冲突）"
        elif current_batch - last > idle_batches:
            reason = f"连续超过 {idle_batches} 批反馈未再被触发"
        if reason:
            archived.append({**rule, "status": "archived", "archive_reason": reason})
        else:
            active.append(rule)
    return active, archived


def _describe_detector(detector: Dict[str, Any]) -> str:
    dtype = detector.get("type")
    if dtype == "regex":
        return f"正则 `{detector['pattern']}`，全篇命中达到 {detector.get('min_occurrences', 1)} 处触发"
    if dtype == "density":
        return (
            f"统计 `{detector['pattern']}` 出现次数，全篇达到 "
            f"{detector.get('min_occurrences', 1)} 次且密度超过 "
            f"{detector.get('threshold')} 次/千字时触发"
        )
    if dtype == "structure":
        return f"检测连续 ≥{detector.get('min_run', 3)} 个结构相似分句（同开头或同结尾）"
    if dtype == "llm":
        return "LLM judge 判定（上线前须通过金标集校准）：" + detector.get("judge_prompt", "")
    return "未知检测器"


def render_skill_md(rules: List[Dict[str, Any]]) -> str:
    """按 house 风格渲染 SKILL.md：何时加载 + 每条规则的定义/坏例/好例/作用域。"""
    lines = [
        "---",
        "name: ai-style",
        "description: 中文文案去「AI 味」检查清单，由用户纠正反馈持续提炼而来",
        "---",
        "",
        "# 去 AI 味写作 Skill",
        "",
        "## 何时加载",
        "",
        "当任务是用中文撰写或改写面向读者的文案（产品发布稿、公众号文章、邮件、README 等），",
        "或用户反馈文字「AI 味太重」「不像人写的」时，加载本 Skill。",
        "",
        "## 使用方式",
        "",
        "起草或改写时逐条对照下面的规则自查。每条规则都给出定义、可检查的检测方法、",
        "坏例与好例；规则只在声明的作用域内生效，作用域之外的文体不要套用。",
        "",
        f"## 规则清单（共 {len(rules)} 条）",
        "",
    ]
    for i, rule in enumerate(rules, 1):
        lines += [
            f"### 规则 {i}：{rule['name']}（`{rule['id']}`）",
            "",
            f"- **定义**：{rule['definition']}",
            f"- **检测方法**：{_describe_detector(rule['detector'])}",
            f"- **坏例**：{rule.get('bad_example', '')}",
            f"- **好例**：{rule.get('good_example', '')}",
            f"- **改写建议**：{rule.get('rewrite_hint', '按定义改写。')}",
            f"- **作用域**：{'、'.join(rule.get('scope', [])) or '通用'}",
            f"- **来源反馈**：{', '.join(rule.get('source_ids', [])) or '无'}",
            "",
        ]
    return "\n".join(lines)


def write_skill(rules: List[Dict[str, Any]], skill_dir: Path | None = None) -> Path:
    out_dir = skill_dir or SKILL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "SKILL.md"
    path.write_text(render_skill_md(rules), encoding="utf-8")
    # 同步保存机器可读的规则集，供 evaluate/judge 直接加载。
    (out_dir / "rules.json").write_text(
        json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


def write_archive(archived: List[Dict[str, Any]], skill_dir: Path | None = None) -> Path | None:
    if not archived:
        return None
    out_dir = (skill_dir or SKILL_DIR) / "archive"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# 已归档规则", ""]
    for rule in archived:
        lines += [
            f"## {rule['name']}（`{rule['id']}`）",
            f"- 归档原因：{rule.get('archive_reason', '未说明')}",
            f"- 原定义：{rule['definition']}",
            f"- 来源反馈：{', '.join(rule.get('source_ids', [])) or '无'}",
            "",
        ]
    path = out_dir / "ARCHIVED.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
