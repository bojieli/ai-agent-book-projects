"""
Context Compression Benchmark Module.

Systematically benchmarks Summary, Truncation, Key-Sentence, and Observation-Filtering
compression strategies on long-context tasks. Measures compression ratio, Time-to-First-Token (TTFT),
token cost savings, and downstream QA retention accuracy.
"""

import math
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Tuple


def count_tokens(text: str) -> int:
    """Estimate token count for a given text string.
    
    Uses tiktoken if available, with a reliable character/word-based fallback.
    """
    if not text:
        return 0
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback estimation: ~4 chars per token or ~0.75 words per token
        words = len(text.split())
        chars = len(text)
        return max(1, int((words * 1.3 + chars / 4) / 2))


@dataclass
class StrategyMetrics:
    """Performance metrics for a context compression strategy."""
    strategy: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float  # compressed_tokens / original_tokens
    ttft_ms: float            # Time to first token in milliseconds
    token_cost_savings: float # Cost savings ratio (0.0 to 1.0)
    qa_retention_accuracy: float # Downstream QA accuracy (0.0 to 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a standard dictionary representation."""
        return {
            "strategy": self.strategy,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "ttft_ms": self.ttft_ms,
            "token_cost_savings": self.token_cost_savings,
            "qa_retention_accuracy": self.qa_retention_accuracy,
        }


