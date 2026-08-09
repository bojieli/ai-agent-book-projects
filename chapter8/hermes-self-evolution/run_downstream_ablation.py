"""Downstream Ablation Engine for Hermes Self-Evolution.

Evaluates baseline vs. self-evolved agent code across synthetic and real task suites:
- Pass rate uplift measurement
- Execution latency change tracking
- Code quality scoring (AST metrics, complexity, readability)
- Regression rate analysis (tasks passed by baseline but failed by evolved agent)
- Statistical ablation reporting with confidence intervals and z-scores
"""

from __future__ import annotations

import ast
import logging
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class AblationTask:
    """A task in the ablation evaluation suite."""

    task_id: str
    name: str
    description: str
    category: str  # "synthetic", "real", "refactoring", "bugfix", "optimization"
    input_data: Any
    expected_output: Any
    verifier: Optional[Callable[[Any, Any], bool]] = None
    quality_rubric: Optional[dict[str, Any]] = None


@dataclass
class TaskResult:
    """Result of running an agent on a single task."""

    task_id: str
    agent_type: str  # "baseline" or "evolved"
    passed: bool
    output: Any
    latency_sec: float
    code_quality_score: float
    error: Optional[str] = None


@dataclass
class AblationReport:
    """Statistical report summarizing baseline vs evolved agent ablation campaign."""

    total_tasks: int
    baseline_pass_rate: float
    evolved_pass_rate: float
    pass_rate_uplift: float
    relative_pass_rate_uplift: float
    baseline_avg_latency_sec: float
    evolved_avg_latency_sec: float
    latency_change_pct: float
    baseline_avg_code_quality: float
    evolved_avg_code_quality: float
    code_quality_score_change: float
    regression_count: int
    regression_rate: float
    net_improvement_count: int
    net_improvement_rate: float
    category_breakdown: dict[str, dict[str, Any]]
    statistical_metrics: dict[str, Any]
    detailed_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class DownstreamAblationEngine:
    """Evaluates baseline vs. self-evolved agent performance across task suites."""

    def __init__(self, quality_evaluator: Optional[Callable[[Any], float]] = None):
        self.custom_quality_evaluator = quality_evaluator

    def evaluate_code_quality(self, code_or_output: Any) -> float:
        """Evaluates code quality score (0.0 to 100.0) based on AST and structural metrics."""
        if self.custom_quality_evaluator is not None:
            try:
                raw_score = float(self.custom_quality_evaluator(code_or_output))
                if math.isnan(raw_score):
                    return 0.0
                return max(0.0, min(100.0, raw_score))
            except Exception as e:
                logger.warning("Custom quality evaluator execution failed: %s", e)

        if not isinstance(code_or_output, str):
            code_str = str(code_or_output)
        else:
            code_str = code_or_output

        # If empty output
        if not code_str.strip():
            return 0.0

        score = 50.0  # Base score for valid non-empty output

        # AST analysis if output is valid Python code
        try:
            tree = ast.parse(code_str)
            score += 15.0  # Valid Python syntax bonus

            functions = [
                n for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

            # Modularization bonus
            if functions or classes:
                score += 10.0

            # Check docstrings and type annotations
            docstring_count = 0
            annotation_count = 0
            for fn in functions:
                if ast.get_docstring(fn):
                    docstring_count += 1
                all_args = fn.args.args + getattr(fn.args, "posonlyargs", []) + fn.args.kwonlyargs
                if fn.returns is not None or any(arg.annotation for arg in all_args):
                    annotation_count += 1

            if docstring_count > 0:
                score += 10.0
            if annotation_count > 0:
                score += 10.0

            # Cyclomatic complexity proxy: count branching statements
            branches = sum(
                1
                for n in ast.walk(tree)
                if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler))
            )
            if branches <= 8:
                score += 5.0
            elif branches > 20:
                score -= 10.0

        except Exception as e:
            # Not valid python code, judge text structure/length
            if len(code_str) > 20 and not code_str.startswith("Error"):
                score += 5.0
        return max(0.0, min(100.0, score))

    def execute_agent(self, agent: Any, task: AblationTask) -> Tuple[Any, float, Optional[str]]:
        """Executes an agent on a task and measures latency."""
        start_time = time.perf_counter()
        output = None
        error = None

        try:
            if callable(agent):
                output = agent(task.input_data)
            elif hasattr(agent, "run") and callable(getattr(agent, "run")):
                output = agent.run(task.input_data)
            elif hasattr(agent, "solve") and callable(getattr(agent, "solve")):
                output = agent.solve(task.input_data)
            elif hasattr(agent, "execute") and callable(getattr(agent, "execute")):
                output = agent.execute(task.input_data)
            elif isinstance(agent, dict) and "run" in agent and callable(agent["run"]):
                output = agent["run"](task.input_data)
            elif hasattr(agent, "__call__"):
                output = agent(task.input_data)
            else:
                output = str(agent)
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}"
            output = None

        latency_sec = time.perf_counter() - start_time
        return output, latency_sec, error

    def verify_output(self, output: Any, task: AblationTask, error: Optional[str]) -> bool:
        """Verifies if agent output matches task expectations."""
        if error is not None:
            return False

        if task.verifier is not None:
            try:
                return bool(task.verifier(output, task.expected_output))
            except Exception:
                return False

        if output == task.expected_output:
            return True

        if isinstance(output, str) and isinstance(task.expected_output, str):
            return output.strip() == task.expected_output.strip()

        return False

    def run_single_task(self, agent: Any, task: AblationTask, agent_type: str) -> TaskResult:
        """Runs an agent on a single task and returns TaskResult."""
        output, latency_sec, error = self.execute_agent(agent, task)
        passed = self.verify_output(output, task, error)
        if error is not None or output is None:
            quality_score = 0.0
        else:
            quality_score = self.evaluate_code_quality(output)
        return TaskResult(
            task_id=task.task_id,
            agent_type=agent_type,
            passed=passed,
            output=output,
            latency_sec=latency_sec,
            code_quality_score=quality_score,
            error=error,
        )

    def run_ablation_campaign(
        self,
        baseline_agent: Any = None,
        evolved_agent: Any = None,
        tasks: Optional[list[Union[dict, AblationTask]]] = None,
    ) -> AblationReport:
        """Runs full downstream ablation campaign comparing baseline vs evolved agents."""
        if baseline_agent is None:
            baseline_agent = create_default_baseline_agent()
        if evolved_agent is None:
            evolved_agent = create_default_evolved_agent()

        if tasks is None:
            task_objs = create_default_task_suite()
        else:
            task_objs = []
            for t in tasks:
                if isinstance(t, AblationTask):
                    task_objs.append(t)
                elif isinstance(t, dict):
                    task_objs.append(
                        AblationTask(
                            task_id=t.get("task_id", f"task_{len(task_objs)+1}"),
                            name=t.get("name", "Custom Task"),
                            description=t.get("description", ""),
                            category=t.get("category", "synthetic"),
                            input_data=t.get("input_data"),
                            expected_output=t.get("expected_output"),
                            verifier=t.get("verifier"),
                            quality_rubric=t.get("quality_rubric"),
                        )
                    )
                else:
                    logger.warning("Invalid task item: %s", t)
                    raise ValueError(f"Task item must be an AblationTask instance or dict, got: {type(t)}")
        total_tasks = len(task_objs)
        baseline_results: list[TaskResult] = []
        evolved_results: list[TaskResult] = []

        # Run tasks for baseline and evolved agents
        for task in task_objs:
            b_res = self.run_single_task(baseline_agent, task, "baseline")
            e_res = self.run_single_task(evolved_agent, task, "evolved")
            baseline_results.append(b_res)
            evolved_results.append(e_res)

        # Compute pass rates
        b_passed = sum(1 for r in baseline_results if r.passed)
        e_passed = sum(1 for r in evolved_results if r.passed)

        baseline_pass_rate = round(b_passed / total_tasks, 4) if total_tasks > 0 else 0.0
        evolved_pass_rate = round(e_passed / total_tasks, 4) if total_tasks > 0 else 0.0
        pass_rate_uplift = round(evolved_pass_rate - baseline_pass_rate, 4)

        rel_uplift = (
            round((pass_rate_uplift / baseline_pass_rate) * 100.0, 2)
            if baseline_pass_rate > 0
            else (100.0 if pass_rate_uplift > 0 else 0.0)
        )

        # Compute latencies
        b_latencies = [r.latency_sec for r in baseline_results]
        e_latencies = [r.latency_sec for r in evolved_results]

        b_avg_lat = round(sum(b_latencies) / total_tasks, 6) if total_tasks > 0 else 0.0
        e_avg_lat = round(sum(e_latencies) / total_tasks, 6) if total_tasks > 0 else 0.0

        lat_change_pct = (
            round(((e_avg_lat - b_avg_lat) / b_avg_lat) * 100.0, 2)
            if b_avg_lat > 0
            else 0.0
        )

        # Compute code quality scores
        b_qualities = [r.code_quality_score for r in baseline_results]
        e_qualities = [r.code_quality_score for r in evolved_results]

        b_avg_qual = round(sum(b_qualities) / total_tasks, 2) if total_tasks > 0 else 0.0
        e_avg_qual = round(sum(e_qualities) / total_tasks, 2) if total_tasks > 0 else 0.0
        qual_change = round(e_avg_qual - b_avg_qual, 2)

        # Detect regressions (baseline passed, evolved failed)
        regressions = 0
        net_improvements = 0

        category_data: dict[str, dict[str, Any]] = {}

        detailed_results = []
        for b_res, e_res, task in zip(baseline_results, evolved_results, task_objs):
            cat = task.category
            if cat not in category_data:
                category_data[cat] = {
                    "total": 0,
                    "baseline_passed": 0,
                    "evolved_passed": 0,
                    "regressions": 0,
                }

            category_data[cat]["total"] += 1
            if b_res.passed:
                category_data[cat]["baseline_passed"] += 1
            if e_res.passed:
                category_data[cat]["evolved_passed"] += 1

            if b_res.passed and not e_res.passed:
                regressions += 1
                category_data[cat]["regressions"] += 1
            elif not b_res.passed and e_res.passed:
                net_improvements += 1

            detailed_results.append(
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "category": task.category,
                    "baseline_passed": b_res.passed,
                    "evolved_passed": e_res.passed,
                    "baseline_latency_sec": round(b_res.latency_sec, 5),
                    "evolved_latency_sec": round(e_res.latency_sec, 5),
                    "baseline_quality_score": b_res.code_quality_score,
                    "evolved_quality_score": e_res.code_quality_score,
                    "is_regression": b_res.passed and not e_res.passed,
                    "is_improvement": not b_res.passed and e_res.passed,
                }
            )

        regression_rate = round(regressions / b_passed, 4) if b_passed > 0 else 0.0
        net_improvement_rate = (
            round((net_improvements - regressions) / total_tasks, 4)
            if total_tasks > 0
            else 0.0
        )

        # Statistical significance calculation (Z-test for proportions)
        z_score, p_value, ci_lower, ci_upper = self._calculate_proportion_ztest(
            b_passed, e_passed, total_tasks
        )

        statistical_metrics = {
            "z_score": round(z_score, 4),
            "p_value": round(p_value, 4),
            "statistically_significant": p_value < 0.05,
            "confidence_interval_95": (round(ci_lower, 4), round(ci_upper, 4)),
        }

        return AblationReport(
            total_tasks=total_tasks,
            baseline_pass_rate=baseline_pass_rate,
            evolved_pass_rate=evolved_pass_rate,
            pass_rate_uplift=pass_rate_uplift,
            relative_pass_rate_uplift=rel_uplift,
            baseline_avg_latency_sec=b_avg_lat,
            evolved_avg_latency_sec=e_avg_lat,
            latency_change_pct=lat_change_pct,
            baseline_avg_code_quality=b_avg_qual,
            evolved_avg_code_quality=e_avg_qual,
            code_quality_score_change=qual_change,
            regression_count=regressions,
            regression_rate=regression_rate,
            net_improvement_rate=net_improvement_rate,
            net_improvement_count=net_improvements,
            category_breakdown=category_data,
            statistical_metrics=statistical_metrics,
            detailed_results=detailed_results,
        )

    def _calculate_proportion_ztest(
        self, p1_count: int, p2_count: int, n: int
    ) -> Tuple[float, float, float, float]:
        """Calculates Z-score, approximate p-value, and 95% CI for two proportions."""
        if n <= 0:
            return 0.0, 1.0, 0.0, 0.0

        p1 = p1_count / n
        p2 = p2_count / n
        diff = p2 - p1

        p_pooled = (p1_count + p2_count) / (2 * n)
        se_pooled = math.sqrt(2 * p_pooled * (1 - p_pooled) / n) if p_pooled > 0 and p_pooled < 1 else 0.0

        if se_pooled > 0:
            z_score = diff / se_pooled
        else:
            z_score = 0.0

        # Approximate p-value using normal distribution error function
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))

        se_diff = math.sqrt((p1 * (1 - p1) / n) + (p2 * (1 - p2) / n))
        ci_lower = diff - 1.96 * se_diff
        ci_upper = diff + 1.96 * se_diff

        return z_score, p_value, ci_lower, ci_upper


