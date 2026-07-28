"""
orchestrator.py —— 多角色移交（handoff）编排器。

核心机制（实验 10-2）：
- 全程维护一段【共享对话历史】history（user/assistant/tool 消息）。
- 每次调用大模型时，把【当前角色】的系统提示词临时拼到 history 前面，
  并只暴露【当前角色的工具集 + transfer_to_agent】。
- 模型可以：
    1) 调用自己的专属工具（正常 function calling）；
    2) 调用 transfer_to_agent 把控制权移交给别的角色——
       此时编排器换掉「系统提示词 + 工具集」，但 history 原样保留，
       于是新角色天然继承了全部对话历史（共享上下文）。
- 循环直到某个角色给出「没有工具调用」的最终回复。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from openai import OpenAI

from roles import ROLES, DEFAULT_ROLE, transfer_tool_schema
from tools import TOOL_SCHEMAS, TOOL_IMPLEMENTATIONS


# ---- 终端着色（无第三方依赖）----
class C:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"


@dataclass
class Handoff:
    from_role: str
    to_role: str
    reason: str


class MultiRoleOrchestrator:
    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-5.6-luna",
        max_steps: int = 20,
        verbose: bool = True,
        start_role: str = DEFAULT_ROLE,
    ):
        if start_role not in ROLES:
            raise ValueError(f"未知的起始角色 {start_role!r}，可选：{list(ROLES.keys())}")
        self.client = client
        self.model = model
        self.max_steps = max_steps
        self.verbose = verbose

        self.history: List[dict] = []          # 共享对话历史（不含 system）
        self.current_role: str = start_role    # 当前控制权所在角色（可自定义起始角色）
        self.handoffs: List[Handoff] = []      # 记录移交链
        self._tool_call_counts: Dict[str, int] = {}  # 相同工具调用去重计数（防死循环）
        # 分工记录：(role, kind, detail)，kind ∈ {"tool", "transfer", "final"}，
        # 用于运行结束后打印「哪个角色做了什么」的分工总览。
        self.activity: List[tuple] = []

    # -------------------------------------------------------------- 工具装配
    def _tools_for_current_role(self) -> List[dict]:
        """当前角色可见的工具 = 专属工具集 + transfer_to_agent。"""
        role = ROLES[self.current_role]
        schemas = [TOOL_SCHEMAS[name] for name in role.tools]
        schemas.append(transfer_tool_schema())  # 每个角色都能移交
        return schemas

    def _messages_for_api(self) -> List[dict]:
        """把当前角色的系统提示词拼到共享历史前面。"""
        system_msg = {"role": "system", "content": ROLES[self.current_role].system_prompt}
        return [system_msg] + self.history

    # -------------------------------------------------------------- 日志
    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def _log_role_banner(self):
        role = ROLES[self.current_role]
        self._log(
            f"\n{C.BOLD}{C.CYAN}┌── 当前角色: {role.title} ({role.name}){C.RESET}"
            f"{C.DIM}  工具: {role.tools + ['transfer_to_agent']}{C.RESET}"
        )

    # -------------------------------------------------------------- 单步
    def _run_one_llm_turn(self) -> Optional[str]:
        """
        执行一次「模型调用 + 工具处理」。
        返回值：
          - None  表示还要继续循环（发生了工具调用/移交）
          - str   表示这是最终回复（模型没有再调用工具），流程结束
        """
        self._log_role_banner()

        kwargs = dict(
            model=self.model,
            messages=self._messages_for_api(),
            tools=self._tools_for_current_role(),
            temperature=0,
        )
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            # 推理模型（如 gpt-5.x）只接受默认 temperature，会拒绝自定义值；
            # 移除该参数重试一次（同 book-translation / voice-werewolf 的做法）。
            if "temperature" not in str(e).lower():
                raise
            kwargs.pop("temperature", None)
            response = self.client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        # 没有工具调用 => 最终回复
        if not msg.tool_calls:
            content = msg.content or ""
            self.history.append({"role": "assistant", "content": content})
            self.activity.append((self.current_role, "final", ""))
            self._log(f"{C.GREEN}└── [{self.current_role}] 最终回复:{C.RESET}\n{content}")
            return content

        # 有工具调用：先把 assistant 消息（含 tool_calls）写进历史
        self.history.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        pending_transfer: Optional[Handoff] = None

        # 逐个处理工具调用，并为每个调用回填一条 tool 消息（OpenAI 要求）
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            if name == "transfer_to_agent":
                target = args.get("target_role", "")
                reason = args.get("reason", "")
                if target == self.current_role:
                    # 拒绝自我移交：让模型改用自己的工具或选别的角色
                    result = (
                        f"移交失败：你已经是 {target} 角色，不能移交给自己。"
                        "请直接使用你自己的工具完成当前部分，或移交给其他角色。"
                    )
                    self._log(f"{C.RED}└── transfer 被拒: 不能移交给自己 ({target}){C.RESET}")
                elif target in ROLES:
                    pending_transfer = Handoff(self.current_role, target, reason)
                    self.activity.append((self.current_role, "transfer", target))
                    result = f"已移交给 {target}。对方将继承完整对话历史并继续处理。"
                    self._log(
                        f"{C.MAGENTA}└── ⇢ transfer_to_agent: "
                        f"{self.current_role} → {target}{C.RESET}\n"
                        f"    {C.YELLOW}reason:{C.RESET} {reason}"
                    )
                else:
                    result = f"移交失败：未知角色 {target!r}。可选：{list(ROLES.keys())}"
                    self._log(f"{C.RED}└── transfer 失败: 未知角色 {target!r}{C.RESET}")
            else:
                impl = TOOL_IMPLEMENTATIONS.get(name)
                if impl is None:
                    result = f"工具 {name} 不存在。"
                else:
                    try:
                        result = impl(**args)
                    except (TypeError, ValueError) as exc:
                        # 模型偶尔会传错/漏参数（如 {"q": ...} 而非 {"query": ...}）
                        # 或给出无法转换的值；把错误作为工具结果回给模型让它自行纠正，
                        # 而不是让整个移交流程崩溃。
                        result = f"工具 {name} 调用失败：{exc}。请检查参数名与取值后重试。"
                    self.activity.append((self.current_role, "tool", name))
                # 防死循环：同一 (角色,工具,参数) 反复调用时给出纠偏提示
                sig = f"{self.current_role}:{name}:{tc.function.arguments}"
                self._tool_call_counts[sig] = self._tool_call_counts.get(sig, 0) + 1
                if self._tool_call_counts[sig] >= 3:
                    result += (
                        "\n[系统提示] 你已多次重复完全相同的调用。请停止重复，"
                        "直接给出最终文本，或调用 transfer_to_agent 移交给下一个角色。"
                    )
                self._log(
                    f"{C.BLUE}└── 🔧 调用工具 {name}{C.RESET} "
                    f"{C.DIM}args={args}{C.RESET}\n"
                    f"    {C.DIM}→ {result[:300]}{C.RESET}"
                )

            self.history.append(
                {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
            )

        # 处理完本轮所有工具调用后，如有移交则切换角色（保留 history）
        if pending_transfer is not None:
            self.handoffs.append(pending_transfer)
            self.current_role = pending_transfer.to_role

        return None  # 继续循环

    # -------------------------------------------------------------- 主循环
    def run(self, user_message: str) -> str:
        """处理一条用户消息，跑完整个多角色移交流程，返回最终回复。"""
        self.history.append({"role": "user", "content": user_message})
        self._log(f"{C.BOLD}👤 用户:{C.RESET} {user_message}")

        final_answer = ""
        for step in range(self.max_steps):
            result = self._run_one_llm_turn()
            if result is not None:
                final_answer = result
                break
        else:
            final_answer = "（达到最大步数上限，流程终止）"
            self._log(f"{C.RED}{final_answer}{C.RESET}")

        return final_answer

    # -------------------------------------------------------------- 汇总
    def handoff_chain_str(self) -> str:
        """返回可读的移交链，如 triage → research → data_analysis → writing → triage。"""
        if not self.handoffs:
            return DEFAULT_ROLE + "（未发生移交）"
        chain = [self.handoffs[0].from_role]
        for h in self.handoffs:
            chain.append(h.to_role)
        return " → ".join(chain)

    def role_work_summary(self) -> str:
        """
        返回「哪个角色做了什么」的分工总览——按角色首次出场顺序，
        列出每个角色实际调用过的专属工具，以及谁产出了最终回复。
        这直接印证：同一段共享历史上，不同专业角色各司其职地接力完成任务。
        """
        order: List[str] = []
        tools_by_role: Dict[str, List[str]] = {}
        final_role: Optional[str] = None
        for role, kind, detail in self.activity:
            if role not in order:
                order.append(role)
                tools_by_role[role] = []
            if kind == "tool" and detail not in tools_by_role[role]:
                tools_by_role[role].append(detail)
            elif kind == "final":
                final_role = role
        if not order:
            return "（无角色活动记录）"
        width = max(len(r) for r in order)
        lines: List[str] = []
        for role in order:
            used = tools_by_role[role]
            desc = "、".join(used) if used else "（仅路由/移交，未用专属工具）"
            if role == final_role:
                desc += "  ⇒ 产出最终回复"
            lines.append(f"  {role.ljust(width)} : {desc}")
        return "\n".join(lines)
