"""
event_loop_demo.py —— 事件驱动 Agent 的端到端演示（单进程、可离线运行）

本章"事件驱动的异步 Agent"一节指出：真正的"主动服务"不仅需要 Agent 能定时
检查世界，更需要世界能主动通知 Agent。本脚本用最小的代码把这一点跑起来——

  1. 注册若干"事件触发器"（trigger source），每个触发器在后台线程里运行，
     在事件真正发生的那一刻把一个结构化 Event 推入统一的事件队列：
       - 一次性定时器 OneShotTimer      —— 对应书中 set_timer 的"一次性定时器"
       - 循环定时器   RecurringTimer     —— 对应书中 set_timer 的"循环定时器"
       - 文件监听     FileWatchTrigger   —— 对应 n8n 等平台的文件变更触发器
  2. 事件循环 EventLoop 从队列里逐个取出事件，唤醒 Agent 处理——这正是
     "Agent 注册、外部触发"的完整闭环：注册时声明关心什么事件，触发时被异步唤醒。

与需要起 HTTP 服务器的 server.py / client.py 不同，本脚本在单个进程里同时扮演
"外部世界"和"Agent"，因此适合用来直观演示事件驱动的行为。

离线模式（--mock）：不调用大模型，用一个"模拟动作"打印 Agent 被唤醒后的处理
过程，可在没有 API Key 的环境下观察完整的触发→唤醒→处理闭环。
真实模式（默认）：接入 EventTriggeredAgent，由大模型真正处理每个事件。

用法示例：
    python event_loop_demo.py --mock                       # 离线演示全部触发器
    python event_loop_demo.py --mock --trigger timer       # 只演示一次性定时器
    python event_loop_demo.py --mock --trigger recurring --interval 3 --duration 12
    python event_loop_demo.py --trigger file --watch-dir ./watched   # 真实 Agent 处理文件事件
"""

import os
import sys
import time
import queue
import logging
import argparse
import threading
from datetime import datetime
from typing import Optional, Callable

from event_types import Event, EventType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("event_loop")


# ============================================================================
# 事件触发器（trigger source）
# ============================================================================

class TriggerSource(threading.Thread):
    """事件触发器基类：在后台线程中运行，把事件推入共享的事件队列。

    注册（register）体现在实例化并 start()；触发（fire）体现在 run() 中
    满足条件时调用 self.emit(event)。这与书中"注册时由 Agent 主动调用工具、
    触发时由外部事件异步回调"的两个时刻一一对应。
    """

    def __init__(self, name: str, event_queue: "queue.Queue[Event]"):
        super().__init__(name=name, daemon=True)
        self.event_queue = event_queue
        self._stop = threading.Event()

    def emit(self, event: Event):
        """触发：把事件推入事件队列，唤醒事件循环。"""
        logger.info(f"⚡ [{self.name}] 触发事件 -> {event.event_type.value}: {event.content}")
        self.event_queue.put(event)

    def stop(self):
        self._stop.set()


class OneShotTimer(TriggerSource):
    """一次性定时器：延迟 delay 秒后触发一次 timer_trigger 事件。

    对应书中"用户要求给 DMV 打电话，当前是周六，Agent 设置'下周一上午 10:00
    致电 DMV'"这类有明确时间点的任务。
    """

    def __init__(self, event_queue, delay: float, content: str, timer_id: str = "oneshot"):
        super().__init__(name=f"OneShotTimer({timer_id})", event_queue=event_queue)
        self.delay = delay
        self.content = content
        self.timer_id = timer_id

    def run(self):
        logger.info(f"⏱️  [{self.name}] 已注册：{self.delay:.0f} 秒后触发")
        if self._stop.wait(self.delay):
            return
        self.emit(Event(
            event_type=EventType.TIMER_TRIGGER,
            content=self.content,
            metadata={"timer_id": self.timer_id, "kind": "one_shot",
                      "scheduled_delay_seconds": self.delay},
        ))


