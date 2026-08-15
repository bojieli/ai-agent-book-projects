"""
demo.py —— 一条命令跑出多提供商性能对比表 / 并发压测表。

用法：
    python demo.py                      # 使用默认参数，多提供商横向对比
    python demo.py --num-requests 20 --concurrency 5
    python demo.py --serial             # 串行发送（并发=1）
    python demo.py --list               # 仅列出将要测试的提供商

    # 指定任意一个 OpenAI 兼容端点（不改代码即可测新模型/新提供商）：
    python demo.py --base-url https://api.deepseek.com --model deepseek-chat \
                   --api-key-env DEEPSEEK_API_KEY

    # 并发压测：对同一模型逐步提升并发，找限流点、看延迟长尾随并发的变化：
    python demo.py --model gpt-5.6-luna --concurrency-sweep 1,2,4,8

    # 离线自检（无需 key/网络）：用合成数据跑通指标聚合数学
    python demo.py --mock
    python demo.py --mock --concurrency-sweep 1,2,4,8,16

默认只测"手上有有效 key"的提供商（OpenAI / Kimi / 豆包）。
未设置对应环境变量的提供商会被自动跳过。
"""

from __future__ import annotations

import argparse
import json
import os

# 若安装了 python-dotenv 且存在 .env，则自动加载（可选，不强制）
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001
    pass

from benchmark import (
    DEFAULT_PROVIDERS,
    ProviderConfig,
    ProviderSummary,
    run_benchmark,
    sweep_concurrency,
    synthetic_summary,
)


# 短 prompt：控制成本，同时保证有稳定的输出用于测吞吐。
DEFAULT_PROMPT = "用一句话解释什么是大语言模型。"

# 主对比表可选的指标族（成功率始终显示）。--metrics 用逗号选择子集。
METRIC_KEYS = ["ttft", "e2e", "throughput", "tokens"]


def _fmt(v, unit: str = "", scale: float = 1.0, digits: int = 1) -> str:
    """把可能为 None 的数值格式化为对齐的字符串。"""
    if v is None:
        return "  N/A"
    return f"{v * scale:.{digits}f}{unit}"


def _render_table(headers: list[str], rows: list[list[str]]) -> None:
    """按中文宽度对齐打印一张表。"""
    def width(text: str) -> int:
        return sum(2 if ord(c) > 127 else 1 for c in text)

    cols = len(headers)
    col_w = [width(headers[i]) for i in range(cols)]
    for row in rows:
        for i in range(cols):
            col_w[i] = max(col_w[i], width(row[i]))

    def pad(text: str, w: int) -> str:
        return text + " " * (w - width(text))

    sep = "-+-".join("-" * col_w[i] for i in range(cols))
    print()
    print(" | ".join(pad(headers[i], col_w[i]) for i in range(cols)))
    print(sep)
    for row in rows:
        print(" | ".join(pad(row[i], col_w[i]) for i in range(cols)))
    print()


def _print_errors(summaries: list[ProviderSummary]) -> None:
    """打印失败明细，便于定位可用性问题。"""
    if not any(s.errors for s in summaries):
        return
    print("失败请求明细（可用性下降原因）：")
    for s in summaries:
        if s.errors:
            for e in s.errors[:3]:
                print(f"  - {s.provider}: {e}")
            if len(s.errors) > 3:
                print(f"    ... 以及另外 {len(s.errors) - 3} 条同类错误")
    print()


def print_table(summaries: list[ProviderSummary], metrics: list[str]) -> None:
    """打印多提供商横向对比表（成功率 + 所选指标族）。"""
    headers = ["Provider/Model", "成功率"]
    for m in metrics:
        if m == "ttft":
            headers += ["TTFT均值", "TTFT_p95"]
        elif m == "e2e":
            headers += ["端到端均值", "端到端p95"]
        elif m == "throughput":
            headers += ["吞吐"]
        elif m == "tokens":
            headers += ["输出tok"]

    rows: list[list[str]] = []
    for s in summaries:
        row = [
            s.provider,
            f"{s.success}/{s.total} ({s.availability * 100:.0f}%)",
        ]
        for m in metrics:
            if m == "ttft":
                row += [_fmt(s.stat("ttft", "mean"), "ms", 1000, 0),
                        _fmt(s.stat("ttft", "p95"), "ms", 1000, 0)]
            elif m == "e2e":
                row += [_fmt(s.stat("latency", "mean"), "s", 1, 2),
                        _fmt(s.stat("latency", "p95"), "s", 1, 2)]
            elif m == "throughput":
                row += [_fmt(s.stat("throughput", "mean"), " t/s", 1, 1)]
            elif m == "tokens":
                row += [_fmt(s.stat("completion_tokens", "mean"), "", 1, 0)]
        rows.append(row)

    _render_table(headers, rows)
    _print_errors(summaries)


