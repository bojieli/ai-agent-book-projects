"""
自建的轻量级 tracing / 可观测系统。

设计沿用分布式追踪的 span 树模型（见书 6.x「Agent 的可观测性」）：
    - 一次 agent 任务 = 一条 Trace
    - 每次 LLM 调用 / 工具调用 = 一个 Span
    - Span 记录：所属步骤、类型、token 用量（prompt/completion/cached）、时延、成本

用法：
    tracer = Tracer(client)
    resp = tracer.chat(step="turn-1", tool="query_order",
                       model=..., messages=..., temperature=0)
    tracer.print_breakdown()   # 打印按步骤/工具聚合的成本拆解

离线复用（不打模型、只算成本）：
    tracer = Tracer.from_records(records, pricing=..., name=...)
    # records 里是此前真实运行录下的每一步 token 用量（canned token counts）
"""

import math
import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional

from config import Pricing, default_pricing


def _percentile(values: List[float], q: float) -> float:
    """最近秩（nearest-rank）百分位，避免引入 numpy 依赖。q 取 0~100。"""
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    # 最近秩 = ceil(q/100 * N)。不能用 int(round(x + 0.5))：当 q/100*N 恰为
    # 整数 k 时，round(k + 0.5) 的银行家舍入会得到 k+1（如 n=100、q=99 时
    # 秩变成 100，把 p99 报成最大值）。
    rank = max(1, min(len(xs), math.ceil(q / 100.0 * len(xs))))
    return xs[rank - 1]


@dataclass
class Span:
    """一次被追踪的调用（这里主要是 LLM 调用）。"""
    step: str                 # 逻辑步骤名，如 "turn-2"
    tool: str                 # 该步骤关联的工具/动作名，用于归因“哪一步最贵”
    kind: str = "llm"         # span 类型：llm / tool
    prompt_tokens: int = 0
    cached_tokens: int = 0
    completion_tokens: int = 0
    # 该轮输入里「工具返回结果」占用的累计 token（同一份工具返回会在后续每轮被反复计费）。
    # 由上层用 tokenizer 估算并填入；离线复用时从 records 读回。-1 表示未知。
    tool_ctx_tokens: int = -1
    latency_s: float = 0.0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def uncached_prompt_tokens(self) -> int:
        return max(self.prompt_tokens - self.cached_tokens, 0)


