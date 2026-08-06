#!/usr/bin/env python3
"""协作工具 —— 统一命令行入口 (实验 4-4)

《深入理解 AI Agent》第 4 章 实验 4-4「协作工具 MCP 服务器」的命令行界面。
在不启动 MCP 服务器的前提下，直接列出、单独调用各协作工具，并运行端到端演示。

协作工具分三类（对应书中"协作工具"一节）：
  1. 子 Agent 管理：spawn_subagent / send_message_to_subagent / cancel_subagent
     （支持同步/异步两种模式，以及 minimal / llm_generated 两种上下文传递策略）
  2. 人类协作（HITL）：request_admin_approval / request_admin_input（含超时与默认行为）
  3. 多渠道通知：email / slack / telegram / discord

示例：
  python main.py list                     # 列出全部协作工具
  python main.py demo                      # 运行离线端到端协作演示（无需 API Key）
  python main.py subagent compare          # 对比两种上下文传递策略
  python main.py subagent spawn --task "查询订单 A12345 状态" --strategy minimal
  python main.py hitl approve --message "删除 1000 条记录？" --timeout 5 --auto-approve
  python main.py notify slack --message "部署完成 ✅"

说明：
  - 子 Agent 的执行、以及 llm_generated 上下文策略需要 OPENAI_API_KEY；
    未配置时自动退回到确定性的离线模拟（结果会明确标注"未调用 LLM"）。
  - 真实发送通知 / 邮件需要在 .env 中配置对应渠道的凭据；未配置时工具会
    返回"未配置"的说明，命令本身仍可正常解析与运行。
"""

import argparse
import asyncio
import json
import os
import sys

# src/ 下的模块使用裸导入（与 quickstart.py / subagent_comparison.py 一致）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import subagent_tools as sa  # noqa: E402
import hitl_tools as hitl  # noqa: E402
import notification_tools as notify  # noqa: E402


def _print(obj) -> None:
    """统一以带缩进的 JSON 打印工具返回结果。"""
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def _parse_json_arg(value):
    """尝试按 JSON 解析；不是合法 JSON 时按原始字符串返回（供子 Agent 直接使用）。"""
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


# ---------------------------------------------------------------------------
# 工具清单
# ---------------------------------------------------------------------------

COLLAB_TOOLS = {
    "子 Agent 管理": [
        ("spawn_subagent", "创建子 Agent（同步/异步，minimal/llm_generated 上下文策略）"),
        ("send_message_to_subagent", "向子 Agent 发送后续消息并获取回复"),
        ("cancel_subagent", "取消子 Agent（异步任务会中止后台协程）"),
        ("get_subagent_status", "查询子 Agent 状态与结果（用于异步）"),
    ],
    "人类协作 (HITL)": [
        ("request_admin_approval", "关键决策前请求管理员批准（支持超时与默认行为）"),
        ("request_admin_input", "向管理员请求补充输入"),
        ("respond_to_request", "管理员对待处理请求作出批准/拒绝"),
        ("list_pending_requests", "列出全部待处理的审批请求"),
    ],
    "多渠道通知": [
        ("send_email", "发送邮件通知（SMTP / SendGrid）"),
        ("send_slack_message", "通过 Webhook 发送 Slack 消息"),
        ("send_telegram_message", "发送 Telegram 消息"),
        ("send_discord_message", "通过 Webhook 发送 Discord 消息"),
    ],
}


def cmd_list(args) -> None:
    print("协作工具清单（实验 4-4）\n" + "=" * 60)
    for category, tools in COLLAB_TOOLS.items():
        print(f"\n【{category}】")
        for name, desc in tools:
            print(f"  - {name:<28} {desc}")
    print("\n提示：`python main.py <子命令> -h` 查看每个工具的参数。")


# ---------------------------------------------------------------------------
# 子 Agent 子命令
# ---------------------------------------------------------------------------