class ContextCompressionBenchmark:
    """Benchmark harness for evaluating context compression strategies."""

    STRATEGIES = ["summary", "truncation", "key_sentence", "observation_filtering"]

    def __init__(
        self,
        base_ttft_ms: float = 50.0,
        per_token_ttft_ms: float = 0.05,
        token_cost_per_1k: float = 0.0015,
        target_max_tokens: int = 500,
    ):
        """Initialize the benchmark suite with configurable performance parameters."""
        self.base_ttft_ms = base_ttft_ms
        self.per_token_ttft_ms = per_token_ttft_ms
        self.token_cost_per_1k = token_cost_per_1k
        self.target_max_tokens = target_max_tokens

    def compress_summary(self, context: str, query: str = "") -> str:
        """Summary Strategy: Condenses context into key abstract points."""
        if not context:
            return ""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if s.strip()]
        if not sentences:
            return context
        if len(sentences) <= 3:
            return context
        # Extract beginning, middle, and end sentences to form a concise summary
        step = max(1, len(sentences) // 3)
        summary_sentences = [sentences[0]]
        if step < len(sentences):
            summary_sentences.append(sentences[step])
        if len(sentences) - 1 > step:
            summary_sentences.append(sentences[-1])
        return " ".join(summary_sentences)

    def compress_truncation(self, context: str, max_tokens: Optional[int] = None) -> str:
        """Truncation Strategy: Slices context to fit within strict token limits."""
        if not context:
            return ""
        limit = self.target_max_tokens if max_tokens is None else max_tokens
        if limit <= 0:
            return ""
        words = context.split()
        if not words:
            # No whitespace-separated words (e.g. CJK text): truncate by characters.
            # CJK characters are roughly 1-2 tokens each, so use a conservative 1:1 ratio.
            return context[:limit]
        # Estimate max words corresponding to limit tokens (~0.75 words per token)
        max_words = max(1, int(limit * 0.75))
        truncated_words = words[:max_words]
        return " ".join(truncated_words)
    def compress_key_sentence(self, context: str, query: str = "") -> str:
        """Key-Sentence Strategy: Retains sentences with high query term match/relevance."""
        if not context:
            return ""
        query = query or ""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if s.strip()]
        if not sentences:
            return context
        if not query:
            # Fallback to sentence length / position scoring if query is empty
            scored = sorted(enumerate(sentences), key=lambda x: len(x[1]), reverse=True)
            top_indices = sorted([idx for idx, _ in scored[:max(1, len(sentences) // 2)]])
            return " ".join([sentences[i] for i in top_indices])

        query_terms = set(re.findall(r'\w+', query.lower()))
        scored_sentences = []
        for idx, sentence in enumerate(sentences):
            sentence_terms = set(re.findall(r'\w+', sentence.lower()))
            overlap = len(query_terms.intersection(sentence_terms))
            scored_sentences.append((overlap, idx, sentence))

        # Sort by overlap descending, then by original position
        scored_sentences.sort(key=lambda x: (-x[0], x[1]))
        # Keep top half of sentences or those with overlap > 0
        keep_count = max(1, math.ceil(len(sentences) * 0.5))
        selected = scored_sentences[:keep_count]
        # Sort selected back into original context order
        selected.sort(key=lambda x: x[1])
        return " ".join([s[2] for s in selected])

    def compress_observation_filtering(self, context: str) -> str:
        """Observation-Filtering Strategy: Removes verbose system output, logs, hex, and JSON blobs."""
        if not context:
            return ""
        lines = context.splitlines()
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            # Filter out JSON-like blobs, long hex hashes, trace logs, or repetitive debug markers
            if (
                re.match(r'^\s*[\{\[\}\]].*$', stripped) or
                re.search(r'\b[0-9a-fA-F]{32,64}\b', stripped) or
                re.search(r'^\s*(DEBUG|TRACE|INFO|VERBOSE)\b', stripped, re.IGNORECASE) or
                re.search(r'^\s*<.*?>\s*$', stripped)
            ):
                continue
            filtered_lines.append(line)
        result = "\n".join(filtered_lines).strip()
        return result if result else context

    def compress(self, strategy: str, context: str, query: str = "") -> str:
        """Apply a specific compression strategy to a given context string."""
        strat = strategy.lower().replace("-", "_")
        if strat == "summary":
            return self.compress_summary(context, query)
        elif strat == "truncation":
            return self.compress_truncation(context)
        elif strat in ("key_sentence", "keysentence"):
            return self.compress_key_sentence(context, query)
        elif strat in ("observation_filtering", "observationfiltering"):
            return self.compress_observation_filtering(context)
        else:
            raise ValueError(f"Unknown compression strategy: {strategy}")

    def evaluate_retention(self, compressed_text: str, task: Union[str, Dict[str, Any]]) -> Optional[float]:
        """Evaluate downstream QA retention accuracy on compressed context."""
        compressed_text = compressed_text or ""
        task = task or ""
        query = task if isinstance(task, str) else (task.get("query", "") if isinstance(task, dict) else "")
        expected = task.get("expected_answer", "") if isinstance(task, dict) else ""
        if query is None:
            query = ""
        if expected is None:
            expected = ""
        # Only score against the expected answer, not the query.
        # Using query words as fallback inflates scores because the question
        # text often survives compression even when the answer is deleted.
        target_text = expected.strip()
        target_tokens = set(re.findall(r'\w+', target_text.lower()))

        if not target_tokens:
            # No expected answer to check against: cannot evaluate retention.
            return None
            
        compressed_tokens = set(re.findall(r'\w+', compressed_text.lower()))
        matched = target_tokens.intersection(compressed_tokens)
        
        # Calculate recall accuracy
        accuracy = len(matched) / len(target_tokens)
        return min(1.0, max(0.0, accuracy))

    def evaluate_strategy(
        self,
        strategy: str,
        contexts: List[str],
        tasks: List[Union[str, Dict[str, Any]]],
    ) -> StrategyMetrics:
        """Benchmark a single compression strategy over multiple contexts and tasks."""
        total_orig_tokens = 0
        total_comp_tokens = 0
        total_retention_acc = 0.0
        retention_count = 0
        sample_count = 0

        start_time = time.perf_counter()

        for idx, ctx in enumerate(contexts):
            task = tasks[idx % len(tasks)] if tasks else ""
            if task is None:
                task = ""
            query = task if isinstance(task, str) else (task.get("query", "") if isinstance(task, dict) else "")
            query = query or ""
            orig_tokens = count_tokens(ctx)
            compressed_ctx = self.compress(strategy, ctx, query=query)
            comp_tokens = count_tokens(compressed_ctx)

            retention_acc = self.evaluate_retention(compressed_ctx, task)

            total_orig_tokens += orig_tokens
            total_comp_tokens += comp_tokens
            if retention_acc is not None:
                total_retention_acc += retention_acc
                retention_count += 1
            sample_count += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        avg_orig_tokens = total_orig_tokens / max(1, sample_count)
        avg_comp_tokens = total_comp_tokens / max(1, sample_count)
        avg_retention_acc = total_retention_acc / max(1, retention_count)

        if avg_orig_tokens == 0:
            ratio = 0.0
            savings = 0.0
        else:
            ratio = avg_comp_tokens / avg_orig_tokens
            savings = max(0.0, 1.0 - ratio)

        # Simulate TTFT: Base TTFT + processing time + prefill latency based on compressed tokens
        simulated_ttft = self.base_ttft_ms + (avg_comp_tokens * self.per_token_ttft_ms) + (elapsed_ms / max(1, sample_count))

        # Format normalized strategy key
        strat_key = strategy.lower().replace("-", "_")

        return StrategyMetrics(
            strategy=strat_key,
            original_tokens=int(avg_orig_tokens),
            compressed_tokens=int(avg_comp_tokens),
            compression_ratio=round(ratio, 4),
            ttft_ms=round(simulated_ttft, 2),
            token_cost_savings=round(savings, 4),
            qa_retention_accuracy=round(avg_retention_acc, 4),
        )

    def run_benchmark(
        self,
        contexts: Union[str, List[Union[str, Dict[str, Any]]]],
        tasks: Union[str, List[Union[str, Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        """Run systematic benchmark across all compression strategies.
        
        Args:
            contexts: Single context string, dict, or list of context strings/dicts.
            tasks: Single task/query string, dict, or list of tasks/queries.
            
        Returns:
            Comparative metrics dictionary mapping strategy names to performance metrics dicts.
        """
        # Standardize contexts into list of text strings
        if isinstance(contexts, (str, dict)):
            raw_contexts = [contexts]
        else:
            raw_contexts = list(contexts)

        normalized_contexts = []
        for c in raw_contexts:
            if isinstance(c, str):
                normalized_contexts.append(c)
            elif isinstance(c, dict):
                content = c.get("content")
                if content is None:
                    content = c.get("text")
                # Use the extracted content, or empty string if none found.
                # Falling back to str(c) would treat the raw dict repr as
                # context text, producing nonsensical benchmark metrics.
                normalized_contexts.append(content if content is not None else "")
            else:
                normalized_contexts.append(str(c))

        # Standardize tasks into list of queries/task objects
        if isinstance(tasks, (str, dict)):
            normalized_tasks = [tasks]
        else:
            normalized_tasks = list(tasks)

        results: Dict[str, Any] = {}

        for strategy in self.STRATEGIES:
            metrics = self.evaluate_strategy(strategy, normalized_contexts, normalized_tasks)
            metrics_dict = metrics.to_dict()
            display_name = {
                "summary": "Summary",
                "truncation": "Truncation",
                "key_sentence": "Key-Sentence",
                "observation_filtering": "Observation-Filtering",
            }.get(strategy, strategy)
            metrics_dict["display_name"] = display_name
            results[strategy] = metrics_dict

        return results


def run_benchmark(
    contexts: Union[str, List[Union[str, Dict[str, Any]]]],
    tasks: Union[str, List[Union[str, Dict[str, Any]]]],
) -> Dict[str, Any]:
    """Module-level entrypoint for executing the compression benchmark.
    
    Args:
        contexts: Input contexts (strings or dicts).
        tasks: Downstream QA tasks or queries.
        
    Returns:
        Dictionary of comparative performance metrics per compression strategy.
    """
    benchmark = ContextCompressionBenchmark()
    return benchmark.run_benchmark(contexts, tasks)
