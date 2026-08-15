"""Offline tests for the experiment harness; live API evidence is stored separately."""

import json
from pathlib import Path

from experiment import (
    AgentResult,
    CardBuilder,
    ChatTurn,
    Chunk,
    MemoryAgent,
    LLMReranker,
    NoReranker,
    ToolCall,
    TokenPricing,
    Usage,
    VectorMemoryIndex,
    aggregate,
    completion_assessment,
    conversation_chunks,
    interaction_analysis,
    pricing_coverage,
    retrieval_metrics,
    select_core_cards,
)


class FakeEmbedder:
    def __init__(self):
        self.last_usage = Usage()
        self.last_latency_ms = 0.1

    def embed(self, texts):
        self.last_usage = Usage(input_tokens=len(texts), cost_usd=0.001 * len(texts))
        vectors = []
        for text in texts:
            lower = text.lower()
            vectors.append([float("checking" in lower), float("medical" in lower), 1.0])
        return vectors


class FakeToolChat:
    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools=None, tool_choice=None):
        self.calls += 1
        if self.calls == 1:
            return ChatTurn(
                "",
                [ToolCall("call-1", "search_memory", {"query": "checking account"})],
                Usage(input_tokens=10, output_tokens=2, cost_usd=0.01),
                4.0,
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": "search_memory", "arguments": '{"query":"checking account"}'}}],
                },
            )
        return ChatTurn(
            "The checking account is 4429853327.", [], Usage(input_tokens=20, output_tokens=8, cost_usd=0.02), 5.0,
            {"role": "assistant", "content": "The checking account is 4429853327."},
        )


class FakeMultiSearchChat(FakeToolChat):
    def complete(self, messages, tools=None, tool_choice=None):
        self.calls += 1
        if self.calls <= 2:
            call_id = f"call-{self.calls}"
            query = "checking account" if self.calls == 1 else "routing number"
            return ChatTurn(
                "",
                [ToolCall(call_id, "search_memory", {"query": query})],
                Usage(input_tokens=5, output_tokens=2),
                1.0,
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {"name": "search_memory", "arguments": json.dumps({"query": query})},
                    }],
                },
            )
        return ChatTurn("complete", [], Usage(input_tokens=5, output_tokens=1), 1.0,
                        {"role": "assistant", "content": "complete"})


def load_case(test_id="layer1_01_bank_account"):
    import sys

    eval_dir = Path(__file__).resolve().parents[2] / "chapter3" / "user-memory-evaluation"
    if str(eval_dir) not in sys.path:
        sys.path.insert(0, str(eval_dir))
    from framework import UserMemoryEvaluationFramework

    return UserMemoryEvaluationFramework(str(eval_dir / "test_cases")).get_test_case(test_id)


def test_chunking_is_stable_and_preserves_source():
    case = load_case()
    first = conversation_chunks(case, rounds_per_chunk=8, overlap=2)
    second = conversation_chunks(case, rounds_per_chunk=8, overlap=2)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert len(first) > 1
    assert all(c.conversation_id == "bank_setup_001" for c in first)
    assert "4429853327" in "\n".join(c.text for c in first)


def test_rag_agent_executes_real_tool_loop_shape_and_tracks_metrics():
    chunks = [
        Chunk("a", "c1", "checking account 4429853327", 1, 1),
        Chunk("b", "c1", "medical appointment", 2, 2),
    ]
    index = VectorMemoryIndex(chunks, FakeEmbedder())
    result = MemoryAgent(FakeToolChat()).rag("What is my checking account?", index, NoReranker())
    assert result.answer.endswith("4429853327.")
    assert result.steps == 2
    assert result.tool_calls == 1
    assert result.retrieved_chunks[0].chunk_id == "a"
    assert result.latency_ms > 9
    assert result.usage.cost_usd >= 0.031


def test_611_agent_can_make_followup_searches_and_exposes_tool_efficiency():
    chunks = [Chunk("a", "c", "checking account routing number", 1, 1)]
    index = VectorMemoryIndex(chunks, FakeEmbedder())
    result = MemoryAgent(FakeMultiSearchChat()).rag(
        "account?", index, NoReranker(), allow_followup_searches=True, max_search_rounds=3
    )
    assert result.answer == "complete"
    assert result.steps == 3
    assert result.tool_calls == 2
    assert [event["event"] for event in result.trace] == ["search_memory", "search_memory", "answer"]


