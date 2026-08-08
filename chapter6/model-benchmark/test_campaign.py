from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from analysis import availability_summary, completion_audit, markdown, percentile, summarize_workloads
from campaign import (
    CampaignStore,
    Observation,
    Price,
    PromptFactory,
    Provider,
    error_details,
    execution_config_fingerprint,
    measure_anthropic,
    measure_gemini,
    measure_stream,
)


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["stream"] is True
        usage = SimpleNamespace(
            prompt_tokens=100,
            completion_tokens=12,
            prompt_tokens_details=SimpleNamespace(cached_tokens=40),
            completion_tokens_details=SimpleNamespace(reasoning_tokens=5),
        )
        return iter([
            SimpleNamespace(
                id="request-1", usage=None,
                choices=[SimpleNamespace(
                    finish_reason=None,
                    delta=SimpleNamespace(content=None, reasoning_content="think"),
                )],
            ),
            SimpleNamespace(
                id="request-1", usage=None,
                choices=[SimpleNamespace(
                    finish_reason=None,
                    delta=SimpleNamespace(content="answer", reasoning_content=None),
                )],
            ),
            SimpleNamespace(id="request-1", usage=usage, choices=[]),
        ])


def fake_client():
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))


def provider():
    return Provider(
        name="test", model="test-model", api_key_env="UNUSED", base_url="https://example.test/v1",
        pricing=Price(1.0, 0.1, 2.0, currency="USD", source_url="https://example.test", as_of="2026-07-29", status="verified"),
    )


def observation(cell: str, ok: bool, scheduled: str, **overrides):
    values = dict(
        campaign_id="campaign", phase="availability", cell_id=cell,
        provider="test", model="test-model", scheduled_at_utc=scheduled,
        started_at_utc=scheduled, ended_at_utc=scheduled,
        target_context_tokens=100, target_output_tokens=10, concurrency=1,
        request_index=0, ok=ok,
    )
    values.update(overrides)
    return Observation(**values)


def test_prompt_factory_hits_exact_reference_token_count():
    factory = PromptFactory()
    text = factory.build(256, 64)
    assert len(factory.encoding.encode(text)) == 256
    assert "64 tokens" in text


def test_measure_stream_records_usage_cache_reasoning_and_hash():
    row = measure_stream(
        provider(), campaign_id="c", phase="workload", cell_id="id", prompt="hello",
        target_context_tokens=10, target_output_tokens=12, concurrency=1,
        request_index=0, client=fake_client(),
    )
    assert row.ok is True
    assert row.input_tokens == 100
    assert row.cached_input_tokens == 40
    assert row.output_tokens == 12
    assert row.visible_output_tokens == 7
    assert row.reasoning_tokens == 5
    assert row.thinking_ttft_s is not None
    assert row.output_sha256
    assert row.output_text == "answer"
    assert row.prompt_sha256


def test_store_is_resumable_and_ignores_duplicate_cell(tmp_path: Path):
    store = CampaignStore(tmp_path / "campaign.sqlite3")
    row = observation("same", True, "2026-01-01T00:00:00+00:00")
    store.add(row)
    store.add(row)
    assert store.has("same")
    count = store.connection.execute("SELECT count(*) FROM observations").fetchone()[0]
    store.close()
    assert count == 1


def test_campaign_binding_rejects_changed_execution_but_allows_repricing(tmp_path: Path):
    import pytest

    config = {
        "providers": [{
            "name": "p", "model": "m", "api_key_env": "KEY",
            "protocol": "openai", "pricing": {"input_per_million": 1.0},
        }],
        "workload": {"context_tokens": [8192], "output_tokens": [512], "requests_per_cell": 100},
        "availability": {"duration_hours": 168, "interval_seconds": 3600},
        "rate_limit": {"concurrency_levels": [1, 2], "requests_per_level": 100},
        "agent_cost": {"rounds": 2},
    }
    store = CampaignStore(tmp_path / "campaign.sqlite3")
    first = store.bind_campaign("c", config)
    repriced = {**config, "providers": [{
        **config["providers"][0], "pricing": {"input_per_million": 2.0},
    }]}
    assert store.bind_campaign("c", repriced) == first
    changed = {**config, "workload": {**config["workload"], "output_tokens": [2048]}}
    assert execution_config_fingerprint(changed) != first
    with pytest.raises(RuntimeError, match="bound to execution fingerprint"):
        store.bind_campaign("c", changed)
    store.close()


