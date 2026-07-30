"""
tools.py —— 各专业角色的专属工具实现 + OpenAI function-calling schema。

设计原则（配合实验 10-2）：
- 所有被实验场景实际调用的工具都执行真实工作，不用预置答案冒充检索。
- research.web_search：Tavily 真实联网检索，并返回可追溯 URL 与摘录。
- coding.execute_python：真实执行 Python 代码并捕获标准输出（子进程 + 超时）。
- data_analysis.calculate / descriptive_stats：真实的安全计算。
- writing.count_characters：真实的中英文字数统计。

每个工具函数签名为 func(**kwargs) -> str（统一返回字符串，方便塞回对话历史）。
"""

from __future__ import annotations

import ast
import json
import operator
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# research 角色：web_search —— 真实 Tavily 搜索
# ---------------------------------------------------------------------------

def web_search(query: str, receipt_sink: Optional[Callable[[dict], None]] = None) -> str:
    """Run a real Tavily web search and return attributable source excerpts."""
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("web_search requires TAVILY_API_KEY; no mock fallback is allowed")
    body = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 8,
        "include_answer": True,
        "include_raw_content": False,
    }
    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = response.status
            raw_response = response.read().decode("utf-8", "replace")
            payload = json.loads(raw_response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1000]
        raise RuntimeError(f"Tavily HTTP {exc.code}: {detail}") from None
    if receipt_sink:
        receipt_sink({
            "kind": "tavily_search",
            "request": {
                "method": "POST",
                "url": "https://api.tavily.com/search",
                "headers": {"Content-Type": "application/json"},
                "body": {key: value for key, value in body.items() if key != "api_key"},
            },
            "response": {
                "http_status": status,
                "raw_body": raw_response,
            },
            "duration_seconds": round(time.monotonic() - started, 3),
        })
    results = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content"),
            "score": item.get("score"),
        })
    if not results:
        return json.dumps({
            "provider": "tavily",
            "query": query,
            "answer": payload.get("answer"),
            "results": [],
        }, ensure_ascii=False)
    return json.dumps({
        "provider": "tavily",
        "query": query,
        "answer": payload.get("answer"),
        "results": results,
    }, ensure_ascii=False)


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
            "description": "通过 Tavily 真实联网检索信息，返回带 URL 的来源摘录。用于查数据、事实、资料。",
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
