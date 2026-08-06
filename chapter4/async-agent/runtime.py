"""Flux 异步 Agent 运行时（实验 4-6 核心）。

实现设计文档第 5 节的事件处理循环，重点覆盖实验 4-6 的四个能力：
  1. 异步工具执行：run_terminal_command 立即返回占位符，任务在后台跑。
  2. 事件队列与批量处理：非紧急事件进 pending，异步结果到达时一次性批量追加。
  3. 打断机制：用户"取消/停止"立即取消当前 turn + 所有异步工具，并留痕。
  4. 并行工具的取消与状态查询：query_task / cancel_task 按 ID 操作；
     异步完成后以"新事件"把真实结果注入对话。

架构（三个协程协作，全部基于 asyncio 单线程）：
  - inbox 队列：所有进来的事件（用户输入、打断、异步完成通知）先入 inbox。
  - _dispatcher：从 inbox 取事件 -> 判定紧急度 -> 分流（立即处理 / 排队 / 打断）。
  - _worker   ：从 work 队列取"事件批次" -> 追加到轨迹 -> 跑一轮 LLM（run_llm_turn）。
    每一轮 LLM 作为可取消的子任务（turn_task），打断时直接 cancel 它。
"""

from __future__ import annotations

import asyncio
import datetime
import json
import os
import time
from typing import Optional

from events import Event, EventType, Urgency, classify_urgency
from tasks import TaskManager, TaskState

# ------------------------- LLM 工具定义（function calling） -------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": ("异步执行一个受限的真实日志分析子进程。调用后立即返回 task_id，"
                            "不会阻塞；进度来自子进程 stdout。自然完成后，真实返回码、输出哈希和"
                            "文件分析指标会作为新的系统事件出现。取消会终止对应 OS 进程。"),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的终端命令，如 `python analyze_logs.py`"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "立即返回当前时间。用于回答用户'现在几点了'之类的即时问题。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_task",
            "description": "查询某个后台异步任务的当前进度与状态。",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "string", "description": "任务 ID，如 T1"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_task",
            "description": "按 task_id 取消一个正在运行的后台异步任务。",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "string", "description": "任务 ID，如 T1"}},
                "required": ["task_id"],
            },
        },
    },
]

SYSTEM_PROMPT = """你是一个异步 Agent（基于 Flux 框架）。你可以调用工具来完成任务。

关键行为准则：
1. run_terminal_command 是【异步】的：调用后命令在后台运行并立即返回 task_id。
   你应当简要告知用户"任务已在后台启动"，然后【结束本轮回复，不要空等结果】。
2. 当你看到形如 "[系统事件｜异步任务完成] task_id=... 结果：..." 的消息时，
   说明后台任务真的完成了，这时再基于结果给出分析/整合结论。
3. 如果用户在后台任务运行期间提出简短问题（例如"现在几点了？"），
   立即用对应工具（如 get_current_time）回答，【不要等待】后台任务。
4. 你可以用 query_task 查询任意后台任务进度，用 cancel_task 按 ID 取消任务。
5. 收到 "[用户打断]" 时，立即停止当前工作并简短确认已停止。
6. 严格按用户给出的计划执行（例如"谁先完成就查其余进度，未过 50% 就取消"）。
   注意：只取消【进度未超过 50%】的任务；进度已超过 50% 的任务应【保留并等待其完成】，不要取消它。
   每个还在运行的任务只需查询一次进度即可做出取消/保留决定，不要反复查询。
7. 回答简洁、用中文，除非用户明确要求其它语言或格式。
"""

MAX_STEPS = 8  # 单轮内最多的工具调用往返次数（防止死循环）

# 日志配色（各来源一种颜色），供 runtime 与离线演示脚本共用。
_LOG_COLORS = {
    "USER": "\033[96m", "AGENT": "\033[92m", "TOOL": "\033[93m",
    "TASK": "\033[95m", "SYSTEM": "\033[90m", "TRAJ": "\033[94m",
    "STATE": "\033[95m",
}


