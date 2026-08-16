"""Unit tests for chapter7/model-benchmark/rate_ramp_benchmark.py."""

from pathlib import Path
import sys

# Ensure chapter7/model-benchmark is in sys.path
ch6_dir = Path(__file__).resolve().parent.parent / "chapter7" / "model-benchmark"
if str(ch6_dir) not in sys.path:
    sys.path.insert(0, str(ch6_dir))

from rate_ramp_benchmark import (
    RateRampBenchmark,
    calculate_percentile,
    run_benchmark,
)


def test_calculate_percentile():
    assert calculate_percentile([], 50) == 0.0
    assert calculate_percentile([42.0], 95) == 42.0

    vals = list(range(1, 101))  # 1 to 100
    assert abs(calculate_percentile(vals, 50) - 50.5) < 0.1
    assert abs(calculate_percentile(vals, 95) - 95.05) < 0.1
    assert abs(calculate_percentile(vals, 99) - 99.01) < 0.1


def test_rate_ramp_benchmark_default_run():
    config = {
        "start_rate": 1,
        "end_rate": 50,
        "step_rate": 10,
        "requests_per_step": 5,
        "sample_size": 100,
    }
    metrics = run_benchmark(config)

    assert "config" in metrics
    assert "ramp_steps" in metrics
    assert "overall_metrics" in metrics
    assert "backoff_curves" in metrics
    assert "evidence_package" in metrics

    # Check ramp steps cover rate progression
    rates = [step["rate_req_per_sec"] for step in metrics["ramp_steps"]]
    assert 1 in rates
    assert 50 in rates

    # Check overall metrics structure
    overall = metrics["overall_metrics"]
    assert overall["total_requests"] == len(metrics["ramp_steps"]) * 5
    assert "ttft_p50" in overall
    assert "ttft_p95" in overall
    assert "ttft_p99" in overall
    assert "error_rate" in overall
    assert "rate_limit_429_count" in overall

    # Check evidence package
    evidence = metrics["evidence_package"]
    assert len(evidence) <= 100
    assert len(evidence) > 0
    assert "request_id" in evidence[0]
    assert "ttft_sec" in evidence[0]
    assert "status_code" in evidence[0]


def test_rate_ramp_benchmark_custom_request_fn():
    # Custom request function that triggers 429 rate limit at high rates
    def mock_request_fn(rate, concurrency, req_idx):
        if rate >= 30:
            return {
                "request_id": f"mock-{rate}-{req_idx}",
                "timestamp": "2026-08-09T12:00:00.000Z",
                "target_rate": rate,
                "concurrency": concurrency,
                "status_code": 429,
                "ttft_sec": 0.25,
                "total_latency_sec": 1.5,
                "backoff_sec": 1.0,
                "retry_count": 2,
                "error_type": "rate_limit_429",
            }
        return {
            "request_id": f"mock-{rate}-{req_idx}",
            "timestamp": "2026-08-09T12:00:00.000Z",
            "target_rate": rate,
            "concurrency": concurrency,
            "status_code": 200,
            "ttft_sec": 0.10,
            "total_latency_sec": 0.30,
            "backoff_sec": 0.0,
            "retry_count": 0,
            "error_type": None,
        }

    config = {
        "rates": [10, 20, 30, 40, 50],
        "requests_per_step": 4,
        "sample_size": 20,
        "request_fn": mock_request_fn,
    }

    bench = RateRampBenchmark(config)
    metrics = bench.run()

    # Rates 10 and 20 are 200 OK (8 reqs), Rates 30, 40, 50 are 429 (12 reqs)
    overall = metrics["overall_metrics"]
    assert overall["total_requests"] == 20
    assert overall["successful_requests"] == 8
    assert overall["rate_limit_429_count"] == 12
    assert overall["error_rate"] == 0.6

    backoff = metrics["backoff_curves"]
    assert backoff["total_429_count"] == 12
    assert backoff["by_rate"][30]["429_count"] == 4
    assert backoff["by_rate"][30]["avg_backoff_sec"] == 1.0


def test_compile_evidence_package_sample_size():
    bench = RateRampBenchmark({"sample_size": 100})
    raw_records = [{"id": i, "target_rate": 10} for i in range(250)]
    evidence = bench.compile_evidence_package(raw_records, sample_size=100)
    assert len(evidence) == 100

    assert bench.compile_evidence_package(raw_records, sample_size=0) == []


def test_calculate_backoff_curves_missing_fields():
    bench = RateRampBenchmark()
    sparse_records = [
        {"status_code": 429, "backoff_sec": 1.5},
        {"status_code": 429, "backoff_sec": 0.5},
    ]
    res = bench.calculate_backoff_curves(sparse_records)
    assert res["total_429_count"] == 2
    assert res["overall_avg_backoff_sec"] == 1.0


def test_explicit_rates_config_parsing():
    bench = RateRampBenchmark({"rates": [10, 20, 30]})
    cfg = bench.config
    assert cfg["start_rate"] == 10
    assert cfg["end_rate"] == 30
    assert cfg["rates"] == [10, 20, 30]
def test_backoff_curves_with_non_dict_and_zero_backoff_429():
    bench = RateRampBenchmark()
    records = [
        "not_a_dict",
        {"status_code": 429, "backoff_sec": 0.0},  # 429 without backoff
        {"status_code": 429, "backoff_sec": 2.0},  # 429 with backoff
    ]
    res = bench.calculate_backoff_curves(records)
    assert res["total_429_count"] == 2
    # overall_avg_backoff should be based on requests with backoff > 0 (2.0 / 1 = 2.0)
    assert res["overall_avg_backoff_sec"] == 2.0


