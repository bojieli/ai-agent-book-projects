#!/usr/bin/env python3
"""
实验 6-6：从配对比较数据构建模型排行榜 —— 命令行入口

统一的 argparse 命令行工具，把整个流程拆成三个子命令：

    battle        运行两两对战，生成对战结果（模拟 / Chatbot Arena 真实数据 / LLM 评判）
    elo           从对战结果计算 Elo 或 Bradley-Terry 评分
    leaderboard   把对战结果或评分渲染成最终排行榜表格
    pipeline      一步跑完 对战 -> Elo -> 排行榜（默认离线可复现）

其中 battle 的 simulate/arena 来源与 elo、leaderboard、pipeline 均为纯离线计算，
无需任何 API；只有 --source llm（LLM 评判对战）需要 LLM API Key：优先用官方
Anthropic（ANTHROPIC_API_KEY），若无则自动回退到 OpenRouter（OPENROUTER_API_KEY），
也可用 --judge-backend openrouter 强制走 OpenRouter（direct key 失效时）。

示例：
    # 离线一条龙：模拟对战 -> Elo -> 排行榜
    python cli.py pipeline

    # 分步运行
    python cli.py battle --source simulate --num-battles 5000 --output battles.json
    python cli.py elo --input battles.json --method bradley-terry --bootstrap 100
    python cli.py leaderboard --input battles.json --top-n 20
"""
import argparse
import json
import os
import sys
import warnings
from typing import List, Optional

import pandas as pd

# Bradley-Terry 的 LogisticRegression 在新版 sklearn 会对 penalty=None 抛
# FutureWarning；bootstrap 会重复上百次，这里静音以保持排行榜输出整洁。
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

from battle_simulator import DEFAULT_TRUE_SKILLS, simulate_battles
from elo_rating import EloRatingSystem


