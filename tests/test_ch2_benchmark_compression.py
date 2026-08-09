import sys
from pathlib import Path

# Add module directory to path for imports
ch2_dir = Path(__file__).resolve().parent.parent / "chapter2" / "context-compression"
if str(ch2_dir) not in sys.path:
    sys.path.insert(0, str(ch2_dir))

from benchmark_compression import (
    ContextCompressionBenchmark,
    StrategyMetrics,
    count_tokens,
    run_benchmark,
)


def test_count_tokens_valid_text():
    text = "The quick brown fox jumps over the lazy dog."
    tokens = count_tokens(text)
    assert isinstance(tokens, int)
    assert tokens > 0
    assert count_tokens("") == 0
    assert count_tokens(None) == 0


def test_strategy_metrics_to_dict():
    metrics = StrategyMetrics(
        strategy="summary",
        original_tokens=100,
        compressed_tokens=40,
        compression_ratio=0.4,
        ttft_ms=52.0,
        token_cost_savings=0.6,
        qa_retention_accuracy=0.85,
    )
    d = metrics.to_dict()
    assert d["strategy"] == "summary"
    assert d["original_tokens"] == 100
    assert d["compressed_tokens"] == 40
    assert d["compression_ratio"] == 0.4
    assert d["ttft_ms"] == 52.0
    assert d["token_cost_savings"] == 0.6
    assert d["qa_retention_accuracy"] == 0.85


def test_compress_summary():
    benchmark = ContextCompressionBenchmark()
    long_text = (
        "First sentence sets the primary context for the system. "
        "Second sentence adds secondary details that might not be as critical. "
        "Third sentence contains deep domain explanations. "
        "Fourth sentence provides concluding summary notes."
    )
    compressed = benchmark.compress_summary(long_text)
    assert isinstance(compressed, str)
    assert len(compressed) <= len(long_text)


def test_compress_truncation():
    benchmark = ContextCompressionBenchmark(target_max_tokens=10)
    long_text = "Word " * 100
    compressed = benchmark.compress_truncation(long_text, max_tokens=10)
    words = compressed.split()
    assert len(words) <= 10


def test_compress_key_sentence():
    benchmark = ContextCompressionBenchmark()
    context = (
        "Python is a high level programming language. "
        "Artificial Intelligence uses python heavily for deep learning. "
        "Baking bread requires flour and yeast. "
        "Gardening is a relaxing hobby."
    )
    query = "python artificial intelligence programming"
    compressed = benchmark.compress_key_sentence(context, query)
    assert "Python" in compressed or "programming" in compressed


def test_compress_observation_filtering():
    benchmark = ContextCompressionBenchmark()
    context = (
        "User asked for system status.\n"
        "DEBUG: 2026-08-09 10:00:00 - payload hash 9f8e7d0a1b2c3d4e5f6a7b8c9d0e1f2a\n"
        '{"status": "ok", "code": 200, "meta": {"debug_trace": [1, 2, 3]}}\n'
        "System operational efficiency is at 99.5%.\n"
        "TRACE [0x7fff]: hex signature 0x1234567890abcdef1234567890abcdef\n"
        "All services healthy."
    )
    compressed = benchmark.compress_observation_filtering(context)
    assert "DEBUG:" not in compressed
    assert "System operational efficiency" in compressed
    assert "All services healthy." in compressed


def test_run_benchmark_entrypoint():
    contexts = [
        "The server failed due to memory exhaustion at midnight. DEBUG: trace log 0x1234. Fix applied.",
        "Quantum computing relies on qubits and superposition. TRACE: log output. Qubits enable parallel state evaluation.",
    ]
    tasks = [
        {"query": "Why did server fail?", "expected_answer": "memory exhaustion"},
        {"query": "What do qubits enable?", "expected_answer": "parallel state evaluation"},
    ]

    metrics_dict = run_benchmark(contexts, tasks)
    assert isinstance(metrics_dict, dict)

    for strat in ["summary", "truncation", "key_sentence", "observation_filtering"]:
        assert strat in metrics_dict
        m = metrics_dict[strat]
        assert "original_tokens" in m
        assert "compressed_tokens" in m
        assert "compression_ratio" in m
        assert "ttft_ms" in m
        assert "token_cost_savings" in m
        assert "qa_retention_accuracy" in m
        assert 0.0 <= m["compression_ratio"] <= 1.5
        assert m["ttft_ms"] > 0
        assert 0.0 <= m["qa_retention_accuracy"] <= 1.0

    # Check display names inside metrics payloads
    assert metrics_dict["summary"]["display_name"] == "Summary"
    assert metrics_dict["truncation"]["display_name"] == "Truncation"
    assert metrics_dict["key_sentence"]["display_name"] == "Key-Sentence"
    assert metrics_dict["observation_filtering"]["display_name"] == "Observation-Filtering"


def test_run_benchmark_single_context_and_task():
    result = run_benchmark("Single context string for testing benchmark.", "Single task query.")
    assert "summary" in result
    assert result["summary"]["original_tokens"] > 0
def test_edge_cases():
    benchmark = ContextCompressionBenchmark()
    assert benchmark.compress_summary("") == ""
    assert benchmark.compress_summary(None) == ""
    assert benchmark.compress_truncation("Hello world", max_tokens=0) == ""
    assert benchmark.compress_truncation(None) == ""
    assert benchmark.compress_key_sentence(None) == ""
    assert benchmark.compress_observation_filtering(None) == ""
    assert benchmark.evaluate_retention("", None) == 0.0


def test_dict_empty_content_and_none_task():
    result = run_benchmark([{"content": ""}], [None])
    assert "summary" in result
    assert result["summary"]["display_name"] == "Summary"
