"""
Tests for CostEfficiencyAnalyzer (实验 7-9 成本效率分析).

Covers trajectory parsing, per-turn metrics, cost calculation, efficiency
scoring, turn classification, recommendations, and edge cases (empty, single
turn, all-wasteful, all-cached). Fully offline — no model calls, no network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
COST_DIR = HERE / "chapter7" / "agent-cost-analysis"
if str(COST_DIR) not in sys.path:
    sys.path.insert(0, str(COST_DIR))

# The chapter directory ships its own config.py (with a dotenv import). Pop any
# stale cached `config` module so the analyzer's self-contained import wins.
sys.modules.pop("config", None)

from cost_efficiency_analyzer import (  # noqa: E402
    CostEfficiencyAnalyzer,
    EfficiencyReport,
    TurnMetrics,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _turn(
    step: str = "turn-1",
    *,
    tool: str | None = "query_order",
    prompt_tokens: int = 100,
    cached_tokens: int = 0,
    completion_tokens: int = 20,
    tool_ctx_tokens: int = 50,
    latency_s: float = 1.5,
    **extra,
) -> dict:
    t = {
        "step": step,
        "tool": tool or "",
        "kind": "llm",
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "completion_tokens": completion_tokens,
        "tool_ctx_tokens": tool_ctx_tokens,
        "latency_s": latency_s,
    }
    t.update(extra)
    return t


def _trace(spans: list[dict], **extra) -> dict:
    trace = {"model": "gpt-4o-mini", "scenarios": [{"key": "naive", "name": "A", "spans": spans}]}
    trace.update(extra)
    return trace


# --------------------------------------------------------------------------- #
# Trajectory parsing
# --------------------------------------------------------------------------- #
def test_parses_scenarios_trace_shape():
    spans = [_turn("turn-1"), _turn("turn-2", tool="query_logistics")]
    report = CostEfficiencyAnalyzer().analyze_trajectory(_trace(spans))
    assert report.total_turns == 2
    assert [m.turn_id for m in report.turn_metrics] == [1, 2]


def test_parses_bare_list_of_turns():
    spans = [_turn("turn-1"), _turn("turn-2")]
    report = CostEfficiencyAnalyzer().analyze_trajectory(spans)
    assert report.total_turns == 2


def test_parses_spans_key_dict():
    spans = [_turn("turn-1"), _turn("turn-2")]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert report.total_turns == 2


def test_parses_turns_key_dict():
    report = CostEfficiencyAnalyzer().analyze_trajectory(
        {"turns": [_turn("turn-1"), _turn("turn-2"), _turn("turn-3")]}
    )
    assert report.total_turns == 3


def test_skips_scenario_without_spans():
    trace = {
        "scenarios": [
            {"key": "empty", "name": "no spans"},
            {"key": "both", "name": "B", "spans": [_turn("turn-1")]},
        ]
    }
    report = CostEfficiencyAnalyzer().analyze_trajectory(trace)
    assert report.total_turns == 1


def test_uses_embedded_pricing_when_not_explicit():
    # input $10/M, output $20/M, cached $5/M — clearly different from default.
    spans = [_turn("turn-1", prompt_tokens=1_000_000, completion_tokens=500_000)]
    trace = {"pricing": {"input": 10.0, "output": 20.0, "cached": 5.0}, "spans": spans}
    report = CostEfficiencyAnalyzer().analyze_trajectory(trace)
    # 1M uncached input @ $10 + 0.5M output @ $20 = 10 + 10 = $20
    assert abs(report.total_cost_usd - 20.0) < 1e-6


def test_explicit_pricing_overrides_embedded():
    spans = [_turn("turn-1", prompt_tokens=1_000_000, completion_tokens=0)]
    trace = {"pricing": {"input": 10.0, "output": 20.0, "cached": 5.0}, "spans": spans}
    analyzer = CostEfficiencyAnalyzer(pricing={"input": 1.0, "output": 2.0, "cached": 0.5})
    report = analyzer.analyze_trajectory(trace)
    assert abs(report.total_cost_usd - 1.0) < 1e-6


# --------------------------------------------------------------------------- #
# Per-turn metrics
# --------------------------------------------------------------------------- #
def test_per_turn_metrics_fields():
    report = CostEfficiencyAnalyzer().analyze_trajectory(
        {"spans": [_turn("turn-1", prompt_tokens=200, cached_tokens=50,
                         completion_tokens=30, latency_s=2.0)]}
    )
    m = report.turn_metrics[0]
    assert isinstance(m, TurnMetrics)
    assert m.input_tokens == 200
    assert m.output_tokens == 30
    assert m.cache_hit_ratio == pytest.approx(0.25)
    assert m.latency_ms == pytest.approx(2000.0)
    assert m.tool_calls == 1
    assert m.classification in {"productive", "wasteful", "cached", "expensive"}


def test_latency_ms_from_latency_ms_field():
    report = CostEfficiencyAnalyzer().analyze_trajectory(
        {"spans": [_turn("turn-1", latency_s=None, latency_ms=750.0)]}
    )
    assert report.turn_metrics[0].latency_ms == pytest.approx(750.0)


def test_tool_calls_explicit_field_overrides_tool_presence():
    span = _turn("turn-1", tool="query_order", tool_calls=3)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].tool_calls == 3


def test_tool_calls_zero_when_no_tool():
    span = _turn("turn-1", tool=None, prompt_tokens=10, completion_tokens=5)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].tool_calls == 0


def test_turn_id_from_step_string():
    spans = [_turn("turn-7"), _turn("turn-3")]
    report = CostEfficiencyAnalyzer().analyze_trajectory(spans)
    assert [m.turn_id for m in report.turn_metrics] == [7, 3]


def test_null_numeric_fields_coerced():
    span = _turn("turn-1", prompt_tokens=None, cached_tokens=None,
                 completion_tokens=None, tool_ctx_tokens=None, latency_s=None)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    m = report.turn_metrics[0]
    assert m.input_tokens == 0
    assert m.output_tokens == 0
    assert m.cache_hit_ratio == 0.0
    assert m.latency_ms == 0.0


# --------------------------------------------------------------------------- #
# Cost calculation
# --------------------------------------------------------------------------- #
def test_cost_calculation_default_pricing():
    # gpt-4o-mini: $0.15/M input, $0.075/M cached, $0.60/M output
    span = _turn("turn-1", prompt_tokens=1_000_000, cached_tokens=400_000,
                 completion_tokens=500_000)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    expected = (600_000 * 0.15 + 400_000 * 0.075 + 500_000 * 0.60) / 1_000_000
    assert report.total_cost_usd == pytest.approx(expected)


def test_cumulative_costs_running_sum():
    spans = [_turn("turn-1"), _turn("turn-2"), _turn("turn-3")]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    per = [m.cost_usd for m in report.turn_metrics]
    assert report.cumulative_costs == pytest.approx(
        [per[0], per[0] + per[1], per[0] + per[1] + per[2]]
    )
    assert report.cumulative_costs[-1] == pytest.approx(report.total_cost_usd)


def test_tokens_per_tool_call_aggregate():
    spans = [
        _turn("turn-1", prompt_tokens=100, completion_tokens=50, tool="a"),
        _turn("turn-2", prompt_tokens=200, completion_tokens=50, tool="b"),
    ]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    # total tokens = 400, total tool calls = 2
    assert report.tokens_per_tool_call == pytest.approx(200.0)


def test_tokens_per_tool_call_zero_when_no_tools():
    spans = [_turn("turn-1", tool=None, prompt_tokens=100, completion_tokens=20)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert report.tokens_per_tool_call == 0.0


def test_latency_per_turn_aggregate():
    spans = [_turn("turn-1", latency_s=1.0), _turn("turn-2", latency_s=3.0)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert report.latency_per_turn == pytest.approx(2000.0)


# --------------------------------------------------------------------------- #
# Turn classification
# --------------------------------------------------------------------------- #
def test_productive_turn_classification():
    # tool call + modest tokens + no cache + cheap -> productive
    span = _turn("turn-1", tool="query_order", prompt_tokens=100,
                 completion_tokens=20, cached_tokens=0)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].classification == "productive"


def test_wasteful_turn_classification():
    # no tool calls + high tokens
    span = _turn("turn-1", tool=None, prompt_tokens=2000, completion_tokens=500,
                 cached_tokens=0)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].classification == "wasteful"


def test_cached_turn_classification():
    # high cache hit ratio, tool call present, not wasteful/expensive
    span = _turn("turn-1", tool="query_order", prompt_tokens=2000,
                 cached_tokens=1800, completion_tokens=10)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].classification == "cached"


def test_expensive_turn_absolute_threshold():
    # Force a high absolute cost above the configured threshold.
    span = _turn("turn-1", tool="query_order", prompt_tokens=2_000_000,
                 completion_tokens=1_000_000, cached_tokens=0)
    analyzer = CostEfficiencyAnalyzer(expensive_cost_threshold=0.5)
    report = analyzer.analyze_trajectory({"spans": [span]})
    # cost = 2M*0.15 + 1M*0.60 = 0.3 + 0.6 = 0.9 > 0.5
    assert report.turn_metrics[0].classification == "expensive"


def test_expensive_turn_relative_threshold():
    # One cheap turn, one costly turn -> the costly one is 1.5x mean.
    spans = [
        _turn("turn-1", tool="a", prompt_tokens=100, completion_tokens=10),
        _turn("turn-2", tool="b", prompt_tokens=2_000_000, completion_tokens=1_000_000),
    ]
    analyzer = CostEfficiencyAnalyzer(expensive_cost_threshold=None)
    report = analyzer.analyze_trajectory({"spans": spans})
    assert report.turn_metrics[1].classification == "expensive"
    assert report.turn_metrics[0].classification != "expensive"


def test_wasteful_takes_priority_over_cached():
    # no tool calls + huge tokens + high cache ratio -> wasteful wins
    span = _turn("turn-1", tool=None, prompt_tokens=5000, cached_tokens=4500,
                 completion_tokens=500)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].classification == "wasteful"


# --------------------------------------------------------------------------- #
# Efficiency scoring
# --------------------------------------------------------------------------- #
def test_efficiency_score_all_productive():
    spans = [_turn(f"turn-{i}", tool="t", prompt_tokens=100, completion_tokens=20)
             for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    # productive_ratio=1.0, no wasteful tokens -> token_efficiency=1.0
    assert report.efficiency_score == pytest.approx(1.0)


def test_efficiency_score_all_wasteful():
    spans = [_turn(f"turn-{i}", tool=None, prompt_tokens=2000, completion_tokens=500)
             for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert report.efficiency_score == pytest.approx(0.0)


def test_efficiency_score_mixed():
    spans = [
        _turn("turn-1", tool="a", prompt_tokens=100, completion_tokens=20),   # productive
        _turn("turn-2", tool=None, prompt_tokens=2000, completion_tokens=500),  # wasteful
    ]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    # productive_ratio = 0.5; wasteful_tokens=2500, total=2620
    # token_efficiency = 1 - 2500/2620
    expected = 0.5 * (1 - 2500 / 2620)
    assert report.efficiency_score == pytest.approx(expected)
    assert 0.0 < report.efficiency_score < 0.5


def test_efficiency_score_clamped_to_unit_interval():
    spans = [_turn("turn-1", tool="a", prompt_tokens=100, completion_tokens=20)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert 0.0 <= report.efficiency_score <= 1.0


# --------------------------------------------------------------------------- #
# Recommendations
# --------------------------------------------------------------------------- #
def test_recommendations_flag_wasteful_turns():
    spans = [_turn("turn-1", tool=None, prompt_tokens=2000, completion_tokens=500)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert any("wasteful" in r and "Turn 1" in r for r in report.recommendations)


def test_recommendations_flag_cache_miss_pattern():
    # Many high-input turns, zero cache hits -> cache miss recommendation.
    spans = [_turn(f"turn-{i}", tool="t", prompt_tokens=2000,
                   cached_tokens=0, completion_tokens=20) for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert any("Cache miss" in r for r in report.recommendations)


def test_recommendations_flag_expensive_turns():
    span = _turn("turn-1", tool="a", prompt_tokens=2_000_000, completion_tokens=1_000_000)
    analyzer = CostEfficiencyAnalyzer(expensive_cost_threshold=0.5)
    report = analyzer.analyze_trajectory({"spans": [span]})
    assert any("expensive" in r and "Turn 1" in r for r in report.recommendations)


def test_recommendations_context_compression_opportunity():
    # Input tokens grow across turns -> compression recommendation.
    spans = [_turn(f"turn-{i}", tool="t", prompt_tokens=100 * i,
                   completion_tokens=20) for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert any("compression" in r.lower() for r in report.recommendations)


def test_recommendations_low_efficiency_verdict():
    spans = [
        _turn("turn-1", tool=None, prompt_tokens=2000, completion_tokens=500),
        _turn("turn-2", tool=None, prompt_tokens=2000, completion_tokens=500),
    ]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert any("Low efficiency" in r for r in report.recommendations)


def test_recommendations_high_efficiency_verdict():
    spans = [_turn(f"turn-{i}", tool="t", prompt_tokens=100, completion_tokens=20)
             for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert any("High efficiency" in r for r in report.recommendations)


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #
def test_empty_trajectory():
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": []})
    assert report.total_turns == 0
    assert report.total_cost_usd == 0.0
    assert report.total_tokens == 0
    assert report.efficiency_score == 0.0
    assert report.turn_metrics == []
    assert report.recommendations == []
    assert report.cumulative_costs == []


def test_empty_scenarios_list():
    report = CostEfficiencyAnalyzer().analyze_trajectory({"scenarios": []})
    assert report.total_turns == 0


def test_single_turn():
    span = _turn("turn-1", tool="query_order", prompt_tokens=200,
                 completion_tokens=30, latency_s=1.5)
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": [span]})
    assert report.total_turns == 1
    assert report.latency_per_turn == pytest.approx(1500.0)
    assert report.cumulative_costs == [report.turn_metrics[0].cost_usd]


def test_all_wasteful_trajectory():
    spans = [_turn(f"turn-{i}", tool=None, prompt_tokens=3000,
                   completion_tokens=500) for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert all(m.classification == "wasteful" for m in report.turn_metrics)
    assert report.efficiency_score == pytest.approx(0.0)
    assert len([r for r in report.recommendations if "wasteful" in r]) == 4


def test_all_cached_trajectory():
    spans = [_turn(f"turn-{i}", tool="t", prompt_tokens=2000,
                   cached_tokens=1800, completion_tokens=20) for i in range(1, 5)]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert all(m.classification == "cached" for m in report.turn_metrics)
    # No cache-miss recommendation since ratio is high.
    assert not any("Cache miss" in r for r in report.recommendations)


def test_default_pricing_values():
    p = CostEfficiencyAnalyzer.default_pricing()
    assert p == {"input": 0.15, "cached": 0.075, "output": 0.60}


def test_analyze_turn_standalone():
    analyzer = CostEfficiencyAnalyzer()
    m = analyzer.analyze_turn(_turn("turn-1", tool="a", prompt_tokens=100,
                                    completion_tokens=20))
    assert isinstance(m, TurnMetrics)
    assert m.turn_id == 1
    assert m.tool_calls == 1


def test_analyze_turn_standalone_none_threshold_never_expensive():
    analyzer = CostEfficiencyAnalyzer(expensive_cost_threshold=None)
    m = analyzer.analyze_turn(_turn("turn-1", tool="a", prompt_tokens=10_000_000,
                                    completion_tokens=5_000_000))
    # Standalone, None threshold -> inf -> never expensive (wasteful needs no tool calls).
    assert m.classification != "expensive"
def test_zero_cost_trajectory_not_flagged_expensive():
    """A fully zero-cost trajectory must not mark productive turns as expensive.

    With a zero mean cost, the relative threshold is zero and
    ``cost_usd >= 0`` would flag every productive turn.  The guard skips
    reclassification when the threshold is zero.
    """
    spans = [
        _turn("turn-1", tool="query_order", prompt_tokens=0,
              completion_tokens=0, cached_tokens=0),
        _turn("turn-2", tool="query_order", prompt_tokens=0,
              completion_tokens=0, cached_tokens=0),
    ]
    analyzer = CostEfficiencyAnalyzer()
    report = analyzer.analyze_trajectory({"spans": spans})
    for m in report.turn_metrics:
        assert m.classification != "expensive", (
            f"Zero-cost turn {m.turn_id} wrongly classified as expensive"
        )


def test_single_zero_cost_turn_not_expensive():
    """A single zero-cost turn with a tool call stays productive, not expensive."""
    span = _turn("turn-1", tool="query_order", prompt_tokens=0,
                 completion_tokens=0, cached_tokens=0)
    analyzer = CostEfficiencyAnalyzer()
    report = analyzer.analyze_trajectory({"spans": [span]})
    assert report.turn_metrics[0].classification != "expensive"
    assert report.efficiency_score > 0.0


def test_invalid_trajectory_type_raises():
    with pytest.raises(TypeError):
        CostEfficiencyAnalyzer().analyze_trajectory("not a trajectory")


def test_report_dataclass_shape():
    spans = [_turn("turn-1")]
    report = CostEfficiencyAnalyzer().analyze_trajectory({"spans": spans})
    assert isinstance(report, EfficiencyReport)
    assert report.total_turns == len(report.turn_metrics)
    assert report.total_cost_usd == pytest.approx(
        sum(m.cost_usd for m in report.turn_metrics)
    )
    assert report.total_tokens == sum(m.total_tokens for m in report.turn_metrics)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
