"""
实验 9-2：用 ReAct Agent + PineClaw Voice 完成一个真实电话任务。

运行：
    python demo.py

默认路径调用 OpenAI 驱动上层 ReAct 决策，并调用官方 pine-voice SDK 拨打真实电话：
  (a) Agent 的 ReAct 轨迹（思考 + 发起 make_phone_call）
  (b) 返回的结构化通话记录（多轮 transcript + 是否达成目标 + 关键字段）
  (c) Agent 基于通话结果向用户的最终汇报
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent import run_agent


def _hr(title: str = "") -> None:
    line = "─" * 72
    if title:
        print(f"\n{line}\n{title}\n{line}")
    else:
        print(line)


def _print_record(rec: dict) -> None:
    print(f"  call_id        : {rec['call_id']}")
    print(f"  被叫号码       : {rec['phone_number']}")
    print(f"  状态           : {rec['status']}  |  是否达成目标: {rec['goal_achieved']}")
    print(f"  通话时长       : {rec['duration_seconds']} 秒")
    print(f"  摘要           : {rec['summary']}")
    print("  关键字段(key_fields):")
    if rec["key_fields"]:
        for k, v in rec["key_fields"].items():
            print(f"      - {k}: {v}")
    else:
        print("      （无）")
    print(f"  需要追问       : {rec['follow_up_needed']}  {rec.get('follow_up_reason', '')}")
    print("  通话转录(transcript):")
    for turn in rec["transcript"]:
        speaker = turn["speaker"]
        # 简单对齐：语音Agent 用 >>，被叫方用 <<
        arrow = ">>" if speaker == "语音Agent" else "<<"
        print(f"      {arrow} [{speaker}] {turn['text']}")


_DEFAULT_TASK = (
    "帮我打电话给诊所预约明天下午 3 点的牙科检查。"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="实验 9-2：把 PineClaw Voice（make_phone_call）当工具的 ReAct 电话 Agent。"
                    "给一个自然语言电话任务，Agent 自行决定号码/目标/上下文并真实拨打，"
                    "读取结构化通话记录后向用户汇报。",
        epilog="示例：\n"
               "  python demo.py --phone +14155551234 # 使用你获准测试的真实号码\n"
               "  python demo.py --dry-run             # 完全离线：脚本化 ReAct 轨迹，无需任何 API Key\n"
               "  python demo.py --task \"帮我打电话给餐厅订今晚 7 点 4 人的位子\" --phone +14155551234\n"
               "  python demo.py --model gpt-4o-mini  # 覆盖 ReAct 模型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--task", default=_DEFAULT_TASK,
                   help="自定义电话任务（自然语言）。默认用书中的宽带账单示例。")
    p.add_argument("--phone", default=None, metavar="号码",
                   help="可选：对方电话号码。给定时作为已知信息交给 Agent（dry-run 下直接用作被叫号码）。")
    p.add_argument("--goal", default=None, metavar="目标",
                   help="可选：明确的通话目标。给定时作为已知信息交给 Agent（dry-run 下直接用作通话目标）。")
    p.add_argument("--model", default=None, metavar="模型",
                   help="可选：覆盖使用的模型（默认取环境变量 OPENAI_MODEL，即 gpt-5.6-luna）。")
    p.add_argument("--dry-run", action="store_true",
                   help="离线脚本模式：不联网、不需要任何 API Key，仅演示 ReAct 循环与数据契约的形状。")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not args.dry_run and not all(os.getenv(k) for k in ("PINE_ACCESS_TOKEN", "PINE_USER_ID")):
        print("错误：真实拨号默认路径需要 PINE_ACCESS_TOKEN 和 PINE_USER_ID。"
              "请复制 env.example 为 .env；--dry-run 仅用于显式测试。")
        sys.exit(1)
    if not args.dry_run and not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
        print("错误：ReAct 决策和结构化提取需要 OPENAI_API_KEY 或 OPENROUTER_API_KEY。")
        sys.exit(1)

    # 书中示例任务：注意这里只给了自然语言任务，Agent 需自行决定通话参数。
    task = args.task

    _hr("用户任务")
    print(task)
    if args.dry_run:
        print("\n[模式] dry-run 离线脚本模拟：以下轨迹与通话记录均为固定脚本，"
              "不调用任何 LLM/电话 API，仅用于演示 ReAct 循环的形状。")

    _hr("ReAct Agent 轨迹")

    def on_event(kind: str, payload) -> None:
        if kind == "think":
            print(f"\n[Agent 思考] {payload}")
        elif kind == "call":
            print("\n[Agent 调用工具 make_phone_call] 入参:")
            print(f"    phone_number = {payload.get('phone_number')}")
            print(f"    goal         = {payload.get('goal')}")
            print(f"    context      = {payload.get('context', '')}")
        elif kind == "record":
            print("\n[PineClaw 返回结构化通话记录]")
            _print_record(payload)
        elif kind == "final":
            pass  # 最终汇报单独打印

    final = run_agent(
        task,
        on_event=on_event,
        model=args.model,
        phone_hint=args.phone,
        goal_hint=args.goal,
        dry_run=args.dry_run,
    )

    _hr("Agent 向用户的最终汇报")
    print(final)
    print()


if __name__ == "__main__":
    main()