def print_sweep_table(summaries: list[ProviderSummary]) -> None:
    """
    打印并发压测表：每一行是一个并发档位，展示延迟长尾（p50/p95/p99/std）、
    可用性与聚合吞吐（RPS / tokens·s⁻¹）随并发的变化。
    """
    headers = [
        "并发", "成功率", "TTFT_p50", "TTFT_p95",
        "端到端p50", "端到端p95", "端到端p99", "端到端std",
        "RPS", "聚合吞吐",
    ]
    rows: list[list[str]] = []
    for s in summaries:
        rows.append([
            str(s.concurrency),
            f"{s.success}/{s.total} ({s.availability * 100:.0f}%)",
            _fmt(s.stat("ttft", "p50"), "ms", 1000, 0),
            _fmt(s.stat("ttft", "p95"), "ms", 1000, 0),
            _fmt(s.stat("latency", "p50"), "s", 1, 2),
            _fmt(s.stat("latency", "p95"), "s", 1, 2),
            _fmt(s.stat("latency", "p99"), "s", 1, 2),
            _fmt(s.stat("latency", "std"), "s", 1, 2),
            _fmt(s.rps, "", 1, 1),
            _fmt(s.agg_throughput, " t/s", 1, 1),
        ])
    _render_table(headers, rows)
    _print_errors(summaries)


def summary_to_dict(s: ProviderSummary) -> dict:
    """把一个汇总序列化为可 JSON 落盘的结构（供 --output 使用）。"""
    def stats(attr: str) -> dict:
        return {
            k: s.stat(attr, k)
            for k in ("mean", "std", "p50", "p95", "p99")
        }

    return {
        "provider": s.provider,
        "model": s.model,
        "concurrency": s.concurrency,
        "total": s.total,
        "success": s.success,
        "availability": s.availability,
        "wall_time_s": s.wall_time,
        "rps": s.rps,
        "agg_throughput_tps": s.agg_throughput,
        "ttft_s": stats("ttft"),
        "latency_s": stats("latency"),
        "throughput_tps": stats("throughput"),
        "completion_tokens_mean": s.stat("completion_tokens", "mean"),
        "errors": s.errors[:20],
    }


