"""事件模型（对应设计文档中的 Event / Trajectory 概念）。

Flux 把 Agent 的一切经历都抽象成"事件"，按时间顺序追加到轨迹（trajectory）里。
本文件定义事件类型、事件对象，以及"事件紧急度"的判定逻辑——这是实验 4-6 里
"批量处理 vs 立即打断"两种处理机制的分类依据。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


class EventType:
    """事件类型常量（对应设计文档第 2 节 Inputs / Interrupts / Thinking / Actions）。"""

    USER_INPUT = "user.input"          # 用户输入（非紧急，走"排队处理"）
    USER_INTERRUPT = "user.interrupt"  # 用户打断（紧急，走"取消式处理"）
    AGENT_OUTPUT = "agent.output"      # Agent 面向用户的最终回复
    AGENT_TOOL_CALL = "agent.tool_call"  # Agent 发起的工具调用（Action）
    TOOL_RESULT = "tool.result"        # 工具返回结果（同步工具 / 异步占位符）
    ASYNC_RESULT = "async.result"      # 异步工具真正完成后注入的新事件
    SYSTEM_NOTE = "system.note"        # 框架注入的系统提示（如取消回执）


class Urgency:
    """事件紧急度：决定采用哪种事件处理机制。"""

    INTERRUPT = "interrupt"  # 取消式处理：立刻打断当前执行并取消异步工具
    IMMEDIATE = "immediate"  # 立即处理：不打断后台异步任务，但马上回应（如用户提问）
    DEFERRED = "deferred"    # 排队处理：累积到 pending 队列，任务完成时批量追加


# 打断类关键词：命中即视为紧急打断
_INTERRUPT_KEYWORDS = ["取消", "停止", "中止", "打住", "别做了", "stop", "cancel", "abort"]

# 疑问类信号：命中即视为需要"立即回应"（而不是排队）
_QUESTION_MARKS = ("?", "？")
_QUESTION_KEYWORDS = ["几点", "多少", "怎么", "如何", "为什么", "是不是", "有没有",
                      "吗", "呢", "what", "when", "how", "why", "which"]


def classify_urgency(text: str) -> str:
    """根据用户消息内容判定紧急度。

    规则（简单、可解释，便于书中讲清楚）：
      1. 含打断关键词（取消/停止/stop...） -> INTERRUPT（紧急，取消式处理）
      2. 是一个提问（带问号或疑问词）      -> IMMEDIATE（立即回应，但不打断后台任务）
      3. 其它（补充性指令，如"用日语回复"）-> DEFERRED（排队，批量处理）
    """
    low = text.lower()
    if any(kw in text or kw in low for kw in _INTERRUPT_KEYWORDS):
        return Urgency.INTERRUPT
    if text.strip().endswith(_QUESTION_MARKS) or any(kw in text or kw in low for kw in _QUESTION_KEYWORDS):
        return Urgency.IMMEDIATE
    return Urgency.DEFERRED


@dataclass
class Event:
    """一条轨迹事件。

    message 字段保存"可直接喂给 LLM 的 OpenAI 消息字典"（保证上下文的高保真回放）；
    没有 message 的事件（若有）只用于日志。
    """

    type: str
    message: Optional[dict] = None        # OpenAI chat 格式消息，供构建 LLM 上下文
    label: str = ""                       # 人类可读的日志标签
    task_id: Optional[str] = None         # 关联的异步任务 ID（若有）
    urgency: Optional[str] = None         # 仅用户输入事件会带
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """序列化为纯 JSON 可写的字典（用于状态检查点持久化）。"""
        return {
            "type": self.type, "message": self.message, "label": self.label,
            "task_id": self.task_id, "urgency": self.urgency, "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        """从检查点字典还原事件对象。"""
        raw_ts = d.get("ts")
        return cls(
            type=d["type"], message=d.get("message"),
            label=d.get("label") or "",
            task_id=d.get("task_id"), urgency=d.get("urgency"),
            ts=raw_ts if raw_ts is not None else time.time(),
        )
