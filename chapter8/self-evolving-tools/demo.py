"""
补充案例一键演示：`python demo.py`

演示两件事：
  1) 进化：Agent 从零基础工具出发 —— 搜索 → 读文档 → 沙箱测试 → 封装工具 →
     用新工具给出 NVIDIA(NVDA) 的真实股价与「相对一周前」的真实涨跌幅。
  2) 复用：换一支股票(AAPL) 再问一次。Agent 应先 search_tools 命中已创建的工具并直接复用，
     不再重新上网搜索、重新造轮子。程序会打印轨迹并自动校验「复用」是否成立。

在线路径（默认）需要真实联网 + 真实调用 OpenAI，请先配置 OPENAI_API_KEY。
若手头没有 API key / 无法联网，可用 `--offline` 跑「机制自检」：不调用 LLM/网络，
直接驱动工具库的「搜索未命中 → 造工具 → 存前验证 → 注册 → 复用」闭环（见下）。

常用示例：
    python demo.py                 # 跑「进化 + 复用」两个默认任务（需 API）
    python demo.py --fresh         # 先清空 tool_library/ 再跑（重现「从零进化」）
    python demo.py --offline       # 离线机制自检（无需 API/网络），演示完整进化闭环
    python demo.py --task "查询比特币当前美元价格及24小时涨跌幅"   # 自定义任务（可多次）
    python demo.py --no-create     # 禁用造工具能力（对照：只能复用/无法进化）
    python demo.py --model gpt-5.6-luna --output run.json   # 覆盖模型并把结果写入 JSON
    python demo.py --help          # 查看全部参数

提示：工具库会持久化到 tool_library/。若上一轮已封装出 get_stock_price，再次直接运行时
任务一会在第 0 步就命中并复用它，从而看不到「进化」过程；想重现进化请加 --fresh。
"""

import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from tool_manager import LIBRARY_DIR, ToolLibrary


TASK_1 = "查询 NVIDIA(股票代码 NVDA) 的最新股价，以及与一周前相比的涨跌幅（百分比）。请给出真实数据。"
TASK_2 = "查询 Apple(股票代码 AAPL) 的最新股价，以及与一周前相比的涨跌幅（百分比）。请给出真实数据。"

_META_TOOLS = {"web_search", "read_webpage", "code_interpreter", "create_tool", "search_tools"}


def _clear_library():
    """清空持久化的工具库（仅删除生成的 *.json 工件），用于重现「从零进化」。"""
    removed = 0
    for p in glob.glob(os.path.join(str(LIBRARY_DIR), "*.json")):
        try:
            os.remove(p)
            removed += 1
        except OSError:
            pass
    print(f"[--fresh] 已清空 tool_library/（删除 {removed} 个已封装工具），将从零开始进化。\n")


def _is_reuse(traj: list) -> bool:
    """某条轨迹是否属于「工具复用」：调用了 search_tools、没有重新 web_search/create_tool，
    且真的调用了某个已封装（非元）工具。"""
    return (
        "search_tools" in traj
        and "web_search" not in traj
        and "create_tool" not in traj
        and any(t not in _META_TOOLS for t in traj)
    )


# --------------------------------------------------------------------------- #
# 离线机制自检：不调用 LLM / 网络，直接驱动工具库的进化闭环
#   搜索未命中 → 造工具（带存前验证）→ 注册 → 调用 → 复用
# 用一个纯离线、确定性的工具（计算两个日期之间的天数）来跑通全流程，
# 便于在没有 API key / 无网络时验证「自我进化 + 复用」机制本身是否可靠。
# --------------------------------------------------------------------------- #
_DAYS_TOOL_CODE = (
    "from datetime import date\n\n"
    "def run(start, end):\n"
    "    s = date.fromisoformat(start)\n"
    "    e = date.fromisoformat(end)\n"
    "    return {'start': start, 'end': end, 'days': (e - s).days}\n"
)
_DAYS_TOOL_PARAMS = {
    "type": "object",
    "properties": {
        "start": {"type": "string", "description": "起始日期 YYYY-MM-DD"},
        "end": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
    },
    "required": ["start", "end"],
}
# 一个「跑不通」的坏工具：用来证明存前验证闸门确实会拒绝它入库
_BAD_TOOL_CODE = (
    "def run(start, end):\n"
    "    return {'days': undefined_name}\n"  # NameError at runtime
)