# ── Sample Agents & Task Suite ───────────────────────────────────


def create_default_baseline_agent() -> Callable[[Any], Any]:
    """Creates a default baseline agent function for ablation campaigns."""

    def baseline_agent(input_data: Any) -> Any:
        if isinstance(input_data, dict):
            task_type = input_data.get("type")
            if task_type == "math":
                nums = input_data.get("numbers", [])
                return sum(nums)  # Naive sum, fails on multiplication/avg
            elif task_type == "code_refactor":
                code = input_data.get("code", "")
                return code  # Returns un-refactored code
            elif task_type == "string_format":
                s = input_data.get("text", "")
                return s.lower()  # Naive lowercase, fails complex title format
            elif task_type == "bug_fix":
                return "def solve(): return None"  # Returns stub
        return input_data

    return baseline_agent


def create_default_evolved_agent() -> Callable[[Any], Any]:
    """Creates a self-evolved agent function with improved capability for ablation campaigns."""

    def evolved_agent(input_data: Any) -> Any:
        if isinstance(input_data, dict):
            task_type = input_data.get("type")
            if task_type == "math":
                op = input_data.get("op", "sum")
                nums = input_data.get("numbers", [])
                if op == "product":
                    res = 1
                    for n in nums:
                        res *= n
                    return res
                elif op == "avg":
                    return sum(nums) / len(nums) if nums else 0
                return sum(nums)
            elif task_type == "code_refactor":
                code = input_data.get("code", "")
                # Evolved agent adds docstrings and annotations
                return f'"""Refactored code."""\nfrom typing import Any\n\n{code.strip()}\n'
            elif task_type == "string_format":
                s = input_data.get("text", "")
                return s.title()
            elif task_type == "bug_fix":
                return (
                    '"""Fixed implementation."""\ndef solve(x: int) -> int:\n'
                    '    """Solves the task correctly."""\n    return x * 2\n'
                )
        return input_data

    return evolved_agent