def test_retrieval_metrics_use_source_selected_gold():
    retrieved = [Chunk("wrong", "c", "", 1, 1), Chunk("gold", "c", "", 2, 2)]
    hit, recall, mrr = retrieval_metrics(retrieved, ["gold", "also-gold"])
    assert hit == 1.0
    assert recall == 0.5
    assert mrr == 0.5


def test_hybrid_resident_context_contains_only_explicit_core_cards():
    cards = [
        {"card_key": "identity", "memory_tier": "core"},
        {"card_key": "old_call_detail", "memory_tier": "supporting"},
    ]
    assert [card["card_key"] for card in select_core_cards(cards, "t")] == ["identity"]


def test_hybrid_requires_at_least_one_core_card():
    import pytest

    with pytest.raises(RuntimeError, match="no core-tier cards"):
        select_core_cards([{"memory_tier": "supporting"}], "case-x")


class FakeCardChat:
    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools=None, tool_choice=None, json_object=False):
        self.calls += 1
        if self.calls == 1:
            content = '{"cards": [{"category": "identity"}]}'
        elif self.calls == 2:
            content = "{malformed"
        else:
            content = json.dumps({
                "cards": [{
                    "category": "identity",
                    "card_key": "user",
                    "backstory": "account setup",
                    "date_created": "2025-01-01",
                    "person": "user",
                    "relationship": "self",
                    "facts": {"name": "Alex"},
                    "source_conversation_ids": ["c1"],
                    "status": "current",
                    "memory_tier": "core",
                }]
            })
        return ChatTurn(
            content, [], Usage(input_tokens=10, output_tokens=5), 2.0,
            {"role": "assistant", "content": content},
        )


def test_card_builder_retries_parse_and_schema_failures_without_weakening_schema():
    chat = FakeCardChat()
    cards, usage, latency = CardBuilder(chat).build(load_case())
    assert chat.calls == 3
    assert cards[0]["memory_tier"] == "core"
    assert cards[0]["source_conversation_ids"] == ["c1"]
    assert usage.input_tokens == 30
    assert usage.output_tokens == 15
    assert latency == 6.0


class FakeRerankerChat:
    def __init__(self):
        self.messages = []
        self.calls = 0

    def complete(self, messages, tools=None, tool_choice=None, json_object=False):
        self.calls += 1
        self.messages.append(messages)
        content = '{"ranking": []}' if self.calls == 1 else '{"ranking": [{"index": 1, "score": 0.9}]}'
        return ChatTurn(
            content, [], Usage(input_tokens=4, output_tokens=2), 1.5,
            {"role": "assistant", "content": content},
        )


def test_llm_reranker_retry_corrects_an_empty_semantic_response():
    chat = FakeRerankerChat()
    reranker = LLMReranker("semantic", chat)
    documents = [Chunk("a", "c", "first", 1, 1), Chunk("b", "c", "second", 2, 2)]
    ranked = reranker.rerank("second", documents, 1)
    assert [row[0].chunk_id for row in ranked] == ["b"]
    assert chat.calls == 2
    assert "previous response was invalid" in chat.messages[1][-1]["content"]
    assert reranker.last_usage.input_tokens == 8
    assert reranker.last_latency_ms == 3.0


def record(**overrides):
    from experiment import RunRecord

    data = dict(
        experiment="6-11", test_id="t", layer="layer1", system="rag", embedding="e1",
        reranker="none", main_model="m1", success=True, reward=0.8, steps=2,
        tool_calls=1, latency_ms=100, cost_usd=0.01, input_tokens=10, output_tokens=2,
        unpriced_tokens=0, retrieval_hit_at_5=1.0, retrieval_recall_at_5=0.5,
        retrieval_mrr=1.0, fixed_query_hit_at_5=1.0, fixed_query_recall_at_5=0.5,
        fixed_query_mrr=1.0,
    )
    data.update(overrides)
    return RunRecord(**data)


