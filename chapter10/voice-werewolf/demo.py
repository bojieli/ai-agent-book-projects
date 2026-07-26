#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实验 10-8：语音狼人杀 Agent 系统 —— 一键跑完整一局。

配套《深入理解 AI Agent》第 10 章「实验 10-8：语音狼人杀 Agent 系统」。

本 demo 演示三件事（对应书中架构设计）：
1. **多 Agent**：每个玩家 = 一个独立 LLM Agent（OpenAI，默认 gpt-5.6-luna）。
2. **信息权限控制**：法官按角色把信息投递进各 Agent 的私有上下文——狼人才知道
   队友、预言家才知道查验结果、公开发言进所有人。游戏后打印审计表 + 自动校验，
   客观证明信息隔离正确。
3. **法官编排**：确定性法官编排夜晚（刀/验/用药）→ 白天（死讯/发言/投票）→ 结算。

语音是**可选增强**（--voice，用 OpenAI tts-1 合成公开发言），默认文本模式即可
完整、可复现地跑完一局。

用法：
    export OPENAI_API_KEY=your-openai-api-key
    python demo.py                 # 文本模式跑完整一局（LLM 决策，默认）
    python demo.py --offline       # 离线模式：规则决策，零成本、可复现，无需 API Key
    python demo.py --seed 7        # 换一局身份分布
    python demo.py --players 9 --wolves 3   # 自定义人数与狼人数
    python demo.py --voice         # 额外把公开发言合成语音到 audio/
    python demo.py --voice --play  # 合成并播放（macOS afplay）
    python demo.py --offline --log game.log  # 把完整对局日志另存一份到文件