def create_default_task_suite() -> list[AblationTask]:
    """Creates a benchmark task suite containing synthetic and real tasks."""
    return [
        AblationTask(
            task_id="task_synth_01",
            name="Synthetic Math Summation",
            description="Sum a list of numbers",
            category="synthetic",
            input_data={"type": "math", "op": "sum", "numbers": [10, 20, 30]},
            expected_output=60,
        ),
        AblationTask(
            task_id="task_synth_02",
            name="Synthetic Math Product",
            description="Multiply a list of numbers",
            category="synthetic",
            input_data={"type": "math", "op": "product", "numbers": [2, 3, 4]},
            expected_output=24,
        ),
        AblationTask(
            task_id="task_real_01",
            name="String Title Formatting",
            description="Format text into title case",
            category="real",
            input_data={"type": "string_format", "text": "hermes agent self evolution"},
            expected_output="Hermes Agent Self Evolution",
        ),
        AblationTask(
            task_id="task_real_02",
            name="Code Refactoring Task",
            description="Refactor code with docstrings and type hints",
            category="refactoring",
            input_data={"type": "code_refactor", "code": "def process(x):\n    return x + 1"},
            expected_output=None,
            verifier=lambda output, exp: isinstance(output, str) and '"""Refactored code."""' in output,
        ),
        AblationTask(
            task_id="task_real_03",
            name="Bug Fixing Task",
            description="Fix buggy function and add type safety",
            category="bugfix",
            input_data={"type": "bug_fix"},
            expected_output=None,
            verifier=lambda output, exp: isinstance(output, str) and "def solve(x: int)" in output,
        ),
    ]