def test_aggregation_and_interaction_report_conditional_reranker_value():
    rows = [
        record(test_id="a"),
        record(test_id="b", success=False, reward=0.3),
        record(test_id="a", reranker="bge", success=True, reward=1.0, retrieval_recall_at_5=1.0, fixed_query_recall_at_5=1.0, latency_ms=130),
        record(test_id="b", reranker="bge", success=True, reward=0.9, retrieval_recall_at_5=1.0, fixed_query_recall_at_5=1.0, latency_ms=130),
    ]
    summary = aggregate(rows, ["reranker"])
    assert {row["reranker"] for row in summary} == {"none", "bge"}
    analysis = interaction_analysis(rows)
    assert analysis["analysis_scope"]["selection_conclusions_allowed"] is False
    assert analysis["analysis_scope"]["scope_status"] == "partial_descriptive_only"
    delta = analysis["reranker_value_by_embedding_and_main_model"][0]
    assert delta["success_rate_delta"] == 0.5
    assert delta["fixed_query_recall_at_5_delta"] == 0.5
    assert delta["latency_ms_delta"] == 30


def test_native_currency_pricing_tracks_cached_and_uncached_without_fx():
    pricing = TokenPricing.from_dict({
        "currency": "CNY",
        "as_of_date": "2026-07-29",
        "source_url": "https://provider.example/pricing",
        "input_per_million": 4.0,
        "cached_input_per_million": 0.7,
        "output_per_million": 21.0,
    })
    usage = pricing.price(1_000_000, 1_000_000, cached_input_tokens=250_000)
    assert usage.cost_by_currency == {"CNY": 24.175}
    assert usage.cost_usd == 0
    assert usage.cached_input_tokens == 250_000
    assert usage.unpriced_tokens == 0


def test_pricing_requires_dated_source_and_three_letter_currency():
    import pytest

    base = {
        "currency": "USD",
        "as_of_date": "2026-07-29",
        "source_url": "https://provider.example/pricing",
        "input_per_million": 1.0,
    }
    for override in (
        {"currency": "dollars"},
        {"as_of_date": "today"},
        {"source_url": "provider.example/pricing"},
    ):
        with pytest.raises(ValueError):
            TokenPricing.from_dict(base | override)


def exact_611_config(readiness=True):
    return {
        "experiment_6_11": {
            "embeddings": ["e1", "e2", "e3", "e4"],
            "rerankers": ["none", "r1", "r2"],
            "main_models": ["m1", "m2"],
        },
        "execution_readiness": {"all_required_backends_ready": readiness},
    }


def exact_611_records():
    return [
        record(
            test_id=f"case-{case:02d}",
            embedding=embedding,
            reranker=reranker,
            main_model=model,
            cost_usd=0,
            cost_by_currency={"USD": 0.001},
        )
        for case in range(60)
        for embedding in ("e1", "e2", "e3", "e4")
        for reranker in ("none", "r1", "r2")
        for model in ("m1", "m2")
    ]


def assess_611(rows, readiness=True):
    return completion_assessment(
        "6-11", rows, exact_611_config(readiness), pricing_coverage(rows)
    )


def test_exact_611_gate_requires_all_1440_real_priced_successes_and_readiness():
    rows = exact_611_records()
    complete = assess_611(rows)
    assert complete["evidence_complete"] is True
    assert complete["expected_full_trajectory_count"] == 1440
    assert interaction_analysis(rows, complete)["analysis_scope"]["selection_conclusions_allowed"] is True

    assert assess_611(rows[:-1])["evidence_complete"] is False

    failed = list(rows)
    failed[0] = record(**({
        **vars(rows[0]), "status": "error", "success": False, "error": "provider failed",
    }))
    assert assess_611(failed)["evidence_complete"] is False

    unpriced = list(rows)
    unpriced[0] = record(**({**vars(rows[0]), "unpriced_tokens": 1}))
    assert assess_611(unpriced)["cost_accounting_complete"] is False

    non_api = list(rows)
    non_api[0] = record(**({**vars(rows[0]), "evidence_mode": "mock"}))
    assert assess_611(non_api)["real_api_evidence_only"] is False
    assert assess_611(rows, readiness=False)["backend_readiness_complete"] is False


def test_pricing_coverage_recovers_schema1_fixed_query_usd():
    row = record(
        cost_usd=0.01,
        fixed_query_retrieval_cost_usd=0.002,
        fixed_query_retrieval_cost_by_currency={},
        fixed_query_unpriced_tokens=3,
    )
    coverage = pricing_coverage([row])
    assert coverage["total_cost_by_currency"] == {"USD": 0.012}
    assert coverage["observed_token_count"] == 15
    assert coverage["legacy_fixed_query_unpriced_token_lower_bound"] == 3