async def _subagent_dispatch(args) -> None:
    if args.sub_action == "spawn":
        res = await sa.spawn_subagent(
            task=args.task,
            context_strategy=args.strategy,
            mode=args.mode,
            parent_context=_parse_json_arg(args.parent_context),
            role=args.role,
            minimal_slice=_parse_json_arg(args.minimal_slice),
            business_rules=args.business_rules,
        )
        _print(res)
    elif args.sub_action == "send":
        _print(await sa.send_message_to_subagent(args.id, args.message))
    elif args.sub_action == "cancel":
        _print(await sa.cancel_subagent(args.id))
    elif args.sub_action == "status":
        _print(await sa.get_subagent_status(args.id))
    elif args.sub_action == "compare":
        await sa.run_context_strategy_comparison(task=args.task)


def cmd_subagent(args) -> None:
    asyncio.run(_subagent_dispatch(args))


# ---------------------------------------------------------------------------
# HITL 子命令
# ---------------------------------------------------------------------------

async def _auto_responder(approve: bool, notes: str, delay: float = 1.0) -> None:
    """模拟管理员：轮询待处理请求并作答，用于离线演示 HITL 闭环。"""
    await asyncio.sleep(delay)
    pending = await hitl.list_pending_requests()
    for req in pending.get("requests", []):
        await hitl.respond_to_request(req["request_id"], approve, notes)


async def _hitl_dispatch(args) -> None:
    if args.hitl_action == "approve":
        coro = hitl.request_admin_approval(
            request_message=args.message,
            timeout_seconds=args.timeout,
            urgent=args.urgent,
        )
        if args.auto_approve or args.auto_reject:
            responder = _auto_responder(
                approve=not args.auto_reject,
                notes=args.notes or ("自动模拟批准" if not args.auto_reject else "自动模拟拒绝"),
            )
            res, _ = await asyncio.gather(coro, responder)
        else:
            res = await coro
        _print(res)
    elif args.hitl_action == "input":
        coro = hitl.request_admin_input(prompt=args.prompt, timeout_seconds=args.timeout)
        if args.auto_answer is not None:
            responder = _auto_responder(approve=True, notes=args.auto_answer)
            res, _ = await asyncio.gather(coro, responder)
        else:
            res = await coro
        _print(res)
    elif args.hitl_action == "respond":
        _print(await hitl.respond_to_request(args.id, args.approve, args.notes))
    elif args.hitl_action == "list":
        _print(await hitl.list_pending_requests())


def cmd_hitl(args) -> None:
    asyncio.run(_hitl_dispatch(args))


# ---------------------------------------------------------------------------
# 通知子命令
# ---------------------------------------------------------------------------

async def _notify_dispatch(args) -> None:
    if args.channel == "email":
        _print(await notify.send_email(args.to, args.subject, args.body))
    elif args.channel == "slack":
        _print(await notify.send_slack_message(args.message, webhook_url=args.webhook))
    elif args.channel == "telegram":
        _print(await notify.send_telegram_message(args.message, chat_id=args.chat_id))
    elif args.channel == "discord":
        _print(await notify.send_discord_message(args.message, webhook_url=args.webhook))


def cmd_notify(args) -> None:
    asyncio.run(_notify_dispatch(args))


# ---------------------------------------------------------------------------
# 端到端演示：客服协调 Agent 处理一笔退款
# ---------------------------------------------------------------------------

def _neutralize_network_creds() -> None:
    """演示前清空 .env 中的占位凭据，避免离线演示尝试真实网络请求而阻塞。"""
    from config import config

    config.email.smtp_username = None
    config.email.smtp_password = None
    config.email.sendgrid_api_key = None
    config.im.telegram_bot_token = None
    config.im.slack_webhook_url = None
    config.im.discord_webhook_url = None
    config.hitl.webhook_url = None
    config.hitl.admin_email = None


