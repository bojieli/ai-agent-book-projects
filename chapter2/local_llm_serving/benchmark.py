#!/usr/bin/env python3
"""
本地 LLM 服务性能基准（实验 2-1 配套）

本脚本通过 OpenAI 兼容接口（vLLM 或 Ollama 均可）测量本地部署的小模型在
「服务（serving）」层面的三个核心指标，帮助读者建立对吞吐 / 延迟 / 批处理 /
KV Cache 的直觉：

  1. throughput —— 单流解码吞吐（tokens/s）与首 token 延迟（TTFT）
  2. kv-cache  —— 前缀缓存命中 vs 未命中的 TTFT 对比
                （对应实验 2-1 第 5 点：系统提示词不变时缓存命中更快，
                 修改系统提示词开头几个字符导致缓存失效、需重算整个前缀）
  3. batching  —— 不同并发度下的聚合吞吐，直观展示批处理带来的吞吐提升

所有数字均来自真实服务端的实测，脚本本身不产生任何合成数据。
如果尚未启动服务端，可用 --dry-run 离线查看每个场景将要发出的请求配置。

示例：
    # 先启动服务端（二选一）
    python server.py                    # vLLM（需要 NVIDIA GPU）
    ollama serve && ollama pull qwen3:0.6b   # Ollama（Mac / 无 GPU）

    # 跑全部场景并保存结果
    python benchmark.py --scenario all --output results.json

    # 只看 KV Cache 命中 / 未命中的 TTFT 对比
    python benchmark.py --scenario kv-cache --backend ollama

    # 批处理吞吐扫描
    python benchmark.py --scenario batching --concurrency 1,2,4,8
"""

import argparse
import json
import logging
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("benchmark")

# 各后端的默认 OpenAI 兼容地址
BACKEND_DEFAULTS = {
    "vllm": {"base_url": "http://localhost:8000/v1", "model": "Qwen3-0.6B"},
    "ollama": {"base_url": "http://localhost:11434/v1", "model": "qwen3:0.6b"},
}

# 一段确定性的填充文本，用于把共享前缀撑长，让 KV Cache 的效果更明显
_FILLER_SENTENCE = (
    "You are a meticulous assistant that follows the operating manual precisely. "
)


def build_padded_system_prompt(target_tokens: int) -> str:
    """构造一个约含 target_tokens 个 token 的系统提示词（用重复句子填充）。

    这里用「4 字符 ≈ 1 token」的粗略估计来控制长度，只需保证前缀足够长、
    可复现即可，不追求精确的 token 数。
    """
    header = (
        "# Operating Manual\n"
        "You are a helpful local assistant deployed for the AI Agent book experiment.\n\n"
    )
    approx_chars = max(0, target_tokens * 4 - len(header))
    repeats = approx_chars // len(_FILLER_SENTENCE) + 1
    body = _FILLER_SENTENCE * repeats
    return header + body


def make_client(base_url: str, api_key: str):
    """创建 OpenAI 兼容客户端。"""
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("缺少依赖 openai，请先执行：pip install openai")
        sys.exit(1)
    return OpenAI(base_url=base_url, api_key=api_key)


