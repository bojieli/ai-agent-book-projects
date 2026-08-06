"""
进程内异步消息总线（Message Bus）
================================

模仿 Redis Pub/Sub 的语义，但完全跑在单进程的 asyncio 事件循环里，
无需真正部署 Redis。它承担实验 10-6 里"中心协调"的通信底座：

- 每条消息都封装在 ``Envelope`` 信封里，带上 sender_id / target / type / payload；
- Agent 通过 ``subscribe()`` 拿到一个订阅句柄，按消息类型接收；
- Agent 通过 ``publish()`` 把消息投递给指定目标或广播给所有人；
- 总线本身不做任何业务判断，只负责"可靠地把信封送达订阅者"。

设计要点：
- 使用 ``asyncio.Queue`` 做每个订阅者的收件箱，天然线程/协程安全；
- ``target`` 为 ``BROADCAST`` 时投递给所有订阅了该类型的人（发送者除外）；
- 打印带时间戳的事件日志，方便在演示里"看见"发布/订阅的消息流。
"""

from __future__ import annotations

import asyncio
import itertools
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# 广播目标常量：发给所有订阅者
BROADCAST = "*"

# 全局单调递增的消息序号，方便在日志里追踪顺序
_seq_counter = itertools.count(1)

# 演示启动时间，用于打印相对时间戳（更易读）
_START_TIME = time.monotonic()


def _now() -> float:
    """返回自演示启动以来的秒数（相对时间戳）。"""
    return time.monotonic() - _START_TIME


@dataclass
class Envelope:
    """消息信封：总线里流动的最小单元。"""

    sender_id: str            # 发送者 ID
    target: str               # 目标 Agent ID，或 BROADCAST 表示广播
    type: str                 # 消息类型：task_assigned / status_update / result / terminate / ack ...
    payload: Dict[str, Any] = field(default_factory=dict)  # JSON 负载
    seq: int = field(default_factory=lambda: next(_seq_counter))  # 全局序号
    ts: float = field(default_factory=_now)                       # 相对时间戳

    def short(self) -> str:
        """给日志用的紧凑单行表示。"""
        tgt = "ALL" if self.target == BROADCAST else self.target
        body = json.dumps(self.payload, ensure_ascii=False)
        if len(body) > 80:
            body = body[:77] + "..."
        return (
            f"[t={self.ts:6.2f}s #{self.seq:<3}] "
            f"{self.sender_id:>11} -> {tgt:<11} | {self.type:<14} | {body}"
        )


class Subscription:
    """订阅句柄：内部就是一个收件箱队列 + 关心的消息类型集合。"""

    def __init__(self, owner_id: str, types: Optional[List[str]]):
        self.owner_id = owner_id
        # types 为 None 表示订阅所有类型
        self.types = set(types) if types is not None else None
        self.inbox: "asyncio.Queue[Envelope]" = asyncio.Queue()

    def accepts(self, env: Envelope) -> bool:
        return self.types is None or env.type in self.types

    async def get(self) -> Envelope:
        return await self.inbox.get()

    async def get_nowait_or_wait(self, timeout: float) -> Optional[Envelope]:
        """带超时地取一条消息；超时返回 None（便于子 Agent 在循环里轮询终止信号）。"""
        try:
            return await asyncio.wait_for(self.inbox.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


class MessageBus:
    """异步消息总线：注册订阅者、投递信封、打印消息流日志。"""

    def __init__(self, verbose: bool = True):
        # owner_id -> 该 owner 的订阅列表
        self._subs: Dict[str, List[Subscription]] = {}
        self.verbose = verbose
        # 记录全部流过总线的信封，便于事后统计/断言
        self.history: List[Envelope] = []

    def subscribe(self, owner_id: str, types: Optional[List[str]] = None) -> Subscription:
        """注册一个订阅者，返回订阅句柄。types=None 表示接收所有类型。"""
        sub = Subscription(owner_id, types)
        self._subs.setdefault(owner_id, []).append(sub)
        return sub

    async def publish(self, env: Envelope) -> None:
        """把信封投递到总线：广播或点对点。"""
        self.history.append(env)
        if self.verbose:
            print("  BUS " + env.short())

        delivered = 0
        for owner_id, sub_list in self._subs.items():
            # 点对点：只投递给指定目标
            if env.target != BROADCAST and owner_id != env.target:
                continue
            # 广播时不回投给发送者自己
            if env.target == BROADCAST and owner_id == env.sender_id:
                continue
            for sub in sub_list:
                if sub.accepts(env):
                    await sub.inbox.put(env)
                    delivered += 1

        # 让出事件循环，保证消息尽快被对端取走（更接近真实推送时序）
        await asyncio.sleep(0)

    # —— 便捷构造并发布 ——
    async def send(
        self,
        sender_id: str,
        target: str,
        type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Envelope:
        env = Envelope(sender_id=sender_id, target=target, type=type, payload=payload or {})
        await self.publish(env)
        return env
