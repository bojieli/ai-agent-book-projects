"""确定性「AI 味」检测器：每条规则返回命中位置与证据。

所有检测器都是离线、确定性的，不依赖 LLM 与第三方库。检测器由规则中的
detector 字段驱动，支持四种类型：

- {"type": "regex",    "pattern": ..., "min_occurrences": n}  命中次数达到 n 才触发
- {"type": "density",  "pattern": ..., "min_occurrences": n, "threshold": 次/千字}
- {"type": "structure", "kind": "parallelism", "min_run": 3}   连续 >= 3 个结构相似分句
- {"type": "llm",      "judge_prompt": ...}                    本模块跳过，由 judge.py 处理

regex / density 允许设置 min_occurrences，是为了区分「滥用」与「合法使用」：
单独一处「不是……而是……」可能是真实对比，连用两三处才是 AI 腔。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

# 常见 emoji 码位区间；刻意排除 FE0F 变体选择符，避免「❤️」被重复计数。
EMOJI_PATTERN = r"[☀-➿⬀-⯿⌀-⏿\U0001F000-\U0001FAFF]"

# 分句切分：中文停顿标点之外不算子句边界。
_CLAUSE_RE = re.compile(r"[^，。！？；：、\n…—]+")


def _regex_hits(text: str, detector: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches = list(re.finditer(detector["pattern"], text))
    min_occ = detector.get("min_occurrences", 1)
    if len(matches) < min_occ:
        return []
    return [
        {
            "start": m.start(),
            "end": m.end(),
            "evidence": m.group(),
            "detail": f"共命中 {len(matches)} 处（达到 {min_occ} 处触发阈值）",
        }
        for m in matches
    ]


def _density_hits(text: str, detector: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches = list(re.finditer(detector["pattern"], text))
    count = len(matches)
    min_occ = detector.get("min_occurrences", 1)
    threshold = detector.get("threshold", 0.0)
    density = count * 1000 / max(len(text), 1)
    if count < min_occ or density <= threshold:
        return []
    detail = f"出现 {count} 次，密度 {density:.1f} 次/千字，超过阈值 {threshold} 次/千字"
    return [
        {"start": m.start(), "end": m.end(), "evidence": m.group(), "detail": detail}
        for m in matches
    ]


def _clauses_similar(a: str, b: str) -> bool:
    """判断相邻两个分句是否结构相似：同开头字或同结尾字。

    刻意不用「长度相近」作为判据——随机散文里等长分句太常见，会把
    正常行文误判成排比（防误伤）。
    """
    if not a or not b:
        return False
    return a[0] == b[0] or a[-1] == b[-1]


def detect_parallelism(text: str, min_run: int = 3) -> List[Dict[str, Any]]:
    """检测连续 >= min_run 个结构相似分句的排比堆砌。"""
    clauses = [
        (m.start(), m.end(), m.group().strip())
        for m in _CLAUSE_RE.finditer(text)
        if len(m.group().strip()) >= 2
    ]
    hits: List[Dict[str, Any]] = []
    i = 0
    while i < len(clauses):
        j = i + 1
        while j < len(clauses) and _clauses_similar(clauses[j - 1][2], clauses[j][2]):
            j += 1
        if j - i >= min_run:
            start, end = clauses[i][0], clauses[j - 1][1]
            hits.append({
                "start": start,
                "end": end,
                "evidence": text[start:end],
                "detail": (
                    f"连续 {j - i} 个结构相似分句："
                    + " / ".join(c[2] for c in clauses[i:j])
                ),
            })
        i = max(j, i + 1)
    return hits


def run_detector(text: str, detector: Dict[str, Any]) -> List[Dict[str, Any]]:
    """按 detector 类型分派；llm 类型交给 judge.py，这里返回空。"""
    dtype = detector.get("type")
    if dtype == "regex":
        return _regex_hits(text, detector)
    if dtype == "density":
        return _density_hits(text, detector)
    if dtype == "structure" and detector.get("kind") == "parallelism":
        return detect_parallelism(text, detector.get("min_run", 3))
    return []


def run_rules(text: str, rules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """对一段文本跑所有确定性规则，返回 {rule_id: [命中, ...]}（只含非空）。"""
    result: Dict[str, List[Dict[str, Any]]] = {}
    for rule in rules:
        hits = run_detector(text, rule.get("detector", {}))
        if hits:
            result[rule["id"]] = hits
    return result