def write_output(path: str, meta: dict, summaries: list[ProviderSummary]) -> None:
    payload = {"meta": meta, "results": [summary_to_dict(s) for s in summaries]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"结果已写入：{path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="多维度模型性能基准测试（实验 6-8）：TTFT / 端到端 / 吞吐 / p50·p95·p99·std / 可用性",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--num-requests", type=int, default=10,
                        help="每个档位的请求次数（默认 10，控制成本；书中口径 ≥100）")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="单档位并发数（默认 3；与 --concurrency-sweep 二选一）")
    parser.add_argument("--serial", action="store_true",
                        help="串行发送（等价于 --concurrency 1，看无竞争下的基线延迟）")
    parser.add_argument("--concurrency-sweep", type=str, default=None, metavar="1,2,4,8",
                        help="并发压测：逗号分隔的并发档位列表，对同一模型逐档加压找限流点")
    parser.add_argument("--max-tokens", type=int, default=64,
                        help="每次请求生成的最大 token 数（默认 64，控制成本）")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="单次请求超时（秒），超时记为可用性下降")
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT,
                        help="测试用的短 prompt")
    parser.add_argument("--metrics", type=str, default="all",
                        help="主对比表显示的指标族，逗号分隔，可选 "
                             "ttft/e2e/throughput/tokens 或 all（默认 all；成功率始终显示）")
    parser.add_argument("--output", type=str, default=None, metavar="FILE.json",
                        help="把完整结果（含 p50/p95/p99/std）写入 JSON 文件")
    parser.add_argument("--list", action="store_true",
                        help="仅列出将测试的提供商后退出")

    # 指定任意单个 OpenAI 兼容端点（不改代码即可测新提供商/新模型）
    grp = parser.add_argument_group("自定义端点（指定后只测这一个，忽略默认提供商列表）")
    grp.add_argument("--base-url", type=str, default=None,
                     help="OpenAI 兼容端点的 base_url（OpenAI 官方留空）")
    grp.add_argument("--model", type=str, default=None,
                     help="要测试的模型名（如 gpt-5.6-luna / deepseek-chat）")
    grp.add_argument("--api-key-env", type=str, default="OPENAI_API_KEY",
                     help="读取 API key 的环境变量名（默认 OPENAI_API_KEY）")
    grp.add_argument("--name", type=str, default=None,
                     help="该端点在表格中的展示名（默认用 model 名）")

    parser.add_argument("--mock", action="store_true",
                        help="离线自检：用合成（synthetic）数据跑通指标聚合，"
                             "不发任何网络请求、不需要 key（数字为合成，非真实基准）")
    return parser.parse_args()


def resolve_metrics(raw: str) -> list[str]:
    if raw.strip().lower() == "all":
        return list(METRIC_KEYS)
    chosen = [m.strip() for m in raw.split(",") if m.strip()]
    bad = [m for m in chosen if m not in METRIC_KEYS]
    if bad:
        raise SystemExit(f"未知指标：{', '.join(bad)}；可选：{', '.join(METRIC_KEYS)} 或 all")
    return chosen


def build_providers(args: argparse.Namespace) -> tuple[list[ProviderConfig], list[ProviderConfig]]:
    """
    返回 (available, skipped)。
    若指定了 --base-url 或 --model，则构造单个自定义提供商（覆盖默认列表）。
    """
    if args.base_url or args.model:
        if not args.model:
            raise SystemExit("使用自定义端点时必须提供 --model")
        cfg = ProviderConfig(
            name=args.name or f"custom/{args.model}",
            model=args.model,
            api_key_env=args.api_key_env,
            base_url=args.base_url,
        )
        available = [cfg] if cfg.is_available() else []
        skipped = [] if cfg.is_available() else [cfg]
        return available, skipped

    available = [p for p in DEFAULT_PROVIDERS if p.is_available()]
    skipped = [p for p in DEFAULT_PROVIDERS if not p.is_available()]
    return available, skipped


def run_mock(args: argparse.Namespace, metrics: list[str]) -> None:
    """用合成数据演示指标聚合，无需 key/网络。"""
    print("=" * 72)
    print("多维度模型性能基准测试（实验 6-8）—— 合成数据自检模式 [SYNTHETIC]")
    print("=" * 72)
    print("⚠️  以下所有数字均为合成（伪随机）生成，仅用于验证指标聚合数学，")
    print("    不代表任何真实模型/提供商/网络环境的性能，切勿作为选型依据。")
    print("-" * 72)

    name = args.name or (args.model and f"custom/{args.model}") or "mock/demo-model"
    model = args.model or "demo-model"

    if args.concurrency_sweep:
        levels = parse_sweep_levels(args.concurrency_sweep)
        print(f"并发压测（合成）：{name}  档位={levels}  N={args.num_requests}/档")
        summaries = [
            synthetic_summary(name, model, args.num_requests, c, fail_rate=0.02, seed=42)
            for c in levels
        ]
        print_sweep_table(summaries)
        print("解读：并发上升 → 端到端 p95/p99 与 std 走高（长尾变差），")
        print("      可用性因限流下降，聚合吞吐先升后趋平（触及服务端上限即触顶）。")
    else:
        concurrency = 1 if args.serial else args.concurrency
        print(f"单档位对比（合成）：并发={concurrency}  N={args.num_requests}/家")
        # 造三个"提供商"，参数不同以体现横向差异
        summaries = [
            synthetic_summary("mockA/fast-low-ttft", "fast", args.num_requests,
                              concurrency, base_ttft=0.20, base_gen_throughput=110, seed=1),
            synthetic_summary("mockB/balanced", "balanced", args.num_requests,
                              concurrency, base_ttft=0.35, base_gen_throughput=85, seed=2),
            synthetic_summary("mockC/high-throughput", "hi-tp", args.num_requests,
                              concurrency, base_ttft=0.55, base_gen_throughput=140,
                              fail_rate=0.05, seed=3),
        ]
        print_table(summaries, metrics)

    if args.output:
        write_output(args.output, {"mode": "mock-synthetic", "note": "数字为合成，非真实基准"},
                     summaries)


