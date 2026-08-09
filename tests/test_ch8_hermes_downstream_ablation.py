"""Unit tests for chapter8/hermes-self-evolution/run_downstream_ablation.py."""

from pathlib import Path
import sys
import time
import pytest

# Ensure chapter8/hermes-self-evolution is in sys.path
ch8_dir = Path(__file__).resolve().parent.parent / "chapter8" / "hermes-self-evolution"
if str(ch8_dir) not in sys.path:
    sys.path.insert(0, str(ch8_dir))

from run_downstream_ablation import (
    AblationReport,
    AblationTask,
    DownstreamAblationEngine,
    TaskResult,
    run_ablation_campaign,
)


def test_ablation_engine_initialization():
    """Test initializing DownstreamAblationEngine and code quality scoring."""
    engine = DownstreamAblationEngine()

    # Valid Python code quality check
    code_sample = '''"""Sample module."""
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
    score = engine.evaluate_code_quality(code_sample)
    assert 0.0 <= score <= 100.0
    assert score > 70.0  # High score due to docstrings and type hints

    # Invalid code / empty text check
    empty_score = engine.evaluate_code_quality("")
    assert empty_score == 0.0


def test_run_ablation_campaign_defaults():
    """Test running ablation campaign with default sample agents and task suite."""
    report = run_ablation_campaign()

    assert isinstance(report, AblationReport)
    assert report.total_tasks == 5
    assert 0.0 <= report.baseline_pass_rate <= 1.0
    assert 0.0 <= report.evolved_pass_rate <= 1.0
    assert report.evolved_pass_rate >= report.baseline_pass_rate
    assert report.pass_rate_uplift == round(report.evolved_pass_rate - report.baseline_pass_rate, 4)

    # Check metrics fields
    assert "z_score" in report.statistical_metrics
    assert "p_value" in report.statistical_metrics
    assert "confidence_interval_95" in report.statistical_metrics

    # Dictionary indexing test
    assert report["total_tasks"] == 5
    assert report["pass_rate_uplift"] == report.pass_rate_uplift


def test_run_ablation_campaign_custom_agents_and_tasks():
    """Test running ablation campaign with custom baseline/evolved agents and task list."""

    def baseline_agent(inp):
        return inp.get("val", 0) + 1  # Buggy logic: adds 1 instead of multiplying

    def evolved_agent(inp):
        return inp.get("val", 0) * 2  # Correct logic: multiplies by 2

    custom_tasks = [
        AblationTask(
            task_id="t1",
            name="Double Number Task 1",
            description="Double 5",
            category="synthetic",
            input_data={"val": 5},
            expected_output=10,
        ),
        AblationTask(
            task_id="t2",
            name="Double Number Task 2",
            description="Double 10",
            category="synthetic",
            input_data={"val": 10},
            expected_output=20,
        ),
    ]

    report = run_ablation_campaign(
        baseline_agent=baseline_agent,
        evolved_agent=evolved_agent,
        tasks=custom_tasks,
    )

    assert report.total_tasks == 2
    assert report.baseline_pass_rate == 0.0
    assert report.evolved_pass_rate == 1.0
    assert report.pass_rate_uplift == 1.0
    assert report.regression_count == 0
    assert report.regression_rate == 0.0


def test_ablation_engine_regression_detection():
    """Test identifying regression tasks (passed by baseline, failed by evolved)."""
    engine = DownstreamAblationEngine()

    def baseline_agent(inp):
        return inp  # Correct for baseline

    def evolved_agent(inp):
        return "wrong"  # Regressed in evolved version

    task = AblationTask(
        task_id="reg_01",
        name="Regression Test Task",
        description="Verify regression detection",
        category="real",
        input_data="hello",
        expected_output="hello",
    )

    report = engine.run_ablation_campaign(
        baseline_agent=baseline_agent,
        evolved_agent=evolved_agent,
        tasks=[task],
    )

    assert report.total_tasks == 1
    assert report.baseline_pass_rate == 1.0
    assert report.evolved_pass_rate == 0.0
    assert report.regression_count == 1
    assert report.regression_rate == 1.0


def test_ablation_latency_and_quality_metrics():
    """Test measuring latency change percentage and code quality delta."""
    engine = DownstreamAblationEngine()

    def slow_baseline(inp):
        time.sleep(0.01)
        return "print('hello')"

    def fast_evolved(inp):
        time.sleep(0.001)
        return (
            '"""Module doc."""\n'
            'def greet(x: int) -> str:\n'
            '    """Greet user."""\n'
            '    return f"hello {x}"\n'
        )

    tasks = [
        AblationTask(
            task_id="lat_01",
            name="Latency and Quality Task",
            description="Measure timing and AST quality",
            category="optimization",
            input_data=None,
            expected_output=None,
            verifier=lambda output, exp: True,
        )
    ]

    b_score = engine.evaluate_code_quality(slow_baseline(None))
    e_score = engine.evaluate_code_quality(fast_evolved(None))
    assert e_score > b_score

    report = engine.run_ablation_campaign(
        baseline_agent=slow_baseline,
        evolved_agent=fast_evolved,
        tasks=tasks,
    )

    assert report.baseline_avg_latency_sec > report.evolved_avg_latency_sec
    assert report.latency_change_pct < 0.0  # Latency reduced
    assert report.evolved_avg_code_quality > report.baseline_avg_code_quality
    assert report.code_quality_score_change > 0.0


def test_custom_quality_evaluator_clamping():
    """Regression test: custom quality scorer returns are clamped between 0.0 and 100.0."""
    engine_high = DownstreamAblationEngine(quality_evaluator=lambda code: 150.0)
    engine_low = DownstreamAblationEngine(quality_evaluator=lambda code: -50.0)
    assert engine_high.evaluate_code_quality("code") == 100.0
    assert engine_low.evaluate_code_quality("code") == 0.0


def test_async_function_quality_scoring():
    """Regression test: async functions are recognized for docstrings and type annotations."""
    engine = DownstreamAblationEngine()
    async_code = '''"""Async module."""
