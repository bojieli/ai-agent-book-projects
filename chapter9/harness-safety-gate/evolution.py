"""实验 8-8：由用户反馈触发的高风险操作确认门禁。

诊断 → 候选生成 → 模型外验证门槛 → 发布决定，全部在本模块。
与实验 8-5 的对照：8-5 改控制层（重试/熔断），信号来自系统内部错误日志；
本实验改安全/验证层（工具调度确认门禁），信号来自用户纠正、点踩与事后审计。

与 8-5 的另一处差异：候选是新增的独立模块 confirmation_gate.py，不覆盖
稳定代码，因此本实验不需要 Docker 沙箱——候选只做不执行源码的编译与
AST 静态检查，再在内存模拟环境上回放模拟工具调度（executor 由验证器
注入，候选无法触碰真实文件系统、Shell 或数据库）。
"""

from __future__ import annotations

import ast
from collections import defaultdict
import difflib
import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parent
SUPPORT_THRESHOLD = 2
MAX_SOURCE_BYTES = 64_000

CHECK_NAMES = (
    "static_compile",
    "security_scan",
    "gate_contract",
    "boundary_replay",
    "retention_replay",
    "confirmation_single_use",
)

# 候选只允许纯计算的标准库；AST 扫描是执行前的快速预筛。
ALLOWED_IMPORTS = {"hashlib", "hmac", "json", "re", "secrets", "string"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__", "input", "breakpoint"}

_DESTRUCTIVE_SQL = re.compile(r"\b(DROP\s+TABLE|TRUNCATE)\b", re.IGNORECASE)
_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
_HAS_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)
_DANGEROUS_SHELL = re.compile(r"\brm\s+-[rf]+\b|\bmkfs\b|\bshutdown\b|\bdd\s+if=", re.IGNORECASE)


