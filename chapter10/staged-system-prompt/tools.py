"""
工具实现与工具集定义。

本文件包含两部分：
1. Workspace：一个进程内的“虚拟工作区”，负责保存需求、文件内容，
   并提供真实的代码执行 / 语法检查 / 复杂度分析能力。
2. 三个阶段各自的工具 JSON Schema（供 OpenAI function calling 使用）。

关键点：不同阶段暴露给模型的工具集是不同的，这是“阶段化系统提示词”实验
的核心之一——提示词换了角色，工具也随之切换。
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from typing import Dict, List


# ----------------------------------------------------------------------------
# 触发阶段转换的“信号工具”名字。Agent 主循环看到这些工具被调用就切换阶段。
# ----------------------------------------------------------------------------
COMPLETE_REQUIREMENTS = "complete_requirements_analysis"  # 阶段1 -> 阶段2
SUBMIT_FOR_REVIEW = "submit_for_review"                   # 阶段2 -> 阶段3
REQUEST_REVISION = "request_revision"                     # 阶段3 -> 阶段2（回退）
APPROVE_CODE = "approve_code"                             # 阶段3 -> 完成


class Workspace:
    """跨阶段共享的任务状态（需求、文件、审查意见）。"""

    def __init__(self) -> None:
        # 阶段1 收集到的、已确认的需求（key -> value）
        self.requirements: Dict[str, str] = {}
        # 阶段2 写出的“文件系统”（path -> content）
        self.files: Dict[str, str] = {}
        # 阶段3 退回时记录的问题清单，供阶段2 修复时参考
        self.review_issues: List[str] = []

    # --- 阶段1：需求分析师的工具实现 -------------------------------------
    def save_requirement(self, key: str, value: str) -> str:
        self.requirements[key] = value
        return f"已记录需求 [{key}] = {value}"

    # --- 阶段2：软件工程师的工具实现 -------------------------------------
    def write_file(self, path: str, content: str) -> str:
        self.files[path] = content
        return f"已写入文件 {path}（{len(content)} 字符，{content.count(chr(10)) + 1} 行）"

    def read_file(self, path: str) -> str:
        if path not in self.files:
            return f"错误：文件 {path} 不存在。当前文件列表：{list(self.files) or '空'}"
        return self.files[path]

    def execute_code(self, code: str) -> str:
        """在临时目录里真实执行一段 Python，返回 stdout/stderr（带超时）。"""
        return _run_python_source(code)

    # --- 阶段3：代码审查员的工具实现 -------------------------------------
    def run_linter(self, path: str) -> str:
        """轻量静态检查：语法编译 + 常见坏味道，不引入额外依赖。"""
        if path not in self.files:
            return f"错误：文件 {path} 不存在。"
        source = self.files[path]
        problems: List[str] = []

        # 1) 语法能否编译
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return f"[linter] 语法错误：第 {exc.lineno} 行 {exc.msg}"

        # 2) 逐行的风格问题（阈值定得“严格但可达标”，方便演示先退回再通过）
        for i, line in enumerate(source.splitlines(), start=1):
            if len(line) > 120:
                problems.append(f"L{i}: 行超过 120 字符（{len(line)}），请折行或精简")
            if line.rstrip() != line:
                problems.append(f"L{i}: 行尾有多余空白")
            if "\t" in line:
                problems.append(f"L{i}: 使用了 Tab 缩进，建议用空格")

        # 3) 基于 AST 的问题：缺少模块 docstring、裸 except
        if not ast.get_docstring(tree):
            problems.append("模块缺少文件级 docstring（请在文件开头加一段三引号说明）")
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                problems.append(f"L{node.lineno}: 使用了裸 except，建议捕获具体异常")

        if not problems:
            return "[linter] 通过：未发现问题。"
        return "[linter] 发现 %d 个问题：\n- %s" % (len(problems), "\n- ".join(problems))

    def run_tests(self, path: str) -> str:
        """冒烟测试：把文件跑起来，验证 import / 主流程不崩溃。"""
        if path not in self.files:
            return f"错误：文件 {path} 不存在。"
        # 造一个假的“下载文件夹”，让整理脚本有东西可整理
        harness = (
            "import os, tempfile, runpy, sys\n"
            "d = tempfile.mkdtemp()\n"
            "for name in ['a.jpg','b.pdf','c.txt','d.mp3','readme']:\n"
            "    open(os.path.join(d, name), 'w').close()\n"
            "sys.argv = ['script', d]\n"
            "print('SMOKE_TEST target dir:', d)\n"
            + self.files[path]
        )
        result, returncode = _run_python(harness)
        # 以退出码为准：超时（returncode 为 None）和非零退出都不能算 PASS；
        # Traceback/Error 子串检查作为额外防线保留。
        ok = returncode == 0 and "Traceback" not in result and "Error" not in result
        verdict = "PASS" if ok else "FAIL"
        return f"[tests] 冒烟测试结果：{verdict}\n{result}"

    def analyze_complexity(self, path: str) -> str:
        """用 AST 估算复杂度：函数数量、最大分支数、最大嵌套深度。"""
        if path not in self.files:
            return f"错误：文件 {path} 不存在。"
        try:
            tree = ast.parse(self.files[path])
        except SyntaxError as exc:
            return f"[complexity] 无法解析：{exc.msg}"

        funcs = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        branch_types = (ast.If, ast.For, ast.While, ast.Try, ast.With)
        total_branches = sum(1 for n in ast.walk(tree) if isinstance(n, branch_types))

        def depth(node: ast.AST, level: int = 0) -> int:
            best = level
            for child in ast.iter_child_nodes(node):
                inc = 1 if isinstance(child, branch_types) else 0
                best = max(best, depth(child, level + inc))
            return best

        return (
            "[complexity] 函数数量=%d，分支/循环语句=%d，最大嵌套深度=%d"
            % (len(funcs), total_branches, depth(tree))
        )


def _run_python(source: str, timeout: int = 10) -> tuple:
    """执行源码，返回 (合并后的输出, 退出码)；超时时退出码为 None。"""
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "snippet.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(source)
        try:
            proc = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return f"执行超时（>{timeout}s）", None
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        parts = []
        if out:
            parts.append("stdout:\n" + out)
        if err:
            parts.append("stderr:\n" + err)
        parts.append(f"退出码: {proc.returncode}")
        return "\n".join(parts), proc.returncode


def _run_python_source(source: str, timeout: int = 10) -> str:
    """把源码写到临时文件并用子进程执行，返回合并后的输出。"""
    return _run_python(source, timeout)[0]


# ----------------------------------------------------------------------------
# 各阶段的工具 Schema（OpenAI tools 格式）。每个阶段只暴露自己那套工具。
# ----------------------------------------------------------------------------

def _tool(name: str, description: str, properties: dict, required: list) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


STAGE1_TOOLS = [
    _tool(
        "ask_clarifying_question",
        "向用户提出一个澄清需求的问题，用户会回答。需求不明确时必须先问清楚。",
        {"question": {"type": "string", "description": "要问用户的问题"}},
        ["question"],
    ),
    _tool(
        "save_requirement",
        "把一条已经确认的需求记录到需求文档中，供后续实现阶段使用。",
        {
            "key": {"type": "string", "description": "需求项名称，如 file_types"},
            "value": {"type": "string", "description": "需求项取值/描述"},
        },
        ["key", "value"],
    ),
    _tool(
        COMPLETE_REQUIREMENTS,
        "当所有关键需求都已澄清并记录后调用，结束需求分析阶段，进入代码实现阶段。",
        {"summary": {"type": "string", "description": "对已确认需求的一句话总结"}},
        ["summary"],
    ),
]

STAGE2_TOOLS = [
    _tool(
        "write_file",
        "写入（或覆盖）一个文件的完整内容。",
        {
            "path": {"type": "string", "description": "文件路径，如 organize_downloads.py"},
            "content": {"type": "string", "description": "文件的完整内容"},
        },
        ["path", "content"],
    ),
    _tool(
        "read_file",
        "读取一个已写入文件的内容。",
        {"path": {"type": "string", "description": "文件路径"}},
        ["path"],
    ),
    _tool(
        "execute_code",
        "执行一段 Python 代码用于自测/验证，返回标准输出与错误。",
        {"code": {"type": "string", "description": "要执行的 Python 代码"}},
        ["code"],
    ),
    _tool(
        SUBMIT_FOR_REVIEW,
        "当代码实现完成且自测通过后调用，提交给代码审查员，进入审查阶段。",
        {"file": {"type": "string", "description": "要提交审查的主文件路径"}},
        ["file"],
    ),
]

STAGE3_TOOLS = [
    _tool(
        "run_linter",
        "对文件运行静态检查，返回代码风格/规范问题。",
        {"file": {"type": "string", "description": "文件路径"}},
        ["file"],
    ),
    _tool(
        "run_tests",
        "对文件运行冒烟测试，验证能否正常运行。",
        {"file": {"type": "string", "description": "文件路径"}},
        ["file"],
    ),
    _tool(
        "analyze_complexity",
        "分析文件的代码复杂度（函数数、分支数、嵌套深度）。",
        {"file": {"type": "string", "description": "文件路径"}},
        ["file"],
    ),
    _tool(
        REQUEST_REVISION,
        "当审查发现必须修复的问题时调用，把代码退回实现阶段并附上问题清单。",
        {
            "issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "需要修复的问题列表",
            }
        },
        ["issues"],
    ),
    _tool(
        APPROVE_CODE,
        "当代码通过所有审查、质量达标时调用，批准代码，任务完成。",
        {"comment": {"type": "string", "description": "审查通过的简短评语"}},
        ["comment"],
    ),
]