class RecurringTimer(TriggerSource):
    """循环定时器：每隔 interval 秒触发一次 timer_trigger 事件。

    对应书中"每小时检查一次服务器健康状况""每周五发送进展报告"，以及
    OpenClaw Heartbeat 式的定时轮询。
    """

    def __init__(self, event_queue, interval: float, content: str, timer_id: str = "recurring"):
        super().__init__(name=f"RecurringTimer({timer_id})", event_queue=event_queue)
        self.interval = interval
        self.content = content
        self.timer_id = timer_id

    def run(self):
        logger.info(f"🔁 [{self.name}] 已注册：每 {self.interval:.0f} 秒触发一次")
        tick = 0
        while not self._stop.wait(self.interval):
            tick += 1
            self.emit(Event(
                event_type=EventType.TIMER_TRIGGER,
                content=f"{self.content}（第 {tick} 次）",
                metadata={"timer_id": self.timer_id, "kind": "recurring",
                          "interval_seconds": self.interval, "tick": tick},
            ))


class FileWatchTrigger(TriggerSource):
    """文件监听：轮询目录，发现新增或被修改的文件时触发 file_change 事件。

    对应书中"n8n 等工作流平台的触发器生态：Webhook、定时器、邮件、数据库
    变更、文件监听"。这里用轮询实现，不依赖第三方库，便于跨平台离线运行。
    """

    def __init__(self, event_queue, watch_dir: str, poll_interval: float = 1.0):
        super().__init__(name=f"FileWatch({watch_dir})", event_queue=event_queue)
        self.watch_dir = watch_dir
        self.poll_interval = poll_interval
        self._snapshot = {}

    def _scan(self):
        snapshot = {}
        try:
            for entry in os.scandir(self.watch_dir):
                if entry.is_file():
                    snapshot[entry.name] = entry.stat().st_mtime
        except FileNotFoundError:
            pass
        return snapshot

    def run(self):
        os.makedirs(self.watch_dir, exist_ok=True)
        self._snapshot = self._scan()
        logger.info(f"👀 [{self.name}] 已注册：轮询间隔 {self.poll_interval:.0f} 秒"
                    f"（当前已有 {len(self._snapshot)} 个文件）")
        while not self._stop.wait(self.poll_interval):
            current = self._scan()
            for name, mtime in current.items():
                if name not in self._snapshot:
                    change = "created"
                elif mtime != self._snapshot[name]:
                    change = "modified"
                else:
                    continue
                self.emit(Event(
                    event_type=EventType.FILE_CHANGE,
                    content=f"检测到文件{'新增' if change == 'created' else '修改'}，请查看其内容并给出简要处理建议。",
                    metadata={"path": os.path.join(self.watch_dir, name), "change": change},
                ))
            self._snapshot = current


# ============================================================================
# 事件循环（event loop）
# ============================================================================

class EventLoop:
    """统一事件队列 + 单线程分发。

    所有触发器把异构事件推入同一个队列；事件循环按到达顺序取出，每个事件
    唤醒一次 Agent 处理。这正是书中"将所有输入统一建模为事件流，通过事件
    循环驱动 Agent 的思考和行动"的最小实现。
    """

    def __init__(self, dispatch: Callable[[Event], None]):
        self.event_queue: "queue.Queue[Event]" = queue.Queue()
        self.dispatch = dispatch
        self.triggers = []
        self.processed = 0

    def add_trigger(self, trigger: TriggerSource):
        self.triggers.append(trigger)

    def run(self, duration: float):
        """启动所有触发器，运行 duration 秒后停止。"""
        deadline = time.monotonic() + duration
        for t in self.triggers:
            t.start()

        logger.info(f"🟢 事件循环启动，将运行 {duration:.0f} 秒，等待事件唤醒 Agent...\n")
        while time.monotonic() < deadline:
            try:
                event = self.event_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self.processed += 1
            logger.info(f"\n{'='*80}\n📥 事件循环取出第 {self.processed} 个事件"
                        f" -> 唤醒 Agent\n{'='*80}")
            try:
                self.dispatch(event)
            except Exception as e:  # noqa: BLE001 - 演示中不希望单个事件异常终止循环
                logger.error(f"❌ 处理事件时出错: {e}")

        for t in self.triggers:
            t.stop()
        logger.info(f"\n🔴 事件循环结束，共处理 {self.processed} 个事件。")