def _load_stable_dispatcher():
    """按路径加载稳定版调度器，避免依赖包结构。"""
    spec = importlib.util.spec_from_file_location(
        "stable_tool_dispatcher", ROOT / "stable" / "tool_dispatcher.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STABLE = _load_stable_dispatcher()


def sha256_text(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _short_sha(source: str) -> str:
    return sha256_text(source)[:12]


def classify_risk(tool_name: str, args: Dict[str, Any] | None = None) -> Tuple[str | None, str]:
    """参考风险分类器：基于工具名与参数模式判定是否需要用户确认。

    返回 (风险类别, 原因)；风险类别为 None 表示低风险，可直接执行。
    诊断阶段用它聚合失败簇；候选模块需自带等价逻辑并接受回放验证。
    """
    args = args or {}
    if tool_name == "delete_file":
        return "delete_file", "删除文件不可逆，执行前必须经用户确认"
    if tool_name == "git_push" and args.get("force"):
        return "force_push", "force push 会覆盖远端提交历史"
    if tool_name == "sql_query":
        query = str(args.get("query", ""))
        if _DESTRUCTIVE_SQL.search(query):
            return "destructive_sql", "DROP/TRUNCATE 会销毁整张表"
        if _DELETE_FROM.search(query) and not _HAS_WHERE.search(query):
            return "destructive_sql", "无 WHERE 的 DELETE 会清空整表"
    if tool_name == "run_shell" and _DANGEROUS_SHELL.search(str(args.get("command", ""))):
        return "dangerous_shell", "Shell 命令包含不可逆的破坏性模式"
    return None, ""


def diagnose(trajectories: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """聚合跨轨迹的相同故障模式：达到支持门槛才创建修改请求。

    三类信号（用户纠正、点踩、事后审计）按风险类别合并计数；用户已确认
    的操作与低风险调用的负反馈不计入失败簇。
    """
    trajectories = list(trajectories)
    clusters: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for item in trajectories:
        if item.get("outcome", "failure") != "failure":
            continue  # 正常完成（含用户已确认）的轨迹不构成失败信号
        for call in item.get("tool_calls", []):
            if call.get("user_confirmed", False):
                continue  # 用户已确认的操作不算违规
            kind, _reason = classify_risk(call.get("tool"), call.get("args"))
            if kind is None:
                continue  # 低风险调用的负反馈不归因到确认门禁
            clusters[kind][item["id"]] = item

    patterns: List[Dict[str, Any]] = []
    for kind in sorted(clusters):
        items = clusters[kind]
        if len(items) < SUPPORT_THRESHOLD:
            continue  # 跨轨迹支持不足，不创建修改请求
        first = next(iter(items.values()))
        call = next(
            c for c in first["tool_calls"]
            if classify_risk(c.get("tool"), c.get("args"))[0] == kind
        )
        patterns.append({
            "cluster_id": f"unconfirmed_{kind}",
            "risk_kind": kind,
            "tool": call.get("tool"),
            "signals": sorted({it["signal"] for it in items.values()}),
            "source_case_ids": sorted(items),
            "cross_trajectory_support": len(items),
        })
    if not patterns:
        return {
            "change_required": False,
            "target": None,
            "source_case_ids": [],
            "patterns": [],
            "reason": "没有任何未确认高风险调用模式达到跨轨迹支持门槛。",
        }
    source_ids = sorted({cid for pattern in patterns for cid in pattern["source_case_ids"]})
    sources = [
        {
            "id": item["id"],
            "signal": item.get("signal"),
            "trajectory_sha256": sha256_text(repr(sorted(item.items(), key=lambda kv: kv[0]))),
        }
        for item in trajectories if item.get("id") in source_ids
    ]
    return {
        "change_required": True,
        "target": "stable/tool_dispatcher.py",
        "target_component": "tool_dispatch_confirmation_gate",
        "source_case_ids": source_ids,
        "source_trajectories": sources,
        "patterns": patterns,
        "reason": (
            "工具调度层缺少高风险调用确认门禁：删除、force push、DROP TABLE 等不可逆操作"
            "未经用户确认即被执行。失败信号来自用户纠正、用户点踩与事后审计三类外部反馈，"
            "根因在 Harness 的流程缺失，不在模型能力——换更强的模型也照样犯。"
        ),
        "change_contract": {
            "expected_fix": [
                "高风险调用（删除、force push、DROP/TRUNCATE、无 WHERE 的 DELETE、破坏性 Shell）执行前被挂起并要求确认",
                "确认 token 一次性且绑定具体操作与参数，不能复用到其他调用",
            ],
            "potential_regressions": [
                "read_file/write_file 等低风险调用被额外挂起",
                "用户已确认的操作仍被拒绝执行",
                "确认 token 可重复使用或跨操作复用",
            ],
        },
    }


GATE_TEMPLATE = r'''"""候选模块：高风险工具调用确认门禁。

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
'''

REJECTED_GATE_TEMPLATE = GATE_TEMPLATE.replace(
    'VERSION = "1.1.0-candidate"', 'VERSION = "1.0.1-rejected"'
).replace(
    '''def classify(tool_name, args=None):
    """返回挂起原因；返回 None 表示低风险，可直接执行。"""''',
    '''def classify(tool_name, args=None):
    """故意过宽的反例：放行一切调用，保留为已拒绝候选。"""''',
).replace(
    '''    args = args or {}
    if tool_name == "delete_file":''',
    '''    args = args or {}
    return None
    if tool_name == "delete_file":''',
)

# 稳定版 dispatch 的最小接入点（提案 diff，验证不依赖它落盘）
OLD_DISPATCH_HEAD = "def dispatch(tool_name, args=None, *, env=None):"
NEW_DISPATCH_HEAD = "def dispatch(tool_name, args=None, *, env=None, confirm_token=None):"
OLD_DISPATCH_RETURN = '    return {"tool": tool_name, "args": args, "result": TOOLS[tool_name](env, **args)}'
NEW_DISPATCH_RETURN = (
    "    from confirmation_gate import dispatch as gated_dispatch  # 最小接入：先过确认门禁\n"
    "    def execute(name, call_args):\n"
    '        return {"tool": name, "args": call_args, "result": TOOLS[name](env, **call_args)}\n'
    "    return gated_dispatch(tool_name, args, execute=execute, confirm_token=confirm_token)"
)


def _integration_diff(stable_source: str) -> str:
    """生成对稳定版调度器的最小接入 diff（仅作提案，不修改 stable/）。"""
    integrated = stable_source.replace(OLD_DISPATCH_HEAD, NEW_DISPATCH_HEAD, 1)
    integrated = integrated.replace(OLD_DISPATCH_RETURN, NEW_DISPATCH_RETURN, 1)
    if integrated == stable_source:
        raise ValueError("稳定版 dispatch 结构与预期不符，无法生成接入 diff")
    return "".join(difflib.unified_diff(
        stable_source.splitlines(keepends=True),
        integrated.splitlines(keepends=True),
        fromfile="stable/tool_dispatcher.py",
        tofile="candidate/tool_dispatcher.py",
    ))


def candidate_from_gate(
    gate_source: str,
    *,
    integration_diff: str = "",
    impact_prediction: Dict[str, Any] | None = None,
    generator_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """把生成的门禁模块与溯源信息打包成可评审候选。"""
    diff = "".join(difflib.unified_diff(
        [],
        gate_source.splitlines(keepends=True),
        fromfile="/dev/null",
        tofile="candidate/confirmation_gate.py",
    ))
    added = sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())
    return {
        "module": "confirmation_gate.py",
        "source": gate_source,
        "diff": diff,
        "integration_diff": integration_diff,
        "changed": bool(gate_source.strip()),
        "impact_prediction": impact_prediction or {},
        "generator_metadata": generator_metadata or {},
        "source_sha256": sha256_text(gate_source),
        "patch_size": {"added_lines": added, "deleted_lines": 0, "changed_lines": added},
    }


def generate_candidate(stable_source: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    """确定性对照候选：不触碰 stable/，只产出新模块源码。"""
    if not diagnosis.get("change_required"):
        return candidate_from_gate("", generator_metadata={"generator": "deterministic", "api_calls": 0})
    return candidate_from_gate(
        GATE_TEMPLATE,
        integration_diff=_integration_diff(stable_source),
        impact_prediction={
            "unconfirmed_high_risk_executions": {"before": "直接执行", "after": 0},
            "low_risk_calls_suspended": {"before": 0, "after": 0},
        },
        generator_metadata={"generator": "deterministic", "model": None, "api_calls": 0},
    )


def generate_rejected_control(stable_source: str, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
    """故意过宽的反例：门禁存在但放行一切，保留为已拒绝候选。"""
    return candidate_from_gate(
        REJECTED_GATE_TEMPLATE,
        integration_diff=_integration_diff(stable_source),
        impact_prediction={"unconfirmed_high_risk_executions": {"after": "仍然直接执行"}},
        generator_metadata={"generator": "negative_control", "api_calls": 0},
    )


def _safe_ast(source: str) -> bool:
    """执行前的快速预筛：只允许白名单导入，禁止危险内建调用。"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] not in ALLOWED_IMPORTS for alias in node.names):
                return False
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                return False
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FORBIDDEN_CALLS
        ):
            return False
    return True


def _load_gate(source: str) -> Dict[str, Any]:
    """在干净命名空间中加载候选模块（此前必须通过 AST 预筛）。"""
    namespace: Dict[str, Any] = {"__name__": "candidate_confirmation_gate"}
    exec(compile(source, "candidate/confirmation_gate.py", "exec"), namespace)
    return namespace


def _check_contract(gate: Dict[str, Any]) -> bool:
    return all(
        callable(gate.get(name))
        for name in ("requires_confirmation", "issue_confirmation", "dispatch")
    )


def _make_executor(env: Dict[str, Any], calls: List[tuple]):
    """注入给候选的执行器：在内存模拟环境上回放稳定版调度。"""
    def execute(tool_name, args):
        calls.append((tool_name, args))
        return STABLE.dispatch(tool_name, args, env=env)
    return execute


def _replay_case(gate: Dict[str, Any], case: Dict[str, Any]) -> Tuple[bool, str]:
    """回放单条用例：挂起/拒绝时执行器绝不允许被调用。"""
    env = STABLE.default_env()
    calls: List[tuple] = []
    execute = _make_executor(env, calls)
    last_token = None
    for step in case["steps"]:
        token = step.get("confirm_token")
        if step.get("confirm"):
            last_token = gate["issue_confirmation"](step["tool"], step.get("args"))
            token = last_token
        elif step.get("confirm_for"):
            other = step["confirm_for"]
            last_token = gate["issue_confirmation"](other["tool"], other.get("args"))
            token = last_token
        elif step.get("use_token") == "previous":
            token = last_token
        before = len(calls)
        outcome = gate["dispatch"](
            step["tool"], step.get("args"), execute=execute, confirm_token=token
        )
        expect = step["expect"]
        status = outcome.get("status") if isinstance(outcome, dict) else None
        if status != expect:
            return False, f"{case['id']}: 期望 {expect}，实际 {status}"
        if expect in ("pending_confirmation", "rejected") and len(calls) != before:
            return False, f"{case['id']}: 未确认/被拒绝的调用竟然执行了"
        if expect == "executed" and len(calls) != before + 1:
            return False, f"{case['id']}: 已确认的调用未被执行"
    return True, ""


def _replay_all(gate: Dict[str, Any], cases: Iterable[Dict[str, Any]]) -> bool:
    try:
        return all(_replay_case(gate, case)[0] for case in cases)
    except Exception:
        return False


def _check_single_use(gate: Dict[str, Any]) -> bool:
    """确认 token 的一次性与绑定性：用后作废，第二次调用不得执行。"""
    try:
        env = STABLE.default_env()
        calls: List[tuple] = []
        execute = _make_executor(env, calls)
        path = "tmp/cache-0417.tmp"
        token = gate["issue_confirmation"]("delete_file", {"path": path})
        first = gate["dispatch"]("delete_file", {"path": path}, execute=execute, confirm_token=token)
        second = gate["dispatch"]("delete_file", {"path": path}, execute=execute, confirm_token=token)
        return (
            first.get("status") == "executed"
            and second.get("status") != "executed"
            and len(calls) == 1
            and path not in env["files"]
        )
    except Exception:
        return False


def validate_candidate(
    candidate_source: str,
    boundary_cases: Iterable[Dict[str, Any]],
    retention_cases: Iterable[Dict[str, Any]],
) -> Dict[str, bool]:
    """模型外发布门槛：AST 静态检查 + 边界集/保留集回放，失败即关闭。"""
    checks = {name: False for name in CHECK_NAMES}
    try:
        if len(candidate_source.encode("utf-8")) > MAX_SOURCE_BYTES:
            return checks
    except (UnicodeError, AttributeError):
        return checks
    try:
        compile(candidate_source, "candidate/confirmation_gate.py", "exec")
    except (SyntaxError, ValueError, TypeError):
        return checks
    checks["static_compile"] = True
    if not _safe_ast(candidate_source):
        return checks
    checks["security_scan"] = True
    try:
        gate = _load_gate(candidate_source)
    except Exception:
        return checks
    checks["gate_contract"] = _check_contract(gate)
    if not checks["gate_contract"]:
        return checks
    checks["boundary_replay"] = _replay_all(gate, boundary_cases)
    checks["retention_replay"] = _replay_all(gate, retention_cases)
    checks["confirmation_single_use"] = _check_single_use(gate)
    return checks


def release_manifest(
    stable_source: str,
    candidate: Dict[str, Any],
    diagnosis: Dict[str, Any],
    checks: Dict[str, bool],
    *,
    provenance: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    accepted = candidate.get("changed", False) and bool(checks) and all(checks.values())
    failed = [name for name, passed in checks.items() if not passed]
    contract = diagnosis.get("change_contract", {})
    return {
        "artifact_type": "harness_confirmation_gate_module",
        "failure_cluster": diagnosis.get("patterns", []),
        "source_trajectories": diagnosis.get("source_trajectories", []),
        "inferred_root_cause": diagnosis.get("reason"),
        "target_component": diagnosis.get("target_component"),
        "target_file": diagnosis.get("target"),
        "candidate_module": candidate.get("module", "confirmation_gate.py"),
        "code_diff": candidate.get("diff", ""),
        "integration_diff": candidate.get("integration_diff", ""),
        "impact_prediction": candidate.get("impact_prediction", {}),
        "expected_fix": contract.get("expected_fix", []),
        "potential_regressions": contract.get("potential_regressions", []),
        "stable_version": _short_sha(stable_source),
        "stable_sha256": sha256_text(stable_source),
        "candidate_version": _short_sha(candidate.get("source", "")),
        "candidate_sha256": sha256_text(candidate.get("source", "")),
        "rollback_version": _short_sha(stable_source),
        "rollback_sha256": sha256_text(stable_source),
        # 兼容字段：供只读旧版 demo 输出的读者使用
        "diff": candidate.get("diff", ""),
        "patch_size": candidate.get("patch_size", {}),
        "checks": checks,
        "failed_checks": failed,
        "canary_gate": {
            "eligible": accepted,
            "scope": "影子流量灰度；稳定版调度器保持不变",
            "rollback_trigger": "任一高风险调用未确认即执行，或低风险调用被挂起",
        },
        "rollback_gate": {
            "rollback_version": _short_sha(stable_source),
            "artifact_hash_matches_stable": True,
        },
        "provenance": provenance or candidate.get("generator_metadata", {}),
        "decision": "release_to_canary" if accepted else "reject_candidate",
        "rejection_reason": None if accepted else (
            "candidate is empty or unchanged" if not candidate.get("changed")
            else "failed gates: " + ", ".join(failed)
        ),
    }


def write_candidate(candidate_source: str, path: Path) -> None:
    """只写候选制品路径，绝不覆盖稳定模块。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(candidate_source, encoding="utf-8")
def generate_synthetic_perturbations(trajectories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate synthetic edge-case perturbations (null args, whitespace, missing fields) for safety verifier testing."""
    perturbed: List[Dict[str, Any]] = []
    for traj in trajectories:
        item = dict(traj)
        tool_name = item.get("tool_name", "")
        args = item.get("args")

        # Perturbation 1: null args dictionary
        item_null_args = dict(item)
        item_null_args["args"] = None
        item_null_args["id"] = f"{item.get('id', 'traj')}_null_args"
        perturbed.append(item_null_args)

        # Perturbation 2: empty tool name with risk args
        item_empty_tool = dict(item)
        item_empty_tool["tool_name"] = "  "
        item_empty_tool["id"] = f"{item.get('id', 'traj')}_empty_tool"
        perturbed.append(item_empty_tool)

        # Perturbation 3: non-dict args
        item_list_args = dict(item)
        item_list_args["args"] = [tool_name, args]
        item_list_args["id"] = f"{item.get('id', 'traj')}_list_args"
        perturbed.append(item_list_args)

    return perturbed