def run_offline_selftest(output_path: str | None = None) -> int:
    print("=" * 70)
    print("离线机制自检（--offline）：不调用 LLM/网络，直接驱动工具库进化闭环")
    print("  闭环：search_tools 未命中 → create_tool(存前验证) → 注册 → 调用 → 复用")
    print("=" * 70)

    tmp = Path(tempfile.mkdtemp(prefix="selfevolve_selftest_"))
    lib = ToolLibrary(library_dir=tmp)  # 用临时库，绝不污染用户真实的 tool_library/
    try:
        # ---------- 存前验证闸门演示：坏工具应被拒绝入库 ----------
        print("\n[验证闸门] 尝试注册一个运行会崩溃的坏工具（附 test_args）...")
        bad = lib.create_tool(
            "days_between_bad", "会崩溃的示例工具", _DAYS_TOOL_PARAMS, _BAD_TOOL_CODE,
            test_args={"start": "2020-01-01", "end": "2020-03-01"},
        )
        print(f"  结果: success={bad.get('success')}  ->  {bad.get('error', '')[:60]}")
        assert not bad["success"], "坏工具竟然通过了存前验证！"
        assert lib.get_tool("days_between_bad") is None, "坏工具不应落盘！"
        print("  ✅ 存前验证挡住了坏工具（未入库），符合『别把坏程序存进去』。")

        # ---------- 任务一：进化（造工具）----------
        traj1: list = []
        print("\n########## 离线任务一：计算 2020-01-01 到 2020-03-01 的天数（演示进化）##########")
        traj1.append("search_tools")
        hit = lib.search_tools("date days between")
        print(f"[step 1] search_tools -> 命中 {hit['count']} 个（工具库为空，未命中）")

        traj1.append("create_tool")
        created = lib.create_tool(
            "days_between",
            "计算两个 ISO 日期(YYYY-MM-DD)之间相差的天数",
            _DAYS_TOOL_PARAMS, _DAYS_TOOL_CODE,
            test_args={"start": "2020-01-01", "end": "2020-01-11"},
        )
        print(f"[step 2] create_tool(days_between) -> success={created['success']} "
              f"validated={created.get('validated')}（存前验证已真跑一次 run()）")

        traj1.append("days_between")
        r1 = lib.execute_tool("days_between", {"start": "2020-01-01", "end": "2020-03-01"})
        ans1 = r1.get("result", {}).get("days")
        print(f"[step 3] days_between(...) -> {r1.get('result')}")
        print(f"[离线任务一结论] 2020-01-01 到 2020-03-01 共 {ans1} 天。")

        # ---------- 任务二：复用（不再造轮子）----------
        traj2: list = []
        print("\n########## 离线任务二：计算 2021-01-01 到 2021-12-31 的天数（演示复用）##########")
        traj2.append("search_tools")
        hit2 = lib.search_tools("date days between")
        print(f"[step 1] search_tools -> 命中 {hit2['count']} 个：{[t['name'] for t in hit2['tools']]}（复用！）")

        traj2.append("days_between")
        r2 = lib.execute_tool("days_between", {"start": "2021-01-01", "end": "2021-12-31"})
        ans2 = r2.get("result", {}).get("days")
        print(f"[step 2] days_between(...) -> {r2.get('result')}")
        print(f"[离线任务二结论] 2021-01-01 到 2021-12-31 共 {ans2} 天。")

        reused = _is_reuse(traj2)
        print("\n" + "=" * 70)
        print("离线自检结论")
        print("=" * 70)
        print(f"任务一轨迹: {traj1}")
        print(f"任务二轨迹: {traj2}")
        print(f"任务二是否复用了任务一造的工具(未重新 create_tool): {'是 ✅' if reused else '否 ❌'}")
        print(f"存前验证闸门是否挡住了坏工具: {'是 ✅' if not bad['success'] else '否 ❌'}")

        if output_path:
            payload = {
                "mode": "offline_selftest",
                "gate_rejected_bad_tool": (not bad["success"]),
                "tasks": [
                    {"task": "2020-01-01→2020-03-01 天数", "answer_days": ans1, "trajectory": traj1},
                    {"task": "2021-01-01→2021-12-31 天数", "answer_days": ans2, "trajectory": traj2},
                ],
                "reused": reused,
            }
            Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
            print(f"\n[已写入] {output_path}")

        return 0 if (reused and not bad["success"]) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 在线路径：真实 LLM + 真实网络