"""

import argparse
import os
import sys


class _Tee:
    """把写入同时分发到多个流（用于 --log：既打印到终端又落盘到文件）。"""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)

    def flush(self):
        for s in self.streams:
            s.flush()

try:
    from dotenv import load_dotenv
    load_dotenv()  # 若存在 .env 则加载（可选）
except Exception:
    pass

from werewolf.game import Judge, create_players
from werewolf.roles import Role


def verify_isolation(judge: Judge):
    """自动校验信息隔离是否正确，并打印证据。返回是否全部通过。"""
    print("\n" + "=" * 78)
    print("信息隔离自动校验（证明每条敏感信息只进了它该进的上下文）")
    print("=" * 78)
    ok = True

    wolves = judge.wolves()
    wolf_names = {w.name for w in wolves}
    non_wolves = [p for p in judge.players if p.role != Role.WEREWOLF]
    seer = next((p for p in judge.players if p.role == Role.SEER), None)

    # 证据 1：狼人队友身份只在狼人上下文里
    team_line_marker = "狼人阵营的玩家是"
    wolves_have = all(any(team_line_marker in m for m in w.memory) for w in wolves)
    nonwolves_have = any(any(team_line_marker in m for m in p.memory) for p in non_wolves)
    check1 = wolves_have and not nonwolves_have
    ok &= check1
    print(f"\n[校验1] 『狼人队友身份』只进狼人上下文：{'通过 ✓' if check1 else '失败 ✗'}")
    print(f"   - 每个狼人上下文都含队友身份？{wolves_have}")
    print(f"   - 存在非狼人上下文含队友身份？{nonwolves_have}（应为 False）")

    # 证据 2：预言家查验结果只在预言家本人上下文里
    if seer:
        seer_marker = "你查验了"
        seer_has = any(seer_marker in m for m in seer.memory)
        others_have = any(any(seer_marker in m for m in p.memory)
                          for p in judge.players if p.name != seer.name)
        check2 = seer_has and not others_have
        ok &= check2
        print(f"\n[校验2] 『预言家查验结果』只进预言家({seer.name})上下文：{'通过 ✓' if check2 else '失败 ✗'}")
        print(f"   - 预言家上下文含查验结果？{seer_has}")
        print(f"   - 存在其他玩家上下文含查验结果？{others_have}（应为 False）")

    # 证据 3：审计日志里每条记录的 visible_to 与类别相符
    def cat_visible(cat):
        return [set(r.visible_to) for r in judge.audit.records if r.category == cat]
    check3 = all(v == wolf_names for v in cat_visible("狼人队友身份")) and \
             all(v == wolf_names for v in cat_visible("狼人夜间共识"))
    ok &= check3
    print(f"\n[校验3] 审计日志中狼人专属信息的可见集合 == 狼人集合 {sorted(wolf_names)}："
          f"{'通过 ✓' if check3 else '失败 ✗'}")

    check4 = all(set(r.visible_to) == set(judge.names)
                 for r in judge.audit.records if r.category.startswith("公开"))
    ok &= check4
    print(f"[校验4] 审计日志中所有『公开-*』信息可见集合 == 全体玩家："
          f"{'通过 ✓' if check4 else '失败 ✗'}")

    # 对照展示：一个狼人 vs 一个村民的完整私有上下文
    villager = next((p for p in judge.players if p.role == Role.VILLAGER), None)
    a_wolf = wolves[0] if wolves else None
    print("\n—— 对照：同一时刻两名玩家的私有上下文（证明各看各的）——")
    if a_wolf:
        print(f"\n【狼人 {a_wolf.name} 的私有上下文】（含队友身份、夜间共识）")
        for m in a_wolf.memory:
            print(f"   · {m}")
    if villager:
        print(f"\n【村民 {villager.name} 的私有上下文】（不含任何他人身份/查验结果）")
        for m in villager.memory:
            print(f"   · {m}")
    if seer:
        print(f"\n【预言家 {seer.name} 的私有上下文】（含独享的查验结果）")
        for m in seer.memory:
            print(f"   · {m}")

    print("\n" + "=" * 78)
    print(f"信息隔离总校验：{'全部通过 ✓✓✓' if ok else '存在失败 ✗'}")
    print("=" * 78)
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="实验 10-8：语音狼人杀 Agent 系统 —— 法官编排 + 信息权限控制 + 多 Agent。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python demo.py                 文本模式跑完整一局（LLM 决策，需 API Key）\n"
            "  python demo.py --offline       离线规则决策，零成本、可复现，无需 API Key\n"
            "  python demo.py --players 9 --wolves 3   自定义人数与狼人数\n"
            "  python demo.py --voice --play  额外合成并播放公开发言（需 API Key）\n"))
    parser.add_argument("--offline", "--mock", dest="offline", action="store_true",
                        help="离线模式：用规则策略代替 LLM，无需 API Key，零成本且可复现")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子（决定身份分布与离线决策，可复现，默认 42）")
    parser.add_argument("--players", type=int, default=7,
                        help="玩家总数（默认 7）")
    parser.add_argument("--wolves", type=int, default=None,
                        help="狼人数量（默认按玩家总数自动推导：7 人为 2 狼）")
    parser.add_argument("--max-rounds", type=int, default=6, dest="max_rounds",
                        help="昼夜循环的最大回合数上限（默认 6）")
    parser.add_argument("--model", type=str, default=None,
                        help="覆盖 LLM 模型（默认 gpt-5.6-luna，仅在线模式有效）")
    parser.add_argument("--voice", action="store_true",
                        help="用 OpenAI tts-1 把公开发言合成语音（需 API Key；默认关，即纯文本模式）")
    parser.add_argument("--play", action="store_true",
                        help="合成语音后立即播放（macOS afplay；需配合 --voice）")
    parser.add_argument("--log", type=str, default=None, metavar="PATH",
                        help="把完整对局日志（含审计表）另存一份到指定文件")
    return parser


def run_game(args):
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model

    mode = "离线（规则决策）" if args.offline else "在线（LLM 决策）"
    roles_note = "" if args.wolves is None else f"（狼人数={args.wolves}）"
    print("=" * 78)
    print("实验 10-8：语音狼人杀 Agent 系统")
    print(f"模式：{mode} | 模型：{os.environ.get('OPENAI_MODEL', 'gpt-5.6-luna') if not args.offline else '—'} | "
          f"种子：{args.seed} | 语音：{'开' if args.voice else '关（文本模式）'}")
    print(f"配置：{args.players} 人局{roles_note} | 最大回合：{args.max_rounds}")
    print("=" * 78)

    tts = None
    if args.voice:
        from werewolf.tts import TTS
        tts = TTS(os.path.join(os.path.dirname(__file__), "audio"), play=args.play)

    players = create_players(seed=args.seed, players=args.players,
                             wolves=args.wolves, offline=args.offline)
    judge = Judge(players, seed=args.seed, tts=tts, max_rounds=args.max_rounds)
    winner = judge.run()

    # 打印信息可见性审计表 + 自动校验
    judge.audit.print_table(judge.names)
    ok = verify_isolation(judge)

    print(f"\n最终结果：{winner.value} 获胜。")
    return ok


def main():
    args = build_parser().parse_args()

    # 在线模式（LLM 决策 / 语音合成）才需要 API Key；离线模式不需要。
    # LLM 决策支持 OPENAI_API_KEY 或（回退）OPENROUTER_API_KEY；语音合成（--voice，
    # OpenAI tts-1）目前只支持 OPENAI_API_KEY，OpenRouter 无 TTS 端点。
    has_llm_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if args.voice and not os.environ.get("OPENAI_API_KEY"):
        print("错误：语音合成（--voice，OpenAI tts-1）需要 OPENAI_API_KEY。"
              "请先 export OPENAI_API_KEY=your-openai-api-key（见 env.example），或去掉 --voice 跑纯文本模式。")
        sys.exit(1)
    if not args.offline and not has_llm_key:
        print("错误：LLM 决策需要 OPENAI_API_KEY 或 OPENROUTER_API_KEY。"
              "请先 export（见 env.example），或改用离线模式：python demo.py --offline")
        sys.exit(1)

    log_file = None
    orig_stdout = sys.stdout
    if args.log:
        log_file = open(args.log, "w", encoding="utf-8")
        sys.stdout = _Tee(orig_stdout, log_file)
    try:
        run_game(args)
    except ValueError as e:
        print(f"错误：{e}")
        sys.exit(2)
    finally:
        if log_file:
            sys.stdout = orig_stdout
            log_file.close()
            print(f"（完整对局日志已保存到 {args.log}）")


if __name__ == "__main__":
    main()