# --------------------------------------------------------------------------- #
# 通用辅助函数
# --------------------------------------------------------------------------- #
def _load_battles(path: str) -> pd.DataFrame:
    """从 JSON 文件加载对战结果，返回带 model_a/model_b/winner 列的 DataFrame。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    # `[]` from --num-battles 0 has no columns; treat as empty battle frame.
    if len(df) == 0:
        return pd.DataFrame(columns=["model_a", "model_b", "winner"])
    required = {"model_a", "model_b", "winner"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"对战文件 {path} 缺少必要字段 {required}，实际字段：{list(df.columns)}"
        )
    return df


def _save_json(obj, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _battle_stats(df: pd.DataFrame) -> dict:
    """统计每个模型的对战场数与胜场（平局按 0.5 计）。"""
    matches: dict = {}
    wins: dict = {}
    for model_a, model_b, winner in zip(df["model_a"], df["model_b"], df["winner"]):
        matches[model_a] = matches.get(model_a, 0) + 1
        matches[model_b] = matches.get(model_b, 0) + 1
        if winner == "model_a":
            wins[model_a] = wins.get(model_a, 0) + 1.0
        elif winner == "model_b":
            wins[model_b] = wins.get(model_b, 0) + 1.0
        else:  # tie / tie (bothbad)
            wins[model_a] = wins.get(model_a, 0) + 0.5
            wins[model_b] = wins.get(model_b, 0) + 0.5
    return {"matches": matches, "wins": wins}


def _compute_online_elo(df: pd.DataFrame, k: float, init_rating: float) -> pd.DataFrame:
    """在线增量 Elo（按记录顺序处理），返回带 model/rating 列的 DataFrame。"""
    elo = EloRatingSystem(initial_rating=init_rating, k_factor=k)
    for model_a, model_b, winner in zip(df["model_a"], df["model_b"], df["winner"]):
        elo.update_ratings(model_a, model_b, winner)
    rows = [(m, r) for m, r, *_ in elo.get_leaderboard()]
    return pd.DataFrame(rows, columns=["model", "rating"])


def _compute_bradley_terry(df: pd.DataFrame, bootstrap: int) -> pd.DataFrame:
    """Bradley-Terry MLE 评分（可选 bootstrap 置信区间）。"""
    # 延迟导入：Bradley-Terry 依赖 scikit-learn，仅在需要时加载。
    from bradley_terry import compute_bradley_terry_leaderboard
    return compute_bradley_terry_leaderboard(df, bootstrap_rounds=bootstrap)


def _compute_ratings(df: pd.DataFrame, method: str, k: float,
                     init_rating: float, bootstrap: int) -> pd.DataFrame:
    if method == "bradley-terry":
        return _compute_bradley_terry(df, bootstrap)
    return _compute_online_elo(df, k, init_rating)


def _print_leaderboard(ratings: pd.DataFrame, df: Optional[pd.DataFrame],
                       top_n: int, title: str) -> None:
    """打印最终排行榜表格。若评分含置信区间则展示 95% CI 列。"""
    has_ci = {"lower_ci", "upper_ci"}.issubset(ratings.columns)
    stats = _battle_stats(df) if df is not None else {"matches": {}, "wins": {}}

    ratings = ratings.sort_values("rating", ascending=False).reset_index(drop=True)

    print("=" * 78)
    print(title)
    print("=" * 78)
    if has_ci:
        header = f"{'排名':<6}{'模型':<24}{'Elo':>8}   {'95% 置信区间':<20}{'场数':>7}{'胜率':>9}"
    else:
        header = f"{'排名':<6}{'模型':<24}{'Elo':>8}   {'场数':>7}{'胜率':>9}"
    print(header)
    print("-" * 78)

    for idx, row in ratings.head(top_n).iterrows():
        model = str(row["model"])
        n = stats["matches"].get(model, 0)
        w = stats["wins"].get(model, 0.0)
        win_rate = (w / n * 100.0) if n else 0.0
        if has_ci:
            ci = f"[{row['lower_ci']:.0f}, {row['upper_ci']:.0f}]"
            print(f"{idx + 1:<6}{model:<24}{row['rating']:>8.1f}   "
                  f"{ci:<20}{n:>7}{win_rate:>8.1f}%")
        else:
            print(f"{idx + 1:<6}{model:<24}{row['rating']:>8.1f}   "
                  f"{n:>7}{win_rate:>8.1f}%")
    print("-" * 78)
    print(f"共 {len(ratings)} 个模型，"
          f"评分范围 {ratings['rating'].min():.1f} ~ {ratings['rating'].max():.1f}")
    if has_ci:
        avg_ci = (ratings["upper_ci"] - ratings["lower_ci"]).mean()
        print(f"平均 95% 置信区间宽度：{avg_ci:.1f} 分")
    print()


# --------------------------------------------------------------------------- #
# 子命令实现
# --------------------------------------------------------------------------- #
def _make_battles(args) -> List[dict]:
    if args.source == "simulate":
        skills = DEFAULT_TRUE_SKILLS
        if args.models:
            # 用户指定模型名时，围绕 1000 分等距分配潜在实力。
            n = len(args.models)
            skills = {m: 1000.0 + (n - 1 - 2 * i) * 40.0 for i, m in enumerate(args.models)}
        print(f"模拟 {args.num_battles} 场对战（{len(skills)} 个模型，"
              f"平局概率 {args.tie_prob}，随机种子 {args.seed}）...")
        battles = simulate_battles(skills, args.num_battles,
                                   tie_prob=args.tie_prob, seed=args.seed)
        print("真实潜在实力（用于事后对照）：")
        for m, s in sorted(skills.items(), key=lambda kv: -kv[1]):
            print(f"  {m:<24}{s:>8.1f}")
        return battles

    if args.source == "arena":
        from data_loader import load_arena_data, filter_data
        from parallel_processing import optimize_dataframe
        if not os.path.exists(args.arena_file):
            print(f"错误：找不到 Chatbot Arena 数据文件 {args.arena_file}。", file=sys.stderr)
            print("可从以下地址下载并保存为该文件名：", file=sys.stderr)
            print("https://storage.googleapis.com/arena_external_data/public/"
                  "clean_battle_20240814_public.json", file=sys.stderr)
            sys.exit(1)
        df = load_arena_data(args.arena_file)
        df = optimize_dataframe(df)
        df = filter_data(df, anony_only=True, use_dedup=True, min_turn=1)
        if args.sample and args.sample < len(df):
            df = df.sample(n=args.sample, random_state=args.seed).reset_index(drop=True)
            print(f"采样 {args.sample} 场对战。")
        return df[["model_a", "model_b", "winner"]].to_dict("records")

    # source == "llm"
    from llm_judge import run_llm_battles
    print("运行 LLM 评判对战（顺序交换以消除位置偏差）...")
    return run_llm_battles(
        candidate_models=args.candidate_models,
        judge_model=args.judge_model,
        backend=args.judge_backend,
    )


def cmd_battle(args) -> None:
    battles = _make_battles(args)
    _save_json(battles, args.output)
    print(f"\n已生成 {len(battles)} 场对战，写入 {args.output}")


def cmd_elo(args) -> None:
    df = _load_battles(args.input)
    print(f"从 {args.input} 加载 {len(df)} 场对战，方法：{args.method}")
    ratings = _compute_ratings(df, args.method, args.k, args.init_rating, args.bootstrap)
    _print_leaderboard(ratings, df, top_n=args.top_n,
                       title=f"Elo 评分（{args.method}）")
    if args.output:
        _save_json(ratings.to_dict("records"), args.output)
        print(f"评分已写入 {args.output}")


def cmd_leaderboard(args) -> None:
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    sample = data[0] if isinstance(data, list) and data else {}
    if "rating" in sample:  # 输入已是评分文件，直接展示。
        ratings = pd.DataFrame(data)
        _print_leaderboard(ratings, None, top_n=args.top_n, title="模型排行榜")
        return
    # 否则视为对战文件：先计算评分再展示。
    df = _load_battles(args.input)
    print(f"从 {args.input} 加载 {len(df)} 场对战，方法：{args.method}")
    ratings = _compute_ratings(df, args.method, args.k, args.init_rating, args.bootstrap)
    _print_leaderboard(ratings, df, top_n=args.top_n, title="模型排行榜")


def cmd_pipeline(args) -> None:
    print("=" * 78)
    print("实验 6-6：对战 -> Elo -> 排行榜（端到端）")
    print("=" * 78)
    battles = _make_battles(args)
    if args.output:
        _save_json(battles, args.output)
        print(f"对战结果写入 {args.output}")
    df = pd.DataFrame(battles)
    print(f"\n用 {args.method} 方法从 {len(df)} 场对战计算评分...")
    ratings = _compute_ratings(df, args.method, args.k, args.init_rating, args.bootstrap)
    _print_leaderboard(ratings, df, top_n=args.top_n, title="最终排行榜")


# --------------------------------------------------------------------------- #
# 参数解析
# --------------------------------------------------------------------------- #
def _add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", choices=["simulate", "arena", "llm"],
                        default="simulate",
                        help="对战来源：simulate=离线模拟(默认)，arena=真实 Chatbot Arena 数据，"
                             "llm=LLM 评判(需 API)")
    parser.add_argument("--models", nargs="+", default=None,
                        help="simulate：自定义模型名列表（默认使用内置 8 个模型）")
    parser.add_argument("--num-battles", type=int, default=3000,
                        help="simulate：模拟对战场数（默认 3000）")
    parser.add_argument("--tie-prob", type=float, default=0.1,
                        help="simulate：平局概率（默认 0.1）")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子（默认 42）")
    parser.add_argument("--arena-file", default="arena_data.json",
                        help="arena：Chatbot Arena 数据文件路径（默认 arena_data.json）")
    parser.add_argument("--sample", type=int, default=0,
                        help="arena：随机采样 N 场对战，0 表示全部（默认 0）")
    parser.add_argument("--candidate-models", nargs="+", default=None,
                        help="llm：参与对战的候选模型（默认 Claude 系列）")
    parser.add_argument("--judge-model", default="claude-opus-4-8",
                        help="llm：评判模型（默认 claude-opus-4-8）")
    parser.add_argument("--judge-backend", choices=["anthropic", "openrouter", "auto"],
                        default="auto",
                        help="llm：评判后端。auto=有 ANTHROPIC_API_KEY 用官方 Anthropic，"
                             "否则回退到 OpenRouter（OPENROUTER_API_KEY）；"
                             "openrouter=强制走 OpenRouter（direct key 失效时用）")


def _add_rating_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--method", choices=["online-elo", "bradley-terry"],
                        default="online-elo",
                        help="评分方法：online-elo=在线增量 Elo(默认)，"
                             "bradley-terry=官方 MLE 拟合")
    parser.add_argument("--k", type=float, default=4.0,
                        help="online-elo：K 因子/学习率（默认 4.0，官方取值）")
    parser.add_argument("--init-rating", type=float, default=1000.0,
                        help="初始评分（默认 1000）")
    parser.add_argument("--bootstrap", type=int, default=0,
                        help="bradley-terry：bootstrap 轮数以估计 95%% 置信区间（默认 0=不估计）")
    parser.add_argument("--top-n", type=int, default=20,
                        help="排行榜展示的模型数量（默认 20）")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="实验 6-6：从配对比较数据构建模型排行榜（对战 -> Elo -> 排行榜）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", metavar="{battle,elo,leaderboard,pipeline}")

    # battle
    p_battle = sub.add_parser("battle", help="运行两两对战，生成对战结果")
    _add_source_args(p_battle)
    p_battle.add_argument("--output", default="battles.json",
                          help="对战结果输出文件（默认 battles.json）")
    p_battle.set_defaults(func=cmd_battle)

    # elo
    p_elo = sub.add_parser("elo", help="从对战结果计算 Elo / Bradley-Terry 评分")
    p_elo.add_argument("--input", default="battles.json",
                       help="对战结果输入文件（默认 battles.json）")
    _add_rating_args(p_elo)
    p_elo.add_argument("--output", default=None,
                       help="把评分写入 JSON 文件（可选）")
    p_elo.set_defaults(func=cmd_elo)

    # leaderboard
    p_lb = sub.add_parser("leaderboard", help="显示最终排行榜表格")
    p_lb.add_argument("--input", default="battles.json",
                      help="对战结果或评分输入文件（默认 battles.json）")
    _add_rating_args(p_lb)
    p_lb.set_defaults(func=cmd_leaderboard)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="一步跑完 对战 -> Elo -> 排行榜（默认离线）")
    _add_source_args(p_pipe)
    _add_rating_args(p_pipe)
    p_pipe.add_argument("--output", default=None,
                        help="把对战结果写入 JSON 文件（可选）")
    p_pipe.set_defaults(func=cmd_pipeline)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    # 无子命令时默认运行离线端到端演示，保留开箱即用体验。
    args = parser.parse_args(argv if argv is not None else (sys.argv[1:] or ["pipeline"]))
    try:
        args.func(args)
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # 例如无效 ANTHROPIC_API_KEY 触发的 anthropic.AuthenticationError
        print(f"错误：{type(exc).__name__}: {exc}", file=sys.stderr)
        print("（若为 LLM 评审路径，请检查对应 provider 的 API key 是否有效）", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
