"""
多维度模型性能基准测试（实验 6-8 配套代码）

对多个 OpenAI 兼容的 LLM API 提供商，测量以下核心指标：
    - TTFT（Time To First Token，首个 token 到达延迟）
    - 端到端延迟（发出请求到接收完整响应）
    - 吞吐（tokens/s，按生成的输出 token 计；并发下另给聚合吞吐 / RPS）
    - 标准差 / p50 / p95 / p99 延迟分位数（方差大意味着体验不稳定）
    - 可用性 / 成功率（失败即计入可用性下降，不中断整表）

支持两种模式：
    - 单档位对比：多提供商横向对比表（默认）。
    - 并发扫描（压测）：对同一模型逐步提升并发，观察延迟长尾与聚合吞吐随并发的变化。

实现要点：
    - 使用 openai SDK 的流式接口（stream=True）来精确测量 TTFT。
    - 通过 base_url 复用同一套 OpenAI 兼容协议，适配 Kimi / 豆包等国产 API。
    - 单点请求失败被捕获并记录，不影响同一 (provider, model) 的其它请求，
      也不影响其它 provider —— 这样一次运行就能测出"可用性"这一维度。
"""

from __future__ import annotations

import os
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI


# ---------------------------------------------------------------------------
# OpenRouter 回退：对「OpenAI 原生」条目（base_url 为空）在缺主 key 时改走 OpenRouter。
# gpt-5.x 直连 OpenAI 需组织实名认证，只要有 OPENROUTER_API_KEY 就优先走 OpenRouter。
# ---------------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _to_openrouter_model(model: str) -> str:
    """把模型名映射成 OpenRouter id：含 '/' 视为原生 id；gpt-* -> openai/*；
    claude-* -> anthropic/claude-opus-4.8；其余回退到 openai/gpt-5.6-luna。"""
    if "/" in model:
        return model
    if model.startswith("gpt-"):
        return "openai/" + model
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"


# ---------------------------------------------------------------------------
# 提供商配置
# ---------------------------------------------------------------------------
@dataclass
class ProviderConfig:
    """单个待测 (提供商, 模型) 配置。"""

    name: str                 # 展示名，例如 "OpenAI/gpt-5.6-luna"
    model: str                # 传给 API 的模型名
    api_key_env: str          # 读取 API key 的环境变量名
    base_url: Optional[str] = None  # OpenAI 官方留空；其它填各自 base_url

    def api_key(self) -> Optional[str]:
        return os.environ.get(self.api_key_env)

    def _openrouter_key(self) -> Optional[str]:
        return os.environ.get("OPENROUTER_API_KEY", "").strip() or None

    def resolve(self) -> tuple[Optional[str], Optional[str], str, bool]:
        """解析实际使用的 (api_key, base_url, model, 是否经 OpenRouter)。

        仅「OpenAI 原生」条目（base_url 为空）参与回退；带专属 base_url 的条目
        （如 Kimi/豆包）保持不变。回退规则：
          - gpt-5.x 且有 OPENROUTER_API_KEY -> 优先走 OpenRouter（直连需实名认证）；
          - 否则主 key 存在 -> 直连，模型名不变；
          - 否则（OpenAI 原生 + 有 OPENROUTER_API_KEY）-> 走 OpenRouter，模型名映射。
        """
        primary = self.api_key()
        openai_native = self.base_url is None
        orkey = self._openrouter_key() if openai_native else None
        prefer_or = bool(orkey) and self.model.startswith("gpt-5")

        if not prefer_or and primary:
            return primary, self.base_url, self.model, False
        if orkey:
            return orkey, OPENROUTER_BASE_URL, _to_openrouter_model(self.model), True
        return primary, self.base_url, self.model, False

    def is_available(self) -> bool:
        """主 key 存在即可测；OpenAI 原生条目在缺主 key 时可回退 OpenRouter。"""
        if self.api_key():
            return True
        return self.base_url is None and self._openrouter_key() is not None


