"""Rate Ramp Benchmark for LLM Endpoints (Chapter 6).

Simulates multi-concurrency load testing (1 to 50 req/s) against LLM endpoints,
measuring 429 rate limit backoff curves, TTFT percentiles (p50, p95, p99),
error rates, and compiling N=100 evidence packages.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import random
from typing import Any, Callable, Dict, List, Optional, Sequence, Union


def utc_timestamp() -> str:
    """Return ISO 8601 formatted UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def calculate_percentile(values: Sequence[float], percentile: float) -> float:
    """Calculate percentile (0-100) using linear interpolation."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])

    p = max(0.0, min(100.0, percentile))
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return float(sorted_vals[int(k)])

    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return round(float(d0 + d1), 4)


class RateRampBenchmark:
    """Simulates or executes multi-concurrency rate-ramping load tests on LLM endpoints.

    Measures:
    - 429 rate limit backoff curves (attempts, rate limit hits, backoff delays).
    - Time To First Token (TTFT) percentiles: p50, p95, p99.
    - Error rates across load levels.
    - Compiles N=100 evidence packages.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = self._parse_config(config or {})

    def _parse_config(self, config: dict[str, Any]) -> dict[str, Any]:
        start_rate = int(config.get("start_rate", 1))
        end_rate = int(config.get("end_rate", 50))
        step_rate = int(config.get("step_rate", 5))

        if "rates" in config and isinstance(config["rates"], (list, tuple)) and config["rates"]:
            rates = [int(r) for r in config["rates"]]
            start_rate = rates[0]
            end_rate = rates[-1]
        else:
            if start_rate <= end_rate:
                step = max(1, step_rate)
                rates = list(range(start_rate, end_rate + 1, step))
            else:
                step = -max(1, abs(step_rate))
                rates = list(range(start_rate, end_rate - 1, step))
            if not rates or rates[-1] != end_rate:
                rates.append(end_rate)
        return {
            "start_rate": start_rate,
            "end_rate": end_rate,
            "step_rate": step_rate,
            "rates": rates,
            "requests_per_step": int(config.get("requests_per_step", 15)),
            "sample_size": int(config.get("sample_size", 100)),
            "endpoint_url": str(config.get("endpoint_url", "https://api.openai.com/v1/chat/completions")),
            "model": str(config.get("model", "gpt-4o")),
            "max_backoff_sec": float(config.get("max_backoff_sec", 8.0)),
            "request_fn": config.get("request_fn"),
        }

    def simulate_request(
        self, target_rate: int, concurrency: int, request_idx: int
    ) -> dict[str, Any]:
        """Simulate a single endpoint request under load when no live request_fn is provided."""
        # Seed deterministically for test consistency
        rng = random.Random(target_rate * 1000 + request_idx)

        # Base TTFT increases slightly with rate/concurrency
        base_ttft = 0.05 + (target_rate / 100.0) * 0.35 + rng.uniform(0.01, 0.05)
        ttft_sec = round(base_ttft, 4)

        # 429 probability ramps up as target_rate exceeds 25 req/s
        prob_429 = max(0.0, (target_rate - 20) / 40.0) if target_rate > 20 else 0.0
        is_429 = rng.random() < prob_429

        prob_5xx = 0.03 if target_rate > 40 else 0.01
        is_5xx = not is_429 and (rng.random() < prob_5xx)

        if is_429:
            status_code = 429
            retry_count = rng.randint(1, 3)
            backoff_sec = round(min(self.config["max_backoff_sec"], 0.4 * (2 ** (retry_count - 1)) + rng.uniform(0.05, 0.2)), 4)
            error_type = "rate_limit_429"
        elif is_5xx:
            status_code = 500
            retry_count = 0
            backoff_sec = 0.0
            error_type = "server_error_500"
        else:
            status_code = 200
            retry_count = 0
            backoff_sec = 0.0
            error_type = None

        total_latency_sec = round(ttft_sec + rng.uniform(0.1, 0.3) + backoff_sec, 4)

        return {
            "request_id": f"req-{target_rate:02d}-{request_idx:03d}",
            "timestamp": utc_timestamp(),
            "target_rate": target_rate,
            "concurrency": concurrency,
            "status_code": status_code,
            "ttft_sec": ttft_sec,
            "total_latency_sec": total_latency_sec,
            "backoff_sec": backoff_sec,
            "retry_count": retry_count,
            "error_type": error_type,
        }

    def compile_evidence_package(
        self, records: Sequence[dict[str, Any]], sample_size: int = 100
    ) -> list[dict[str, Any]]:
        """Compile exactly sample_size (default N=100) evidence items uniformly sampled from raw records."""
        if not records or not sample_size or sample_size <= 0:
            return []

        valid_records = [r for r in records if isinstance(r, dict)]
        if not valid_records:
            return []

        if len(valid_records) <= sample_size:
            return [dict(r) for r in valid_records]

        # Uniformly sample across the records to cover all rate tiers
        step = len(valid_records) / float(sample_size)
        indices = [int(i * step) for i in range(sample_size)]
        return [dict(valid_records[idx]) for idx in indices]

    def calculate_backoff_curves(
        self, records: Sequence[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compute 429 rate limit backoff curve metrics by request rate level."""
        by_rate: dict[int, dict[str, Any]] = {}
        total_429_backoff_time = 0.0
        max_backoff = 0.0
        total_429 = 0
        total_429_backoff_count = 0

        grouped: dict[int, list[dict[str, Any]]] = {}
        for r in records:
            if not isinstance(r, dict):
                continue
            rate = int(r.get("target_rate", 0) or 0)
            grouped.setdefault(rate, []).append(r)

        for rate in sorted(grouped.keys()):
            step_recs = grouped[rate]
            cnt = len(step_recs)
            hits_429 = sum(1 for r in step_recs if isinstance(r, dict) and r.get("status_code") == 429)
            
            backoffs_429 = [
                float(r.get("backoff_sec") or 0.0)
                for r in step_recs
                if isinstance(r, dict)
                and r.get("status_code") == 429
                and float(r.get("backoff_sec") or 0.0) > 0
            ]
            avg_backoff = round(sum(backoffs_429) / len(backoffs_429), 4) if backoffs_429 else 0.0
            step_max_backoff = max(backoffs_429, default=0.0)

            total_429 += hits_429
            total_429_backoff_count += len(backoffs_429)
            total_429_backoff_time += sum(backoffs_429)
            max_backoff = max(max_backoff, step_max_backoff)

            by_rate[rate] = {
                "total_requests": cnt,
                "429_count": hits_429,
                "backoff_ratio": round(hits_429 / cnt, 4) if cnt > 0 else 0.0,
                "avg_backoff_sec": avg_backoff,
                "max_backoff_sec": round(step_max_backoff, 4),
            }

        overall_avg_backoff = (
            round(total_429_backoff_time / total_429_backoff_count, 4)
            if total_429_backoff_count > 0
            else 0.0
        )

        return {
            "by_rate": by_rate,
            "overall_avg_backoff_sec": overall_avg_backoff,
            "total_backoff_time_sec": round(total_429_backoff_time, 4),
            "max_backoff_observed_sec": round(max_backoff, 4),
            "total_429_count": total_429,
        }

    def run(self, config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Execute rate ramp benchmark and return structured benchmark metrics."""
        if config is not None:
            self.config = self._parse_config(config)

        rates = self.config["rates"]
        reqs_per_step = self.config["requests_per_step"]
        request_fn: Optional[Callable] = self.config["request_fn"]

        all_records: list[dict[str, Any]] = []
        ramp_steps_summary: list[dict[str, Any]] = []

        for rate in rates:
            concurrency = rate
            step_records: list[dict[str, Any]] = []

            for i in range(reqs_per_step):
                if callable(request_fn):
                    rec = request_fn(rate, concurrency, i)
                else:
                    rec = self.simulate_request(rate, concurrency, i)
                step_records.append(rec)
                all_records.append(rec)

            ttfts = [float(r["ttft_sec"]) for r in step_records if isinstance(r, dict) and r.get("ttft_sec") is not None]
            hits_429 = sum(1 for r in step_records if isinstance(r, dict) and r.get("status_code") == 429)
            other_errs = sum(
                1
                for r in step_records
                if not isinstance(r, dict)
                or r.get("status_code") not in (200, 429)
            )
            successes = sum(1 for r in step_records if isinstance(r, dict) and r.get("status_code") == 200)

            # Only throttled (429) requests contribute backoff time to averages.
            backoff_secs = [
                float(r.get("backoff_sec", 0.0) or 0.0)
                for r in step_records
                if isinstance(r, dict)
                and r.get("status_code") == 429
                and float(r.get("backoff_sec", 0.0) or 0.0) > 0
            ]
            avg_backoff = (
                round(sum(backoff_secs) / len(backoff_secs), 4)
                if backoff_secs
                else 0.0
            )

            ramp_steps_summary.append(
                {
                    "rate_req_per_sec": rate,
                    "concurrency": concurrency,
                    "total_requests": len(step_records),
                    "successful_requests": successes,
                    "rate_limit_errors": hits_429,
                    "other_errors": other_errs,
                    "error_rate": round((hits_429 + other_errs) / max(1, len(step_records)), 4),
                    "ttft_p50": calculate_percentile(ttfts, 50),
                    "ttft_p95": calculate_percentile(ttfts, 95),
                    "ttft_p99": calculate_percentile(ttfts, 99),
                    "avg_backoff_sec": avg_backoff,
                }
            )

        all_ttfts = [float(r.get("ttft_sec", 0.0) or 0.0) for r in all_records if isinstance(r, dict)]
        total_reqs = len(all_records)
        total_429 = sum(1 for r in all_records if isinstance(r, dict) and r.get("status_code") == 429)
        total_other = sum(
            1 for r in all_records if isinstance(r, dict) and r.get("status_code") not in (200, 429)
        )
        total_success = sum(1 for r in all_records if isinstance(r, dict) and r.get("status_code") == 200)

        backoff_curves = self.calculate_backoff_curves(all_records)
        evidence_package = self.compile_evidence_package(
            all_records, sample_size=self.config["sample_size"]
        )

        overall_metrics = {
            "total_requests": total_reqs,
            "successful_requests": total_success,
            "total_errors": total_429 + total_other,
            "error_rate": round((total_429 + total_other) / max(1, total_reqs), 4),
            "rate_limit_429_count": total_429,
            "ttft_p50": calculate_percentile(all_ttfts, 50),
            "ttft_p95": calculate_percentile(all_ttfts, 95),
            "ttft_p99": calculate_percentile(all_ttfts, 99),
            "avg_backoff_sec": backoff_curves["overall_avg_backoff_sec"],
        }

        return {
            "config": {
                "start_rate": self.config["start_rate"],
                "end_rate": self.config["end_rate"],
                "step_rate": self.config["step_rate"],
                "sample_size": self.config["sample_size"],
                "endpoint_url": self.config["endpoint_url"],
                "model": self.config["model"],
            },
            "ramp_steps": ramp_steps_summary,
            "overall_metrics": overall_metrics,
            "backoff_curves": backoff_curves,
            "evidence_package": evidence_package,
        }


def run_benchmark(config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Entrypoint function to run rate ramp benchmark and return structured metrics."""
    bench = RateRampBenchmark(config)
    return bench.run()
