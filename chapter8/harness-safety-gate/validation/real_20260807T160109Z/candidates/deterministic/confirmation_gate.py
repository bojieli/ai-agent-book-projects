"""候选模块：高风险工具调用确认门禁。

由 Coding Agent 生成的独立新模块，不覆盖稳定代码。在工具调度前进行
风险分类：高风险调用先挂起，必须持有绑定具体操作与参数的一次性确认
token 才会放行执行。
"""

import hashlib
import hmac
import json
import re

VERSION = "1.1.0-candidate"

_DESTRUCTIVE_SQL = re.compile(r"\b(DROP\s+TABLE|TRUNCATE)\b", re.IGNORECASE)
_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
_HAS_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)
_DANGEROUS_SHELL = re.compile(r"\brm\s+-[rf]+\b|\bmkfs\b|\bshutdown\b|\bdd\s+if=", re.IGNORECASE)

# token -> 操作指纹；取出即作废，保证一次性
_pending = {}


def _fingerprint(tool_name, args):
    canonical = json.dumps({"tool": tool_name, "args": args or {}}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def classify(tool_name, args=None):
    """返回挂起原因；返回 None 表示低风险，可直接执行。"""
    args = args or {}
    if tool_name == "delete_file":
        return "删除文件不可逆，执行前必须经用户确认"
    if tool_name == "git_push" and args.get("force"):
        return "force push 会覆盖远端提交历史"
    if tool_name == "sql_query":
        query = str(args.get("query", ""))
        if _DESTRUCTIVE_SQL.search(query):
            return "DROP/TRUNCATE 会销毁整张表"
        if _DELETE_FROM.search(query) and not _HAS_WHERE.search(query):
            return "无 WHERE 的 DELETE 会清空整表"
    if tool_name == "run_shell" and _DANGEROUS_SHELL.search(str(args.get("command", ""))):
        return "Shell 命令包含不可逆的破坏性模式"
    return None


def requires_confirmation(tool_name, args=None):
    """判断调用是否属于高风险，需要用户显式确认。"""
    return classify(tool_name, args) is not None


def issue_confirmation(tool_name, args=None):
    """为一次具体操作签发一次性确认 token（绑定工具名与完整参数）。"""
    fingerprint = _fingerprint(tool_name, args)
    token = hmac.new(fingerprint.encode("utf-8"), b"confirmation-gate", hashlib.sha256).hexdigest()[:24]
    _pending[token] = fingerprint
    return token


def dispatch(tool_name, args=None, *, execute, confirm_token=None):
    """调度入口：低风险直接执行；高风险必须持有效一次性确认 token。

    execute 由 Harness 注入，本模块不直接触碰任何真实工具。
    """
    args = args or {}
    reason = classify(tool_name, args)
    if reason is None:
        return {"status": "executed", "confirmed": False, "result": execute(tool_name, args)}
    if confirm_token is None:
        return {"status": "pending_confirmation", "reason": reason}
    expected = _pending.pop(confirm_token, None)  # 取出即作废，保证一次性
    if expected is None or not hmac.compare_digest(expected, _fingerprint(tool_name, args)):
        return {"status": "rejected", "reason": "确认 token 无效、已使用或与其他操作不匹配"}
    return {"status": "executed", "confirmed": True, "result": execute(tool_name, args)}
