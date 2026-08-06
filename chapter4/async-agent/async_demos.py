"""离线演示：不依赖任何 LLM / API key，直接驱动异步运行时的底层原语。

`demo.py` 里的四个「场景」需要真实 LLM 做决策；本模块则把实验 4-6 的三项核心
异步能力单独拎出来，用可测量、可复现的方式演示，**无需联网、无需 API key**：

  - demo_parallel  ：并行 vs 串行工具调用的【墙钟时间】对比（真实测量，打印加速比）。
  - demo_interrupt ：长任务运行中被【打断/取消】，随后系统【恢复】并接受新任务。
  - demo_state     ：Agent 状态【检查点持久化】到磁盘，再【跨会话恢复】并校验。

这三个演示共同回答「异步到底带来了什么」——用数字和状态变化说话，而不只是措辞。
"""

from __future__ import annotations

import asyncio
import datetime
import os
import time

from runtime import AgentRuntime, format_log
from events import Event, EventType
from tasks import TaskManager
import tasks


class Logger:
    """与 runtime 同款的彩色时间戳日志器（相对本次演示起点计时）。"""

    def __init__(self) -> None:
        self.t0 = time.time()

    def __call__(self, source: str, text: str) -> None:
        print(format_log(self.t0, source, text), flush=True)


def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78, flush=True)


# ============================ 1. 并行 vs 串行 ============================

# 一组相互独立的【只读感知工具】（读文件 / 搜索 / 查库 / 向量检索）。
# 只读、无副作用，因此可以安全地并行——这正是书中「感知工具天然适合并行」的落点。
_PERCEIVE_TOOLS = [
    ("read_config.json", 0.8),
    ("web_search(‘异步 Agent’)", 1.2),
    ("db_query(orders)", 1.5),
    ("vector_lookup(memory)", 1.0),
]


async def _perceive(name: str, latency: float, log: Logger) -> tuple[str, float, float]:
    """模拟一次带 I/O 延迟的只读感知调用；返回 (名称, 标称延迟, 实测耗时)。"""
    t0 = time.time()
    log("TOOL", f"→ {name} 启动（模拟 I/O 耗时 {latency:.1f}s）")
    await asyncio.sleep(latency)
    dt = time.time() - t0
    log("TOOL", f"✓ {name} 完成（实测 {dt:.2f}s）")
    return name, latency, dt


async def demo_parallel() -> None:
    banner("能力一｜并行工具调用：并行 vs 串行的墙钟时间对比")
    log = Logger()
    log("SYSTEM", "有 4 个相互独立的只读感知工具需要调用（无副作用，可安全并行）。")

    # —— 串行：一个 await 完再 await 下一个 ——
    log("SYSTEM", "\033[0m[串行] 逐个 await（同步 ReAct 的默认做法）……")
    seq_start = time.time()
    for name, lat in _PERCEIVE_TOOLS:
        await _perceive(name, lat, log)
    seq_total = time.time() - seq_start

    # —— 并行：一次性发起，asyncio.gather 并发等待 ——
    log("SYSTEM", "\033[0m[并行] 一次性发起，asyncio.gather 并发等待……")
    par_start = time.time()
    await asyncio.gather(*[_perceive(name, lat, log) for name, lat in _PERCEIVE_TOOLS])
    par_total = time.time() - par_start

    slowest = max(lat for _, lat in _PERCEIVE_TOOLS)
    speedup = seq_total / par_total if par_total else float("inf")

    print("\n  ── 结果对比 ─────────────────────────────────────────────")
    print(f"  {'工具':<26}{'标称延迟':>10}")
    for name, lat in _PERCEIVE_TOOLS:
        print(f"  {name:<26}{lat:>8.1f}s")
    print("  ─────────────────────────────────────────────────────────")
    print(f"  {'串行总耗时（Σ 各工具）':<26}{seq_total:>8.2f}s")
    print(f"  {'并行总耗时（gather）':<26}{par_total:>8.2f}s")
    print(f"  {'并行理论下界（最慢单个）':<26}{slowest:>8.2f}s")
    print(f"  {'加速比 = 串行 / 并行':<26}{speedup:>8.2f}x")
    print("  ─────────────────────────────────────────────────────────")
    print("  结论：独立的只读调用并行化后，墙钟时间由「求和」降到「取最大」。\n")


# ============================ 2. 打断 / 取消 / 恢复 ============================

