#!/usr/bin/env python3
"""Analyze the SQLite evidence produced by the full Experiment 6-8 campaign."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from campaign import (
    DEFAULT_CONFIG,
    DEFAULT_DB,
    PROMPT_SCHEMA_VERSION,
    Price,
    Provider,
    execution_config_fingerprint,
    load_config,
)


HERE = Path(__file__).resolve().parent


def percentile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def describe(values: Iterable[float | int | None]) -> dict[str, float | int | None]:
    present = [float(value) for value in values if value is not None]
    if not present:
        return {"n": 0, "mean": None, "std": None, "p50": None, "p95": None, "p99": None}
    return {
        "n": len(present),
        "mean": statistics.fmean(present),
        "std": statistics.stdev(present) if len(present) > 1 else 0.0,
        "p50": percentile(present, 0.50),
        "p95": percentile(present, 0.95),
        "p99": percentile(present, 0.99),
    }


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def grouped(rows: Sequence[dict[str, Any]], keys: Sequence[str]):
    result: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[tuple(row[key] for key in keys)].append(row)
    return result


def summarize_workloads(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("provider", "model", "target_context_tokens", "target_output_tokens", "concurrency")
    result = []
    for identity, items in sorted(grouped(rows, keys).items()):
        successes = [row for row in items if row["ok"]]
        wall = [row["e2e_s"] for row in successes if row["e2e_s"] is not None]
        visible_output = [
            int(row.get("visible_output_tokens") or max(
                0, int(row.get("output_tokens") or 0) - int(row.get("reasoning_tokens") or 0)
            ))
            for row in successes
        ]
        generation = [
            visible / max(row["e2e_s"] - row["ttft_s"], 1e-9)
            for row, visible in zip(successes, visible_output)
            if visible and row["e2e_s"] is not None and row["ttft_s"] is not None
        ]
        input_prefill = [
            row["input_tokens"] / max(row["ttft_s"], 1e-9)
            for row in successes
            if row["input_tokens"] and row["ttft_s"] is not None
        ]
        target_output = identity[3]
        result.append({
            **dict(zip(keys, identity)),
            "requests": len(items),
            "successes": len(successes),
            "success_rate": len(successes) / len(items),
            "errors": dict(sorted(_counts(row["error_type"] or "unknown" for row in items if not row["ok"]).items())),
            "ttft_s": describe(row["ttft_s"] for row in successes),
            "e2e_s": describe(wall),
            "input_prefill_throughput_tokens_s": describe(input_prefill),
            "output_throughput_tokens_s": describe(generation),
            "actual_input_tokens": describe(row["input_tokens"] for row in successes),
            "actual_output_tokens": describe(row["output_tokens"] for row in successes),
            "visible_output_tokens": describe(visible_output),
            "output_length_attainment_rate": (
                sum(value >= 0.95 * target_output for value in visible_output) / len(successes)
                if successes else 0.0
            ),
            "reasoning_tokens": describe(row["reasoning_tokens"] for row in successes),
            "thinking_ttft_s": describe(row["thinking_ttft_s"] for row in successes),
        })
    return result


def _counts(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = defaultdict(int)
    for value in values:
        result[value] += 1
    return dict(result)


def availability_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for (provider, model), items in sorted(grouped(rows, ("provider", "model")).items()):
        ordered = sorted(items, key=lambda row: row["scheduled_at_utc"] or row["started_at_utc"])
        outages: list[dict[str, Any]] = []
        outage_start: datetime | None = None
        outage_errors: list[str] = []
        availability_start: datetime | None = None
        continuous: list[float] = []
        for row in ordered:
            current = parse_time(row["scheduled_at_utc"] or row["started_at_utc"])
            if row["ok"]:
                if outage_start is not None:
                    outages.append({
                        "started_at_utc": outage_start.isoformat(),
                        "recovered_at_utc": current.isoformat(),
                        "duration_s": (current - outage_start).total_seconds(),
                        "errors": dict(_counts(outage_errors)),
                        "open": False,
                    })
                    outage_start = None
                    outage_errors = []
                if availability_start is None:
                    availability_start = current
            else:
                if availability_start is not None:
                    continuous.append((current - availability_start).total_seconds())
                    availability_start = None
                if outage_start is None:
                    outage_start = current
                outage_errors.append(row["error_type"] or "unknown")
        if ordered:
            last = parse_time(ordered[-1]["scheduled_at_utc"] or ordered[-1]["started_at_utc"])
            if availability_start is not None:
                continuous.append((last - availability_start).total_seconds())
            if outage_start is not None:
                outages.append({
                    "started_at_utc": outage_start.isoformat(),
                    "recovered_at_utc": None,
                    "duration_s": (last - outage_start).total_seconds(),
                    "errors": dict(_counts(outage_errors)),
                    "open": True,
                })
        recovered = [outage["duration_s"] for outage in outages if not outage["open"]]
        successes = sum(row["ok"] for row in ordered)
        result.append({
            "provider": provider,
            "model": model,
            "probes": len(ordered),
            "successes": successes,
            "uptime": successes / len(ordered) if ordered else None,
            "failure_rate": 1 - successes / len(ordered) if ordered else None,
            "error_types": dict(_counts(row["error_type"] or "unknown" for row in ordered if not row["ok"])),
            "outages": outages,
            "outage_count": len(outages),
            "mttr_s": statistics.fmean(recovered) if recovered else None,
            "longest_continuous_availability_s": max(continuous, default=0.0),
            "observed_start_utc": (ordered[0]["scheduled_at_utc"] or ordered[0]["started_at_utc"]) if ordered else None,
            "observed_end_utc": (ordered[-1]["scheduled_at_utc"] or ordered[-1]["started_at_utc"]) if ordered else None,
        })
    return result


def rate_limit_summary(
    batches: Sequence[dict[str, Any]],
    observations: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = {
        identity: dict(_counts(
            row["error_type"] or "unknown"
            for row in items if not row["ok"]
        ))
        for identity, items in grouped(
            observations, ("provider", "model", "concurrency")
        ).items()
    }
    result = []
    for row in sorted(batches, key=lambda item: (item["provider"], item["concurrency"])):
        wall = row["wall_s"]
        result.append({
            "provider": row["provider"],
            "model": row["model"],
            "concurrency": row["concurrency"],
            "requests": row["requested"],
            "successes": row["succeeded"],
            "success_rate": row["succeeded"] / row["requested"] if row["requested"] else None,
            "measured_rpm": row["succeeded"] / wall * 60 if wall else None,
            "measured_input_tpm": row["input_tokens"] / wall * 60 if wall else None,
            "measured_output_tpm": row["output_tokens"] / wall * 60 if wall else None,
            "wall_s": wall,
            "errors": errors.get((row["provider"], row["model"], row["concurrency"]), {}),
        })
    return result


def cost_summary(
    rows: Sequence[dict[str, Any]],
    providers: dict[str, Provider],
) -> list[dict[str, Any]]:
    result = []
    for (provider_name, model, phase), items in sorted(grouped(rows, ("provider", "model", "phase")).items()):
        provider = providers[provider_name]
        price = provider.pricing
        uncached = sum(max(0, row["input_tokens"] - row["cached_input_tokens"]) for row in items)
        cached = sum(row["cached_input_tokens"] for row in items)
        output = sum(row["output_tokens"] for row in items)
        unpriced: dict[str, int] = {}
        native_cost = 0.0
        for label, tokens, rate in (
            ("input", uncached, price.input_per_million),
            ("cached_input", cached, price.cached_input_per_million),
            ("output", output, price.output_per_million),
        ):
            if tokens and rate is None:
                unpriced[label] = tokens
            elif rate is not None:
                native_cost += tokens * rate / 1_000_000
        no_cache_native = None
        if price.input_per_million is not None and price.output_per_million is not None:
            no_cache_native = (
                (uncached + cached) * price.input_per_million
                + output * price.output_per_million
            ) / 1_000_000
        priced = not unpriced and price.native_rates_complete
        usd_conversion = 1.0 if price.currency == "USD" else price.usd_per_currency_unit
        comparable_usd = priced and price.usd_conversion_complete
        measured_usd = native_cost * usd_conversion if comparable_usd else None
        no_cache_usd = (
            no_cache_native * usd_conversion
            if comparable_usd and no_cache_native is not None else None
        )
        result.append({
            "provider": provider_name,
            "model": model,
            "phase": phase,
            "requests": len(items),
            "uncached_input_tokens": uncached,
            "cached_input_tokens": cached,
            "output_tokens": output,
            "currency": price.currency,
            "measured_cost_native": native_cost if priced else None,
            "no_cache_counterfactual_native": no_cache_native if priced else None,
            "cache_savings_native": (
                no_cache_native - native_cost
                if priced and no_cache_native is not None else None
            ),
            "usd_per_currency_unit": usd_conversion if comparable_usd else None,
            "measured_cost_usd": measured_usd,
            "no_cache_counterfactual_usd": no_cache_usd,
            "cache_savings_usd": (
                no_cache_usd - measured_usd
                if no_cache_usd is not None and measured_usd is not None else None
            ),
            "unpriced_tokens": unpriced,
            "native_pricing_complete": priced,
            "pricing_complete": comparable_usd,
            "pricing_status": price.status,
            "pricing_blocker": price.blocker,
        })
    return result


def external_benchmark_comparison(
    config: dict[str, Any],
    workload: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for reference in config.get("external_benchmark_references", []):
        context = reference.get("context_tokens", 32768)
        output = reference.get("output_tokens", 512)
        measured = next((
            row for row in workload
            if row["provider"] == reference.get("provider")
            and row["model"] == reference.get("model")
            and row["target_context_tokens"] == context
            and row["target_output_tokens"] == output
        ), None)
        reference_metrics = reference.get("metrics", {})
        measured_metrics = None
        deltas = None
        if measured:
            measured_metrics = {
                "ttft_p50_s": measured["ttft_s"]["p50"],
                "output_throughput_p50_tokens_s": measured["output_throughput_tokens_s"]["p50"],
            }
            deltas = {
                key: (
                    measured_metrics[key] - float(reference_metrics[key])
                    if measured_metrics.get(key) is not None and key in reference_metrics
                    else None
                )
                for key in measured_metrics
            }
        result.append({
            "provider": reference.get("provider"),
            "model": reference.get("model"),
            "context_tokens": context,
            "output_tokens": output,
            "source_url": reference.get("source_url"),
            "as_of": reference.get("as_of"),
            "reference_metrics": reference_metrics,
            "measured_metrics": measured_metrics,
            "measured_minus_reference": deltas,
        })
    return result


def completion_audit(
    config: dict[str, Any],
    workload: Sequence[dict[str, Any]],
    availability: Sequence[dict[str, Any]],
    rates: Sequence[dict[str, Any]],
    costs: Sequence[dict[str, Any]],
    observations: Sequence[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected_contexts = set(config["workload"]["context_tokens"])
    expected_outputs = set(config["workload"]["output_tokens"])
    exact_workload_design = (
        expected_contexts == {8192, 32768, 131072}
        and expected_outputs == {512, 2048}
        and int(config["workload"].get("requests_per_cell", 0)) >= 100
    )
    exact_availability_design = (
        float(config["availability"].get("duration_hours", 0)) >= 168
        and float(config["availability"].get("interval_seconds", float("inf"))) <= 3600
        and int(config["availability"].get("requests_per_probe", 0)) >= 1
    )
    configured_rate_levels = list(config["rate_limit"].get("concurrency_levels", []))
    exact_rate_ramp_design = (
        len(configured_rate_levels) >= 2
        and configured_rate_levels == sorted(set(configured_rate_levels))
        and int(config["rate_limit"].get("requests_per_level", 0)) >= 100
    )
    workload_cells = {
        (row["provider"], row["target_context_tokens"], row["target_output_tokens"]): row
        for row in workload
    }
    providers = [raw["name"] for raw in config["providers"]]
    missing_cells = []
    undersampled = []
    unsuccessful_cells = []
    for provider in providers:
        for context in expected_contexts:
            for output in expected_outputs:
                row = workload_cells.get((provider, context, output))
                if row is None:
                    missing_cells.append({"provider": provider, "context": context, "output": output})
                elif row["requests"] < max(
                    100, int(config["workload"].get("requests_per_cell", 100))
                ):
                    undersampled.append({
                        "provider": provider, "context": context, "output": output,
                        "requests": row["requests"],
                    })
                elif row["successes"] == 0:
                    unsuccessful_cells.append({
                        "provider": provider, "context": context, "output": output,
                    })
    minimum_attainment = float(config["workload"].get("minimum_output_attainment_rate", 0.95))
    output_attainment_gaps = [
        {
            "provider": row["provider"],
            "context": row["target_context_tokens"],
            "output": row["target_output_tokens"],
            "attainment_rate": row.get("output_length_attainment_rate", 0.0),
            "required": minimum_attainment,
        }
        for row in workload
        if row.get("output_length_attainment_rate", 0.0) < minimum_attainment
    ]
    availability_hours = []
    availability_by_provider = {row["provider"]: row for row in availability}
    for row in availability:
        if row["observed_start_utc"] and row["observed_end_utc"]:
            hours = (
                parse_time(row["observed_end_utc"]) - parse_time(row["observed_start_utc"])
            ).total_seconds() / 3600
            availability_hours.append({"provider": row["provider"], "hours": hours})
    required_availability_hours = float(config["availability"]["duration_hours"])
    expected_probe_count = int(
        required_availability_hours * 3600
        / float(config["availability"]["interval_seconds"])
    ) + 1
    missing_availability_providers = sorted(
        set(providers) - set(availability_by_provider)
    )
    short_availability = [
        row for row in availability_hours
        if row["hours"] < required_availability_hours
    ]
    undersampled_availability = [
        {
            "provider": provider,
            "probes": availability_by_provider[provider]["probes"],
            "required_probes": expected_probe_count,
        }
        for provider in providers
        if provider in availability_by_provider
        and availability_by_provider[provider]["probes"] < expected_probe_count
    ]
    expected_levels = set(config["rate_limit"]["concurrency_levels"])
    measured_levels = defaultdict(set)
    undersampled_rate_levels = []
    for row in rates:
        measured_levels[row["provider"]].add(row["concurrency"])
        if row["requests"] < config["rate_limit"]["requests_per_level"]:
            undersampled_rate_levels.append({
                "provider": row["provider"], "concurrency": row["concurrency"],
                "requests": row["requests"],
            })
    missing_rate_levels = {
        provider: sorted(expected_levels - measured_levels[provider])
        for provider in providers if expected_levels - measured_levels[provider]
    }
    rate_limit_boundaries = {}
    missing_rate_limit_boundaries = []
    for provider in providers:
        provider_rows = sorted(
            (row for row in rates if row["provider"] == provider),
            key=lambda row: row["concurrency"],
        )
        boundary = next(
            (
                row for row in provider_rows
                if row.get("errors", {}).get("rate_limit", 0) > 0
            ),
            None,
        )
        if boundary:
            rate_limit_boundaries[provider] = {
                "first_rate_limited_concurrency": boundary["concurrency"],
                "last_pre_limit_rpm": next(
                    (
                        row["measured_rpm"] for row in reversed(provider_rows)
                        if row["concurrency"] < boundary["concurrency"]
                        and row["successes"] > 0
                    ),
                    None,
                ),
                "last_pre_limit_input_tpm": next(
                    (
                        row["measured_input_tpm"] for row in reversed(provider_rows)
                        if row["concurrency"] < boundary["concurrency"]
                        and row["successes"] > 0
                    ),
                    None,
                ),
            }
        else:
            missing_rate_limit_boundaries.append(provider)
    cost_rounds = defaultdict(int)
    for row in observations:
        if row["phase"] == "agent_cost":
            cost_rounds[row["provider"]] += 1
    missing_cost_traces = {
        provider: config["agent_cost"]["rounds"] - cost_rounds[provider]
        for provider in providers if cost_rounds[provider] < config["agent_cost"]["rounds"]
    }
    incomplete_pricing = [
        row["provider"] for row in costs
        if row["phase"] == "agent_cost" and not row["pricing_complete"]
    ]
    pricing_config_gaps = []
    for raw in config["providers"]:
        pricing = raw.get("pricing", {})
        missing = [
            field for field in (
                "input_per_million",
                "cached_input_per_million",
                "output_per_million",
                "currency",
                "source_url",
                "as_of",
            )
            if pricing.get(field) in (None, "")
        ]
        currency = pricing.get("currency")
        if currency and currency != "USD":
            missing.extend(
                field for field in (
                    "usd_per_currency_unit", "fx_source_url", "fx_as_of"
                )
                if pricing.get(field) in (None, "")
            )
        if missing:
            pricing_config_gaps.append({
                "provider": raw["name"],
                "missing": sorted(set(missing)),
                "status": pricing.get("status", "unresolved"),
                "blocker": pricing.get("blocker"),
            })
        elif (
            pricing.get("status") not in {"verified", "verified_native", "verified_with_fx"}
            or not str(pricing.get("source_url", "")).startswith(("https://", "http://"))
            or (currency != "USD" and not str(pricing.get("fx_source_url", "")).startswith(("https://", "http://")))
        ):
            pricing_config_gaps.append({
                "provider": raw["name"],
                "missing": [],
                "status": pricing.get("status", "unresolved"),
                "blocker": pricing.get("blocker") or "pricing provenance/status is not validated",
            })
    missing_pricing_rows = [
        provider for provider in providers
        if not any(row["provider"] == provider and row["phase"] == "agent_cost" for row in costs)
    ]
    thinking_providers = [
        raw["name"] for raw in config["providers"]
        if raw.get("thinking_budget_tokens") or any(
            tag in raw["model"].casefold() for tag in ("thinking", "reason", "kimi-k3", "gpt-5")
        )
    ]
    thinking_measured = {
        provider for provider in thinking_providers
        if any(
            row["provider"] == provider
            and row["ok"]
            and (row["reasoning_tokens"] > 0 or row["thinking_ttft_s"] is not None)
            for row in observations
        )
    }
    missing_thinking_metrics = sorted(set(thinking_providers) - thinking_measured)
    successful_workload_rows = [
        row for row in observations if row["phase"] == "workload" and row["ok"]
    ]
    missing_raw_evidence = [
        row["cell_id"] for row in successful_workload_rows
        if not row.get("prompt_sha256")
        or not row.get("output_sha256")
        or row.get("output_text") in (None, "")
    ]
    required_families = set(config.get("required_model_families", []))
    observed_families = {
        raw.get("model_family") for raw in config["providers"] if raw.get("model_family")
    }
    missing_model_families = sorted(required_families - observed_families)
    external_reference_gaps = []
    references = config.get("external_benchmark_references", [])
    if not references:
        external_reference_gaps.append({"reason": "no dated external benchmark reference configured"})
    for reference in references:
        missing = [
            field for field in ("source_url", "as_of", "provider", "model", "metrics")
            if not reference.get(field)
        ]
        metrics = reference.get("metrics") or {}
        missing.extend(
            f"metrics.{field}"
            for field in ("ttft_p50_s", "output_throughput_p50_tokens_s")
            if metrics.get(field) is None
        )
        if reference.get("source_url") and not str(reference["source_url"]).startswith(("https://", "http://")):
            missing.append("source_url_http")
        if missing:
            external_reference_gaps.append({
                "provider": reference.get("provider"),
                "model": reference.get("model"),
                "missing": missing,
            })
            continue
        matching = [
            row for row in workload
            if row["provider"] == reference["provider"]
            and row["model"] == reference["model"]
            and row["target_context_tokens"] == reference.get("context_tokens", 32768)
            and row["target_output_tokens"] == reference.get("output_tokens", 512)
            and row["successes"] > 0
        ]
        if not matching:
            external_reference_gaps.append({
                "provider": reference["provider"],
                "model": reference["model"],
                "reason": "no successful matching workload cell for external comparison",
            })
    expected_fingerprint = execution_config_fingerprint(config)
    metadata_matches = bool(
        metadata
        and metadata.get("execution_config_fingerprint") == expected_fingerprint
        and metadata.get("prompt_schema_version") == PROMPT_SCHEMA_VERSION
    )
    same_model_provider_gaps = []
    for group in config.get("same_model_provider_groups", []):
        group_providers = group.get("providers", [])
        if len(group_providers) < 2:
            same_model_provider_gaps.append({
                "logical_model": group.get("logical_model"),
                "reason": "comparison group must name at least two providers",
            })
            continue
        for provider in group_providers:
            for context in expected_contexts:
                for output in expected_outputs:
                    row = workload_cells.get((provider, context, output))
                    if (
                        row is None
                        or row["requests"] < 100
                        or row["successes"] == 0
                    ):
                        same_model_provider_gaps.append({
                            "logical_model": group.get("logical_model"),
                            "provider": provider,
                            "context": context,
                            "output": output,
                            "reason": "missing successful official workload cell",
                        })
    checks = {
        "configuration_matches_exact_8k_32k_128k_x_512_2048_design": exact_workload_design,
        "all_8k_32k_128k_x_512_2048_cells_present": not missing_cells,
        "at_least_100_requests_per_workload_cell": not undersampled and not missing_cells,
        "at_least_one_success_per_workload_cell": not unsuccessful_cells and not missing_cells,
        "visible_output_length_target_attained": not output_attainment_gaps and not missing_cells,
        "availability_observed_for_at_least_168_hours": (
            not missing_availability_providers
            and not short_availability
            and not undersampled_availability
        ),
        "availability_schedule_is_hourly_for_seven_days": exact_availability_design,
        "rate_limit_ramp_configuration_is_progressive": exact_rate_ramp_design,
        "all_rate_limit_levels_measured": not missing_rate_levels and not undersampled_rate_levels,
        "rate_limit_boundary_identified": not missing_rate_limit_boundaries,
        "multi_round_agent_cost_trace_present": not missing_cost_traces,
        "cached_input_output_pricing_complete": (
            not incomplete_pricing
            and not missing_pricing_rows
            and not pricing_config_gaps
        ),
        "thinking_length_or_latency_measured": not missing_thinking_metrics,
        "raw_request_response_evidence_present": (
            bool(successful_workload_rows) and not missing_raw_evidence
        ),
        "required_model_families_covered": bool(required_families) and not missing_model_families,
        "external_monitoring_reference_compared": not external_reference_gaps,
        "execution_config_fingerprint_matches": metadata_matches,
        "same_model_compared_across_providers": (
            bool(config.get("same_model_provider_groups"))
            and not same_model_provider_gaps
        ),
    }
    return {
        "official_complete": all(checks.values()),
        "checks": checks,
        "missing_workload_cells": missing_cells,
        "undersampled_workload_cells": undersampled,
        "unsuccessful_workload_cells": unsuccessful_cells,
        "output_attainment_gaps": output_attainment_gaps,
        "availability_hours": availability_hours,
        "missing_availability_providers": missing_availability_providers,
        "short_availability": short_availability,
        "undersampled_availability": undersampled_availability,
        "missing_rate_levels": missing_rate_levels,
        "undersampled_rate_levels": undersampled_rate_levels,
        "rate_limit_boundaries": rate_limit_boundaries,
        "missing_rate_limit_boundaries": missing_rate_limit_boundaries,
        "missing_cost_traces": missing_cost_traces,
        "incomplete_pricing": incomplete_pricing,
        "pricing_config_gaps": pricing_config_gaps,
        "missing_pricing_rows": missing_pricing_rows,
        "missing_thinking_metrics": missing_thinking_metrics,
        "missing_raw_evidence_cell_ids": missing_raw_evidence,
        "missing_model_families": missing_model_families,
        "external_reference_gaps": external_reference_gaps,
        "expected_execution_config_fingerprint": expected_fingerprint,
        "observed_campaign_metadata": metadata,
        "same_model_provider_gaps": same_model_provider_gaps,
    }


def load_rows(connection: sqlite3.Connection, campaign_id: str, table: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT * FROM {table} WHERE campaign_id = ?", (campaign_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def analyze(db: Path, config_path: Path, campaign_id: str) -> dict[str, Any]:
    config = load_config(config_path)
    providers = {
        raw["name"]: Provider.from_dict(dict(raw)) for raw in config["providers"]
    }
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    try:
        observations = load_rows(connection, campaign_id, "observations")
        batches = load_rows(connection, campaign_id, "batches")
        try:
            metadata_row = connection.execute(
                "SELECT * FROM campaign_metadata WHERE campaign_id = ?", (campaign_id,)
            ).fetchone()
        except sqlite3.OperationalError:
            metadata_row = None
        metadata = dict(metadata_row) if metadata_row else None
    finally:
        connection.close()
    workload = summarize_workloads([row for row in observations if row["phase"] == "workload"])
    availability = availability_summary([row for row in observations if row["phase"] == "availability"])
    rate_observations = [row for row in observations if row["phase"] == "rate_limit"]
    rates = rate_limit_summary(
        [row for row in batches if row["phase"] == "rate_limit"],
        rate_observations,
    )
    costs = cost_summary(observations, providers)
    external_comparison = external_benchmark_comparison(config, workload)
    return {
        "schema_version": "1.0",
        "campaign_id": campaign_id,
        "database": str(db),
        "campaign_metadata": metadata,
        "observation_count": len(observations),
        "workload": workload,
        "availability": availability,
        "rate_limits": rates,
        "costs": costs,
        "external_benchmark_comparison": external_comparison,
        "completion_audit": completion_audit(
            config, workload, availability, rates, costs, observations, metadata
        ),
    }


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def fmt_pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}%}"


def markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Experiment 6-8 campaign: `{report['campaign_id']}`",
        "",
        f"Observations: **{report['observation_count']}**",
        f"Official completion: **{report['completion_audit']['official_complete']}**",
        "",
        "## Standard workloads",
        "",
        "| Provider | Context | Output | N | Success | TTFT p50/p95/p99 (s) | E2E p50/p95/p99 (s) | Input tok/s p50 | Visible output tok/s p50 | Output attainment | Reasoning tok p50 | Thinking TTFT p50 (s) |",
        "|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["workload"]:
        ttft, e2e = row["ttft_s"], row["e2e_s"]
        lines.append(
            f"| {row['provider']} | {row['target_context_tokens']} | {row['target_output_tokens']} | "
            f"{row['requests']} | {fmt_pct(row['success_rate'], 1)} | "
            f"{fmt(ttft['p50'])}/{fmt(ttft['p95'])}/{fmt(ttft['p99'])} | "
            f"{fmt(e2e['p50'])}/{fmt(e2e['p95'])}/{fmt(e2e['p99'])} | "
            f"{fmt(row['input_prefill_throughput_tokens_s']['p50'], 1)} | "
            f"{fmt(row['output_throughput_tokens_s']['p50'], 1)} | "
            f"{fmt_pct(row['output_length_attainment_rate'], 1)} | "
            f"{fmt(row['reasoning_tokens']['p50'], 1)} | "
            f"{fmt(row['thinking_ttft_s']['p50'])} |"
        )
    lines.extend([
        "", "## Availability", "",
        "| Provider | Probes | Uptime | Outages | MTTR (s) | Longest available (h) |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["availability"]:
        lines.append(
            f"| {row['provider']} | {row['probes']} | {fmt_pct(row['uptime'], 2)} | "
            f"{row['outage_count']} | {fmt(row['mttr_s'])} | "
            f"{row['longest_continuous_availability_s'] / 3600:.2f} |"
        )
    lines.extend([
        "", "## Measured rate-limit ramp", "",
        "| Provider | Concurrency | Success | RPM | Input TPM | Output TPM |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in report["rate_limits"]:
        lines.append(
            f"| {row['provider']} | {row['concurrency']} | {fmt_pct(row['success_rate'], 1)} | "
            f"{fmt(row['measured_rpm'], 1)} | {fmt(row['measured_input_tpm'], 1)} | "
            f"{fmt(row['measured_output_tpm'], 1)} |"
        )
    lines.extend([
        "", "## Native and comparable costs", "",
        "| Provider | Phase | Requests | Native cost | Currency | USD cost | Cache savings (native) | Unpriced usage |",
        "|---|---|---:|---:|---|---:|---:|---|",
    ])
    for row in report["costs"]:
        lines.append(
            f"| {row['provider']} | {row['phase']} | {row['requests']} | "
            f"{fmt(row['measured_cost_native'], 6)} | {row['currency'] or '—'} | "
            f"{fmt(row['measured_cost_usd'], 6)} | "
            f"{fmt(row['cache_savings_native'], 6)} | "
            f"{json.dumps(row['unpriced_tokens'], ensure_ascii=False)} |"
        )
    lines.extend(["", "## External monitoring comparison", ""])
    if report["external_benchmark_comparison"]:
        lines.extend(["```json", json.dumps(
            report["external_benchmark_comparison"], ensure_ascii=False, indent=2
        ), "```"])
    else:
        lines.append("No dated external monitoring reference is configured; this manuscript gate is incomplete.")
    lines.extend([
        "", "## Completion audit", "", "```json",
        json.dumps(report["completion_audit"], ensure_ascii=False, indent=2),
        "```", "",
    ])
    return "\n".join(lines)
def export_campaign_summary(
    db_path: Path, config_path: Path | None = None, campaign_id: str = "experiment-6-8"
) -> dict[str, Any]:
    """Export structured JSON and Markdown summary metrics for a campaign database."""
    cfg = config_path or DEFAULT_CONFIG
    report = analyze(db_path, cfg, campaign_id)
    md_text = markdown(report)
    return {
        "report": report,
        "markdown": md_text,
        "official_complete": report["completion_audit"]["official_complete"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze full Experiment 6-8 campaign evidence")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--campaign-id", default="experiment-6-8")
    parser.add_argument("--json", type=Path, default=HERE / "results" / "campaign_report.json")
    parser.add_argument("--markdown", type=Path, default=HERE / "results" / "campaign_report.md")
    args = parser.parse_args()
    report = analyze(args.db, args.config, args.campaign_id)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(f"Wrote {args.json} and {args.markdown}")
    print(f"Official completion: {report['completion_audit']['official_complete']}")
    return 0 if report["completion_audit"]["official_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