def test_backoff_averages_exclude_non_throttled_requests():
    """Findings #2/#4/#6: only 429 (throttled) requests contribute to backoff averages.

    Regression: the pre-fix code averaged every record with backoff_sec > 0, so a
    non-throttled 200 carrying backoff inflated per-rate and total backoff metrics.
    """
    bench = RateRampBenchmark()
    records = [
        {"target_rate": 10, "status_code": 200, "backoff_sec": 5.0},   # non-throttled backoff -> ignored
        {"target_rate": 10, "status_code": 429, "backoff_sec": 0.0},   # throttled, zero backoff
        {"target_rate": 20, "status_code": 429, "backoff_sec": 2.0},   # throttled backoff
        {"target_rate": 20, "status_code": 429, "backoff_sec": 4.0},   # throttled backoff
    ]
    res = bench.calculate_backoff_curves(records)
    # Rate 10 has no 429 backoff > 0 -> 0.0, not 5.0 (old code returned 5.0).
    assert res["by_rate"][10]["avg_backoff_sec"] == 0.0
    # Rate 20 averages only its two throttled backoffs: (2.0 + 4.0) / 2 = 3.0.
    assert res["by_rate"][20]["avg_backoff_sec"] == 3.0
    # Overall averages only throttled backoffs: (2.0 + 4.0) / 2 = 3.0.
    assert res["overall_avg_backoff_sec"] == 3.0
    # Total backoff time counts only throttled backoff: 6.0 (old code returned 11.0).
    assert res["total_backoff_time_sec"] == 6.0


def test_overall_avg_backoff_zero_when_no_throttled_backoff():
    """Finding #2: with no 429 backoff > 0, overall avg is 0.0, not inflated by non-throttled backoffs.

    Regression: the pre-fix code fell back to averaging all backoff-bearing records,
    yielding 5.0 here instead of 0.0.
    """
    bench = RateRampBenchmark()
    records = [
        {"target_rate": 10, "status_code": 200, "backoff_sec": 5.0},
        {"target_rate": 10, "status_code": 429, "backoff_sec": 0.0},
    ]
    res = bench.calculate_backoff_curves(records)
    assert res["overall_avg_backoff_sec"] == 0.0


def test_run_step_summary_backoff_only_counts_throttled():
    """Finding #4: ramp_steps avg_backoff counts only 429 requests.

    Regression: the pre-fix run() step summary averaged every record with
    backoff_sec > 0, so a 200 carrying backoff yielded 9.0 at rate 10.
    """
    def fn(rate, concurrency, idx):
        if rate >= 20:
            return {"target_rate": rate, "status_code": 429, "ttft_sec": 0.2, "backoff_sec": 2.0}
        return {"target_rate": rate, "status_code": 200, "ttft_sec": 0.1, "backoff_sec": 9.0}

    bench = RateRampBenchmark({"rates": [10, 20], "requests_per_step": 2, "request_fn": fn, "sample_size": 5})
    metrics = bench.run()
    step10 = next(s for s in metrics["ramp_steps"] if s["rate_req_per_sec"] == 10)
    step20 = next(s for s in metrics["ramp_steps"] if s["rate_req_per_sec"] == 20)
    assert step10["avg_backoff_sec"] == 0.0  # old code: 9.0
    assert step20["avg_backoff_sec"] == 2.0


def test_run_custom_fn_missing_fields_non_dict_and_none_backoff():
    """Findings #1/#7: run() must not crash on records missing fields, non-dict records, or None backoff.

    Regression: the pre-fix code used ``r["ttft_sec"]`` / ``"ttft_sec" in r`` (crashes on
    non-dict) and ``float(r.get("backoff_sec", 0.0))`` (crashes on None backoff).
    """
    def fn(rate, concurrency, idx):
        if idx == 0:
            return {"target_rate": rate, "status_code": 429, "backoff_sec": None}
        if idx == 1:
            return None  # non-dict record
        return {"target_rate": rate, "status_code": 429, "backoff_sec": 1.0, "ttft_sec": 0.3}

    bench = RateRampBenchmark({"rates": [10], "requests_per_step": 3, "request_fn": fn, "sample_size": 5})
    metrics = bench.run()  # must not raise
    # None backoff treated as 0 -> only the 1.0 record counts toward the average.
    assert metrics["overall_metrics"]["avg_backoff_sec"] == 1.0
    # The non-dict record has no status_code; only idx 0 and idx 2 are 429.
    assert metrics["overall_metrics"]["rate_limit_429_count"] == 2


def test_evidence_package_zero_and_none_sample_size_no_division_error():
    """Finding #3: zero/None sample_size must not cause division by zero.

    Regression: the pre-fix guard ``sample_size <= 0`` raised TypeError on None.
    """
    bench = RateRampBenchmark()
    raw = [{"id": i, "target_rate": 10} for i in range(50)]
    assert bench.compile_evidence_package(raw, sample_size=0) == []
    assert bench.compile_evidence_package(raw, sample_size=None) == []
    assert bench.compile_evidence_package([], sample_size=100) == []


def test_custom_rates_reflected_in_report_config():
    """Finding #5: report config start/end must match a custom rates list, not defaults.

    Regression: the pre-fix _parse_config kept default start_rate=1/end_rate=50 when a
    custom rates list was supplied, so the report showed the wrong range.
    """
    def fn(rate, concurrency, idx):
        return {"target_rate": rate, "status_code": 200, "ttft_sec": 0.1, "backoff_sec": 0.0}

    bench = RateRampBenchmark({"rates": [7, 13, 29], "requests_per_step": 1, "request_fn": fn, "sample_size": 5})
    metrics = bench.run()
    assert metrics["config"]["start_rate"] == 7
    assert metrics["config"]["end_rate"] == 29