def stream_once(
    client,
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> Dict[str, float]:
    """发起一次流式请求，返回 TTFT、总时长、输出 token 数与解码吞吐。

    - ttft：从发起请求到收到第一个内容或推理分片的时间（秒）
    - total：整个响应的墙钟时间（秒）
    - output_tokens：优先取服务端返回的 usage.completion_tokens，
      否则用收到的内容分片数量作为近似
    - decode_tps：解码阶段吞吐 = 输出 token / (总时长 - TTFT)
    """
    start = time.perf_counter()
    ttft: Optional[float] = None
    chunk_count = 0
    usage_tokens: Optional[int] = None

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in stream:
        # 最后一个分片可能只携带 usage 而没有 choices
        if getattr(chunk, "usage", None) is not None:
            try:
                usage_tokens = chunk.usage.completion_tokens
            except AttributeError:
                pass
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        text = (
            getattr(delta, "content", None)
            or getattr(delta, "reasoning_content", None)
            or getattr(delta, "reasoning", None)
        )
        if text:
            if ttft is None:
                ttft = time.perf_counter() - start
            chunk_count += 1

    total = time.perf_counter() - start
    if ttft is None:
        ttft = total
    output_tokens = usage_tokens if usage_tokens is not None else chunk_count
    decode_time = max(total - ttft, 1e-6)
    decode_tps = output_tokens / decode_time if output_tokens else 0.0

    return {
        "ttft": ttft,
        "total": total,
        "output_tokens": float(output_tokens),
        "decode_tps": decode_tps,
    }


# --------------------------------------------------------------------------- #
# 场景实现
# --------------------------------------------------------------------------- #
def scenario_throughput(client, model, args) -> Dict[str, Any]:
    """单流吞吐 + TTFT：连续发起若干次解码密集的请求并汇总统计。"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Write a detailed explanation of how KV Cache works in transformer inference.",
        },
    ]
    runs = []
    for i in range(args.repeats):
        r = stream_once(client, model, messages, args.max_tokens, args.temperature)
        runs.append(r)
        logger.info(
            "throughput 第 %d/%d 次: TTFT=%.3fs, 解码=%.1f tok/s, 输出=%d tok",
            i + 1, args.repeats, r["ttft"], r["decode_tps"], int(r["output_tokens"]),
        )
    return {
        "scenario": "throughput",
        "repeats": args.repeats,
        "ttft_mean_s": statistics.fmean(x["ttft"] for x in runs),
        "decode_tps_mean": statistics.fmean(x["decode_tps"] for x in runs),
        "output_tokens_mean": statistics.fmean(x["output_tokens"] for x in runs),
        "runs": runs,
    }


def scenario_kv_cache(client, model, args) -> Dict[str, Any]:
    """KV Cache 命中 vs 未命中的 TTFT 对比（实验 2-1 第 5 点）。

    - 命中组：系统提示词逐字节不变，重复发送同一请求，服务端前缀缓存命中，
      prefill 几乎可以跳过 → TTFT 明显更低。
    - 未命中组：每次只在系统提示词「开头」插入一个不同的计数串，前缀被改写，
      缓存全部失效，服务端必须重算整个前缀 → TTFT 明显更高。
    两组的提示词长度基本一致，因此差异主要来自前缀缓存是否命中。
    """
    base_prompt = build_padded_system_prompt(args.prefix_tokens)
    user_msg = {"role": "user", "content": "In one short sentence, say hello."}

    # 预热：先发一次把缓存写入（这一次一定是冷启动，不计入统计）
    warm_msgs = [{"role": "system", "content": base_prompt}, user_msg]
    stream_once(client, model, warm_msgs, args.max_tokens, args.temperature)

    hit_ttfts, miss_ttfts = [], []
    for i in range(args.repeats):
        # 命中：完全相同的前缀
        hit = stream_once(client, model, warm_msgs, args.max_tokens, args.temperature)
        hit_ttfts.append(hit["ttft"])

        # 未命中：在开头插入唯一前缀，使缓存失效
        mutated = f"[req-{i}-{time.time_ns()}] " + base_prompt
        miss_msgs = [{"role": "system", "content": mutated}, user_msg]
        miss = stream_once(client, model, miss_msgs, args.max_tokens, args.temperature)
        miss_ttfts.append(miss["ttft"])

        logger.info(
            "kv-cache 第 %d/%d 次: 命中 TTFT=%.3fs, 未命中 TTFT=%.3fs",
            i + 1, args.repeats, hit["ttft"], miss["ttft"],
        )

    hit_mean = statistics.fmean(hit_ttfts)
    miss_mean = statistics.fmean(miss_ttfts)
    return {
        "scenario": "kv-cache",
        "prefix_tokens_approx": args.prefix_tokens,
        "repeats": args.repeats,
        "ttft_hit_mean_s": hit_mean,
        "ttft_miss_mean_s": miss_mean,
        "speedup": (miss_mean / hit_mean) if hit_mean > 0 else None,
        "ttft_hit_s": hit_ttfts,
        "ttft_miss_s": miss_ttfts,
    }


def scenario_batching(client, model, args) -> Dict[str, Any]:
    """批处理：在不同并发度下并发发起请求，测量聚合吞吐。

    连续批处理（continuous batching）是本地 serving 的核心优化：并发越高，
    GPU 利用率越充分，系统聚合吞吐（所有请求合计 tok/s）通常显著上升，
    但单个请求的延迟可能上升。此场景把这个权衡直接量化出来。
    """
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain what a large language model is."},
    ]

    levels = args.concurrency
    rows = []
    for level in levels:
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=level) as pool:
            futures = [
                pool.submit(
                    stream_once, client, model, messages, args.max_tokens, args.temperature
                )
                for _ in range(level)
            ]
            results = [f.result() for f in futures]
        wall = time.perf_counter() - start
        total_tokens = sum(r["output_tokens"] for r in results)
        agg_tps = total_tokens / wall if wall > 0 else 0.0
        per_req_tps = agg_tps / level if level else 0.0
        rows.append(
            {
                "concurrency": level,
                "wall_s": wall,
                "total_output_tokens": total_tokens,
                "aggregate_tps": agg_tps,
                "per_request_tps": per_req_tps,
                "ttft_mean_s": statistics.fmean(r["ttft"] for r in results),
            }
        )
        logger.info(
            "batching 并发=%d: 聚合吞吐=%.1f tok/s, 单请求=%.1f tok/s, 墙钟=%.2fs",
            level, agg_tps, per_req_tps, wall,
        )
    return {"scenario": "batching", "levels": rows}


# --------------------------------------------------------------------------- #
# 结果表格
# --------------------------------------------------------------------------- #
def print_report(results: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 68)
    print("本地 LLM 服务基准结果")
    print("=" * 68)
    for res in results:
        s = res["scenario"]
        if s == "throughput":
            print("\n[throughput] 单流吞吐 / 首 token 延迟")
            print(f"  次数           : {res['repeats']}")
            print(f"  平均 TTFT      : {res['ttft_mean_s']:.3f} s")
            print(f"  平均解码吞吐   : {res['decode_tps_mean']:.1f} tok/s")
            print(f"  平均输出长度   : {res['output_tokens_mean']:.0f} tok")
        elif s == "kv-cache":
            print("\n[kv-cache] 前缀缓存命中 vs 未命中（TTFT）")
            print(f"  前缀长度(约)   : {res['prefix_tokens_approx']} tok")
            print(f"  命中平均 TTFT  : {res['ttft_hit_mean_s']:.3f} s")
            print(f"  未命中平均TTFT : {res['ttft_miss_mean_s']:.3f} s")
            if res.get("speedup"):
                print(f"  缓存加速比     : {res['speedup']:.2f}x")
        elif s == "batching":
            print("\n[batching] 并发度对聚合吞吐的影响")
            print(f"  {'并发':>4} | {'聚合tok/s':>10} | {'单请求tok/s':>12} | {'平均TTFT(s)':>11} | {'墙钟(s)':>8}")
            print(f"  {'-'*4}-+-{'-'*10}-+-{'-'*12}-+-{'-'*11}-+-{'-'*8}")
            for row in res["levels"]:
                print(
                    f"  {row['concurrency']:>4} | {row['aggregate_tps']:>10.1f} | "
                    f"{row['per_request_tps']:>12.1f} | {row['ttft_mean_s']:>11.3f} | {row['wall_s']:>8.2f}"
                )
    print("\n" + "=" * 68)


def describe_dry_run(args) -> None:
    """离线打印将要执行的场景配置，不访问服务端。"""
    print("=" * 68)
    print("DRY RUN —— 仅打印计划，不访问服务端")
    print("=" * 68)
    print(f"后端         : {args.backend}")
    print(f"base_url     : {args.base_url}")
    print(f"模型         : {args.model}")
    print(f"重复次数     : {args.repeats}")
    print(f"max_tokens   : {args.max_tokens}")
    print(f"temperature  : {args.temperature}")
    scenarios = ["throughput", "kv-cache", "batching"] if args.scenario == "all" else [args.scenario]
    print(f"待运行场景   : {', '.join(scenarios)}")
    if "kv-cache" in scenarios:
        prompt = build_padded_system_prompt(args.prefix_tokens)
        print(f"  kv-cache   : 填充前缀约 {args.prefix_tokens} tok（实际 {len(prompt)} 字符）")
    if "batching" in scenarios:
        print(f"  batching   : 并发扫描 {args.concurrency}")
    print("=" * 68)


def parse_concurrency(value: str) -> List[int]:
    try:
        levels = [int(x) for x in value.split(",") if x.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError("--concurrency 需为逗号分隔的正整数，例如 1,2,4,8")
    if not levels or any(x <= 0 for x in levels):
        raise argparse.ArgumentTypeError("--concurrency 中的并发度必须为正整数")
    return levels


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="本地 LLM 服务性能基准：吞吐 / 延迟 / KV Cache / 批处理（实验 2-1 配套）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "场景说明:\n"
            "  throughput  单流解码吞吐(tok/s)与首 token 延迟(TTFT)\n"
            "  kv-cache    前缀缓存命中 vs 未命中的 TTFT 对比\n"
            "  batching    不同并发度下的聚合吞吐（批处理权衡）\n"
            "  all         依次运行以上全部场景\n"
        ),
    )
    parser.add_argument(
        "--scenario",
        choices=["throughput", "kv-cache", "batching", "all"],
        default="all",
        help="要运行的基准场景（默认: all）",
    )
    parser.add_argument(
        "--backend",
        choices=["vllm", "ollama"],
        default="vllm",
        help="服务端类型，用于推断默认地址与模型名（默认: vllm）",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="OpenAI 兼容接口地址，覆盖后端默认值（如 http://localhost:8000/v1）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="模型名，覆盖后端默认值（vLLM 默认 Qwen3-0.6B，Ollama 默认 qwen3:0.6b）",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default="EMPTY",
        help="API Key，本地服务端一般无需真实值（默认: EMPTY）",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="throughput / kv-cache 场景的重复次数（默认: 5）",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=256,
        help="每次请求的最大生成 token 数（默认: 256）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="采样温度（默认: 0.7）",
    )
    parser.add_argument(
        "--prefix-tokens",
        type=int,
        default=1024,
        help="kv-cache 场景中共享前缀的近似 token 长度，越长缓存效果越明显（默认: 1024）",
    )
    parser.add_argument(
        "--concurrency",
        type=parse_concurrency,
        default=[1, 2, 4, 8],
        help="batching 场景的并发度列表，逗号分隔（默认: 1,2,4,8）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="将结果以 JSON 写入指定文件",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="离线打印计划而不访问服务端，用于验证配置",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # 用后端默认值补全 base_url / model
    defaults = BACKEND_DEFAULTS[args.backend]
    if args.base_url is None:
        args.base_url = defaults["base_url"]
    if args.model is None:
        args.model = defaults["model"]

    print("=" * 68)
    print("🚀 本地 LLM 服务性能基准（实验 2-1）")
    print("=" * 68)

    if args.dry_run:
        describe_dry_run(args)
        return 0

    client = make_client(args.base_url, args.api_key)
    logger.info("连接服务端: %s（模型: %s）", args.base_url, args.model)

    scenarios = (
        ["throughput", "kv-cache", "batching"]
        if args.scenario == "all"
        else [args.scenario]
    )
    dispatch = {
        "throughput": scenario_throughput,
        "kv-cache": scenario_kv_cache,
        "batching": scenario_batching,
    }

    results: List[Dict[str, Any]] = []
    try:
        for name in scenarios:
            logger.info("开始场景: %s", name)
            results.append(dispatch[name](client, args.model, args))
    except Exception as e:  # noqa: BLE001
        logger.error("基准执行失败: %s", e)
        logger.info(
            "请确认服务端已启动：vLLM 用 `python server.py`，"
            "Ollama 用 `ollama serve` 并已 `ollama pull %s`",
            args.model,
        )
        return 1

    print_report(results)

    if args.output:
        payload = {
            "backend": args.backend,
            "base_url": args.base_url,
            "model": args.model,
            "results": results,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("结果已写入: %s", args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
