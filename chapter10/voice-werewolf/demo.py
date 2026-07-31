#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实验 10-8：1 名真人通过实时 ASR/TTS 与 5-7 个 AI Agent 玩狼人杀。

配套《深入理解 AI Agent》第 10 章「实验 10-8：语音狼人杀 Agent 系统」。

本 demo 演示三件事（对应书中架构设计）：
1. **多 Agent**：每个玩家 = 一个独立 LLM Agent（OpenAI，默认 gpt-5.6-luna）。
2. **信息权限控制**：法官按角色把信息投递进各 Agent 的私有上下文——狼人才知道
   队友、预言家才知道查验结果、公开发言进所有人。游戏后打印审计表 + 自动校验，
   客观证明信息隔离正确。
3. **法官编排**：确定性法官编排夜晚（刀/验/用药）→ 白天（死讯/发言/投票）→ 结算。

默认路径是双向真人语音验收；全 AI 文本/离线模式只用于补充诊断与 CI。

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
import json
import os
import sys
from pathlib import Path


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
from werewolf.roles import Faction, Role


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
            "  python demo.py                 7 人局：1 真人实时语音 + 6 AI（验收路径）\n"
            "  python demo.py --offline       仅作为 CI 补充的全 AI 离线模式\n"
            "  python demo.py --ai-only       真实 LLM、无真人音频的补充诊断模式\n"))
    parser.add_argument("--offline", "--mock", dest="offline", action="store_true",
                        help="补充测试模式：全 AI 规则策略；不满足实验的真人语音验收")
    parser.add_argument("--ai-only", action="store_true",
                        help="补充诊断模式：真实 LLM 全 AI 文本局；不满足真人语音验收")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子（决定身份分布与离线决策，可复现，默认 42）")
    parser.add_argument("--players", type=int, default=7,
                        help="玩家总数（默认 7）")
    parser.add_argument("--wolves", type=int, default=None,
                        help="狼人数量（验收配置固定为 2）")
    parser.add_argument("--human-seat", type=int, default=1,
                        help="真人座位 Pn（角色仍由 seed 随机分配，默认 P1）")
    parser.add_argument("--confirm-human-consent", action="store_true",
                        help="确认真人参与者已授权麦克风采集和本局实验；真人路径无此标志会拒绝启动")
    parser.add_argument("--max-rounds", type=int, default=8, dest="max_rounds",
                        help="昼夜循环的最大回合数上限（默认 8）")
    parser.add_argument("--model", type=str, default=None,
                        help="覆盖 LLM 模型（默认 gpt-5.6-luna，仅在线模式有效）")
    parser.add_argument("--voice", action="store_true",
                        help="兼容选项：--ai-only 时也为 AI 发言生成 TTS；真人模式默认启用双向语音")
    parser.add_argument("--play", action="store_true",
                        help="合成语音后立即播放（macOS afplay；需配合 --voice）")
    parser.add_argument("--log", type=str, default=None, metavar="PATH",
                        help="把完整对局日志（含审计表）另存一份到指定文件")
    parser.add_argument("--no-interruptions", action="store_true",
                        help="关闭真人在 AI 播放期间的 barge-in（默认允许实时打断）")
    parser.add_argument("--report", default="artifacts/acceptance_report.json",
                        help="保存回合、隐私、策略、语音事件验收报告")
    return parser