async def fetch(url: str) -> str:
    """Fetch data from URL."""
    return "data"
'''
    score = engine.evaluate_code_quality(async_code)
    assert score > 70.0

    async_kwonly_code = '''"""Async kwonly module."""
async def fetch_kw(*, url: str):
    return "data"
'''
    kw_score = engine.evaluate_code_quality(async_kwonly_code)
    assert kw_score >= 85.0

def test_invalid_task_item_validation():
    """Regression test: invalid task item raises ValueError."""
    engine = DownstreamAblationEngine()
    with pytest.raises(ValueError, match="Task item must be an AblationTask instance or dict"):
        engine.run_ablation_campaign(tasks=["invalid_string_task"])

def test_agent_execution_error_sets_quality_score_zero():
    """Regression test: set quality_score = 0.0 when agent execution raises error or returns None."""
    engine = DownstreamAblationEngine()

    def failing_agent(inp):
        raise RuntimeError("Execution crashed with long error stack trace...")

    task = AblationTask(
        task_id="err_01",
        name="Error Task",
        description="Failing agent test",
        category="error_test",
        input_data=None,
        expected_output="ok",
    )

    res = engine.run_single_task(failing_agent, task, "failing")
    assert res.error is not None
    assert res.code_quality_score == 0.0


def test_custom_quality_evaluator_nan_returns_zero():
    """Regression test: custom quality evaluator returning NaN is converted to 0.0."""
    engine = DownstreamAblationEngine(quality_evaluator=lambda code: float("nan"))
    assert engine.evaluate_code_quality("code") == 0.0

def test_net_improvement_count_and_rate():
    """Regression test: net_improvement_count tracks tasks where baseline failed and evolved passed."""
    engine = DownstreamAblationEngine()

    def baseline_agent(inp):
        return "bad"

    def evolved_agent(inp):
        return "good"

    task = AblationTask(
        task_id="imp_01",
        name="Improvement Task",
        description="Check net improvement",
        category="improvement",
        input_data=None,
        expected_output="good",
    )

    report = engine.run_ablation_campaign(baseline_agent, evolved_agent, [task])
    assert report.net_improvement_count == 1
    assert report.net_improvement_rate == 1.0