def run_ablation_campaign(
    baseline_agent: Any = None,
    evolved_agent: Any = None,
    tasks: Optional[list[Union[dict, AblationTask]]] = None,
) -> AblationReport:
    """Entrypoint function to execute a downstream ablation campaign.

    Args:
        baseline_agent: Agent instance/callable representing baseline code.
        evolved_agent: Agent instance/callable representing self-evolved code.
        tasks: List of AblationTask instances or task dictionary definitions.

    Returns:
        AblationReport containing pass rate uplift, latency change, quality score change,
        regression rate, and statistical metrics.
    """
    engine = DownstreamAblationEngine()
    return engine.run_ablation_campaign(baseline_agent, evolved_agent, tasks)


if __name__ == "__main__":
    print("Running Hermes Downstream Ablation Campaign...")
    report = run_ablation_campaign()
    print(f"Total Tasks: {report.total_tasks}")
    print(f"Baseline Pass Rate: {report.baseline_pass_rate * 100:.1f}%")
    print(f"Evolved Pass Rate:  {report.evolved_pass_rate * 100:.1f}%")
    print(f"Pass Rate Uplift:   +{report.pass_rate_uplift * 100:.1f}% ({report.relative_pass_rate_uplift:+.1f}% relative)")
    print(f"Latency Change:     {report.latency_change_pct:+.1f}%")
    print(f"Code Quality Delta: {report.code_quality_score_change:+.1f} pts")
    print(f"Regression Count:   {report.regression_count}")
    print(f"P-Value:            {report.statistical_metrics['p_value']:.4f}")
