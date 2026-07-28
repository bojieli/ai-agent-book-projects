"""
工具库管理：create_tool（封装并持久化）、search_tools（检索复用）、以及被封装工具的执行。

这是 Alita 式「自我进化」的核心：
- Agent 用 code_interpreter 验证过某个方案后，调用 create_tool 把它固化成一个
  「标准工具」——包含 name / description / JSON-Schema 参数 / Python 代码，持久化到 tool_library/。
- 下次遇到同类任务，Agent 应先 search_tools 命中已有工具并直接复用，而不是重新上网搜索、重新写代码。
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
LIBRARY_DIR = PROJECT_DIR / "tool_library"
SANDBOX_PKG_DIR = PROJECT_DIR / ".sandbox_packages"


def normalize_schema(params) -> dict:
    """
    把模型给出的 parameters 规整为合法的 OpenAI function-calling JSON Schema。
    模型常见错误：只给 properties 映射而漏掉顶层 {"type":"object"}。这里做容错，
    否则把这样的工具再暴露给 OpenAI 会触发 400 invalid schema 而中断整个流程。
    """
    if not isinstance(params, dict):
        return {"type": "object", "properties": {}}
    if params.get("type") == "object" and "properties" in params:
        return params
    if "properties" in params:  # 有 properties 但 type 缺失/错误
        out = {"type": "object", "properties": params["properties"]}
        if "required" in params:
            out["required"] = params["required"]
        return out
    # 整个 dict 视为 properties 映射
    return {"type": "object", "properties": params}


class ToolLibrary:
    """基于文件系统的极简工具库。每个工具 = 一个 .json（元数据+代码）。"""

    def __init__(self, library_dir: Path = LIBRARY_DIR):
        self.dir = Path(library_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------- create_tool ----------------------------- #
    def create_tool(self, name: str, description: str, parameters: dict, code: str,
                    test_args: dict | None = None) -> dict:
        """
        把一个功能封装为标准工具并持久化。

        约定：code 里必须定义一个名为 run(**kwargs) 的函数，返回可 JSON 序列化的结果。
        parameters 为 OpenAI function-calling 风格的 JSON Schema（type=object, properties, required）。

        「存前验证」闸门（对应图 8-7 流水线里的「测试」一步、以及本章「工具质量退化」告诫）：
        - 先做**语法编译检查**，语法错误的代码一律拒绝入库；
        - 若给了 test_args，则在沙箱里**真正执行一次 run(**test_args)**，只有成功返回结果
          才允许注册——从而挡住「封装了却根本跑不通」的坏工具污染工具库、再被后续任务反复复用。
        """
        name = name.strip()
        if not name.isidentifier():
            return {"success": False, "error": f"invalid tool name: {name!r} (must be a valid identifier)"}
        if "def run" not in code:
            return {"success": False, "error": "tool code must define a function `def run(**kwargs)`"}
        # 存前验证 1：语法编译检查（坏语法直接挡在库外）
        try:
            compile(code, f"<tool {name}>", "exec")
        except SyntaxError as e:
            return {"success": False, "error": f"tool code has a syntax error: {e}"}

        record = {
            "name": name,
            "description": description,
            "parameters": normalize_schema(parameters),
            "code": code,
        }

        # 存前验证 2：给了 test_args 就真跑一次 run()，跑不通就拒绝入库
        validated = False
        if test_args is not None:
            val = self._run_record(record, test_args)
            if not val.get("success"):
                return {
                    "success": False,
                    "error": "工具注册前验证失败：run(**test_args) 没有成功返回。请修正代码或 test_args"
                             "后重新提交（未通过验证的工具不会入库，以免坏工具被后续任务复用）。",
                    "validation": val,
                }
            validated = True

        (self.dir / f"{name}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
        return {
            "success": True,
            "message": f"tool '{name}' created and saved to tool_library/"
                       + ("（已通过存前验证）" if validated else "（未提供 test_args，跳过运行验证）"),
            "name": name,
            "validated": validated,
        }

    # ----------------------------- search_tools ---------------------------- #
    def search_tools(self, query: str) -> dict:
        """按名称/描述做关键词检索，返回命中的工具（用于复用）。"""
        query = (query or "").strip().lower()
        terms = [t for t in query.replace(",", " ").split() if t]
        hits = []
        for rec in self.list_tools():
            haystack = (rec["name"] + " " + rec["description"]).lower()
            score = sum(1 for t in terms if t in haystack)
            if score > 0 or not terms:
                hits.append((score, rec))
        hits.sort(key=lambda x: -x[0])
        return {
            "success": True,
            "query": query,
            "count": len(hits),
            "tools": [
                {"name": r["name"], "description": r["description"], "parameters": r["parameters"]}
                for _, r in hits
            ],
        }

    # ------------------------------ helpers -------------------------------- #
    def list_tools(self) -> list:
        recs = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                recs.append(json.loads(p.read_text()))
            except Exception:  # noqa: BLE001
                continue
        return recs

    def get_tool(self, name: str) -> dict | None:
        p = self.dir / f"{name}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text())

    # -------------------------- execute a wrapped tool --------------------- #
    def execute_tool(self, name: str, arguments: dict, timeout: int = 60) -> dict:
        """
        在子进程沙箱中执行已封装的工具：注入代码 + run(**args)，捕获 JSON 结果。
        PYTHONPATH 指向 .sandbox_packages，使 create 时 pip 安装的依赖可用。
        """
        rec = self.get_tool(name)
        if rec is None:
            return {"success": False, "error": f"tool '{name}' not found in library"}
        return self._run_record(rec, arguments, timeout)

    def _run_record(self, rec: dict, arguments: dict, timeout: int = 60) -> dict:
        """按「工具记录（含 code）」在沙箱子进程里执行 run(**arguments)。

        直接吃 record 而不读磁盘，因此可在工具**尚未落盘时**用于「存前验证」。
        """
        SANDBOX_PKG_DIR.mkdir(exist_ok=True)
        driver = (
            rec["code"]
            + "\n\nif __name__ == '__main__':\n"
            "    import json as _json, sys as _sys\n"
            "    _args = _json.loads(_sys.argv[1])\n"
            "    _out = run(**_args)\n"
            "    print('__TOOL_RESULT__' + _json.dumps(_out, default=str))\n"
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SANDBOX_PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=SANDBOX_PKG_DIR) as f:
            f.write(driver)
            script = f.name
        try:
            r = subprocess.run(
                [sys.executable, script, json.dumps(arguments)],
                capture_output=True, text=True, timeout=timeout, env=env,
            )
            if r.returncode != 0:
                return {"success": False, "error": "tool crashed", "stderr": r.stderr[-3000:]}
            for line in r.stdout.splitlines():
                if line.startswith("__TOOL_RESULT__"):
                    raw = line[len("__TOOL_RESULT__"):]
                    try:
                        return {"success": True, "result": json.loads(raw)}
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "error": f"invalid result marker: {e}",
                            "stdout": r.stdout[-2000:],
                        }
            return {"success": False, "error": "no result marker", "stdout": r.stdout[-2000:]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"timeout after {timeout}s"}
        finally:
            try:
                os.unlink(script)
            except OSError:
                pass