async def _demo() -> None:
    _neutralize_network_creds()
    online = bool(os.getenv("OPENAI_API_KEY"))

    print("=" * 74)
    print("端到端协作演示：客服协调 Agent 处理一笔退款")
    print(f"（子 Agent 执行模式：{'在线 LLM' if online else '离线模拟（未配置 OPENAI_API_KEY）'}）")
    print("=" * 74)

    print("\n[步骤 1/3] 委派子 Agent 审批退款，并对比两种上下文传递策略")
    print("-" * 74)
    if not online:
        print("（提示：未配置 OPENAI_API_KEY，子 Agent 的执行与 llm_generated 策略")
        print("  会返回错误，仅用于展示接口与上下文构建；配置 Key 后可看到真实结果。）")
    await sa.run_context_strategy_comparison()

    print("\n[步骤 2/3] 大额操作触发 HITL：向管理员请求批准（含超时与默认行为）")
    print("-" * 74)
    print("→ 场景 A：管理员在超时前批准（后台模拟应答）")
    approval, _ = await asyncio.gather(
        hitl.request_admin_approval(
            request_message="退款金额 8888 元，超过自动批准阈值，请人工确认。",
            timeout_seconds=10,
            urgent=True,
        ),
        _auto_responder(approve=True, notes="核对无误，同意退款", delay=1.0),
    )
    _print(approval)

    print("\n→ 场景 B：管理员未及时响应，触发超时与保守默认（不批准）")
    timeout_res = await hitl.request_admin_approval(
        request_message="退款金额 8888 元，请人工确认。",
        timeout_seconds=2,
    )
    _print(timeout_res)

    print("\n[步骤 3/3] 多渠道通知协作者处理结果")
    print("-" * 74)
    summary = "退款工单 A12345：子 Agent 审批通过，管理员已确认，已放款。"
    for channel, coro in (
        ("email", notify.send_email("admin@example.com", "退款处理完成", summary)),
        ("slack", notify.send_slack_message(summary)),
        ("telegram", notify.send_telegram_message(summary)),
    ):
        res = await coro
        status = "已发送" if res.get("success") else f"未发送（{res.get('error')}）"
        print(f"  [{channel:<8}] {status}：{summary}")

    print("\n" + "=" * 74)
    print("演示结束。真实发送通知/邮件需在 .env 配置对应渠道凭据；")
    print("子 Agent 的真实 LLM 执行与 llm_generated 策略需配置 OPENAI_API_KEY。")
    print("=" * 74)