# ============================================================================
# 分发处理器：模拟动作 or 真实 Agent
# ============================================================================

def make_mock_dispatch() -> Callable[[Event], None]:
    """离线模拟处理器：不调用大模型，打印 Agent 被唤醒后的处理过程。"""

    def dispatch(event: Event):
        logger.info(f"🤖 Agent 被唤醒，收到消息: {event.to_user_message()}")
        # 用一个确定性的"模拟动作"代替大模型 + 工具调用
        if event.event_type == EventType.TIMER_TRIGGER:
            action = "读取定时任务上下文 -> 执行例行检查 -> 汇报结果"
        elif event.event_type == EventType.FILE_CHANGE:
            path = event.metadata.get("path", "")
            preview = ""
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    preview = f.read(120).replace("\n", " ")
            except OSError:
                preview = "(无法读取文件内容)"
            action = f"读取文件 {os.path.basename(path)} -> 内容预览: {preview!r} -> 生成处理建议"
        else:
            action = "解析事件 -> 调用相关工具 -> 生成处理结果"
        logger.info(f"🛠️  [模拟动作] {action}")
        logger.info(f"✅ Agent 处理完成: 已响应 {event.event_type.value} 事件")

    return dispatch


def make_agent_dispatch(provider: str, model: Optional[str],
                        max_iterations: int) -> Callable[[Event], None]:
    """真实处理器：接入 EventTriggeredAgent，由大模型处理每个事件。"""
    from agent import EventTriggeredAgent, SystemHintConfig, resolve_provider_and_key

    # 通用兜底：直连 provider 的 key 缺失时，若有 OPENROUTER_API_KEY 则自动改走 openrouter。
    resolved_provider, api_key = resolve_provider_and_key(provider)
    if not api_key:
        print(f"❌ 未检测到 provider '{provider}' 对应的 API Key（也未配置 OPENROUTER_API_KEY 兜底）。")
        print(f"   请先设置环境变量，或改用离线演示：python event_loop_demo.py --mock")
        sys.exit(1)
    if resolved_provider != provider:
        print(f"ℹ️  provider '{provider}' 无可用 Key，已自动改用 OpenRouter 兜底（openrouter）。")
        provider = resolved_provider
        # 保留已是 provider/model 形式的显式模型；否则让 openrouter 用其默认模型。
        model = model if (model and "/" in model) else None

    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True,
        save_trajectory=True,
        trajectory_file="event_loop_trajectory.json",
        temperature=0.7,
        max_tokens=4096,
        use_mcp_servers=False,  # 本演示仅用内置工具，避免额外的 MCP 依赖
    )
    agent = EventTriggeredAgent(api_key=api_key, provider=provider,
                               model=model, config=config, verbose=True)
    logger.info(f"✅ 真实 Agent 初始化完成（provider={provider}, model={agent.model}）")

    def dispatch(event: Event):
        result = agent.handle_event(event, max_iterations=max_iterations)
        logger.info(f"✅ Agent 处理完成: success={result['success']}, "
                    f"iterations={result['iterations']}, "
                    f"tool_calls={len(result['tool_calls'])}")

    return dispatch


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="事件驱动 Agent 端到端演示：注册触发器，由外部事件异步唤醒 Agent。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python event_loop_demo.py --mock
      离线演示全部触发器（一次性定时器 + 循环定时器 + 文件监听），无需 API Key
  python event_loop_demo.py --mock --trigger timer
      只演示一次性定时器
  python event_loop_demo.py --mock --trigger recurring --interval 3 --duration 12
      每 3 秒触发一次循环定时器，共运行 12 秒
  python event_loop_demo.py --mock --trigger file --watch-dir ./watched
      监听 ./watched 目录，向其中写入文件即可触发事件
  python event_loop_demo.py --trigger timer --provider kimi
      用真实大模型处理一次性定时器事件（需要设置对应的 API Key）