def test_batch_counts_accumulate_across_resumed_invocations(tmp_path: Path):
    store = CampaignStore(tmp_path / "campaign.sqlite3")
    payload = {
        "batch_id": "b", "campaign_id": "c", "phase": "workload",
        "provider": "p", "model": "m", "target_context_tokens": 8192,
        "target_output_tokens": 512, "concurrency": 4,
        "requested": 1, "succeeded": 1, "input_tokens": 8192,
        "output_tokens": 512, "wall_s": 1.0,
        "started_at_utc": "2026-01-01T00:00:00+00:00",
        "ended_at_utc": "2026-01-01T00:00:01+00:00",
    }
    store.add_batch(payload)
    store.add_batch({
        **payload, "requested": 99, "succeeded": 98,
        "input_tokens": 99 * 8192, "output_tokens": 98 * 512,
        "wall_s": 10.0,
    })
    row = store.connection.execute(
        "SELECT requested, succeeded, input_tokens, output_tokens, wall_s FROM batches"
    ).fetchone()
    assert tuple(row) == (100, 99, 100 * 8192, 99 * 512, 11.0)
    store.close()


def test_availability_groups_failures_and_computes_mttr():
    rows = [
        observation("1", True, "2026-01-01T00:00:00+00:00"),
        observation("2", False, "2026-01-01T01:00:00+00:00", error_type="provider_5xx"),
        observation("3", False, "2026-01-01T02:00:00+00:00", error_type="provider_5xx"),
        observation("4", True, "2026-01-01T03:00:00+00:00"),
    ]
    summary = availability_summary([row.__dict__ | {"ok": int(row.ok)} for row in rows])[0]
    assert summary["uptime"] == 0.5
    assert summary["outage_count"] == 1
    assert summary["mttr_s"] == 7200


def test_percentile_and_workload_summary_include_output_attainment():
    assert percentile([1, 2, 3], 0.5) == 2
    rows = [
        observation(
            "1", True, "2026-01-01T00:00:00+00:00", phase="workload",
            target_output_tokens=100, input_tokens=200, output_tokens=100,
            ttft_s=0.1, e2e_s=1.1,
        ).__dict__,
        observation(
            "2", True, "2026-01-01T00:01:00+00:00", phase="workload",
            target_output_tokens=100, input_tokens=200, output_tokens=90,
            ttft_s=0.2, e2e_s=1.2,
        ).__dict__,
    ]
    summary = summarize_workloads(rows)[0]
    assert summary["requests"] == 2
    assert summary["output_length_attainment_rate"] == 0.5


def test_error_classification_detects_rate_limit():
    exc = RuntimeError("429 rate limit exceeded")
    _, category, _ = error_details(exc)
    assert category == "rate_limit"


def test_error_classification_does_not_mislabel_exhausted_quota_as_rate_limit():
    exc = RuntimeError("429 insufficient_quota: check billing")
    _, category, _ = error_details(exc)
    assert category == "quota_or_balance"


class FakeAnthropicStream:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __iter__(self):
        return iter([
            SimpleNamespace(
                type="content_block_delta",
                delta=SimpleNamespace(type="thinking_delta", thinking="reason"),
            ),
            SimpleNamespace(
                type="content_block_delta",
                delta=SimpleNamespace(type="text_delta", text="answer"),
            ),
        ])

    def get_final_message(self):
        usage = SimpleNamespace(
            input_tokens=60, output_tokens=10,
            cache_creation_input_tokens=20, cache_read_input_tokens=20,
        )
        return SimpleNamespace(
            id="anthropic-1", usage=usage, content=[], stop_reason="end_turn"
        )


def test_native_anthropic_adapter_records_cache_and_ttft():
    client = SimpleNamespace(
        messages=SimpleNamespace(stream=lambda **_kwargs: FakeAnthropicStream())
    )
    row = measure_anthropic(
        Provider("anthropic", "claude-test", "UNUSED", protocol="anthropic"),
        campaign_id="c", phase="workload", cell_id="a", prompt="hello",
        target_context_tokens=10, target_output_tokens=10, concurrency=1,
        request_index=0, client=client,
    )
    assert row.ok
    assert row.input_tokens == 100
    assert row.cached_input_tokens == 20
    assert row.output_tokens == 10
    assert row.visible_output_tokens > 0
    assert row.thinking_ttft_s is not None


def test_native_gemini_adapter_records_thought_tokens():
    usage = SimpleNamespace(
        prompt_token_count=50, cached_content_token_count=10,
        candidates_token_count=8, thoughts_token_count=4,
    )
    parts = [
        SimpleNamespace(text="reason", thought=True),
        SimpleNamespace(text="answer", thought=False),
    ]
    chunk = SimpleNamespace(
        usage_metadata=usage,
        candidates=[SimpleNamespace(
            finish_reason="STOP",
            content=SimpleNamespace(parts=parts),
        )],
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=lambda **_kwargs: iter([chunk]))
    )
    row = measure_gemini(
        Provider("gemini", "gemini-test", "UNUSED", protocol="gemini"),
        campaign_id="c", phase="workload", cell_id="g", prompt="hello",
        target_context_tokens=10, target_output_tokens=10, concurrency=1,
        request_index=0, client=client,
    )
    assert row.ok
    assert row.input_tokens == 50
    assert row.cached_input_tokens == 10
    assert row.reasoning_tokens == 4
    assert row.output_tokens == 12
    assert row.visible_output_tokens == 8