async def demo_interrupt() -> None:
    banner("能力二｜打断与取消：长任务运行中被打断，随后系统恢复")
    tasks.TICK_REAL = 0.15  # 本演示放慢节奏，留出「跑到一半再打断」的时间窗口
    log = Logger()
    completed: list = []

    async def on_complete(state) -> None:
        completed.append(state)

    tm = TaskManager(on_complete=on_complete, log=log)

    # 1) 并行启动三个后台异步任务
    log("SYSTEM", "启动三个并行后台分析任务（fast/mid/slow）……")
    for cmd in ["python analyze_fast.py", "python analyze_mid.py", "python analyze_slow.py"]:
        tm.start(cmd)

    # 2) 运行期间用户即时提问 —— 后台任务不被阻塞
    await asyncio.sleep(1.0)
    now = datetime.datetime.now().strftime("%H:%M:%S")
    log("USER", "（即时提问）现在几点了？")
    log("AGENT", f"现在 {now}。三个后台任务仍在并行推进，未被这次提问阻塞。")

    # 3) 跑到中途，用户发出打断 —— 立即取消所有在跑的任务
    await asyncio.sleep(1.0)
    log("USER", "（打断）取消")
    cancelled = tm.cancel_all()
    await asyncio.sleep(0.05)  # 让 CancelledError 在各协程内落地
    log("SYSTEM", f"已执行打断：取消了 {cancelled}（进度在被取消处冻结）")

    print("\n  ── 打断后各任务状态（进度冻结在中途）───────────────────")
    print(f"  {'task_id':<8}{'命令':<26}{'状态':<12}{'进度':>6}")
    for s in tm.all_states():
        print(f"  {s.task_id:<8}{s.command:<26}{s.status:<12}{s.progress:>5.0f}%")
    print("  ─────────────────────────────────────────────────────────")

    # 4) 恢复：executor 依然健康，接受并跑完一个新任务
    log("SYSTEM", "打断处理完毕，系统恢复空闲，可继续接受新任务……")
    fresh = tm.start("python re_run_summary.py")
    await fresh._task
    log("AGENT", f"已从打断中恢复，新任务 {fresh.task_id} 正常完成："
                 f"{completed[-1].result[:36]}……")
    print("  结论：打断只冻结被取消的任务，运行时本身无损，可立即继续工作。\n")


# ============================ 3. 状态检查点：持久化 / 恢复 ============================

def _seed_trajectory(rt: AgentRuntime) -> None:
    """给运行时灌入一段「已发生」的对话轨迹，模拟会话进行到一半。"""
    rt._append(Event(EventType.USER_INPUT,
                     message={"role": "user", "content": "分析今天的日志并总结异常"},
                     label="用户消息：分析日志"))
    rt._append(Event(EventType.AGENT_TOOL_CALL,
                     message={"role": "assistant", "content": "好的，我这就在后台启动分析。",
                              "tool_calls": [{"id": "call_1", "type": "function",
                                              "function": {"name": "run_terminal_command",
                                                           "arguments": '{"command": "python analyze_fast.py"}'}}]},
                     label="调用工具 run_terminal_command"))
    rt._append(Event(EventType.TOOL_RESULT,
                     message={"role": "tool", "tool_call_id": "call_1",
                              "content": "命令已在后台异步启动。task_id=T1。"},
                     label="工具结果 run_terminal_command"))


async def demo_state() -> None:
    banner("能力三｜状态管理：检查点持久化与跨会话恢复")
    tasks.TICK_REAL = 0.15
    ckpt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)
    path = os.path.join(ckpt_dir, "agent_state.json")

    # —— 会话 A：产生一段轨迹 + 两个仍在运行的后台任务，然后落盘 ——
    log = Logger()
    log("SYSTEM", "会话 A 开始：构造轨迹并启动两个后台任务……")
    rt_a = AgentRuntime(client=None, model="demo-offline")
    rt_a._t0 = log.t0  # 让两个运行时共用同一时间基准，便于观察
    _seed_trajectory(rt_a)
    rt_a.tasks.start("python analyze_fast.py")   # 进行中
    rt_a.tasks.start("python analyze_slow.py")   # 进行中
    await asyncio.sleep(1.2)  # 让进度累积到中途

    before_traj = len(rt_a.trajectory)
    before_tasks = {s.task_id: (s.status, s.progress) for s in rt_a.tasks.all_states()}
    rt_a.save_checkpoint(path)

    # 模拟进程退出：取消掉活着的协程
    rt_a.tasks.cancel_all()
    await asyncio.sleep(0.05)
    log("SYSTEM", "会话 A 结束（进程退出，内存中的运行时已销毁）。")

    # —— 会话 B：全新运行时，从磁盘恢复 ——
    log("SYSTEM", "会话 B 开始：新建空运行时，从检查点恢复……")
    rt_b = AgentRuntime(client=None, model="demo-offline")
    rt_b._t0 = log.t0
    data = rt_b.load_checkpoint(path)

    after_traj = len(rt_b.trajectory)
    msgs = rt_b.build_messages()  # 证明恢复后能重建可喂给 LLM 的上下文

    print("\n  ── 恢复校验 ─────────────────────────────────────────────")
    print(f"  轨迹事件数     保存前 {before_traj}  ->  恢复后 {after_traj}  "
          f"[{'一致 ✓' if before_traj == after_traj else '不一致 ✗'}]")
    print(f"  可重建 LLM 上下文消息 {len(msgs)} 条（system + 轨迹回放）")
    print(f"  {'task_id':<8}{'命令':<26}{'保存前进度':>10}  {'恢复后状态':<12}{'进度':>6}")
    for rec in data["tasks"]:
        tid = rec["task_id"]
        before = before_tasks.get(tid, ("-", 0.0))
        st = rt_b.tasks.query(tid)
        print(f"  {tid:<8}{rec['command']:<26}{before[1]:>9.0f}%  "
              f"{st.status:<12}{st.progress:>5.0f}%")
    print("  ─────────────────────────────────────────────────────────")
    print(f"  检查点文件：{path}")
    print("  结论：轨迹与任务进度完整落盘并跨会话还原；运行中的任务被标记为 suspended，")
    print("        保留了最后已知进度，供上层决定「重跑」还是「按进度续跑」。\n")


# 供 demo.py 复用的离线演示注册表
OFFLINE_DEMOS = {
    "parallel": demo_parallel,
    "interrupt": demo_interrupt,
    "state": demo_state,
}
