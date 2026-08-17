"""
Agent trajectory cost-efficiency analyzer (实验 7-9 成本效率分析).

Builds on the span/trace model from ``tracer.py``: an agent task is a sequence
of turns, each turn carrying token usage (prompt / cached / completion), tool
context tokens, and latency. This module turns a recorded trajectory into an
:class:`EfficiencyReport` — per-turn metrics, a single efficiency score, and
actionable recommendations (wasteful turns, compression opportunities, cache
miss patterns).

It is fully offline: it never calls a model. Pricing is configured per million
tokens (same convention as ``config.Pricing``) and defaults to gpt-4o-mini.

Two trajectory shapes are accepted:

1. A bare list of turn dicts (the spans of one scenario).
2. A trace dict as written by the tracer — ``{"turns": [...]}``,
   ``{"spans": [...]}``, or ``{"scenarios": [{"spans": [...]}, ...]}`` (the
   first scenario with spans is analyzed). A top-level ``"pricing"`` key is
   honoured when no explicit pricing was given to the constructor.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------- #
# Data shapes
# --------------------------------------------------------------------------- #
@dataclass
class TurnMetrics:
    """Per-turn cost-efficiency metrics."""

    turn_id: int
    input_tokens: int
    output_tokens: int
    cache_hit_ratio: float
    cost_usd: float
    latency_ms: float
    tool_calls: int
    classification: str  # productive / wasteful / cached / expensive

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class EfficiencyReport:
    """Aggregate cost-efficiency report for a whole trajectory."""

    total_turns: int
    total_cost_usd: float
    total_tokens: int
    efficiency_score: float
    turn_metrics: list[TurnMetrics]
    recommendations: list[str]
    # Derived aggregate metrics (computed by analyze_trajectory).
    cumulative_costs: list[float] = field(default_factory=list)
    tokens_per_tool_call: float = 0.0
    latency_per_turn: float = 0.0


# --------------------------------------------------------------------------- #
# Analyzer
# --------------------------------------------------------------------------- #
_STEP_RE = re.compile(r"turn[-_ ]]?(\d+)", re.IGNORECASE)


class CostEfficiencyAnalyzer:
    """Analyze the cost-efficiency of a recorded agent trajectory.

    Parameters
    ----------
    pricing:
        Per-million-token USD prices with keys ``input``, ``output`` and
        ``cached``. ``None`` falls back to :meth:`default_pricing` (and to a
        ``pricing`` block embedded in the trajectory, if present).
    wasteful_token_threshold:
        A turn with no tool calls and at least this many total tokens is
        classified ``wasteful``.
    expensive_cost_threshold:
        Per-turn cost (USD) above which a turn is ``expensive``. ``None`` means
        relative: a turn is expensive when its cost exceeds 1.5x the mean
        per-turn cost of the trajectory (computed in :meth:`analyze_trajectory`;
        :meth:`analyze_turn` alone treats ``None`` as "never expensive").
    cached_ratio_threshold:
        Cache hit ratio at or above which a turn is ``cached``.
    """

    def __init__(
        self,
        pricing: dict[str, float] | None = None,
        *,
        wasteful_token_threshold: int = 1000,
        expensive_cost_threshold: float | None = None,
        cached_ratio_threshold: float = 0.5,
    ) -> None:
        self._pricing_explicit = pricing is not None
        self.pricing: dict[str, float] = pricing or self.default_pricing()
        self.wasteful_token_threshold = wasteful_token_threshold
        self.expensive_cost_threshold = expensive_cost_threshold
        self.cached_ratio_threshold = cached_ratio_threshold

    # ---------- pricing ---------- #
    @staticmethod
    def default_pricing() -> dict[str, float]:
        """Default per-million-token USD prices (gpt-4o-mini)."""
        return {"input": 0.15, "cached": 0.075, "output": 0.60}

    def _cost_usd(
        self, input_tokens: int, cached_tokens: int, output_tokens: int
    ) -> float:
        """USD cost for one turn given per-million-token pricing."""
        uncached = max(input_tokens - cached_tokens, 0)
        per_m = 1_000_000.0
        return (
            uncached / per_m * self.pricing.get("input", 0.0)
            + cached_tokens / per_m * self.pricing.get("cached", 0.0)
            + output_tokens / per_m * self.pricing.get("output", 0.0)
        )

    # ---------- turn normalization ---------- #
    @staticmethod
    def _parse_turn_id(turn: dict[str, Any], index: int) -> int:
        raw = turn.get("turn_id")
        if isinstance(raw, (int, float)):
            return int(raw)
        step = turn.get("step") or turn.get("turn") or ""
        if isinstance(step, str):
            m = _STEP_RE.search(step)
            if m:
                return int(m.group(1))
        return index + 1

    @staticmethod
    def _coerce_int(value: Any) -> int:
        """Coerce nullable/numeric JSON values to int (None -> 0)."""
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _coerce_float(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _normalize_turn(self, turn: dict[str, Any]) -> dict[str, Any]:
        """Map a raw turn/span dict onto the analyzer's canonical fields."""
        input_tokens = self._coerce_int(
            turn.get("prompt_tokens", turn.get("input_tokens"))
        )
        output_tokens = self._coerce_int(
            turn.get("completion_tokens", turn.get("output_tokens"))
        )
        cached_tokens = self._coerce_int(turn.get("cached_tokens"))
        explicit_ratio = turn.get("cache_hit_ratio")
        if cached_tokens == 0 and explicit_ratio is not None:
            cached_tokens = round(self._coerce_float(explicit_ratio) * input_tokens)
        if input_tokens > 0:
            cache_hit_ratio = cached_tokens / input_tokens
        elif explicit_ratio is not None:
            cache_hit_ratio = self._coerce_float(explicit_ratio)
        else:
            cache_hit_ratio = 0.0
        cache_hit_ratio = max(0.0, min(1.0, cache_hit_ratio))

        latency_ms: float
        if turn.get("latency_ms") is not None:
            latency_ms = self._coerce_float(turn.get("latency_ms"))
        elif turn.get("latency_s") is not None:
            latency_ms = self._coerce_float(turn.get("latency_s")) * 1000.0
        else:
            latency_ms = 0.0

        tool_calls = turn.get("tool_calls")
        if tool_calls is None:
            tool = turn.get("tool")
            tool_calls = 1 if (isinstance(tool, str) and tool) else 0
        else:
            tool_calls = self._coerce_int(tool_calls)

        return {
            "turn_id": self._parse_turn_id(turn, -1),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "cache_hit_ratio": cache_hit_ratio,
            "latency_ms": latency_ms,
            "tool_calls": tool_calls,
            "tool_ctx_tokens": self._coerce_int(turn.get("tool_ctx_tokens", -1)),
        }

    # ---------- classification ---------- #
    def _classify(
        self,
        total_tokens: int,
        tool_calls: int,
        cache_hit_ratio: float,
        cost_usd: float,
        expensive_threshold: float,
    ) -> str:
        if tool_calls == 0 and total_tokens >= self.wasteful_token_threshold:
            return "wasteful"
        if cost_usd >= expensive_threshold and expensive_threshold > 0:
            return "expensive"
        if cache_hit_ratio >= self.cached_ratio_threshold:
            return "cached"
        return "productive"

    # ---------- public API ---------- #
    def analyze_turn(self, turn: dict[str, Any]) -> TurnMetrics:
        """Analyze a single turn dict into :class:`TurnMetrics`.

        Uses the absolute ``expensive_cost_threshold`` configured on the
        analyzer; when it is ``None`` the turn is never classified expensive
        here (a relative threshold is only available to :meth:`analyze_trajectory`,
        which sees the whole distribution).
        """
        n = self._normalize_turn(turn)
        cost = self._cost_usd(n["input_tokens"], n["cached_tokens"], n["output_tokens"])
        threshold = self.expensive_cost_threshold
        if threshold is None:
            threshold = float("inf")
        classification = self._classify(
            n["input_tokens"] + n["output_tokens"],
            n["tool_calls"],
            n["cache_hit_ratio"],
            cost,
            threshold,
        )
        return TurnMetrics(
            turn_id=n["turn_id"],
            input_tokens=n["input_tokens"],
            output_tokens=n["output_tokens"],
            cache_hit_ratio=n["cache_hit_ratio"],
            cost_usd=cost,
            latency_ms=n["latency_ms"],
            tool_calls=n["tool_calls"],
            classification=classification,
        )

    def _extract_turns(self, trajectory: dict[str, Any] | list[dict]) -> list[dict]:
        """Pull the list of turn dicts out of any supported trajectory shape."""
        if isinstance(trajectory, list):
            return list(trajectory)
        if not isinstance(trajectory, dict):
            raise TypeError(
                "trajectory must be a list of turn dicts or a trace dict, "
                f"got {type(trajectory).__name__}"
            )
        if "turns" in trajectory:
            return list(trajectory["turns"] or [])
        if "spans" in trajectory:
            return list(trajectory["spans"] or [])
        if "scenarios" in trajectory:
            for scenario in trajectory["scenarios"] or []:
                spans = scenario.get("spans") or []
                if spans:
                    return list(spans)
            return []
        # A bare single-turn dict is treated as one turn.
        if {"prompt_tokens", "input_tokens", "step", "tool"} & trajectory.keys():
            return [trajectory]
        return []

    def analyze_trajectory(
        self, trajectory: dict[str, Any] | list[dict]
    ) -> EfficiencyReport:
        """Analyze a full trajectory into an :class:`EfficiencyReport`."""
        # Honour embedded pricing when no explicit pricing was configured.
        if (
            not self._pricing_explicit
            and isinstance(trajectory, dict)
            and isinstance(trajectory.get("pricing"), dict)
        ):
            self.pricing = {**self.pricing, **trajectory["pricing"]}

        turns = self._extract_turns(trajectory)
        metrics = [self.analyze_turn(t) for t in turns]

        total_turns = len(metrics)
        total_cost = sum(m.cost_usd for m in metrics)
        total_tokens = sum(m.total_tokens for m in metrics)

        # Relative expensive threshold: 1.5x mean per-turn cost.
        # When mean cost is zero (e.g. a fully cached or zero-token
        # trajectory), every turn costs $0 and none should be flagged
        # expensive — a zero threshold would mark all of them. Skip the
        # relative reclassification in that case.
        if self.expensive_cost_threshold is None and total_turns > 0:
            mean_cost = total_cost / total_turns
            rel_threshold = mean_cost * 1.5
            if rel_threshold > 0:
                for m in metrics:
                    if m.classification == "productive" and m.cost_usd >= rel_threshold:
                        m.classification = "expensive"
        elif self.expensive_cost_threshold is None:
            rel_threshold = float("inf")
        else:
            rel_threshold = self.expensive_cost_threshold

        # Cumulative cost per turn (running sum).
        cumulative: list[float] = []
        running = 0.0
        for m in metrics:
            running += m.cost_usd
            cumulative.append(running)

        total_tool_calls = sum(m.tool_calls for m in metrics)
        tokens_per_tool_call = (
            total_tokens / total_tool_calls if total_tool_calls > 0 else 0.0
        )
        latency_per_turn = (
            sum(m.latency_ms for m in metrics) / total_turns if total_turns > 0 else 0.0
        )

        # Efficiency score: productive-turn ratio weighted by token efficiency
        # (fraction of tokens NOT spent on wasteful turns).
        productive_turns = sum(1 for m in metrics if m.classification == "productive")
        wasteful_tokens = sum(
            m.total_tokens for m in metrics if m.classification == "wasteful"
        )
        if total_turns == 0:
            efficiency_score = 0.0
        else:
            productive_ratio = productive_turns / total_turns
            token_efficiency = (
                1.0 - wasteful_tokens / total_tokens if total_tokens > 0 else 1.0
            )
            efficiency_score = max(0.0, min(1.0, productive_ratio * token_efficiency))

        recommendations = self._recommendations(
            metrics, efficiency_score, total_cost, total_tokens, rel_threshold
        )

        return EfficiencyReport(
            total_turns=total_turns,
            total_cost_usd=total_cost,
            total_tokens=total_tokens,
            efficiency_score=efficiency_score,
            turn_metrics=metrics,
            recommendations=recommendations,
            cumulative_costs=cumulative,
            tokens_per_tool_call=tokens_per_tool_call,
            latency_per_turn=latency_per_turn,
        )

    # ---------- recommendations ---------- #
    def _recommendations(
        self,
        metrics: list[TurnMetrics],
        efficiency_score: float,
        total_cost: float,
        total_tokens: int,
        expensive_threshold: float,
    ) -> list[str]:
        recs: list[str] = []

        # Wasteful turns: high tokens, no tool calls.
        for m in metrics:
            if m.classification == "wasteful":
                recs.append(
                    f"Turn {m.turn_id} is wasteful: {m.total_tokens} tokens with "
                    f"no tool calls — consider context compression or early stopping."
                )

        # Expensive turns.
        for m in metrics:
            if m.classification == "expensive":
                recs.append(
                    f"Turn {m.turn_id} is expensive: ${m.cost_usd:.6f} exceeds the "
                    f"${expensive_threshold:.6f}/turn threshold — review its prompt size."
                )

        # Cache miss pattern: high input tokens but low cache hit ratio overall.
        if metrics:
            high_input_turns = [m for m in metrics if m.input_tokens >= 1024]
            if high_input_turns:
                mean_ratio = sum(m.cache_hit_ratio for m in high_input_turns) / len(
                    high_input_turns
                )
                if mean_ratio < self.cached_ratio_threshold:
                    recs.append(
                        f"Cache miss pattern: mean cache hit ratio is {mean_ratio:.2%} "
                        f"across {len(high_input_turns)} turns with >=1024 input tokens "
                        f"— stabilize the prompt prefix to benefit from KV-cache."
                    )

        # Context compression opportunity: tool_ctx_tokens growing across turns.
        ctx_growth = self._max_tool_ctx_growth(metrics)
        if ctx_growth > 0:
            recs.append(
                f"Context compression opportunity: tool context tokens grow by "
                f"{ctx_growth} across the trajectory — summarize prior tool results "
                f"to avoid re-billing them every turn."
            )

        # Overall efficiency verdict.
        if metrics:
            if efficiency_score < 0.5:
                recs.append(
                    f"Low efficiency score ({efficiency_score:.2f}): fewer than half "
                    f"of turns are productive — review the trajectory structure."
                )
            elif efficiency_score >= 0.8:
                recs.append(
                    f"High efficiency score ({efficiency_score:.2f}): trajectory is "
                    f"cost-efficient."
                )

        return recs

    @staticmethod
    def _max_tool_ctx_growth(metrics: list[TurnMetrics]) -> int:
        """Largest per-step increase in tool context tokens (0 if unknown)."""
        # tool_ctx_tokens is not stored on TurnMetrics; recompute from the
        # fact that input_tokens tend to grow as context accumulates. We use
        # the raw input-token delta as a proxy when tool_ctx is unavailable.
        if len(metrics) < 2:
            return 0
        growth = 0
        prev = metrics[0].input_tokens
        for m in metrics[1:]:
            delta = m.input_tokens - prev
            if delta > growth:
                growth = delta
            prev = m.input_tokens
        return growth


if __name__ == "__main__":  # pragma: no cover - manual smoke
    import json
    import pathlib

    here = pathlib.Path(__file__).resolve().parent
    trace = json.loads((here / "sample_trace.json").read_text(encoding="utf-8"))
    analyzer = CostEfficiencyAnalyzer()
    report = analyzer.analyze_trajectory(trace)
    print(f"turns={report.total_turns} cost=${report.total_cost_usd:.6f} "
          f"score={report.efficiency_score:.3f}")
    for r in report.recommendations:
        print(" -", r)