def test_completion_requires_every_provider_availability_and_pinned_prices():
    config = {
        "workload": {"context_tokens": [8192], "output_tokens": [512]},
        "availability": {"duration_hours": 168, "interval_seconds": 3600},
        "rate_limit": {"concurrency_levels": [1], "requests_per_level": 1},
        "agent_cost": {"rounds": 1},
        "providers": [
            {
                "name": "provider-a", "model": "shared-model",
                "pricing": {
                    "input_per_million": 1.0,
                    "cached_input_per_million": 0.1,
                    "output_per_million": 2.0,
                    "currency": "USD",
                    "source_url": "https://example.test/pricing",
                    "as_of": "2026-07-29",
                    "status": "verified",
                },
            },
            {
                "name": "provider-b", "model": "shared-model",
                "pricing": {
                    "input_per_million": None,
                    "cached_input_per_million": None,
                    "output_per_million": None,
                    "currency": None,
                    "source_url": None,
                    "as_of": None,
                    "status": "unresolved",
                    "blocker": "exact public model price not found",
                },
            },
        ],
        "same_model_provider_groups": [{
            "logical_model": "shared-model",
            "providers": ["provider-a", "provider-b"],
        }],
    }
    workload = [{
        "provider": "provider-a", "target_context_tokens": 8192,
        "target_output_tokens": 512, "requests": 100, "successes": 100,
    }]
    availability = [{
        "provider": "provider-a", "model": "shared-model", "probes": 169,
        "observed_start_utc": "2026-01-01T00:00:00+00:00",
        "observed_end_utc": "2026-01-08T00:00:00+00:00",
    }]

    audit = completion_audit(config, workload, availability, [], [], [])

    assert audit["checks"]["configuration_matches_exact_8k_32k_128k_x_512_2048_design"] is False
    assert audit["checks"]["availability_observed_for_at_least_168_hours"] is False
    assert audit["missing_availability_providers"] == ["provider-b"]
    assert audit["checks"]["cached_input_output_pricing_complete"] is False
    assert audit["pricing_config_gaps"][0]["provider"] == "provider-b"
    assert audit["checks"]["same_model_compared_across_providers"] is False
    assert audit["same_model_provider_gaps"]


def test_non_usd_pricing_requires_dated_fx_for_comparable_cost():
    price = Price(
        20.0, 2.0, 100.0,
        currency="CNY",
        source_url="https://example.test/cny-pricing",
        as_of="2026-07-29",
        status="verified_native",
    )
    assert price.native_rates_complete is True
    assert price.usd_conversion_complete is False

    converted = Price(
        20.0, 2.0, 100.0,
        currency="CNY",
        source_url="https://example.test/cny-pricing",
        as_of="2026-07-29",
        usd_per_currency_unit=0.139,
        fx_source_url="https://example.test/fx",
        fx_as_of="2026-07-29",
        status="verified_with_fx",
    )
    assert converted.usd_conversion_complete is True


def test_markdown_tolerates_null_percentage_fields() -> None:
    report = {
        "campaign_id": "exp6-8-test",
        "observation_count": 0,
        "completion_audit": {"official_complete": False},
        "workload": [
            {
                "provider": "openai",
                "target_context_tokens": 8192,
                "target_output_tokens": 512,
                "requests": 0,
                "success_rate": None,
                "ttft_s": {"p50": None, "p95": None, "p99": None},
                "e2e_s": {"p50": None, "p95": None, "p99": None},
                "input_prefill_throughput_tokens_s": {"p50": None},
                "output_throughput_tokens_s": {"p50": None},
                "output_length_attainment_rate": None,
                "reasoning_tokens": {"p50": None},
                "thinking_ttft_s": {"p50": None},
            }
        ],
        "availability": [
            {
                "provider": "openai",
                "probes": 0,
                "uptime": None,
                "outage_count": 0,
                "mttr_s": None,
                "longest_continuous_availability_s": 0.0,
            }
        ],
        "rate_limits": [
            {
                "provider": "openai",
                "concurrency": 1,
                "success_rate": None,
                "measured_rpm": None,
                "measured_input_tpm": None,
                "measured_output_tpm": None,
            }
        ],
        "costs": [],
        "external_benchmark_comparison": [],
    }

    result = markdown(report)
    assert "| openai | 8192 | 512 | 0 | — | —/—/— | —/—/— | — | — | — | — | — |" in result
    assert "| openai | 0 | — | 0 | — | 0.00 |" in result
    assert "| openai | 1 | — | — | — | — |" in result

def test_export_campaign_summary_returns_report_and_markdown(tmp_path: Path) -> None:
    from analysis import export_campaign_summary

    store = CampaignStore(tmp_path / "summary.sqlite3")
    store.bind_campaign("exp-test", {"providers": [], "workload": {}, "availability": {}, "rate_limit": {}, "agent_cost": {}})
    store.close()

    exported = export_campaign_summary(tmp_path / "summary.sqlite3", campaign_id="exp-test")
    assert "report" in exported
    assert "markdown" in exported
    assert exported["official_complete"] is False