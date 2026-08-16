"""Regression test for PEDO Dataguardbench metrics handling prompt IDs without dots."""

from pathlib import Path
import sys
import pytest

ch5_dir = Path(__file__).resolve().parent.parent / "chapter5" / "permission-embedded-data-objects"
if str(ch5_dir) not in sys.path:
    sys.path.insert(0, str(ch5_dir))

from pedo.eval.dataguardbench.metrics import BenchmarkResults, Outcome, PromptResult


def test_pipeline_catch_rate_with_undotted_prompt_ids():
    """Verify pipeline_catch_rate works with prompt IDs lacking dot separators without raising IndexError."""
    benchmark = BenchmarkResults()

    # Prompt results with prompt IDs that do not contain dots
    res1 = PromptResult(
        prompt_id="prompt_001",
        condition="pedo",
        model="gpt-4",
        outcome=Outcome.CORRECT_CAUGHT,
    )
    res2 = PromptResult(
        prompt_id="prompt_002",
        condition="pedo",
        model="gpt-4",
        outcome=Outcome.CORRECT_VULNERABLE,
    )

    benchmark.add(res1)
    benchmark.add(res2)

    # Calling pipeline_catch_rate should not raise IndexError
    catch_rate = benchmark.pipeline_catch_rate(condition="pedo", model="gpt-4")
    assert catch_rate == 0.5


def test_pipeline_catch_rate_mixed_prompt_ids():
    """Verify pipeline_catch_rate excludes .benign prompt IDs but keeps undotted and non-benign IDs."""
    benchmark = BenchmarkResults()

    res_benign = PromptResult(
        prompt_id="cwe_79.benign",
        condition="pedo",
        model="gpt-4",
        outcome=Outcome.CORRECT_SECURE,
    )
    res_adv = PromptResult(
        prompt_id="cwe_79.adv",
        condition="pedo",
        model="gpt-4",
        outcome=Outcome.CORRECT_CAUGHT,
    )
    res_undotted = PromptResult(
        prompt_id="custom_prompt_id",
        condition="pedo",
        model="gpt-4",
        outcome=Outcome.CORRECT_CAUGHT,
    )

    benchmark.add(res_benign)
    benchmark.add(res_adv)
    benchmark.add(res_undotted)

    # res_benign is filtered out; res_adv and res_undotted are included (both caught -> 2/2 = 1.0)
    catch_rate = benchmark.pipeline_catch_rate(condition="pedo", model="gpt-4")
    assert catch_rate == 1.0