def format_log(t0: float, source: str, text: str) -> str:
    """把一条日志渲染成「[相对秒] 来源 | 文本」的彩色字符串。"""
    color = _LOG_COLORS.get(source, "")
    reset = "\033[0m" if color else ""
    return f"[{time.time() - t0:6.2f}s] {color}{source:6}{reset} | {text}"


class AgentRuntime:
    def __init__(self, client, model: str, start_time: Optional[float] = None,
                 completion_params: Optional[dict] = None):
        self.client = client
        self.model = model
        # 传给 chat.completions.create 的采样参数。默认 temperature=0.2 适合 gpt-5.6-luna；
        # 推理模型（如 Moonshot kimi-k3）需要 temperature=1 且 max_tokens>=2048，由 make_client 传入。
        self.completion_params = completion_params or {"temperature": 0.2}
        self._t0 = start_time or time.time()

        self.trajectory: list[Event] = []          # 轨迹（工作记忆）
        self.inbox: asyncio.Queue = asyncio.Queue()  # 所有进来的原始事件
        self.work: asyncio.Queue = asyncio.Queue()   # 待处理的事件批次
        self.pending: list[Event] = []               # 非紧急事件的排队缓冲

        self.tasks = TaskManager(on_complete=self._on_task_complete, log=self.log)
        self.turn_task: Optional[asyncio.Task] = None
        self.running = True
        self._STOP = object()

    # ------------------------------- 日志 -------------------------------

    def log(self, source: str, text: str) -> None:
        print(format_log(self._t0, source, text), flush=True)

    def _append(self, event: Event) -> None:
        """把事件追加到轨迹，并打印轨迹留痕。"""
        self.trajectory.append(event)
        self.log("TRAJ", f"+ {event.type:18} {event.label}")

    def build_messages(self) -> list[dict]:
        """把轨迹渲染成 OpenAI chat 消息列表。"""
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for e in self.trajectory:
            if e.message:
                msgs.append(e.message)
        return msgs

    # ------------------------- 对外接口：提交事件 -------------------------

    async def submit_user_message(self, text: str, urgency: Optional[str] = None) -> None:
        """提交一条用户消息（demo 用它模拟用户输入）。"""
        u = urgency or classify_urgency(text)
        if u == Urgency.INTERRUPT:
            ev = Event(EventType.USER_INTERRUPT, urgency=u,
                       message={"role": "user", "content": f"[用户打断] {text}"},
                       label=f"用户打断：{text}")
        else:
            ev = Event(EventType.USER_INPUT, urgency=u,
                       message={"role": "user", "content": text},
                       label=f"用户消息（{u}）：{text}")
        self.log("USER", f"({u}) {text}")
        await self.inbox.put(ev)

    async def _on_task_complete(self, state: TaskState) -> None:
        """异步任务自然完成 -> 把真实结果作为【新事件】注入 inbox。"""
        ev = Event(
            EventType.ASYNC_RESULT, task_id=state.task_id,
            message={"role": "user",
                     "content": (f"[系统事件｜异步任务完成] task_id={state.task_id} "
                                 f"命令=`{state.command}` 结果：{state.result}")},
            label=f"异步完成 {state.task_id}",
        )
        await self.inbox.put(ev)

    # ------------------------------- 主循环 -------------------------------

    async def serve(self) -> None:
        dispatcher = asyncio.create_task(self._dispatcher())
        worker = asyncio.create_task(self._worker())
        await asyncio.gather(dispatcher, worker)

    def _is_idle(self) -> bool:
        return (not self.tasks.any_running()
                and self.work.empty()
                and self.inbox.empty()
                and (self.turn_task is None or self.turn_task.done()))

    def _drain_pending(self) -> list[Event]:
        drained, self.pending = self.pending, []
        return drained

    async def _dispatcher(self) -> None:
        """事件分流：实现设计文档 5.1 的两种处理机制。"""
        while self.running:
            ev = await self.inbox.get()
            if ev is self._STOP:
                await self.work.put(self._STOP)
                break

            if ev.type == EventType.USER_INTERRUPT:
                # —— 取消式处理：立刻打断当前 turn + 取消所有异步工具 ——
                await self._handle_interrupt(ev)

            elif ev.type == EventType.ASYNC_RESULT:
                # —— 异步结果到达：批量把 pending 一并追加，再触发 LLM ——
                batch = [ev] + self._drain_pending()
                if len(batch) > 1:
                    self.log("SYSTEM", f"异步结果到达，批量处理 {len(batch)-1} 条积压的非紧急事件")
                await self.work.put(batch)

            elif ev.type == EventType.USER_INPUT:
                if ev.urgency == Urgency.IMMEDIATE:
                    # 立即处理（如用户提问），不打断后台异步任务
                    await self.work.put([ev])
                elif self._is_idle():
                    # 空闲时，普通指令也直接处理（例如一开始下达的任务）
                    await self.work.put([ev])
                else:
                    # 排队处理：累积到 pending，等下一次异步结果时批量追加
                    self.pending.append(ev)
                    self.log("SYSTEM", f"事件进入排队缓冲（当前积压 {len(self.pending)} 条）")

    async def _handle_interrupt(self, ev: Event) -> None:
        # 1) 取消正在进行的 LLM turn
        if self.turn_task and not self.turn_task.done():
            self.turn_task.cancel()
        # 2) 取消所有后台异步工具
        cancelled = self.tasks.cancel_all()
        # 3) 组装打断批次：打断事件 + 系统回执 + 被丢弃的积压事件（留痕）
        note = Event(
            EventType.SYSTEM_NOTE,
            message={"role": "user",
                     "content": (f"[系统] 已执行打断：取消了后台任务 {cancelled or '（无）'}。"
                                 f"请向用户简短确认已停止。")},
            label=f"打断回执，取消任务 {cancelled or '（无）'}",
        )
        batch = [ev, note] + self._drain_pending()
        await self.work.put(batch)

    async def _worker(self) -> None:
        """逐批处理事件：追加到轨迹后跑一轮可被取消的 LLM。"""
        while self.running:
            batch = await self.work.get()
            if batch is self._STOP:
                break
            self.turn_task = asyncio.create_task(self._process_batch(batch))
            try:
                await self.turn_task
            except asyncio.CancelledError:
                self.log("SYSTEM", "当前 LLM turn 已被打断取消")

    async def _process_batch(self, batch: list[Event]) -> None:
        for e in batch:
            self._append(e)
        await self.run_llm_turn()

    # ------------------------------- LLM turn -------------------------------

    async def run_llm_turn(self) -> None:
        """调用 LLM 做决策；同步工具就地执行并回填，异步工具启动后回占位符。"""
        for _ in range(MAX_STEPS):
            messages = self.build_messages()
            _t = time.time()
            resp = await self.client.chat.completions.create(
                model=self.model, messages=messages,
                tools=TOOL_SCHEMAS, tool_choice="auto", **self.completion_params,
            )
            self.log("SYSTEM", f"LLM 调用耗时 {time.time()-_t:.2f}s（{len(messages)} 条消息）")
            msg = resp.choices[0].message

            assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ]

            self._append(Event(
                EventType.AGENT_TOOL_CALL if msg.tool_calls else EventType.AGENT_OUTPUT,
                message=assistant_msg,
                label=("调用工具 " + ", ".join(tc.function.name for tc in msg.tool_calls)
                       if msg.tool_calls else "回复用户"),
            ))

            if msg.content and msg.content.strip():
                self.log("AGENT", msg.content.strip())

            if not msg.tool_calls:
                return  # 本轮结束：Agent 给出了最终回复

            # 执行每个工具调用
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result_text = self._exec_tool(name, args)
                self._append(Event(
                    EventType.TOOL_RESULT,
                    message={"role": "tool", "tool_call_id": tc.id, "content": result_text},
                    label=f"工具结果 {name}",
                ))

    def _exec_tool(self, name: str, args: dict) -> str:
        """执行工具，返回给 LLM 的文本结果。"""
        if name == "run_terminal_command":
            command = args.get("command", "")
            state = self.tasks.start(command)
            return (f"命令已在后台【异步】启动。task_id={state.task_id}，命令=`{command}`。"
                    f"我不会阻塞等待；任务完成后其结果会以系统事件形式返回。"
                    f"可用 query_task('{state.task_id}') 查询进度或 cancel_task('{state.task_id}') 取消。")

        if name == "get_current_time":
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log("TOOL", f"get_current_time -> {now}")
            return f"当前时间是 {now}。"

        if name == "query_task":
            tid = args.get("task_id", "")
            st = self.tasks.query(tid)
            if not st:
                return f"未找到任务 {tid}。"
            self.log("TOOL", f"query_task({tid}) -> {st.status} {st.progress:.0f}%")
            return f"task_id={tid} 命令=`{st.command}` 状态={st.status} 进度={st.progress:.0f}%。"

        if name == "cancel_task":
            tid = args.get("task_id", "")
            st = self.tasks.query(tid)
            progress = f"{st.progress:.0f}%" if st else "未知"
            ok = self.tasks.cancel(tid)
            self.log("TOOL", f"cancel_task({tid}) -> {'已取消' if ok else '无法取消'} (进度 {progress})")
            return (f"任务 {tid} 已取消（取消时进度 {progress}）。" if ok
                    else f"任务 {tid} 无法取消（可能已完成或不存在）。")

        return f"未知工具：{name}"

    # ------------------------------- 收尾 -------------------------------

    async def wait_until_idle(self, stable: float = 1.3, timeout: float = 90.0) -> None:
        """阻塞直到系统持续空闲 stable 秒（或超时）。"""
        start = time.time()
        last_busy = time.time()
        while True:
            busy = (self.tasks.any_running() or not self.work.empty()
                    or not self.inbox.empty() or bool(self.pending)
                    or (self.turn_task is not None and not self.turn_task.done()))
            now = time.time()
            if busy:
                last_busy = now
            elif now - last_busy >= stable:
                return
            if now - start >= timeout:
                self.log("SYSTEM", "wait_until_idle 超时返回")
                return
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        self.running = False
        await self.inbox.put(self._STOP)

    # ------------------------- 状态检查点（持久化 / 恢复） -------------------------

    def snapshot(self) -> dict:
        """把 Agent 的可持久化状态导出为一个 JSON 友好的字典。

        状态 = 轨迹（工作记忆）+ 全部异步任务的最后已知状态。这是「跨会话恢复」
        的基础：进程重启后，能据此还原对话上下文与后台任务的进度。
        """
        return {
            "model": self.model,
            "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "trajectory": [e.to_dict() for e in self.trajectory],
            "tasks": self.tasks.snapshot(),
        }

    def save_checkpoint(self, path: str) -> str:
        """把当前状态写入检查点文件（JSON），返回文件路径。"""
        data = self.snapshot()
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log("STATE", f"已保存检查点 -> {path}"
                          f"（{len(data['trajectory'])} 条轨迹事件，{len(data['tasks'])} 个任务）")
        return path

    def load_checkpoint(self, path: str) -> dict:
        """从检查点文件恢复轨迹与任务状态（原地覆盖当前状态）。"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        trajectory = data.get("trajectory") or []
        tasks = data.get("tasks") or []
        self.trajectory = [Event.from_dict(d) for d in trajectory]
        self.tasks.restore(tasks)
        self.log("STATE", f"已从检查点恢复 <- {path}"
                          f"（{len(self.trajectory)} 条轨迹事件，{len(tasks)} 个任务）")
        return data