""",
    )
    parser.add_argument(
        "--trigger", choices=["timer", "recurring", "file", "all"], default="all",
        help="要演示的触发器类型：timer=一次性定时器，recurring=循环定时器，"
             "file=文件监听，all=全部（默认：all）",
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="离线模式：不调用大模型，用模拟动作演示触发→唤醒→处理闭环（无需 API Key）",
    )
    parser.add_argument(
        "--duration", type=float, default=12.0,
        help="事件循环总运行时长（秒），到时后停止所有触发器（默认：12）",
    )
    parser.add_argument(
        "--delay", type=float, default=3.0,
        help="一次性定时器的延迟触发时间（秒）（默认：3）",
    )
    parser.add_argument(
        "--interval", type=float, default=4.0,
        help="循环定时器的触发间隔（秒）（默认：4）",
    )
    parser.add_argument(
        "--watch-dir", default="watched_dir",
        help="文件监听触发器监视的目录，不存在会自动创建（默认：watched_dir）",
    )
    parser.add_argument(
        "--provider", default=os.getenv("LLM_PROVIDER", "kimi"),
        choices=["dashscope", "qwen", "bailian", "siliconflow", "doubao", "kimi", "moonshot", "openrouter"],
        help="真实模式使用的大模型提供商（默认：环境变量 LLM_PROVIDER 或 kimi）",
    )
    parser.add_argument(
        "--model", default=os.getenv("LLM_MODEL"),
        help="真实模式的模型名覆盖（默认：使用提供商默认模型）",
    )
    parser.add_argument(
        "--max-iterations", type=int, default=10,
        help="真实模式下单个事件的最大工具调用轮数（默认：10）",
    )
    return parser


def main():
    args = build_parser().parse_args()

    print("\n" + "=" * 80)
    print("🚀 事件驱动 Agent 演示（EVENT-DRIVEN AGENT DEMO）")
    print("=" * 80)
    print(f"触发器: {args.trigger} | 模式: {'离线模拟' if args.mock else '真实 Agent'} | "
          f"时长: {args.duration:.0f}s")
    print("=" * 80 + "\n")
    sys.stdout.flush()

    if args.mock:
        dispatch = make_mock_dispatch()
    else:
        dispatch = make_agent_dispatch(args.provider, args.model, args.max_iterations)

    loop = EventLoop(dispatch)

    if args.trigger in ("timer", "all"):
        loop.add_trigger(OneShotTimer(
            loop.event_queue, delay=args.delay, timer_id="daily_backup_check",
            content="一次性定时器到期：请检查每日备份是否已经完成。",
        ))
    if args.trigger in ("recurring", "all"):
        loop.add_trigger(RecurringTimer(
            loop.event_queue, interval=args.interval, timer_id="health_check",
            content="循环定时器到期：请检查服务器健康状况。",
        ))
    if args.trigger in ("file", "all"):
        loop.add_trigger(FileWatchTrigger(loop.event_queue, watch_dir=args.watch_dir))
        print(f"💡 提示：向目录 {args.watch_dir}/ 写入或修改文件即可触发 file_change 事件。")
        print(f"   例如另开一个终端执行：echo hello > {args.watch_dir}/note.txt\n")
    sys.stdout.flush()

    if not loop.triggers:
        print("❌ 没有可运行的触发器。")
        sys.exit(1)

    try:
        loop.run(duration=args.duration)
    except KeyboardInterrupt:
        print("\n⚠️  收到中断信号，正在停止...")
        for t in loop.triggers:
            t.stop()

    print("\n" + "=" * 80)
    print(f"📊 演示结束：共处理 {loop.processed} 个事件。")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