def parse_sweep_levels(raw: str) -> list[int]:
    try:
        levels = [int(x) for x in raw.split(",") if x.strip()]
    except ValueError:
        raise SystemExit(f"--concurrency-sweep 需为逗号分隔的整数，如 1,2,4,8；收到：{raw!r}")
    levels = [c for c in levels if c >= 1]
    if not levels:
        raise SystemExit("--concurrency-sweep 至少需要一个 ≥1 的并发档位")
    return levels


def main() -> None:
    args = parse_args()
    metrics = resolve_metrics(args.metrics)

    if args.mock:
        run_mock(args, metrics)
        return

    available, skipped = build_providers(args)

    print("=" * 72)
    print("多维度模型性能基准测试（实验 6-8）")
    print("=" * 72)
    if skipped:
        for p in skipped:
            print(f"[跳过] {p.name} —— 未设置环境变量 {p.api_key_env}")
    if not available:
        print("没有任何可用提供商：请设置对应 API key 环境变量，")
        print("或用 --mock 在无 key 情况下离线验证指标聚合。")
        return

    print(f"待测提供商：{', '.join(p.name for p in available)}")

    # ---- 并发压测模式 ----
    if args.concurrency_sweep:
        levels = parse_sweep_levels(args.concurrency_sweep)
        print(f"模式：并发压测（逐档加压找限流点）  档位={levels}")
        print(f"参数：N={args.num_requests}/档, max_tokens={args.max_tokens}, "
              f"timeout={args.timeout}s")
        print(f"Prompt：{args.prompt!r}")
        if args.list:
            return
        all_summaries: list[ProviderSummary] = []
        for cfg in available:
            print("-" * 72)
            print(f"压测 {cfg.name}:")
            summaries = sweep_concurrency(
                cfg, args.prompt, args.num_requests, levels,
                args.max_tokens, args.timeout,
            )
            print_sweep_table(summaries)
            all_summaries.extend(summaries)
        if args.output:
            write_output(args.output,
                         {"mode": "concurrency-sweep", "levels": levels}, all_summaries)
        return

    # ---- 单档位横向对比模式（默认，保持原行为）----
    concurrency = 1 if args.serial else args.concurrency
    print(f"参数：N={args.num_requests}/家, 并发={concurrency}, "
          f"max_tokens={args.max_tokens}, timeout={args.timeout}s")
    print(f"Prompt：{args.prompt!r}")

    if args.list:
        return

    print("-" * 72)
    summaries = run_benchmark(
        providers=available,
        prompt=args.prompt,
        num_requests=args.num_requests,
        concurrency=concurrency,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )

    print_table(summaries, metrics)

    print("指标说明：")
    print("  成功率  = 成功请求数 / 总请求数（可用性维度）")
    print("  TTFT    = 首个 token 到达延迟（流式测得），越低越流畅")
    print("  端到端  = 请求发出到响应结束的总耗时")
    print("  吞吐    = 输出 token 数 / 生成阶段耗时（tokens/s）")
    print("  p95     = 95 分位延迟，反映长尾/稳定性（方差大则体验不稳）")
    print("  提示    = 加 --concurrency-sweep 1,2,4,8 可做并发压测，看指标随并发的变化")

    if args.output:
        write_output(args.output,
                     {"mode": "single", "concurrency": concurrency}, summaries)


if __name__ == "__main__":
    main()
