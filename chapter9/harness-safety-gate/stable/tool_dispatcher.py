"""稳定版本 1.0.0 的 Harness 工具调度器（教学简化版）。

注册了 read_file / write_file / delete_file / run_shell / git_push /
sql_query 六个工具，dispatch 不做任何风险分级，直接调用目标工具——
这正是本实验要修复的缺陷：删除文件、force push、DROP TABLE 等不可逆
操作在未经用户确认时也会被执行。

所有工具只作用于调用方传入的内存模拟环境 env（默认由 default_env()
构造），不触碰真实文件系统、Shell、Git 远端或数据库，因此失败回放与
候选验证都可以离线安全运行。
"""

import re

VERSION = "1.0.0"


def default_env():
    """返回一份内存模拟环境：文件、Shell 历史、Git 提交与数据库表。"""
    return {
        "files": {
            "reports/2026-Q1-draft.docx": "（尚未定稿的季度报告草稿）",
            "notes/todo.md": "- 周五前备份报告草稿\n",
            "tmp/cache-0417.tmp": "临时缓存，可安全清理",
        },
        "shell_history": [],
        "git": {
            "local": ["c3f9a21 修复登录页样式"],
            "remote": ["9f8e7d0 同事的提交：更新依赖锁定"],
        },
        "db": {
            "users": [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}],
            "orders": [{"id": 101, "amount": 59.0}, {"id": 102, "amount": 12.5}],
        },
    }


def _read_file(env, path):
    if path not in env["files"]:
        return {"ok": False, "error": f"文件不存在: {path}"}
    return {"ok": True, "content": env["files"][path]}


def _write_file(env, path, content):
    env["files"][path] = content
    return {"ok": True, "bytes": len(content)}


def _delete_file(env, path):
    if path not in env["files"]:
        return {"ok": False, "error": f"文件不存在: {path}"}
    del env["files"][path]
    return {"ok": True, "deleted": path}


def _run_shell(env, command):
    env["shell_history"].append(command)
    return {"ok": True, "output": f"[模拟 shell] 已记录命令: {command}"}


def _git_push(env, remote="origin", branch="main", force=False):
    if force:
        # force push 用本地历史覆盖远端，同事的提交就此丢失
        env["git"]["remote"] = list(env["git"]["local"])
    else:
        env["git"]["remote"].extend(env["git"]["local"])
    return {"ok": True, "remote": remote, "branch": branch, "force": force}


def _table_name(text):
    match = re.search(r"\bFROM\s+([\w.-]+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    parts = text.split()
    return parts[2] if len(parts) > 2 else ""


def _sql_query(env, query):
    text = " ".join(str(query).strip().rstrip(";").split())
    upper = text.upper()
    table = _table_name(text)
    if upper.startswith("SELECT"):
        return {"ok": True, "rows": list(env["db"].get(table, []))}
    if upper.startswith("DROP TABLE"):
        existed = table in env["db"]
        env["db"].pop(table, None)
        return {"ok": True, "dropped": table, "existed": existed}
    if upper.startswith("TRUNCATE"):
        removed = len(env["db"].get(table, []))
        env["db"][table] = []
        return {"ok": True, "truncated": table, "removed_rows": removed}
    if upper.startswith("DELETE"):
        rows = env["db"].get(table, [])
        match = re.search(r"\bWHERE\s+id\s*=\s*(\d+)", text, re.IGNORECASE)
        if match:
            # 教学简化：仅支持 WHERE id = N 的定点删除
            target = int(match.group(1))
            env["db"][table] = [row for row in rows if row.get("id") != target]
        else:
            env["db"][table] = []
        return {"ok": True, "removed_rows": len(rows) - len(env["db"][table])}
    return {"ok": True}


TOOLS = {
    "read_file": _read_file,
    "write_file": _write_file,
    "delete_file": _delete_file,
    "run_shell": _run_shell,
    "git_push": _git_push,
    "sql_query": _sql_query,
}


def dispatch(tool_name, args=None, *, env=None):
    """直接执行注册的工具。

    当前版本没有任何风险检查：高风险调用与读取文件一样被立即执行，
    不存在确认 token 的概念。这就是失败轨迹归因出的缺陷。
    """
    if tool_name not in TOOLS:
        raise KeyError(f"未注册的工具: {tool_name}")
    env = default_env() if env is None else env
    args = args or {}
    return {"tool": tool_name, "args": args, "result": TOOLS[tool_name](env, **args)}
