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
import random
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
                return 0.0

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
            else (round(evolved_pass_rate * 100.0, 2) if pass_rate_uplift > 0 else 0.0)
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
        net_improvement_count = net_improvements - regressions
        net_improvement_rate = (
            round(net_improvement_count / total_tasks, 4)
            if total_tasks > 0
            else 0.0
        )

        # Paired statistical analysis: both agents are evaluated on the same
        # tasks, so pass/fail outcomes are paired, not independent. McNemar's
        # test is the correct paired test for binary outcomes; a paired
        # bootstrap produces a confidence interval for the uplift and latency
        # delta that respects the within-task correlation.
        mcnemar_stat, mcnemar_p = self._mcnemar_test(baseline_results, evolved_results)
        uplift_ci = self._paired_bootstrap_ci(
            baseline_results, evolved_results, metric="passed", n_bootstrap=2000
        )
        latency_ci = self._paired_bootstrap_ci(
            baseline_results, evolved_results, metric="latency_sec", n_bootstrap=2000
        )

        statistical_metrics = {
            "test": "mcnemar_paired",
            "mcnemar_chi2": round(mcnemar_stat, 4),
            "p_value": round(mcnemar_p, 4),
            "statistically_significant": mcnemar_p < 0.05,
            "uplift_confidence_interval_95": (round(uplift_ci[0], 4), round(uplift_ci[1], 4)),
            "latency_change_confidence_interval_95": (round(latency_ci[0], 6), round(latency_ci[1], 6)),
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
            net_improvement_count=net_improvement_count,
            category_breakdown=category_data,
            statistical_metrics=statistical_metrics,
            detailed_results=detailed_results,
        )

    def _mcnemar_test(
        self, baseline_results: list[TaskResult], evolved_results: list[TaskResult]
    ) -> Tuple[float, float]:
        """McNemar's test for paired binary (pass/fail) outcomes.

        Both agents run on the same tasks, so their outcomes are paired.
        The test considers only the discordant pairs:
          b: baseline passed, evolved failed  (regressions)
          c: baseline failed, evolved passed  (improvements)
        With continuity correction: chi2 = (|b - c| - 1)^2 / (b + c).
        When b + c == 0 there is no discordance; the result is not significant.
        """
        b = sum(1 for br, er in zip(baseline_results, evolved_results) if br.passed and not er.passed)
        c = sum(1 for br, er in zip(baseline_results, evolved_results) if not br.passed and er.passed)
        discordant = b + c
        if discordant == 0:
            return 0.0, 1.0
        chi2 = (abs(b - c) - 1) ** 2 / discordant
        # p-value from the chi-square distribution with 1 df: p = erfc(sqrt(chi2 / 2))
        p_value = math.erfc(math.sqrt(chi2 / 2.0))
        return chi2, p_value

    def _paired_bootstrap_ci(
        self,
        baseline_results: list[TaskResult],
        evolved_results: list[TaskResult],
        metric: str = "passed",
        n_bootstrap: int = 2000,
        confidence: float = 0.95,
        seed: int = 42,
    ) -> Tuple[float, float]:
        """Paired bootstrap confidence interval for the per-task delta.

        Resamples tasks (with replacement) as paired units, recomputing the
        metric delta within each resample so within-task correlation is
        preserved. For ``metric="passed"`` the delta is the pass-rate uplift;
        for ``metric="latency_sec"`` it is the mean latency change. Returns the
        (lower, upper) bounds of the confidence interval.
        """
        n = min(len(baseline_results), len(evolved_results))
        if n == 0:
            return 0.0, 0.0
        rng = random.Random(seed)
        deltas: list[float] = []
        for _ in range(n_bootstrap):
            indices = [rng.randrange(n) for _ in range(n)]
            if metric == "passed":
                b_rate = sum(1 for i in indices if baseline_results[i].passed) / n
                e_rate = sum(1 for i in indices if evolved_results[i].passed) / n
                deltas.append(e_rate - b_rate)
            else:
                b_mean = sum(baseline_results[i].latency_sec for i in indices) / n
                e_mean = sum(evolved_results[i].latency_sec for i in indices) / n
                deltas.append(e_mean - b_mean)
        deltas.sort()
        alpha = (1.0 - confidence) / 2.0
        lower_idx = int(math.floor(alpha * n_bootstrap))
        upper_idx = int(math.ceil((1.0 - alpha) * n_bootstrap)) - 1
        lower_idx = max(0, min(lower_idx, n_bootstrap - 1))
        upper_idx = max(0, min(upper_idx, n_bootstrap - 1))
        return deltas[lower_idx], deltas[upper_idx]


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
    print(f"Pass Rate Uplift:   {report.pass_rate_uplift * 100:+.1f}% ({report.relative_pass_rate_uplift:+.1f}% relative)")
    print(f"Latency Change:     {report.latency_change_pct:+.1f}%")
    print(f"Code Quality Delta: {report.code_quality_score_change:+.1f} pts")
    print(f"Regression Count:   {report.regression_count}")
    print(f"McNemar p-Value:    {report.statistical_metrics['p_value']:.4f}")
