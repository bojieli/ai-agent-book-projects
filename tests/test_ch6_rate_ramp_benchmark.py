"""Unit tests for chapter6/model-benchmark/rate_ramp_benchmark.py."""

from pathlib import Path
import sys

# Ensure chapter6/model-benchmark is in sys.path
ch6_dir = Path(__file__).resolve().parent.parent / "chapter6" / "model-benchmark"
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
