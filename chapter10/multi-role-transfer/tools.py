"""
tools.py —— 各专业角色的专属工具实现 + OpenAI function-calling schema。

设计原则（配合实验 10-2）：
- 工具用「轻量真实实现」或「可控 mock」，重点不是工具多强，
  而是展示「自主角色移交」这一机制。
- research.web_search：内置知识库 mock（可控、可复现），
  未命中时诚实返回「未检索到」。
- coding.execute_python：真实执行 Python 代码并捕获标准输出（子进程 + 超时）。
- data_analysis.calculate / descriptive_stats：真实的安全计算。
- writing.count_characters：真实的中英文字数统计。

每个工具函数签名为 func(**kwargs) -> str（统一返回字符串，方便塞回对话历史）。
"""

from __future__ import annotations

import ast
import operator
import os
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List


# ---------------------------------------------------------------------------
# research 角色：web_search —— 内置知识库 mock
# ---------------------------------------------------------------------------

# 一个极小的「联网检索结果」知识库。命中关键词即返回内置资料，
# 保证 demo 可复现，同时不依赖真实外网。
_KNOWLEDGE_BASE = [
    {
        "keywords": ["新能源", "汽车", "销量", "nev", "电动车"],
        "content": (
            "【检索结果·中国乘用车市场信息联席会/中汽协】\n"
            "中国新能源汽车年度销量（单位：万辆）：\n"
            "- 2021 年：352.1 万辆\n"
            "- 2022 年：688.7 万辆\n"
            "- 2023 年：949.5 万辆\n"
            "备注：包含纯电动(BEV)与插电混动(PHEV)乘用车。"
        ),
    },
    {
        "keywords": ["光伏", "装机", "太阳能"],
        "content": (
            "【检索结果·国家能源局】\n"
            "中国光伏新增装机量（单位：GW）：\n"
            "- 2021 年：54.9 GW\n"
            "- 2022 年：87.4 GW\n"
            "- 2023 年：216.9 GW"
        ),
    },
    {
        "keywords": ["python", "gil", "全局解释器锁"],
        "content": (
            "【检索结果·技术资料】\n"
            "CPython 的 GIL(全局解释器锁)保证同一时刻只有一个线程执行字节码，"
            "因此 CPU 密集型任务用多线程无法并行，需改用多进程或 C 扩展。"
            "PEP 703 提出可选的 no-GIL 构建，Python 3.13 起以实验特性提供。"
        ),
    },
]


def web_search(query: str) -> str:
    """在内置知识库中检索（mock 联网检索）。"""
    q = (query or "").lower()
    hits: List[str] = []
    for entry in _KNOWLEDGE_BASE:
        if any(kw.lower() in q for kw in entry["keywords"]):
            hits.append(entry["content"])
    if hits:
        return "\n\n".join(hits)
    return (
        f"未在内置知识库中检索到与「{query}」直接相关的权威数据。"
        "请换一个更具体的检索词，或说明需要哪一年的数据。"
    )


# ---------------------------------------------------------------------------
# coding 角色：execute_python —— 真实执行代码并捕获 stdout（带超时）
# ---------------------------------------------------------------------------

def execute_python(code: str, timeout: int = 10) -> str:
    """把源码写到临时文件并用子进程执行，返回 stdout（带超时）。"""
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "snippet.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(code)
        try:
            proc = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return f"执行超时（>{timeout}s）"
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode != 0:
            return (
                f"代码执行出错：退出码 {proc.returncode}\n"
                f"stderr：\n{err}\n"
                f"已捕获输出：\n{out}"
            )
        return out if out else "（代码已执行，但没有任何 print 输出）"


# ---------------------------------------------------------------------------
# data_analysis 角色：calculate（安全表达式求值）+ descriptive_stats
# ---------------------------------------------------------------------------

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    """只支持四则运算/幂/取模的安全表达式求值（不走 Python 内置 eval）。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("表达式包含不被支持的运算，只允许 + - * / ** % 与括号。")


def calculate(expression: str) -> str:
    """安全地计算一个纯数学表达式，例如 (949.5/352.1)**(1/2)-1 。"""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
    except Exception as exc:  # noqa: BLE001
        return f"计算失败：{exc}"
    return f"{expression} = {result}"


def descriptive_stats(numbers: List[float]) -> str:
    """给一组数值返回基本描述统计（均值/最大/最小/极差）。"""
    if not numbers:
        return "输入为空，无法统计。"
    nums = [float(x) for x in numbers]
    n = len(nums)
    mean = sum(nums) / n
    return (
        f"样本量={n}, 均值={mean:.4f}, 最小={min(nums)}, "
        f"最大={max(nums)}, 极差={max(nums) - min(nums)}"
    )


# ---------------------------------------------------------------------------
# writing 角色：count_characters —— 中英文字数统计
# ---------------------------------------------------------------------------

def count_characters(text: str) -> str:
    """统计文本的字符数与中文字符数，帮助控制篇幅。"""
    if text is None:
        text = ""
    total = len(text)
    chinese = sum(1 for ch in text if "一" <= ch <= "鿿")
    return f"总字符数={total}, 其中中文字符={chinese}"


# ---------------------------------------------------------------------------
# 工具注册表：名称 -> (实现函数, OpenAI schema)
# ---------------------------------------------------------------------------

# 每个工具的 OpenAI function-calling schema。
TOOL_SCHEMAS: Dict[str, dict] = {
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网检索信息（本实验用内置知识库 mock）。用于查数据、事实、资料。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词或问题"},
                },
                "required": ["query"],
            },
        },
    },
    "execute_python": {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "执行一段 Python 代码并返回其 print 输出。适合写脚本、跑逻辑。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 源码，用 print 输出结果"},
                },
                "required": ["code"],
            },
        },
    },
    "calculate": {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "安全计算一个数学表达式，支持 + - * / ** % 和括号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 (949.5/352.1)**(1/2)-1"},
                },
                "required": ["expression"],
            },
        },
    },
    "descriptive_stats": {
        "type": "function",
        "function": {
            "name": "descriptive_stats",
            "description": "对一组数值做基本描述统计（均值/最大/最小/极差）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "数值数组",
                    },
                },
                "required": ["numbers"],
            },
        },
    },
    "count_characters": {
        "type": "function",
        "function": {
            "name": "count_characters",
            "description": "统计文本字符数与中文字符数，帮助控制篇幅。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要统计的文本"},
                },
                "required": ["text"],
            },
        },
    },
}

# 工具名 -> 实现函数
TOOL_IMPLEMENTATIONS: Dict[str, Callable[..., str]] = {
    "web_search": web_search,
    "execute_python": execute_python,
    "calculate": calculate,
    "descriptive_stats": descriptive_stats,
    "count_characters": count_characters,
}