# 默认只跑"手上有有效 key"的三家提供商。
# 需要扩展时，往这里追加 ProviderConfig 即可（例如 DeepSeek 官方 vs SiliconFlow 对比）。
DEFAULT_PROVIDERS: list[ProviderConfig] = [
    # OpenAI 官方（一个 key 测多个模型，观察同厂不同规格的差异）
    # gpt-5.6-luna 为当前廉价旗舰；无 OPENAI_API_KEY 时自动经 OpenRouter 路由
    # （openai/gpt-5.6-luna），gpt-5.x 只要有 OPENROUTER_API_KEY 就优先走 OpenRouter。
    ProviderConfig(
        name="OpenAI/gpt-5.6-luna",
        model="gpt-5.6-luna",
        api_key_env="OPENAI_API_KEY",
    ),
    # 月之暗面 Kimi（OpenAI 兼容）
    ProviderConfig(
        name="Moonshot/moonshot-v1-8k",
        model="moonshot-v1-8k",
        api_key_env="MOONSHOT_API_KEY",
        base_url="https://api.moonshot.cn/v1",
    ),
    # 字节豆包 / 火山方舟（OpenAI 兼容）
    ProviderConfig(
        name="Doubao/doubao-1.5-pro-32k",
        model="doubao-1-5-pro-32k-250115",
        api_key_env="ARK_API_KEY",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    ),
]


# ---------------------------------------------------------------------------
# 单次请求测量
# ---------------------------------------------------------------------------
@dataclass
class RequestResult:
    """一次流式请求的测量结果。"""

    ok: bool
    ttft: Optional[float] = None            # 首 token 延迟（秒）
    latency: Optional[float] = None         # 端到端延迟（秒）
    completion_tokens: Optional[int] = None # 生成的输出 token 数
    throughput: Optional[float] = None      # 输出吞吐（tokens/s）
    error: Optional[str] = None             # 失败原因（可用性下降时记录）