def cmd_demo(args) -> None:
    asyncio.run(_demo())


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="协作工具命令行入口（实验 4-4）：子 Agent 管理 / 人类协作 / 多渠道通知",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python main.py list\n"
            "  python main.py demo\n"
            "  python main.py subagent compare\n"
            "  python main.py subagent spawn --task '查询订单 A12345 状态' --strategy minimal\n"
            "  python main.py hitl approve --message '删除 1000 条记录？' --timeout 5 --auto-approve\n"
            "  python main.py notify slack --message '部署完成'\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<命令>")

    sub.add_parser("list", help="列出全部协作工具").set_defaults(func=cmd_list)

    p_demo = sub.add_parser("demo", help="运行离线端到端协作演示（无需 API Key）")
    p_demo.set_defaults(func=cmd_demo)

    # subagent
    p_sa = sub.add_parser("subagent", help="子 Agent 管理工具")
    sa_sub = p_sa.add_subparsers(dest="sub_action", required=True, metavar="<动作>")

    p_spawn = sa_sub.add_parser("spawn", help="创建子 Agent")
    p_spawn.add_argument("--task", required=True, help="委派给子 Agent 的子任务")
    p_spawn.add_argument("--strategy", default="minimal",
                         choices=["minimal", "llm_generated"], help="上下文传递策略")
    p_spawn.add_argument("--mode", default="sync", choices=["sync", "async"],
                         help="sync 同步等待结果；async 返回 task_id")
    p_spawn.add_argument("--role", default=None, help="子 Agent 的角色（用于系统提示词）")
    p_spawn.add_argument("--parent-context", default=None,
                         help="主 Agent 轨迹/状态（JSON 字符串）")
    p_spawn.add_argument("--minimal-slice", default=None,
                         help="minimal 策略下手动挑选的信息（字符串或 JSON）")
    p_spawn.add_argument("--business-rules", default=None,
                         help="llm_generated 策略下的隐私/压缩规则")

    p_send = sa_sub.add_parser("send", help="向子 Agent 发送后续消息")
    p_send.add_argument("--id", required=True, help="子 Agent ID")
    p_send.add_argument("--message", required=True, help="消息内容")

    p_cancel = sa_sub.add_parser("cancel", help="取消子 Agent")
    p_cancel.add_argument("--id", required=True, help="子 Agent ID")

    p_status = sa_sub.add_parser("status", help="查询子 Agent 状态/结果")
    p_status.add_argument("--id", required=True, help="子 Agent ID")

    p_cmp = sa_sub.add_parser("compare", help="对比 minimal 与 llm_generated 两种策略")
    p_cmp.add_argument("--task", default=None, help="用于对比的共同子任务")
    p_sa.set_defaults(func=cmd_subagent)

    # hitl
    p_hitl = sub.add_parser("hitl", help="人类协作（HITL）工具")
    hitl_sub = p_hitl.add_subparsers(dest="hitl_action", required=True, metavar="<动作>")

    p_appr = hitl_sub.add_parser("approve", help="请求管理员批准")
    p_appr.add_argument("--message", required=True, help="需要批准的内容")
    p_appr.add_argument("--timeout", type=int, default=None, help="等待秒数（超时后按默认行为）")
    p_appr.add_argument("--urgent", action="store_true", help="标记为紧急")
    p_appr.add_argument("--auto-approve", action="store_true", help="后台模拟管理员批准（离线演示用）")
    p_appr.add_argument("--auto-reject", action="store_true", help="后台模拟管理员拒绝（离线演示用）")
    p_appr.add_argument("--notes", default=None, help="管理员备注")

    p_inp = hitl_sub.add_parser("input", help="向管理员请求输入")
    p_inp.add_argument("--prompt", required=True, help="问题/提示")
    p_inp.add_argument("--timeout", type=int, default=None, help="等待秒数")
    p_inp.add_argument("--auto-answer", default=None, help="后台模拟管理员回答（离线演示用）")

    p_resp = hitl_sub.add_parser("respond", help="管理员对请求作答")
    p_resp.add_argument("--id", required=True, help="请求 ID")
    grp = p_resp.add_mutually_exclusive_group(required=True)
    grp.add_argument("--approve", dest="approve", action="store_true", help="批准")
    grp.add_argument("--reject", dest="approve", action="store_false", help="拒绝")
    p_resp.add_argument("--notes", default=None, help="备注")

    hitl_sub.add_parser("list", help="列出待处理请求")
    p_hitl.set_defaults(func=cmd_hitl)

    # notify
    p_notify = sub.add_parser("notify", help="多渠道通知工具")
    notify_sub = p_notify.add_subparsers(dest="channel", required=True, metavar="<渠道>")

    p_email = notify_sub.add_parser("email", help="发送邮件")
    p_email.add_argument("--to", required=True, help="收件人")
    p_email.add_argument("--subject", required=True, help="主题")
    p_email.add_argument("--body", required=True, help="正文")

    p_slack = notify_sub.add_parser("slack", help="发送 Slack 消息")
    p_slack.add_argument("--message", required=True, help="消息内容")
    p_slack.add_argument("--webhook", default=None, help="Slack Webhook URL（默认取 .env）")

    p_tg = notify_sub.add_parser("telegram", help="发送 Telegram 消息")
    p_tg.add_argument("--message", required=True, help="消息内容")
    p_tg.add_argument("--chat-id", default=None, help="Telegram chat id（默认取 .env）")

    p_dc = notify_sub.add_parser("discord", help="发送 Discord 消息")
    p_dc.add_argument("--message", required=True, help="消息内容")
    p_dc.add_argument("--webhook", default=None, help="Discord Webhook URL（默认取 .env）")
    p_notify.set_defaults(func=cmd_notify)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