class Tracer:
    """包裹 OpenAI client，自动记录每次 LLM 调用的 usage / 时延 / 成本。"""

    def __init__(self, client=None, name: str = "trace",
                 pricing: Optional[Pricing] = None):
        self.client = client
        self.name = name
        self.pricing = pricing or default_pricing()
        self.spans: List[Span] = []

    # ---------- 采集 ----------
    def chat(self, step: str, tool: str, tool_ctx_tokens: int = -1, **kwargs):
        """发起一次被追踪的 chat.completions 调用。

        kwargs 原样透传给 openai client（model / messages / temperature 等）。
        tool_ctx_tokens：本轮输入里工具返回结果占用的累计 token（可选，用于成本归因）。
        返回原始的 OpenAI response 对象，方便上层取 content。
        """
        t0 = time.time()
        resp = self.client.chat.completions.create(**kwargs)
        latency = time.time() - t0

        usage = resp.usage
        # Some OpenAI-compatible providers omit usage (null); match from_records coercion.
        if usage is None:
            span = Span(
                step=step,
                tool=tool,
                kind="llm",
                tool_ctx_tokens=tool_ctx_tokens,
                latency_s=latency,
                cost_usd=0.0,
            )
            self.spans.append(span)
            return resp

        # cached_tokens 藏在 prompt_tokens_details 里，注意做防御式读取
        cached = 0
        details = getattr(usage, "prompt_tokens_details", None)
        if details is not None:
            cached = getattr(details, "cached_tokens", 0) or 0

        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        span = Span(
            step=step,
            tool=tool,
            kind="llm",
            prompt_tokens=prompt_tokens,
            cached_tokens=cached,
            completion_tokens=completion_tokens,
            tool_ctx_tokens=tool_ctx_tokens,
            latency_s=latency,
            cost_usd=self.pricing.cost_usd(
                prompt_tokens, cached, completion_tokens),
        )
        self.spans.append(span)
        return resp

    # ---------- 离线复用（canned token counts → 重新计成本）----------
    @classmethod
    def from_records(cls, records: List[dict], name: str = "trace",
                     pricing: Optional[Pricing] = None) -> "Tracer":
        """用此前录下的 token 用量重建一条 trace，并按给定单价重算成本（不打模型）。"""
        tr = cls(client=None, name=name, pricing=pricing)
        for r in records:
            span = Span(
                step=r.get("step", ""),
                tool=r.get("tool", ""),
                kind=r.get("kind", "llm"),
                # Missing/null tool_ctx → -1 (unknown); keep explicit 0 (known-zero).
                prompt_tokens=int(r.get("prompt_tokens") or 0),
                cached_tokens=int(r.get("cached_tokens") or 0),
                completion_tokens=int(r.get("completion_tokens") or 0),
                tool_ctx_tokens=(-1 if r.get("tool_ctx_tokens") is None
                                 else int(r.get("tool_ctx_tokens"))),
                latency_s=float(r.get("latency_s") or 0.0),
            )
            span.cost_usd = tr.pricing.cost_usd(
                span.prompt_tokens, span.cached_tokens, span.completion_tokens)
            tr.spans.append(span)
        return tr

    def to_records(self) -> List[dict]:
        """导出每一步的原始 token 用量（用于落盘成 canned trace，供离线复用）。"""
        out = []
        for s in self.spans:
            d = asdict(s)
            d.pop("cost_usd", None)   # 成本由单价重算，不落盘固定值
            out.append(d)
        return out

    # ---------- 聚合 ----------
    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.spans)

    def total_prompt_tokens(self) -> int:
        return sum(s.prompt_tokens for s in self.spans)

    def total_cached_tokens(self) -> int:
        return sum(s.cached_tokens for s in self.spans)

    def total_completion_tokens(self) -> int:
        return sum(s.completion_tokens for s in self.spans)

    def total_uncached_prompt_tokens(self) -> int:
        return sum(s.uncached_prompt_tokens for s in self.spans)

    def total_tool_ctx_tokens(self) -> int:
        return sum(s.tool_ctx_tokens for s in self.spans if s.tool_ctx_tokens >= 0)

    def total_latency(self) -> float:
        return sum(s.latency_s for s in self.spans)

    def cache_rate(self) -> float:
        pin = self.total_prompt_tokens()
        return self.total_cached_tokens() / pin if pin else 0.0

    def component_costs(self) -> dict:
        """把总成本拆成三个成本构成要素（对应书「成本的构成要素」）：
            - 未缓存输入 / 缓存输入 / 输出
        以及输入侧里「工具返回注入」token 占比（若已知）。"""
        p = self.pricing
        uncached_in = self.total_uncached_prompt_tokens()
        cached_in = self.total_cached_tokens()
        out = self.total_completion_tokens()
        return {
            "uncached_input_cost": uncached_in / 1_000_000 * p.input_per_m,
            "cached_input_cost": cached_in / 1_000_000 * p.cached_per_m,
            "output_cost": out / 1_000_000 * p.output_per_m,
            "uncached_input_tokens": uncached_in,
            "cached_input_tokens": cached_in,
            "output_tokens": out,
            "tool_ctx_tokens": self.total_tool_ctx_tokens(),
        }

    def cost_distribution(self) -> dict:
        """按步骤的单步成本分布（p50/p95/p99）。对应书「成本分布 p50/p95/p99」。"""
        costs = [s.cost_usd for s in self.spans]
        n = len(costs)
        return {
            "n": n,
            "mean": (sum(costs) / n) if n else 0.0,
            "p50": _percentile(costs, 50),
            "p95": _percentile(costs, 95),
            "p99": _percentile(costs, 99),
            "max": max(costs) if costs else 0.0,
        }

    # ---------- 打印 ----------
    def print_breakdown(self, title: Optional[str] = None):
        """打印一次 agent 任务的按步骤成本拆解表，并指出最贵的一步、成本构成与分布。"""
        print()
        print(f"===== 成本拆解: {title or self.name} =====")
        header = (
            f"{'步骤':<8} {'工具/动作':<20} {'输入tok':>8} {'缓存tok':>8} "
            f"{'工具tok':>8} {'输出tok':>8} {'时延(s)':>8} {'成本($)':>12}"
        )
        print(header)
        print("-" * len(header))
        for s in self.spans:
            tctx = s.tool_ctx_tokens if s.tool_ctx_tokens >= 0 else "-"
            print(
                f"{s.step:<8} {s.tool:<20} {s.prompt_tokens:>8} {s.cached_tokens:>8} "
                f"{str(tctx):>8} {s.completion_tokens:>8} {s.latency_s:>8.2f} "
                f"{s.cost_usd:>12.6f}"
            )
        print("-" * len(header))
        tctx_total = self.total_tool_ctx_tokens() if any(
            s.tool_ctx_tokens >= 0 for s in self.spans) else "-"
        print(
            f"{'合计':<8} {'':<20} {self.total_prompt_tokens():>8} "
            f"{self.total_cached_tokens():>8} {str(tctx_total):>8} "
            f"{self.total_completion_tokens():>8} "
            f"{self.total_latency():>8.2f} {self.total_cost():>12.6f}"
        )

        # 归因：哪一步最贵
        if self.spans:
            worst = max(self.spans, key=lambda s: s.cost_usd)
            total = self.total_cost()
            share = worst.cost_usd / total * 100 if total else 0
            print(
                f"\n最贵的一步 → {worst.step} / {worst.tool}: "
                f"${worst.cost_usd:.6f}（占总成本 {share:.1f}%）"
            )

        # 成本构成拆解（未缓存输入 / 缓存输入 / 输出）
        comp = self.component_costs()
        total = self.total_cost() or 1e-12
        print("成本构成:")
        print(f"  未缓存输入  {comp['uncached_input_tokens']:>8} tok  "
              f"${comp['uncached_input_cost']:.6f}  ({comp['uncached_input_cost']/total*100:.1f}%)")
        print(f"  缓存输入    {comp['cached_input_tokens']:>8} tok  "
              f"${comp['cached_input_cost']:.6f}  ({comp['cached_input_cost']/total*100:.1f}%)")
        print(f"  输出        {comp['output_tokens']:>8} tok  "
              f"${comp['output_cost']:.6f}  ({comp['output_cost']/total*100:.1f}%)")
        if comp["tool_ctx_tokens"] > 0:
            print(f"  其中「工具返回注入」累计输入 {comp['tool_ctx_tokens']} tok "
                  f"（同一份工具返回在后续每轮被反复计费）")

        # 单步成本分布
        dist = self.cost_distribution()
        print(f"单步成本分布(n={dist['n']}): 均值 ${dist['mean']:.6f}  "
              f"p50 ${dist['p50']:.6f}  p95 ${dist['p95']:.6f}  p99 ${dist['p99']:.6f}")