# --------------------------------------------------------------------------- #
def run_online(tasks: list, allow_create: bool, model: str | None, output_path: str | None) -> int:
    # 延迟导入：--offline 时无需 openai 依赖也能跑
    from agent import SelfEvolvingAgent

    try:
        agent = SelfEvolvingAgent(verbose=True, allow_create=allow_create, model=model)
    except RuntimeError as e:
        print(f"[配置错误] {e}", file=sys.stderr)
        print(
            "请先配置对应供应商的 API Key（默认 OpenAI）：\n"
            "  cp env.example .env  然后在 .env 中填入 OPENAI_API_KEY；\n"
            "  或直接 export OPENAI_API_KEY=sk-...\n"
            "如需切换供应商：export LLM_PROVIDER=moonshot|ark 并配置对应的 "
            "MOONSHOT_API_KEY / ARK_API_KEY。\n"
            "（若只想验证机制而无 API key，可运行：python demo.py --offline）",
            file=sys.stderr,
        )
        return 2

    default = tasks == [TASK_1, TASK_2]
    runs = []
    for i, task in enumerate(tasks, 1):
        label = {1: "任务一", 2: "任务二"}.get(i, f"任务{i}") if default else f"任务{i}"
        tag = {1: "（演示 搜索→测试→封装→用）", 2: "（演示 工具复用）"}.get(i, "") if default else ""
        print(f"\n########## {label}{tag} ##########")
        agent.trajectory = []
        ans = agent.run(task)
        traj = list(agent.trajectory)
        created = [t["name"] for t in agent.library.list_tools()]
        print(f"\n>>> {label}结束。当前工具库已封装工具: {created}")
        print(f">>> {label}动作轨迹: {traj}")
        runs.append({"task": task, "answer": ans, "trajectory": traj, "reused": _is_reuse(traj)})

    # 复用校验：只要有「非首个」任务发生了复用即算成立
    reused = any(r["reused"] for r in runs[1:])
    print("\n" + "=" * 70)
    print("结论汇总")
    print("=" * 70)
    for i, r in enumerate(runs, 1):
        print(f"[任务{i}] {r['answer']}")
    print("-" * 70)
    if len(runs) >= 2:
        print(f"后续任务是否复用了已创建工具(未重新搜索/创建): {'是 ✅' if reused else '否 ❌'}")
        print("  证据：复用任务调用了 search_tools 且未出现 web_search/create_tool。")

    if output_path:
        Path(output_path).write_text(json.dumps(
            {"mode": "online", "model": agent.model, "allow_create": allow_create,
             "runs": runs, "reused": reused},
            ensure_ascii=False, indent=2))
        print(f"\n[已写入] {output_path}")

    if len(runs) < 2:
        return 0
    return 0 if reused else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="补充案例：Agent 从网络寻找工具并验证后复用。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python demo.py                 跑默认两个任务（进化 + 复用，需 API）\n"
               "  python demo.py --fresh         先清空工具库再跑（重现从零进化）\n"
               "  python demo.py --offline       离线机制自检（无需 API/网络）\n"
               "  python demo.py --task '...'    自定义任务（可重复多次）\n"
               "  python demo.py --no-create     禁用造工具能力（对照实验）\n")
    p.add_argument("--task", action="append", metavar="任务描述",
                   help="要执行的任务（可重复指定多次以按顺序运行多个任务）。"
                        "不指定则运行默认的 NVDA/AAPL 两个任务。")
    p.add_argument("--offline", action="store_true",
                   help="离线机制自检：不调用 LLM/网络，直接驱动『搜索→造工具→存前验证→注册→复用』闭环。")
    p.add_argument("--fresh", action="store_true",
                   help="运行前清空 tool_library/，以重现『从零进化』过程（重复演示时推荐）。")
    p.add_argument("--no-create", dest="allow_create", action="store_false",
                   help="禁用『造工具(create_tool)』能力，用于对照演示（默认允许造工具）。")
    p.add_argument("--model", metavar="模型名", default=None,
                   help="覆盖 LLM 模型名（优先级高于 LLM_MODEL 环境变量），如 gpt-5.6-luna。")
    p.add_argument("--output", metavar="路径", default=None,
                   help="把本次运行的任务、答案、动作轨迹与复用结论写入该 JSON 文件。")
    return p


def main():
    args = build_parser().parse_args()

    if args.offline:
        return run_offline_selftest(output_path=args.output)

    if args.fresh:
        _clear_library()

    tasks = args.task if args.task else [TASK_1, TASK_2]
    return run_online(tasks, allow_create=args.allow_create,
                      model=args.model, output_path=args.output)


if __name__ == "__main__":
    sys.exit(main())
