"""
demo.py —— 实验 10-1 演示入口：多角色转换 / transfer_to_agent

最简运行（一条命令，跑默认复合任务）：
    python demo.py

其它常用方式：
    python demo.py --list-roles              # 离线：只打印角色花名册后退出（无需 API Key）
    python demo.py --scenario coding         # 换一个内置场景（会路由到 coding 角色）
    python demo.py --task "..."              # 自定义任务
    python demo.py --role research            # 指定起始角色（默认 triage 前台分诊）
    python demo.py --interactive             # 交互式多轮对话（角色与共享历史跨轮保留）
    python demo.py --model gpt-5.6-luna --max-steps 30

演示一个需要【多次跨领域切换】的复合任务，预期出现
    triage → research → data_analysis → writing
的自主移交链——每次移交都由当前角色自己判断并调用 transfer_to_agent 触发。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from roles import ROLES, DEFAULT_ROLE
from orchestrator import MultiRoleOrchestrator, C


def _to_openrouter_model(model: str) -> str:
    """把模型名映射到 OpenRouter 命名空间（用于无 OPENAI_API_KEY 的回退路径）。"""
    if "/" in model:
        return model                      # 已是 OpenRouter 命名空间，原样使用
    if model.startswith("gpt-"):
        return "openai/" + model          # gpt-* -> openai/gpt-*
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"          # 兜底：当前便宜旗舰

# 尽量读取 .env（可选依赖，没装也能跑，只要 shell 里已 export）
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# 内置场景：每个都刻意跨多个领域，以逼出多次自主移交。
# 键名用于 --scenario；值为 (任务文本, 一句话说明)。
# ---------------------------------------------------------------------------
COMPOSITE_TASK = (
    "我在准备一份给投资人看的材料。请帮我：\n"
    "1) 查一下中国 2021、2022、2023 三年的新能源汽车销量；\n"
    "2) 据此算出这三年的年均复合增长率(CAGR)；\n"
    "3) 把数据和这个增长率结论，写成一段面向投资人的、不超过 120 字的中文总结。"
)

SCENARIOS: dict[str, tuple[str, str]] = {
    "cagr": (
        COMPOSITE_TASK,
        "默认场景。跨检索/计算/写作三领域：查销量 → 算 CAGR → 写投资总结，"
        "预期链路 triage → research → data_analysis → writing。",
    ),
    "solar": (
        "帮我查一下中国 2021、2022、2023 三年的光伏新增装机量，"
        "算出这三年的年均复合增长率(CAGR)，再写成一句话面向读者的结论。",
        "另一组数据的同类链路（research → data_analysis → writing），验证机制而非记住答案。",
    ),
    "coding": (
        "请写一个 Python 脚本：计算斐波那契数列前 20 项，并求它们的和；"
        "运行脚本得到结果后，用一句话向非技术读者解释这个结果。",
        "路由到 coding 角色用 execute_python 真正跑代码，再由 writing/triage 收尾。",
    ),
}
DEFAULT_SCENARIO = "cagr"


def print_roster():
    """打印角色花名册，证明存在 5 个角色、各有不同系统提示词/工具集。"""
    print(f"{C.BOLD}=== 角色花名册（共 {len(ROLES)} 个专业角色）==={C.RESET}")
    for name, role in ROLES.items():
        default_tag = "（默认入口）" if name == DEFAULT_ROLE else ""
        tools = role.tools + ["transfer_to_agent"]
        first_line = role.system_prompt.strip().splitlines()[0]
        print(
            f"{C.CYAN}• {name}{C.RESET} — {role.title}{default_tag}\n"
            f"    工具集: {tools}\n"
            f"    系统提示词(首句): {first_line}"
        )
    print()


def print_scenarios():
    """打印内置场景列表（供 --help / --list-roles 参考）。"""
    print(f"{C.BOLD}=== 内置场景（--scenario）==={C.RESET}")
    for key, (_task, desc) in SCENARIOS.items():
        default_tag = "（默认）" if key == DEFAULT_SCENARIO else ""
        print(f"{C.CYAN}• {key}{C.RESET}{default_tag} — {desc}")
    print()


def parse_args() -> argparse.Namespace:
    """命令行参数——均为可选，不传时行为与最初版本完全一致（跑默认复合任务）。"""
    parser = argparse.ArgumentParser(
        prog="demo.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "实验 10-1 演示：多角色转换 / transfer_to_agent。\n"
            "在一段【共享对话历史】上，5 个专业角色通过 transfer_to_agent 自主接力，"
            "触发形如 triage → research → data_analysis → writing 的移交链。"
        ),
        epilog=(
            "示例：\n"
            "  python demo.py                     # 跑默认场景（新能源汽车 CAGR 投资总结）\n"
            "  python demo.py --list-roles        # 离线：只看角色/场景清单，不调用 API\n"
            "  python demo.py --scenario coding   # 换到会路由至 coding 角色的场景\n"
            "  python demo.py --task '帮我...'    # 自定义任务\n"
            "  python demo.py --role research     # 从 research 角色起步\n"
            "  python demo.py --interactive       # 交互式多轮，角色与共享历史跨轮保留\n"
        ),
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default=DEFAULT_SCENARIO,
        help=f"选择一个内置场景（默认 {DEFAULT_SCENARIO}）；被 --task 覆盖。可选：{list(SCENARIOS.keys())}",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="自定义任务文本，覆盖 --scenario；不传则使用所选内置场景。",
    )
    parser.add_argument(
        "--role",
        "--starting-role",
        dest="role",
        choices=list(ROLES.keys()),
        default=DEFAULT_ROLE,
        help=f"指定起始角色（默认 {DEFAULT_ROLE} 前台分诊）。可选：{list(ROLES.keys())}",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互式多轮模式：复用同一编排器，角色与共享历史跨轮保留（Ctrl-C / 输入 exit 退出）。",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="覆盖 OPENAI_MODEL 环境变量（默认沿用环境变量，未设置则为 gpt-5.6-luna）。",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="单条用户消息的最大 LLM 轮数硬上限，防止死循环（默认 20）。",
    )
    parser.add_argument(
        "--list-roles",
        action="store_true",
        help="离线打印角色花名册与内置场景后退出，不需要 API Key（用于自检）。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="保存完整、脱敏的机器可读实验轨迹与验收结论。",
    )
    return parser.parse_args()


def print_run_summary(orch: MultiRoleOrchestrator, final: str):
    """打印一次运行的移交链、分工总览与最终成果。"""
    print(f"\n{C.BOLD}================ 运行汇总 ================{C.RESET}")
    print(f"{C.MAGENTA}自主移交链:{C.RESET} {orch.handoff_chain_str()}")
    print(f"{C.MAGENTA}移交次数:{C.RESET} {len(orch.handoffs)}")
    for i, h in enumerate(orch.handoffs, 1):
        print(f"  {i}. {h.from_role} → {h.to_role}  |  reason: {h.reason}")
    print(f"\n{C.MAGENTA}各角色分工（谁用了什么工具、谁产出最终回复）:{C.RESET}")
    print(orch.role_work_summary())
    print(f"\n{C.GREEN}最终成果:{C.RESET}\n{final}")


def save_evidence(
    path: Path,
    orch: MultiRoleOrchestrator,
    final: str,
    *,
    model: str,
    base_url: str,
    task: str,
) -> dict:
    """Persist direct receipts and fail-closed manuscript acceptance gates."""
    tools_by_role: dict[str, list[str]] = {}
    for role, kind, detail in orch.activity:
        if kind == "tool":
            tools_by_role.setdefault(role, []).append(detail)
    tool_contents = [
        str(message.get("content", ""))
        for message in orch.history
        if message.get("role") == "tool"
    ]
    real_search = any(
        '"provider": "tavily"' in content and '"url":' in content
        for content in tool_contents
    )
    counted_drafts: list[str] = []
    for message in orch.history:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            if call.get("function", {}).get("name") != "count_characters":
                continue
            try:
                arguments = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            if isinstance(arguments.get("text"), str):
                counted_drafts.append(arguments["text"])
    final_draft = counted_drafts[-1] if counted_drafts else ""
    chain = [orch.handoffs[0].from_role] + [h.to_role for h in orch.handoffs] if orch.handoffs else []
    required_roles_in_order = all(
        role in chain and chain.index(role) < chain.index(next_role)
        for role, next_role in zip(
            ["triage", "research", "data_analysis"],
            ["research", "data_analysis", "writing"],
        )
    )
    final_chars = len(final)
    gates = {
        "real_web_search_with_urls": real_search,
        "triage_research_analysis_writing_order": required_roles_in_order,
        "research_used_web_search": "web_search" in tools_by_role.get("research", []),
        "data_analysis_used_calculate": "calculate" in tools_by_role.get("data_analysis", []),
        "writing_checked_length": "count_characters" in tools_by_role.get("writing", []),
        "final_not_step_limit": not orch.terminated_by_limit,
        "final_nonempty": bool(final.strip()),
        "investor_summary_within_120_characters": bool(final_draft) and len(final_draft) <= 120,
        "shared_history_visible_after_handoffs": all(
            later["history_messages_visible"] >= earlier["history_messages_visible"]
            for earlier, later in zip(orch.api_calls, orch.api_calls[1:])
        ),
    }
    payload = {
        "schema_version": "1.0",
        "experiment": "10-1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": {
            "model": model,
            "base_url": base_url,
            "search": "Tavily",
            "credentials_redacted": True,
        },
        "task": task,
        "handoffs": [vars(h) for h in orch.handoffs],
        "handoff_chain": chain,
        "activity": [
            {"role": role, "kind": kind, "detail": detail}
            for role, kind, detail in orch.activity
        ],
        "api_calls": orch.api_calls,
        "steps_used": orch.steps_used,
        "history": orch.history,
        "final_answer": final,
        "final_character_count": final_chars,
        "counted_investor_summary": final_draft,
        "counted_investor_summary_characters": len(final_draft),
        "acceptance_gates": gates,
        "status": "complete" if all(gates.values()) else "incomplete",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n机器可读证据: {path}  status={payload['status']}")
    return payload


def run_interactive(orch: MultiRoleOrchestrator):
    """交互式多轮：同一编排器跨轮复用，共享历史与当前角色持续保留。"""
    print(
        f"{C.BOLD}=== 交互式多轮模式 ==={C.RESET}\n"
        f"{C.DIM}输入你的请求后回车；输入 exit / quit 或按 Ctrl-C 退出。"
        f"角色与对话历史会跨轮保留（共享上下文）。{C.RESET}"
    )
    turn = 0
    while True:
        try:
            user_message = input(f"\n{C.BOLD}👤 你（当前控制权在 {orch.current_role}）> {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出交互模式。")
            break
        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit", "q"}:
            print("已退出交互模式。")
            break
        turn += 1
        final = orch.run(user_message)
        print_run_summary(orch, final)


def main():
    args = parse_args()

    # ---- 离线自检路径：无需 API Key ----
    if args.list_roles:
        print_roster()
        print_scenarios()
        return

    model = args.model or os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")

    # 通用回退：优先直连 OPENAI_API_KEY；否则用 OPENROUTER_API_KEY 走 OpenRouter；
    # 都没有则报清晰错误。
    # 特例：gpt-5.x 系列直连 OpenAI 需组织验证，且其 /v1/chat/completions 对带工具的
    # 推理模型支持受限（reasoning_effort 限制）。因此只要设置了 OPENROUTER_API_KEY，
    # 就对 gpt-5.x 优先改走 OpenRouter，避免直连报错。
    prefer_openrouter = model.startswith("gpt-5") and os.environ.get("OPENROUTER_API_KEY")
    api_key = None if prefer_openrouter else os.environ.get("OPENAI_API_KEY")
    if api_key:
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    elif os.environ.get("OPENROUTER_API_KEY"):
        api_key = os.environ["OPENROUTER_API_KEY"]
        base_url = "https://openrouter.ai/api/v1"
        model = _to_openrouter_model(model)
        why = "gpt-5.x 优先走 OpenRouter" if prefer_openrouter else "未检测到 OPENAI_API_KEY"
        print(f"（{why}，改用 OpenRouter；模型映射为 {model}）")
    else:
        print("错误：未找到环境变量 OPENAI_API_KEY 或 OPENROUTER_API_KEY。请先设置后重试。",
              file=sys.stderr)
        print("（提示：只想看角色/场景清单可运行 `python demo.py --list-roles`，无需 Key。）",
              file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=base_url)

    print_roster()

    orch = MultiRoleOrchestrator(
        client=client,
        model=model,
        max_steps=args.max_steps,
        verbose=True,
        start_role=args.role,
    )

    if args.interactive:
        print(f"{C.BOLD}=== 模型 model={model}，起始角色 {args.role} ==={C.RESET}")
        run_interactive(orch)
        return

    # ---- 脚本化：单条复合任务，端到端跑完一次 ----
    task = args.task if args.task is not None else SCENARIOS[args.scenario][0]
    scenario_tag = "自定义任务" if args.task is not None else f"场景 {args.scenario}"
    print(f"{C.BOLD}=== 开始执行（{scenario_tag}，model={model}，起始角色={args.role}）==={C.RESET}")

    final = orch.run(task)
    print_run_summary(orch, final)
    if args.output:
        save_evidence(
            args.output,
            orch,
            final,
            model=model,
            base_url=base_url,
            task=task,
        )


if __name__ == "__main__":
    main()
