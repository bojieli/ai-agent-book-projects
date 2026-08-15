"""
实验 6-7：Agent 任务的端到端成本分析（可运行 demo + CLI）。

两种运行方式：
  1) 在线（--live，默认）：真实调用模型（默认 gpt-5.6-luna），token 与 cached_tokens
     取自 API 返回的 usage，成本按单价换算。需要 OPENAI_API_KEY 或 OPENROUTER_API_KEY
     （无 OpenAI key 时自动回退到 OpenRouter；gpt-5.x 只要有 OpenRouter key 就优先走它）。
  2) 离线（--offline）：不打模型，读入一份此前真实运行录下的 trace（canned token
     counts），用可配置的单价重新计算成本、成本构成与 A/B 对比表。无需 API key。

无论哪种方式，都会产出两份交付：
  (a) 单次任务的「按步骤 + 按成本构成」拆解（哪一步最贵、输入/缓存/输出各占多少）。
  (b) A/B 对比表：朴素 vs 仅 KV-cache vs 仅压缩 vs 两者叠加（完整 2×2），
     量化 总 token / 缓存 token / 缓存率 / 成本 / 相对基线的节省。

示例：
  python demo.py                          # 在线，默认跑 A(朴素)+B(优化) 两组
  python demo.py --scenario all           # 在线，跑完整 2×2 四组
  python demo.py --live --save-trace out.json   # 在线跑并把真实用量落盘
  python demo.py --offline                # 离线，用内置 sample_trace.json 重算
  python demo.py --offline --model gpt-4o # 离线，换 gpt-4o 单价重算同一份用量
  python demo.py --offline --price-input 0.20 --price-cached 0.10 --price-output 0.80
"""

import argparse
import json
import os
import sys

import config
from config import PRICING_PRESETS, Pricing


DEFAULT_TRACE = os.path.join(os.path.dirname(__file__), "sample_trace.json")
SCENARIO_KEYS = ["naive", "kv", "compress", "both"]


def _pct(saved: float, base: float) -> str:
    if base == 0:
        return "0.0%"
    return f"{saved / base * 100:.1f}%"


def build_pricing(args) -> Pricing:
    """根据 --model 预设 + --price-* 覆盖，构造本次计费用的单价。"""
    base = PRICING_PRESETS.get(args.model)
    if base is None:
        base = config.default_pricing()
    return Pricing(
        input_per_m=args.price_input if args.price_input is not None else base.input_per_m,
        cached_per_m=args.price_cached if args.price_cached is not None else base.cached_per_m,
        output_per_m=args.price_output if args.price_output is not None else base.output_per_m,
    )


def resolve_scenarios(arg: str):
    """把 --scenario 解析成有序去重的场景 key 列表。"""
    if arg == "all":
        return list(SCENARIO_KEYS)
    if arg == "ab":
        return ["naive", "both"]
    keys, seen = [], set()
    for k in arg.split(","):
        k = k.strip()
        if k and k not in seen:
            keys.append(k)
            seen.add(k)
    return keys


# ---------------------------------------------------------------------------
# 采集：在线跑真实模型，或离线从 trace 文件读回
# ---------------------------------------------------------------------------
def collect_live(keys, pricing, warmup: bool):
    import agent

    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")):
        print("未检测到 OPENAI_API_KEY 或 OPENROUTER_API_KEY，请先 export 其一 "
              "（无 OpenAI key 时会自动回退到 OpenRouter），或改用 --offline（离线复算，无需 key）。",
              file=sys.stderr)
        sys.exit(1)

    # 构造 client 并解析实际模型名（可能被回退映射成 OpenRouter id）。
    client, resolved = config.make_client_and_model(config.MODEL)
    if resolved != config.MODEL:
        print(f">>> 已回退到 OpenRouter：模型 {config.MODEL} -> {resolved}")
        config.MODEL = resolved
        agent.MODEL = resolved
        try:
            agent._encoder.cache_clear()
        except Exception:
            pass
    tracers = []
    for k in keys:
        name, kv, compress = agent.SCENARIOS[k]
        # KV-cache 组先跑一次「预热」，把稳定前缀写入 OpenAI 的 prompt cache，
        # 让正式计量时更稳定地命中 cached_tokens（真实系统里前缀早已是热的）。
        if kv and warmup:
            print(f">>> 预热 [{name}] 的稳定前缀（写入 prompt cache）...")
            agent.run_scenario(client, kv, compress, name=name, pricing=pricing)
        print(f">>> 正在运行 [{name}] {'(在线计量)' if kv else ''}...")
        tr = agent.run_scenario(client, kv, compress, name=name, pricing=pricing)
        tracers.append((k, tr))
    return tracers