def measure_once(
    client: OpenAI,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
) -> RequestResult:
    """
    发起一次流式请求并测量各项指标。

    任何异常都被捕获为一次"失败"，用于统计可用性 —— 绝不向上抛出，
    以免单点故障中断整表测试。
    """
    start = time.perf_counter()
    first_token_at: Optional[float] = None
    completion_tokens = 0
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
            stream=True,
            # 请求用量统计（部分 OpenAI 兼容服务支持；不支持时下方回退到计数）
            stream_options={"include_usage": True},
            timeout=timeout,
        )

        reported_tokens: Optional[int] = None
        for chunk in stream:
            # 首个"有内容"的 chunk 到达时刻即 TTFT
            if chunk.choices:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    completion_tokens += 1  # 回退计数：以流式 chunk 近似 token 数
            # 若服务在末尾回传了精确 usage，则以其为准
            usage = getattr(chunk, "usage", None)
            if usage is not None:
                reported_tokens = getattr(usage, "completion_tokens", None)

        end = time.perf_counter()

        if first_token_at is None:
            # 拿到了响应但没有任何内容 token，视为失败
            return RequestResult(ok=False, error="empty response (no content token)")

        final_tokens = reported_tokens if reported_tokens else completion_tokens
        latency = end - start
        ttft = first_token_at - start
        # 吞吐按"生成阶段"计：输出 token 数 / (端到端 - 首 token 延迟)
        gen_time = max(latency - ttft, 1e-6)
        throughput = final_tokens / gen_time if final_tokens else 0.0

        return RequestResult(
            ok=True,
            ttft=ttft,
            latency=latency,
            completion_tokens=final_tokens,
            throughput=throughput,
        )
    except Exception as exc:  # noqa: BLE001 —— 故意兜底，任何错误都记为可用性下降
        return RequestResult(ok=False, error=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# 聚合结果
# ---------------------------------------------------------------------------
@dataclass
class ProviderSummary:
    provider: str
    model: str
    total: int
    success: int
    results: list[RequestResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    concurrency: int = 1        # 本次批次使用的并发数（并发扫描时用于标注行）
    wall_time: float = 0.0      # 整批请求的墙钟耗时（秒），用于算聚合吞吐/RPS

    @property
    def availability(self) -> float:
        return self.success / self.total if self.total else 0.0

    @property
    def rps(self) -> Optional[float]:
        """吞吐（请求/秒）：成功请求数 / 整批墙钟耗时。并发越高一般越大，直到触顶。"""
        if self.wall_time <= 0:
            return None
        return self.success / self.wall_time

    @property
    def agg_throughput(self) -> Optional[float]:
        """聚合输出吞吐（tokens/s）：全部成功请求的输出 token 总数 / 整批墙钟耗时。"""
        if self.wall_time <= 0:
            return None
        total_tokens = sum(
            r.completion_tokens for r in self.results
            if r.ok and r.completion_tokens
        )
        return total_tokens / self.wall_time if total_tokens else 0.0

    def _vals(self, attr: str) -> list[float]:
        return [getattr(r, attr) for r in self.results if r.ok and getattr(r, attr) is not None]

    @staticmethod
    def _pct(values: list[float], q: float) -> Optional[float]:
        """线性插值分位数；样本过少时退化为最大/最小值。"""
        if not values:
            return None
        s = sorted(values)
        if len(s) == 1:
            return s[0]
        pos = q * (len(s) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(s) - 1)
        frac = pos - lo
        return s[lo] + (s[hi] - s[lo]) * frac

    def stat(self, attr: str, kind: str) -> Optional[float]:
        vals = self._vals(attr)
        if not vals:
            return None
        if kind == "mean":
            return statistics.mean(vals)
        if kind == "std":
            # 标准差：样本 <2 时无从谈起，返回 0 而非报错
            return statistics.stdev(vals) if len(vals) >= 2 else 0.0
        if kind == "p50":
            return self._pct(vals, 0.50)
        if kind == "p95":
            return self._pct(vals, 0.95)
        if kind == "p99":
            return self._pct(vals, 0.99)
        raise ValueError(kind)


def benchmark_provider(
    cfg: ProviderConfig,
    prompt: str,
    num_requests: int,
    concurrency: int,
    max_tokens: int,
    timeout: float,
) -> ProviderSummary:
    """对单个提供商发起 num_requests 次请求（并发 concurrency）。"""
    # 这是延迟基准：显式关闭 SDK 自动重试（max_retries=0），让一次超时/挂起的
    # 请求被如实记为「失败」（计入可用性下降），而不是被静默重试从而拉高延迟、
    # 掩盖真实故障。每次请求仍带 per-call timeout（见 measure_once）。
    # 再加一个客户端级 timeout 作为兜底，避免个别请求永久挂起拖死线程池。
    # 解析实际使用的凭据/端点/模型（OpenAI 原生条目缺 key 时回退 OpenRouter）。
    api_key, base_url, model, via_openrouter = cfg.resolve()
    if via_openrouter:
        print(f"    （回退 OpenRouter：{cfg.model} -> {model}）", flush=True)
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=0,
    )
    results: list[RequestResult] = []

    batch_start = time.perf_counter()
    if concurrency <= 1:
        for _ in range(num_requests):
            results.append(measure_once(client, model, prompt, max_tokens, timeout))
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [
                pool.submit(measure_once, client, model, prompt, max_tokens, timeout)
                for _ in range(num_requests)
            ]
            for fut in as_completed(futures):
                results.append(fut.result())
    wall_time = time.perf_counter() - batch_start

    success = sum(1 for r in results if r.ok)
    errors = [r.error for r in results if not r.ok and r.error]
    return ProviderSummary(
        provider=cfg.name,
        model=model,
        total=num_requests,
        success=success,
        results=results,
        errors=errors,
        concurrency=concurrency,
        wall_time=wall_time,
    )


def run_benchmark(
    providers: list[ProviderConfig],
    prompt: str,
    num_requests: int,
    concurrency: int,
    max_tokens: int,
    timeout: float,
) -> list[ProviderSummary]:
    """依次对每个提供商跑基准测试（提供商之间串行，单提供商内部并发）。"""
    summaries: list[ProviderSummary] = []
    for cfg in providers:
        print(f"  → 正在测试 {cfg.name} "
              f"(model={cfg.model}, N={num_requests}, 并发={concurrency}) ...", flush=True)
        summary = benchmark_provider(
            cfg, prompt, num_requests, concurrency, max_tokens, timeout
        )
        print(f"    完成：成功 {summary.success}/{summary.total}", flush=True)
        summaries.append(summary)
    return summaries


def sweep_concurrency(
    cfg: ProviderConfig,
    prompt: str,
    num_requests: int,
    concurrency_levels: list[int],
    max_tokens: int,
    timeout: float,
) -> list[ProviderSummary]:
    """
    压测：对同一 (provider, model) 逐步提升并发，返回每个并发档位的汇总。

    对应书中"通过逐步提升并发量来找到限流点，记录 RPM/TPM 上限"——
    随着并发上升，单请求延迟（p95）会变差、可用性可能因限流而下降，
    而聚合吞吐（RPS / tokens·s⁻¹）会先升后平（触及服务端上限即触顶）。
    """
    summaries: list[ProviderSummary] = []
    for c in concurrency_levels:
        print(f"  → {cfg.name} @ 并发={c} (N={num_requests}) ...", flush=True)
        summary = benchmark_provider(cfg, prompt, num_requests, c, max_tokens, timeout)
        print(f"    完成：成功 {summary.success}/{summary.total}, "
              f"墙钟 {summary.wall_time:.2f}s", flush=True)
        summaries.append(summary)
    return summaries


# ---------------------------------------------------------------------------
# 合成（synthetic）数据：仅供离线演示指标聚合，绝非真实基准
# ---------------------------------------------------------------------------
def synthetic_summary(
    provider: str,
    model: str,
    num_requests: int,
    concurrency: int,
    *,
    base_ttft: float = 0.30,
    base_gen_throughput: float = 90.0,
    fail_rate: float = 0.0,
    seed: int = 0,
) -> ProviderSummary:
    """
    用伪随机数生成一批"看起来像真实测量"的 RequestResult，用于：
      1) 在没有 API key / 没有网络时验证指标聚合数学（p50/p95/p99/std/可用性）；
      2) 演示并发上升时延迟长尾变差、可用性可能下降的趋势。

    ⚠️ 生成的所有数字都是合成的，不代表任何真实模型/提供商的性能。
    并发越高，用一个简单的排队模型抬高 TTFT 与端到端延迟，仅为呈现趋势。
    """
    rng = random.Random(seed + concurrency * 1000)
    # 并发放大系数：并发越高，排队等待越久（简单线性 + 抖动模型）
    contention = 1.0 + 0.12 * max(concurrency - 1, 0)

    results: list[RequestResult] = []
    total_tokens = 0
    sum_latency = 0.0
    for _ in range(num_requests):
        # 高并发下失败率随之升高（模拟限流），封顶 60%
        eff_fail = min(fail_rate * contention, 0.60)
        if rng.random() < eff_fail:
            results.append(RequestResult(ok=False, error="synthetic: rate_limited (429)"))
            continue
        # TTFT：对数正态形状，右偏（长尾），再乘并发放大
        ttft = base_ttft * contention * rng.lognormvariate(0.0, 0.35)
        gen_tp = max(base_gen_throughput * rng.uniform(0.75, 1.15), 1.0)
        tokens = rng.randint(28, 48)
        gen_time = tokens / gen_tp
        latency = ttft + gen_time
        total_tokens += tokens
        sum_latency += latency
        results.append(RequestResult(
            ok=True,
            ttft=ttft,
            latency=latency,
            completion_tokens=tokens,
            throughput=gen_tp,
        ))

    success = sum(1 for r in results if r.ok)
    # 合成墙钟：把成功请求的总延迟按并发均摊，得到一个自洽的批次耗时
    wall_time = max(sum_latency / max(concurrency, 1), 1e-6)
    errors = [r.error for r in results if not r.ok and r.error]
    return ProviderSummary(
        provider=provider,
        model=model,
        total=num_requests,
        success=success,
        results=results,
        errors=errors,
        concurrency=concurrency,
        wall_time=wall_time,
    )