def run_game(args):
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model
        import werewolf.agent as agent_module
        agent_module._MODEL = args.model

    live_human = not args.offline and not args.ai_only
    mode = "真人实时语音 + AI" if live_human else ("离线全 AI 补充测试" if args.offline else "在线全 AI 补充诊断")
    roles_note = "" if args.wolves is None else f"（狼人数={args.wolves}）"
    print("=" * 78)
    print("实验 10-8：语音狼人杀 Agent 系统")
    configured_model = (os.getenv("ARK_MODEL") or os.getenv("MOONSHOT_MODEL") or
                        os.getenv("OPENAI_MODEL") or "provider default")
    print(f"模式：{mode} | 模型：{configured_model if not args.offline else '—'} | "
          f"种子：{args.seed} | 真人语音：{'开' if live_human else '关（非验收路径）'}")
    print(f"配置：{args.players} 人局{roles_note} | 最大回合：{args.max_rounds}")
    print("=" * 78)

    tts = None
    if live_human:
        from werewolf.human import LiveVoiceSession
        tts = LiveVoiceSession(os.path.join(os.path.dirname(__file__), "audio"),
                               allow_interruptions=not args.no_interruptions)
    elif args.voice:
        from werewolf.tts import TTS
        tts = TTS(os.path.join(os.path.dirname(__file__), "audio"), play=args.play)

    wolves = 2 if args.wolves is None else args.wolves
    if live_human and not (6 <= args.players <= 8):
        raise ValueError("验收路径必须是 6-8 人局")
    if live_human and wolves != 2:
        raise ValueError("验收路径角色配置要求恰好 2 只狼人")
    if not 1 <= args.human_seat <= args.players:
        raise ValueError("--human-seat 超出玩家座位范围")
    players = create_players(seed=args.seed, players=args.players,
                             wolves=wolves, offline=args.offline,
                             human_seat=args.human_seat if live_human else None,
                             voice=tts if live_human else None)
    judge = Judge(players, seed=args.seed, tts=tts, max_rounds=args.max_rounds)
    winner = judge.run()

    # 打印信息可见性审计表 + 自动校验
    judge.audit.print_table(judge.names)
    isolation_ok = verify_isolation(judge)

    strategy = None
    if not args.offline:
        from werewolf.strategy_audit import evaluate_strategy
        strategy = evaluate_strategy(judge)

    role_counts = {role.value: sum(1 for p in players if p.role == role) for role in Role}
    human_players = [p.name for p in players if getattr(p, "is_human", False)]
    from werewolf.strategy_audit import strategy_acceptance_passes
    strategy_pass = strategy_acceptance_passes(strategy)
    voice_has_asr = bool(live_human and any(e["type"] == "human_asr" for e in tts.events))
    voice_has_tts = bool(live_human and any(e["type"] == "tts_ready" for e in tts.events))
    roster_pass = (
        6 <= len(players) <= 8
        and role_counts.get("狼人") == 2
        and role_counts.get("预言家") == 1
        and role_counts.get("女巫") == 1
    )
    winner_determined = winner in {Faction.GOOD, Faction.WEREWOLF}
    ok = bool(
        live_human and isolation_ok and roster_pass and len(human_players) == 1
        and voice_has_asr and voice_has_tts and strategy_pass
        and judge.completed_rounds >= 3 and winner_determined
    )
    report = {
        "schema_version": 1,
        "experiment": "10-8",
        "generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S%z"),
        "acceptance_path": live_human,
        "players": len(players),
        "human_players": human_players,
        "human_role_randomized_to": next((p.role.value for p in players if getattr(p, "is_human", False)), None),
        "role_counts": role_counts,
        "completed_day_night_vote_cycles": judge.completed_rounds,
        "winner": winner.value,
        "information_isolation_pass": isolation_ok,
        "strategy_audit": strategy,
        "strategy_audit_pass": strategy_pass,
        "voice_events": tts.events if live_human else [],
        "voice_has_asr": voice_has_asr,
        "voice_has_tts": voice_has_tts,
        "barge_in_events": sum(1 for e in (tts.events if live_human else []) if e["type"] == "barge_in"),
        "gates": {
            "exact_6_to_8_player_role_roster": {"status": "pass" if roster_pass else "fail"},
            "one_authorized_human_participant": {"status": "pass" if live_human and len(human_players) == 1 else "not_run" if not live_human else "fail"},
            "real_human_asr": {"status": "pass" if voice_has_asr else "not_run" if not live_human else "fail"},
            "real_ai_and_judge_tts": {"status": "pass" if voice_has_tts else "not_run" if not live_human else "fail"},
            "three_complete_cycles": {"status": "pass" if judge.completed_rounds >= 3 else "fail" if live_human else "supplemental_only", "observed": judge.completed_rounds},
            "information_isolation": {"status": "pass" if isolation_ok else "fail"},
            "real_llm_strategy_acceptance": {"status": "pass" if strategy_pass else "not_run" if args.offline else "fail"},
            "winner_determined_by_game_rule": {"status": "pass" if winner_determined else "fail"},
        },
        "overall_status": "pass" if ok else "incomplete" if live_human else "supplemental_only",
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if winner == Faction.UNDECIDED:
        print("\n最终结果：本局未决，没有阵营满足胜利条件。")
    else:
        print(f"\n最终结果：{winner.value} 获胜。")
    print(f"验收报告：{report_path} | {report['overall_status'].upper()}")
    return ok if live_human else isolation_ok


def main():
    args = build_parser().parse_args()

    # 在线模式（LLM 决策 / 语音合成）才需要 API Key；离线模式不需要。
    # LLM 决策支持 OPENAI_API_KEY 或（回退）OPENROUTER_API_KEY；语音合成（--voice，
    # OpenAI tts-1）目前只支持 OPENAI_API_KEY，OpenRouter 无 TTS 端点。
    live_human = not args.offline and not args.ai_only
    if live_human and not args.confirm_human_consent:
        print("拒绝采集音频：真人验收路径必须显式传入 --confirm-human-consent")
        sys.exit(2)
    has_llm_key = any(os.environ.get(k) for k in ("ARK_API_KEY", "MOONSHOT_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"))
    if (args.voice or live_human) and not os.environ.get("OPENAI_API_KEY"):
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
        ok = run_game(args)
        if not ok:
            sys.exit(1)
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