def collect_offline(keys, pricing, trace_path):
    from tracer import Tracer

    if not os.path.exists(trace_path):
        print(f"找不到 trace 文件：{trace_path}", file=sys.stderr)
        sys.exit(1)
    with open(trace_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    by_key = {s.get("key", s.get("name")): s for s in data.get("scenarios", [])}
    print(f"离线模式：读入 {trace_path}")
    print(f"  该 trace 采集自模型 = {data.get('model', '?')}，"
          f"共 {len(by_key)} 个场景的真实录制用量（token 数为实测，成本按当前单价重算）。")

    tracers = []
    for k in keys:
        sc = by_key.get(k)
        if sc is None:
            print(f"  [跳过] trace 中没有场景 '{k}'（可用在线模式 --save-trace 补录）",
                  file=sys.stderr)
            continue
        spans = sc.get("spans")
        if not spans:
            print(f"  [跳过] trace 中场景 '{k}' 缺少 spans 数据"
                  f"（可用在线模式 --save-trace 补录）", file=sys.stderr)
            continue
        tr = Tracer.from_records(spans, name=sc.get("name", k), pricing=pricing)
        tracers.append((k, tr))
    if not tracers:
        print("trace 里没有任何被选中的场景，退出。", file=sys.stderr)
        sys.exit(1)
    return tracers


# ---------------------------------------------------------------------------
# 交付 (b)：A/B 对比表
# ---------------------------------------------------------------------------
def print_ab_table(tracers):
    print("\n\n===== A/B 成本对比（同一个 8 轮客服退款任务）=====")
    header = (f"{'方案':<26} {'总输入tok':>10} {'缓存tok':>10} {'缓存率':>8} "
              f"{'输出tok':>8} {'总成本($)':>12} {'vs基线':>10}")
    print(header)
    print("-" * len(header))

    base_cost = tracers[0][1].total_cost()
    for _, tr in tracers:
        pin = tr.total_prompt_tokens()
        cac = tr.total_cached_tokens()
        rate = f"{(cac / pin * 100):.1f}%" if pin else "0.0%"
        cost = tr.total_cost()
        vs = "基线" if abs(cost - base_cost) < 1e-12 else f"-{_pct(base_cost - cost, base_cost)}"
        print(f"{tr.name:<26} {pin:>10} {cac:>10} {rate:>8} "
              f"{tr.total_completion_tokens():>8} {cost:>12.6f} {vs:>10}")
    print("-" * len(header))

    # 用第一个（基线）和最后一个（通常是 both 优化）做重点量化
    base_k, base = tracers[0]
    best_k, best = tracers[-1]
    if base_k != best_k:
        tok_a = base.total_prompt_tokens() + base.total_completion_tokens()
        tok_b = best.total_prompt_tokens() + best.total_completion_tokens()
        cost_a, cost_b = base.total_cost(), best.total_cost()
        print(f"\n重点对比：{base.name}  →  {best.name}")
        print(f"  总 token:   A={tok_a}  →  B={tok_b}   "
              f"减少 {tok_a - tok_b} ({_pct(tok_a - tok_b, tok_a)})")
        print(f"  缓存 token: A={base.total_cached_tokens()}  →  "
              f"B={best.total_cached_tokens()}   （B 靠稳定前缀命中缓存）")
        print(f"  总成本:     A=${cost_a:.6f}  →  B=${cost_b:.6f}   "
              f"降低 ${cost_a - cost_b:.6f} ({_pct(cost_a - cost_b, cost_a)})")
        if cost_b > 0:
            print(f"  成本倍率:   A 是 B 的 {cost_a / cost_b:.2f} 倍")

    print("\n结论: 稳定长前缀让重复的系统提示/工具定义/历史轮次按缓存价计费，")
    print("      叠加上下文压缩控制上下文增长，二者共同显著降低了端到端成本。")


def dump_output(path, tracers, pricing, model):
    out = {
        "model": model,
        "pricing": {"input": pricing.input_per_m, "cached": pricing.cached_per_m,
                    "output": pricing.output_per_m},
        "scenarios": [],
    }
    import agent
    for k, tr in tracers:
        name = agent.SCENARIOS[k][0] if k in agent.SCENARIOS else tr.name
        out["scenarios"].append({
            "key": k, "name": name,
            "total_cost": tr.total_cost(),
            "component_costs": tr.component_costs(),
            "cost_distribution": tr.cost_distribution(),
            "spans": tr.to_records(),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n已写出结果到 {path}")


def build_parser():
    p = argparse.ArgumentParser(
        prog="demo.py",
        description="实验 6-7：Agent 任务端到端成本分析——对客服退款 Agent 做全链路成本拆解，"
                    "并对比 KV-cache / 上下文压缩两个杠杆的成本差异（完整 2×2 A/B）。",
        epilog="示例：\n"
               "  python demo.py                       # 在线，默认跑 A(朴素)+B(优化)\n"
               "  python demo.py --scenario all        # 在线，跑完整 2×2 四组\n"
               "  python demo.py --offline             # 离线，用内置 canned trace 重算（无需 key）\n"
               "  python demo.py --offline --model gpt-4o   # 换单价离线重算\n"
               "  python demo.py --live --save-trace out.json  # 在线跑并落盘真实用量\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true",
                      help="在线模式（默认）：真实调用 OpenAI，需要 OPENAI_API_KEY。")
    mode.add_argument("--offline", action="store_true",
                      help="离线模式：不打模型，从 trace 文件读真实录制的 token 用量并按单价重算成本。")
    p.add_argument("--trace", metavar="FILE", default=DEFAULT_TRACE,
                   help=f"离线模式读取的 trace（canned token counts）文件，默认 {os.path.basename(DEFAULT_TRACE)}。")
    p.add_argument("--save-trace", metavar="FILE", default=None,
                   help="在线模式下把本次真实 token 用量落盘为 trace 文件（供之后 --offline 复算）。")
    p.add_argument("--scenario", metavar="NAME", default="ab",
                   help="选择要跑的 A/B 场景：ab(默认,=naive+both) / all(2×2 四组) / "
                        "或逗号分隔的子集 naive,kv,compress,both。")
    p.add_argument("--model", metavar="NAME", default=config.MODEL,
                   help=f"模型名（决定默认单价预设，可选 {', '.join(PRICING_PRESETS)}），"
                        f"默认 {config.MODEL}。")
    p.add_argument("--price-input", type=float, default=None,
                   help="覆盖输入单价（每百万 token 美元）。")
    p.add_argument("--price-cached", type=float, default=None,
                   help="覆盖缓存命中输入单价（每百万 token 美元）。")
    p.add_argument("--price-output", type=float, default=None,
                   help="覆盖输出单价（每百万 token 美元）。")
    p.add_argument("--no-warmup", action="store_true",
                   help="在线模式下关闭 KV-cache 组的前缀预热（默认预热以稳定命中缓存）。")
    p.add_argument("--output", metavar="FILE", default=None,
                   help="把成本拆解结果（含成本构成/分布/逐步用量）写成 JSON 文件。")
    return p


def main():
    args = build_parser().parse_args()

    # 让 agent / tracer 使用选定模型
    config.MODEL = args.model
    try:
        import agent
        agent.MODEL = args.model
        agent._encoder.cache_clear()
    except Exception:
        pass

    pricing = build_pricing(args)
    keys = resolve_scenarios(args.scenario)
    bad = [k for k in keys if k not in SCENARIO_KEYS]
    if bad:
        print(f"未知场景 {bad}，可选：{SCENARIO_KEYS} / all / ab", file=sys.stderr)
        sys.exit(2)

    print(f"模型: {args.model}")
    print(f"单价(每百万token): 输入 ${pricing.input_per_m} / 缓存输入 ${pricing.cached_per_m} "
          f"/ 输出 ${pricing.output_per_m}")

    if args.offline:
        tracers = collect_offline(keys, pricing, args.trace)
    else:
        print("说明: OpenAI prompt caching 自动生效（前缀>=1024token 且近期命中相同前缀），")
        print("      命中的输入 token 出现在 usage.prompt_tokens_details.cached_tokens。")
        tracers = collect_live(keys, pricing, warmup=not args.no_warmup)
        if args.save_trace:
            dump_output(args.save_trace, tracers, pricing, args.model)

    # 交付 (a)：逐场景成本拆解
    for _, tr in tracers:
        tr.print_breakdown(title=f"{tr.name}（单次任务全链路拆解）")

    # 交付 (b)：A/B 对比表
    if len(tracers) >= 2:
        print_ab_table(tracers)

    if args.output:
        dump_output(args.output, tracers, pricing, args.model)


if __name__ == "__main__":
    main()
