"""
Main entry point for Context-Aware Agent
"""

import os
import sys
import argparse
import logging
from agent import ContextAwareAgent, ContextMode
from config import PROVIDERS, SUPPORTED_PROVIDERS, canonical_provider, resolve_backend
import json
from pathlib import Path
import subprocess
import time
from typing import Dict, Any, List
from tabulate import tabulate
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _completed(result: Dict[str, Any]) -> bool:
    """Return terminal-response status with compatibility for old results."""
    return bool(result.get("completed", result.get("success", False)))

# Load .env so API keys configured there are available via os.getenv.
# (config.py calls load_dotenv() too, but main.py only imports agent, which
#  does not import config, so we must trigger it here.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AblationTestSuite:
    """Test suite for exploring context importance through ablation studies"""
    
    def __init__(self, api_key: str, provider: str = "siliconflow", model: str = None):
        """
        Initialize test suite
        
        Args:
            api_key: API key for the LLM provider
            provider: LLM provider to use
            model: Optional model override
        """
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.test_results = []
        
    def create_complex_financial_task(self) -> str:
        """
        Create a complex task that requires multiple tool calls and reasoning
        
        Returns:
            Task description
        """
        return """Analyze the financial report from this PDF: https://www.berkshirehathaway.com/qtrly/1stqtr23.pdf

Please complete the following analysis:
1. Extract the total revenue figures from Q1 2023
2. Convert the revenue from USD to EUR, GBP, and JPY
3. Calculate the following metrics:
   - Average revenue across the three converted currencies
   - Percentage difference between highest and lowest converted values
   - If the company maintains a 15% profit margin, what would be the profit in each currency?

Provide a comprehensive financial summary with all calculations shown."""
    
    def create_multinational_budget_task(self) -> str:
        """
        Create a task requiring multiple currency conversions and calculations
        
        Returns:
            Task description  
        """
        return """A multinational company has the following Q1 2024 expenses documented in this report:
https://raw.githubusercontent.com/adobe/pdfservices-node-sdk-samples/master/resources/extractPDFInput.pdf

Tasks to complete:
1. Parse the PDF and extract all monetary values mentioned
2. The company operates in 5 regions with expenses in different currencies:
   - US Office: $2,500,000 USD
   - UK Office: £1,800,000 GBP  
   - Japan Office: ¥380,000,000 JPY
   - EU Office: €2,100,000 EUR
   - Singapore Office: $3,200,000 SGD
3. Convert all expenses to USD for consolidation
4. Calculate:
   - Total global expenses in USD
   - Average expense per region
   - What percentage each region represents of total expenses
   - If we apply a 8% cost reduction uniformly, what would be the new expense for each region in their local currency?

Present a detailed financial analysis with all conversions and calculations."""
    
    def run_single_test(self, task: str, context_mode: ContextMode, test_name: str,
                        case_name: str = "default") -> Dict[str, Any]:
        """
        Run a single ablation test

        Args:
            task: Task to execute
            context_mode: Context mode to test
            test_name: Name of the test
            case_name: Name of the case/task this test belongs to

        Returns:
            Test results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Running test: {test_name} [case: {case_name}]")
        logger.info(f"Context mode: {context_mode.value}")
        logger.info(f"{'='*60}")

        agent = ContextAwareAgent(self.api_key, context_mode, provider=self.provider, model=self.model)

        start_time = time.time()
        result = agent.execute_task(task)
        execution_time = time.time() - start_time
        completed = _completed(result)

        # Analyze the result
        test_result = {
            "test_name": test_name,
            "case_name": case_name,
            "context_mode": context_mode.value,
            "execution_time": round(execution_time, 2),
            "iterations": result.get("iterations", 0),
            "num_tool_calls": len(result["trajectory"].tool_calls),
            # This legacy suite has no task-specific correctness rubric. Keep
            # ``success`` as a compatibility alias, but report completion
            # separately so a refusal is not presented as task success.
            "completed": completed,
            "success": completed,
            "task_success": None,
            "has_final_answer": result.get("final_answer") is not None,
            "error": result.get("error"),
            "reasoning_steps": len(result["trajectory"].reasoning_steps),
            "final_answer_preview": (result.get("final_answer", "")[:200] + "...") if result.get("final_answer") else None
        }
        
        # Log summary
        logger.info(f"Test completed in {test_result['execution_time']}s")
        logger.info(f"Terminal response completed: {test_result['completed']}")
        logger.info(f"Tool calls made: {test_result['num_tool_calls']}")
        logger.info(f"Iterations: {test_result['iterations']}")
        
        if test_result["error"]:
            logger.error(f"Error occurred: {test_result['error']}")
        
        return test_result
    
    def run_ablation_study(self, context_modes: List[ContextMode] = None,
                          cases: List[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Run ablation study across specified context modes and one or more cases.

        Args:
            context_modes: List of context modes to test (defaults to all modes)
            cases: List of {"name", "task"} dicts to run each mode against.
                   Defaults to a single multinational-budget case, which
                   preserves the original single-task behaviour.

        Returns:
            Flat list of test results (one entry per case x mode).
        """
        # Default: single multinational-budget case (preserves prior behaviour).
        if cases is None:
            cases = [{
                "name": "Multinational Budget",
                "task": self.create_multinational_budget_task()
            }]

        # Map context modes to test names
        mode_names = {
            ContextMode.FULL: "Baseline - Full Context",
            ContextMode.NO_HISTORY: "Ablation 1 - No Historical Tool Calls",
            ContextMode.NO_REASONING: "Ablation 2 - No Reasoning Process",
            ContextMode.NO_TOOL_CALLS: "Ablation 3 - No Tool Call Commands",
            ContextMode.NO_TOOL_RESULTS: "Ablation 4 - No Tool Call Results"
        }

        if context_modes is None:
            context_modes = list(mode_names.keys())

        results = []
        for case in cases:
            case_name = case["name"]
            task = case["task"]
            for context_mode in context_modes:
                test_name = mode_names[context_mode]
                try:
                    result = self.run_single_test(task, context_mode, test_name, case_name=case_name)
                    results.append(result)
                    self.test_results.append(result)

                    # Add delay between tests to avoid rate limiting
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"Failed to run test {test_name} [case: {case_name}]: {str(e)}")
                    results.append({
                        "test_name": test_name,
                        "case_name": case_name,
                        "context_mode": context_mode.value,
                        "error": str(e),
                        "completed": False,
                        "success": False,
                        "task_success": False,
                    })

        return results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze ablation study results
        
        Args:
            results: List of test results
            
        Returns:
            Analysis summary
        """
        analysis = {
            "total_tests": len(results),
            "completed_tests": sum(1 for r in results if _completed(r)),
            # Compatibility key for existing report consumers. It now counts
            # terminal responses, not verified task successes.
            "successful_tests": sum(1 for r in results if _completed(r)),
            "context_mode_impact": {}
        }
        
        # Analyze impact of each ablation
        baseline = next((r for r in results if r["context_mode"] == "full"), None)
        
        if baseline:
            for result in results:
                if result["context_mode"] != "full":
                    mode_analysis = {
                        "completion_maintained": _completed(result),
                        "success_maintained": _completed(result),
                        "execution_time_delta": result.get("execution_time", 0) - baseline.get("execution_time", 0),
                        "iteration_delta": result.get("iterations", 0) - baseline.get("iterations", 0),
                        "tool_call_delta": result.get("num_tool_calls", 0) - baseline.get("num_tool_calls", 0),
                        "failure_reason": None
                    }
                    
                    # Identify failure reasons
                    if not _completed(result):
                        if result["context_mode"] == "no_tool_calls":
                            mode_analysis["failure_reason"] = "Cannot execute tools without tool call capability"
                        elif result["context_mode"] == "no_tool_results":
                            mode_analysis["failure_reason"] = "Cannot make informed decisions without tool results"
                        elif result["context_mode"] == "no_history":
                            mode_analysis["failure_reason"] = "May repeat actions or lose track of progress"
                        elif result["context_mode"] == "no_reasoning":
                            mode_analysis["failure_reason"] = "Lacks planning and strategic thinking"
                    
                    analysis["context_mode_impact"][result["context_mode"]] = mode_analysis
        
        return analysis
    
    def print_results_table(self, results: List[Dict[str, Any]]):
        """
        Print results in a formatted table
        
        Args:
            results: List of test results
        """
        # Prepare data for tabulation
        table_data = []
        for result in results:
            table_data.append([
                result.get("case_name", "default"),
                result["context_mode"],
                "✓" if _completed(result) else "✗",
                f"{result.get('execution_time', 0)}s",
                result.get("iterations", 0),
                result.get("num_tool_calls", 0),
                result.get("reasoning_steps", 0),
                "Yes" if result.get("has_final_answer", False) else "No"
            ])

        headers = ["Case", "Context Mode", "Completed", "Time", "Iterations", "Tool Calls", "Reasoning Steps", "Final Answer"]

        print("\n" + "="*80)
        print("ABLATION STUDY RESULTS")
        print("="*80)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def print_comparison_matrix(self, results: List[Dict[str, Any]]):
        """
        Print a mode x case comparison matrix so the effect of each context
        component can be read at a glance across every case.

        Args:
            results: List of test results
        """
        cases = []
        for r in results:
            c = r.get("case_name", "default")
            if c not in cases:
                cases.append(c)

        modes = []
        for r in results:
            m = r["context_mode"]
            if m not in modes:
                modes.append(m)

        # Index results by (mode, case) for quick lookup.
        by_key = {(r["context_mode"], r.get("case_name", "default")): r for r in results}

        table_data = []
        for mode in modes:
            row = [mode]
            for case in cases:
                r = by_key.get((mode, case))
                if r is None:
                    row.append("-")
                elif _completed(r):
                    row.append(f"✓ {r.get('iterations', 0)}it/{r.get('num_tool_calls', 0)}tc")
                else:
                    row.append(f"✗ {r.get('iterations', 0)}it/{r.get('num_tool_calls', 0)}tc")
            table_data.append(row)

        headers = ["Context Mode"] + cases
        print("\n" + "="*80)
        print("COMPARISON MATRIX (rows = context mode, cols = case; cell = completion it=iterations tc=tool calls)")
        print("="*80)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def visualize_results(self, results: List[Dict[str, Any]]):
        """
        Create visualizations of ablation study results
        
        Args:
            results: List of test results
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, skipping visualizations")
            return
            
        # Extract data for visualization
        modes = [r["context_mode"] for r in results]
        iterations = [r.get("iterations", 0) for r in results]
        tool_calls = [r.get("num_tool_calls", 0) for r in results]
        exec_times = [r.get("execution_time", 0) for r in results]
        success = [1 if _completed(r) else 0 for r in results]
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("Ablation Study: Impact of Context Components", fontsize=16)
        
        # Plot 1: terminal-response completion rate
        axes[0, 0].bar(modes, success, color=['green' if s else 'red' for s in success])
        axes[0, 0].set_title("Terminal Responses by Context Mode")
        axes[0, 0].set_ylabel("Completed (1) / No response (0)")
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Plot 2: Iterations Required
        axes[0, 1].bar(modes, iterations, color='blue')
        axes[0, 1].set_title("Iterations Required")
        axes[0, 1].set_ylabel("Number of Iterations")
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Plot 3: Tool Calls Made
        axes[1, 0].bar(modes, tool_calls, color='orange')
        axes[1, 0].set_title("Tool Calls Made")
        axes[1, 0].set_ylabel("Number of Tool Calls")
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Execution Time
        axes[1, 1].bar(modes, exec_times, color='purple')
        axes[1, 1].set_title("Execution Time")
        axes[1, 1].set_ylabel("Time (seconds)")
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig("ablation_study_results.png", dpi=150, bbox_inches='tight')
        logger.info("Visualization saved as 'ablation_study_results.png'")
    
    def generate_report(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """
        Generate a comprehensive report of the ablation study
        
        Args:
            results: List of test results
            analysis: Analysis summary
            
        Returns:
            Report text
        """
        report = """
# Context Ablation Study Report

## Executive Summary
This ablation study explores the effect of different context components on AI
agent behavior. This legacy suite reports terminal-response completion and
tool-use behavior; it does not claim task correctness without a task-specific
rubric.

## Test Configuration
- **Provider**: {provider}
- **Model**: {model}
- **Task**: Complex financial analysis requiring PDF parsing, currency conversion, and calculations
- **Context Modes Tested**: {num_modes}

## Key Findings

### 1. Complete Lack of Historical Tool Calls (NO_HISTORY)
**Impact**: Agent loses track of previous actions and may repeat operations unnecessarily.
- **Behavior**: Agent cannot reference past tool executions, leading to redundant API calls
- **Performance**: {no_history_perf}
- **Critical for**: Multi-step tasks requiring sequential dependencies

### 2. Lack of Reasoning Process (NO_REASONING)
**Impact**: Agent operates without strategic planning or step-by-step thinking.
- **Behavior**: Direct execution without planning leads to inefficient or incorrect solutions
- **Performance**: {no_reasoning_perf}
- **Critical for**: Complex tasks requiring logical decomposition

### 3. Lack of Tool Call Commands (NO_TOOL_CALLS)
**Impact**: Agent cannot execute any external tools.
- **Behavior**: The model may return a refusal or describe the missing tools;
  a terminal response is not evidence that the financial task was completed.
- **Performance**: {no_tool_calls_perf}
- **Critical for**: Any task requiring external data or computation

### 4. Lack of Tool Call Results (NO_TOOL_RESULTS)
**Impact**: Agent operates blind to the outcomes of its actions.
- **Behavior**: The model may stop with a warning, repeat actions, or produce an
  incorrect conclusion; correctness must be checked by a task-specific rubric.
- **Performance**: {no_tool_results_perf}
- **Critical for**: Tasks requiring iterative refinement or result validation

## Statistical Summary
- **Total Tests Run**: {total_tests}
- **Terminal Responses**: {successful_tests}
- **Average Execution Time (Full Context)**: {avg_exec_time}s
- **Average Tool Calls (Full Context)**: {avg_tool_calls}

## Conclusion
The ablation study records how each context component changes execution behavior:
1. **Tool calls** determine whether the agent can interact with external tools
2. **Tool results** provide feedback for decision-making
3. **Reasoning** can affect planning and execution efficiency
4. **History** can prevent redundant actions and maintain task coherence

Task-level claims require a separate evaluator, such as the canonical numeric
rubric used by `run_experiment_1_1.py`.

## Recommendations
- Always maintain complete context for production agents
- Consider context windowing rather than removal for memory optimization
- Implement fallback mechanisms when context components are unavailable
"""
        
        # Fill in performance metrics
        def get_perf_string(mode):
            mode_result = next((r for r in results if r["context_mode"] == mode), None)
            if mode_result:
                return f"{'COMPLETED' if _completed(mode_result) else 'NO TERMINAL RESPONSE'} - {mode_result.get('iterations', 0)} iterations, {mode_result.get('execution_time', 0)}s"
            return "N/A"
        
        # Calculate baseline metrics
        baseline = next((r for r in results if r["context_mode"] == "full"), None)
        avg_exec_time = baseline.get("execution_time", 0) if baseline else 0
        avg_tool_calls = baseline.get("num_tool_calls", 0) if baseline else 0
        
        report = report.format(
            provider=self.provider,
            model=self.model or "default",
            num_modes=len(results),
            no_history_perf=get_perf_string("no_history"),
            no_reasoning_perf=get_perf_string("no_reasoning"),
            no_tool_calls_perf=get_perf_string("no_tool_calls"),
            no_tool_results_perf=get_perf_string("no_tool_results"),
            total_tests=analysis["total_tests"],
            successful_tests=analysis["successful_tests"],
            avg_exec_time=avg_exec_time,
            avg_tool_calls=avg_tool_calls
        )
        
        return report


def run_single_task(api_key: str, task: str, context_mode: str = "full", provider: str = "siliconflow", model: str = None, output: str = None):
    """
    Run a single task with the agent

    Args:
        api_key: API key for the LLM provider
        task: Task description
        context_mode: Context mode to use
        provider: LLM provider to use
        model: Optional model override
        output: Optional path for the JSON result (default task_result_{mode}.json)
    """
    # Parse context mode
    mode_map = {
        "full": ContextMode.FULL,
        "no_history": ContextMode.NO_HISTORY,
        "no_reasoning": ContextMode.NO_REASONING,
        "no_tool_calls": ContextMode.NO_TOOL_CALLS,
        "no_tool_results": ContextMode.NO_TOOL_RESULTS
    }
    
    if context_mode not in mode_map:
        logger.error(f"Invalid context mode: {context_mode}")
        logger.info(f"Valid modes: {', '.join(mode_map.keys())}")
        return
    
    # Create agent
    agent = ContextAwareAgent(api_key, mode_map[context_mode], provider=provider, model=model)
    
    logger.info(f"Running task with context mode: {context_mode}")
    logger.info(f"Task: {task[:100]}...")
    
    # Execute task
    result = agent.execute_task(task)
    
    # Print results
    print("\n" + "="*60)
    print("TASK EXECUTION RESULT")
    print("="*60)
    print(f"Context Mode: {context_mode}")
    print(f"Terminal response completed: {_completed(result)}")
    print(f"Iterations: {result.get('iterations', 0)}")
    print(f"Tool Calls: {len(result['trajectory'].tool_calls)}")
    
    if result.get('final_answer'):
        print(f"\nFinal Answer:")
        print("-"*40)
        print(result['final_answer'])
    
    if result.get('error'):
        print(f"\nError: {result['error']}")
    
    # Save detailed results
    output_file = output or f"task_result_{context_mode}.json"
    with open(output_file, 'w') as f:
        # Convert trajectory to serializable format
        serializable_result = {
            "completed": _completed(result),
            "task_success": result.get("task_success"),
            # Backwards-compatible alias for older result readers.
            "success": _completed(result),
            "iterations": result.get("iterations", 0),
            "final_answer": result.get("final_answer"),
            "error": result.get("error"),
            "context_mode": context_mode,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "result": tc.result,
                    "timestamp": tc.timestamp
                }
                for tc in result["trajectory"].tool_calls
            ],
            "reasoning_steps": result["trajectory"].reasoning_steps,
            # Credential-free, provider-native request/response evidence.  The
            # ablation is about the context visible on each inference, so a
            # post-hoc summary is not sufficient to validate Experiment 1-1.
            "api_turns": result["trajectory"].api_turns,
            "provider": result.get("provider", provider),
            "model": result.get("model", model),
            "base_url": result.get("base_url"),
            "using_openrouter": result.get("using_openrouter", False),
        }
        json.dump(serializable_result, f, indent=2)
    
    logger.info(f"Detailed results saved to {output_file}")


def ensure_sample_pdfs():
    """
    Ensure sample PDFs exist, create them if they don't
    
    Returns:
        bool: True if PDFs are available
    """
    pdf_dir = Path("fixtures/pdfs")
    sample_pdf = pdf_dir / "simple_expense_report.pdf"
    
    if not pdf_dir.exists() or not sample_pdf.exists():
        print("\n📚 Sample PDFs not found. Creating them...")
        try:
            # Run the PDF creation script
            result = subprocess.run(
                [sys.executable, "create_sample_pdf.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("✅ Sample PDFs created successfully in fixtures/pdfs/")
                return True
            else:
                print(f"⚠️ Could not create PDFs: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠️ Error creating PDFs: {str(e)}")
            return False
    return True


def get_sample_tasks():
    """
    Get sample tasks for testing
    
    Returns:
        list: List of sample task dictionaries
    """
    # Check if we're running locally or need to use online PDFs
    local_pdfs = Path("fixtures/pdfs").exists()
    
    if local_pdfs:
        pdf_path = "file://" + str(Path.cwd() / "fixtures/pdfs" / "simple_expense_report.pdf")
        pdf_note = "Using local PDF"
    else:
        # Use a publicly available PDF for testing
        pdf_path = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        pdf_note = "Using online sample PDF"
    
    return [
        {
            "name": "📊 Currency Conversion Task",
            "description": "Convert between multiple currencies",
            "task": """Convert $1000 USD to EUR, GBP, and JPY. 
Then calculate the average value across all three converted currencies."""
        },
        {
            "name": "📄 PDF Analysis Task",
            "description": f"Extract and analyze data from PDF ({pdf_note})",
            "task": f"""Analyze this PDF document: {pdf_path}
Extract any text content and provide a summary of what you found."""
        },
        {
            "name": "💰 Complex Financial Analysis",
            "description": "Multi-step financial calculation",
            "task": """A company has the following quarterly revenues:
- Q1: $2,500,000 USD
- Q2: €2,100,000 EUR
- Q3: £1,800,000 GBP
- Q4: ¥380,000,000 JPY

Please:
1. Convert all revenues to USD
2. Calculate the total annual revenue in USD
3. Determine the average quarterly revenue
4. Find which quarter had the highest revenue
5. If the company has a 20% profit margin, calculate the annual profit in USD"""
        },
        {
            "name": "🌍 Multi-Currency Budget Planning",
            "description": "International budget calculations",
            "task": """An international conference has the following budget allocations:
- Venue (UK): £45,000
- Speakers (US): $75,000
- Catering (France): €38,000
- Technology (Japan): ¥8,500,000
- Marketing (Singapore): S$25,000

Tasks:
1. Convert all amounts to USD
2. Calculate the total budget
3. Determine what percentage each category represents
4. If we need to cut the budget by 15%, how much should each category be reduced to (in their original currencies)?"""
        },
        {
            "name": "📈 Investment Portfolio Analysis",
            "description": "Analyze international investment returns",
            "task": """An investor has the following international investments with their current values:
- US Tech Stocks: $125,000 (purchased for $100,000)
- European Bonds: €85,000 (purchased for €90,000)
- UK Real Estate: £200,000 (purchased for £175,000)
- Japanese ETFs: ¥15,000,000 (purchased for ¥12,000,000)

Calculate:
1. Convert all current values to USD
2. Convert all purchase prices to USD (use current exchange rates for simplicity)
3. Calculate the profit/loss for each investment in USD
4. Determine the total portfolio value and overall return percentage
5. Which investment performed best in percentage terms?"""
        }
    ]


def get_ablation_cases(num_cases: int = 1) -> List[Dict[str, str]]:
    """
    Build a list of self-contained cases for the ablation study.

    Reuses the pre-defined sample tasks, skipping the PDF task (which needs
    network access) so the study is reproducible offline apart from the LLM
    call itself. num_cases=1 returns a single case; larger values add more.

    Args:
        num_cases: How many cases to include (clamped to [1, available]).

    Returns:
        List of {"name", "task"} dicts.
    """
    samples = get_sample_tasks()
    # Indices 0/2/3/4 are currency/finance tasks (index 1 is the PDF task).
    candidates = [samples[0], samples[2], samples[3], samples[4]]
    num_cases = max(1, min(num_cases, len(candidates)))
    return [{"name": c["name"], "task": c["task"]} for c in candidates[:num_cases]]


def run_ablation_study(api_key: str, provider: str = "siliconflow", model: str = None,
                       context_modes: List[str] = None, num_cases: int = 1,
                       output: str = None):
    """
    Run ablation study to test importance of context

    Args:
        api_key: API key for the LLM provider
        provider: LLM provider to use
        model: Optional model override
        context_modes: List of context mode names to test (defaults to all)
        num_cases: Number of cases to run each mode against. 1 (default) keeps
            the original single multinational-budget task; >1 runs a multi-case
            comparison across the sample tasks.
        output: Optional path for the raw JSON results (default ablation_results.json)
    """
    # Parse context modes if provided
    mode_map = {
        "full": ContextMode.FULL,
        "no_history": ContextMode.NO_HISTORY,
        "no_reasoning": ContextMode.NO_REASONING,
        "no_tool_calls": ContextMode.NO_TOOL_CALLS,
        "no_tool_results": ContextMode.NO_TOOL_RESULTS
    }

    modes_to_test = None
    if context_modes:
        modes_to_test = []
        for mode_name in context_modes:
            if mode_name in mode_map:
                modes_to_test.append(mode_map[mode_name])
            else:
                logger.error(f"Invalid context mode: {mode_name}")
                logger.info(f"Valid modes: {', '.join(mode_map.keys())}")
                return

    # Build cases. num_cases <= 1 keeps the original single-case behaviour.
    cases = None
    if num_cases and num_cases > 1:
        cases = get_ablation_cases(num_cases)

    test_suite = AblationTestSuite(api_key, provider=provider, model=model)

    logger.info("Starting ablation study...")
    if modes_to_test:
        logger.info(f"Testing modes: {', '.join(context_modes)}")
    else:
        logger.info("Testing all context modes")
    logger.info(f"Cases: {len(cases) if cases else 1}")

    results = test_suite.run_ablation_study(modes_to_test, cases=cases)

    # Analyze results
    analysis = test_suite.analyze_results(results)

    # Print results table
    test_suite.print_results_table(results)

    # Print mode x case comparison matrix
    test_suite.print_comparison_matrix(results)

    # Generate visualizations
    try:
        test_suite.visualize_results(results)
    except Exception as e:
        logger.warning(f"Could not generate visualizations: {str(e)}")

    # Generate and save report
    report = test_suite.generate_report(results, analysis)
    with open("ablation_study_report.md", "w") as f:
        f.write(report)
    logger.info("Report saved as 'ablation_study_report.md'")

    # Save raw results
    output_file = output or "ablation_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Raw results saved as '{output_file}'")
    
    # Print analysis summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"Terminal Response Rate: {analysis['completed_tests']}/{analysis['total_tests']}")
    print("\nContext Mode Impacts:")
    for mode, impact in analysis["context_mode_impact"].items():
        print(f"\n{mode.upper()}:")
        print(f"  - Completion Maintained: {impact['completion_maintained']}")
        print(f"  - Execution Time Delta: {impact['execution_time_delta']:.2f}s")
        print(f"  - Iteration Delta: {impact['iteration_delta']}")
        print(f"  - Tool Call Delta: {impact['tool_call_delta']}")
        if impact['failure_reason']:
            print(f"  - Failure Reason: {impact['failure_reason']}")


def interactive_mode(api_key: str, provider: str = "siliconflow", model: str = None):
    """
    Run the agent in interactive mode
    
    Args:
        api_key: API key for the LLM provider
        provider: LLM provider to use
        model: Optional model override
    """
    # Store current provider and model
    current_provider = provider
    current_model = model
    current_api_key = api_key
    
    # Available providers
    available_providers = list(SUPPORTED_PROVIDERS)
    
    print("\n" + "="*60)
    print("INTERACTIVE MODE - Context-Aware Agent")
    print(f"Provider: {current_provider.upper()} | Model: {current_model or 'default'}")
    print("="*60)
    print("Available commands:")
    print("  - Type your task/question")
    print("  - 'samples' to see sample tasks")
    print("  - 'sample <number>' to run a sample task")
    print("  - 'create_pdfs' to create sample PDF files")
    print("  - 'providers' to list available providers")
    print("  - 'provider <name>' to switch provider")
    print("  - 'modes' to see available context modes")
    print("  - 'mode <mode_name>' to switch context mode")
    print("  - 'reset' to reset agent trajectory")
    print("  - 'status' to show current configuration")
    print("  - 'help' to show all commands")
    print("  - 'quit' to exit")
    print("-"*60)
    
    # Ensure sample PDFs exist
    ensure_sample_pdfs()
    
    # Get sample tasks
    sample_tasks = get_sample_tasks()
    
    # Initialize agent with full context
    mode_map = {
        "full": ContextMode.FULL,
        "no_history": ContextMode.NO_HISTORY,
        "no_reasoning": ContextMode.NO_REASONING,
        "no_tool_calls": ContextMode.NO_TOOL_CALLS,
        "no_tool_results": ContextMode.NO_TOOL_RESULTS
    }
    
    current_mode = ContextMode.FULL
    agent = ContextAwareAgent(current_api_key, current_mode, provider=current_provider, model=current_model)
    
    while True:
        try:
            # Show current provider in prompt
            prompt = f"\n[{current_provider.upper()}]> "
            user_input = input(prompt).strip()
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == 'help':
                print("\n📚 Available Commands:")
                print("  samples          - Display all available sample tasks")
                print("  sample <n>       - Run sample task number n")
                print("  providers        - List all available LLM providers")
                print("  provider <name>  - Switch to a different provider")
                print("  modes            - List available context modes")
                print("  mode <name>      - Switch context mode")
                print("  status           - Show current configuration")
                print("  reset            - Reset agent trajectory")
                print("  create_pdfs      - Generate sample PDF files")
                print("  help             - Show this help message")
                print("  quit             - Exit interactive mode")
                print("\nOr type any task/question to execute it.")
            
            elif user_input.lower() == 'samples':
                print("\n📋 Available sample tasks:")
                for i, sample in enumerate(sample_tasks, 1):
                    print(f"\n{i}. {sample['name']}")
                    print(f"   {sample['description']}")
            
            elif user_input.lower().startswith('sample '):
                try:
                    sample_num = int(user_input.split()[1])
                    if 1 <= sample_num <= len(sample_tasks):
                        sample = sample_tasks[sample_num - 1]
                        print(f"\n📌 Running: {sample['name']}")
                        print(f"Task: {sample['task']}")
                        print("\nProcessing...")
                        
                        result = agent.execute_task(sample['task'])
                        
                        print(f"\n{'='*40}")
                        print(f"Terminal response completed: {_completed(result)}")
                        print(f"Iterations: {result.get('iterations', 0)}")
                        print(f"Tool Calls: {len(result['trajectory'].tool_calls)}")
                        
                        if result.get('final_answer'):
                            print(f"\nAnswer:")
                            print(result['final_answer'])
                        
                        if result.get('error'):
                            print(f"\nError: {result['error']}")
                    else:
                        print(f"Invalid sample number. Use 'sample 1' through 'sample {len(sample_tasks)}'")
                except (ValueError, IndexError):
                    print(f"Invalid sample number. Use 'sample 1' through 'sample {len(sample_tasks)}'")
            
            elif user_input.lower() == 'create_pdfs':
                print("\n📄 Creating sample PDFs...")
                try:
                    result = subprocess.run(
                        [sys.executable, "create_sample_pdf.py"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        print("✅ Sample PDFs created successfully in fixtures/pdfs/")
                        # Update sample tasks with new PDF paths
                        sample_tasks = get_sample_tasks()
                    else:
                        print(f"⚠️ Could not create PDFs: {result.stderr}")
                except Exception as e:
                    print(f"⚠️ Error creating PDFs: {str(e)}")
            
            elif user_input.lower() == 'providers':
                print("\n🔌 Available providers:")
                for p in available_providers:
                    status = " (current)" if p == current_provider else ""
                    spec = PROVIDERS.get(canonical_provider(p))
                    if spec is None:
                        print(f"  - {p}{status}")
                        continue
                    # Derived from the registry, so a new entry shows up here
                    # without touching this command.
                    if not spec.requires_key:
                        keys = "no API key needed"
                    else:
                        keys = " / ".join(spec.key_vars)
                        keys += " ✓" if spec.api_key() else " (not set)"
                    print(f"  - {p}: {spec.default_model} [{keys}]{status}")
            
            elif user_input.lower().startswith('provider '):
                new_provider = user_input[9:].strip().lower()
                if new_provider in available_providers:
                    # Resolve through the registry: it knows each provider's key
                    # variables, which providers need no key (ollama) and the
                    # OpenRouter fallback, and it reports exactly which variable
                    # to set when nothing is available.
                    try:
                        new_backend = resolve_backend(new_provider)
                    except ValueError as exc:
                        print(f"❌ {exc}")
                        continue
                    # ContextAwareAgent resolves again, so only hand it a key it
                    # would treat as that provider's own. On the fallback path
                    # new_backend.api_key is the OpenRouter key; passing it would
                    # send an OpenRouter key to the provider's own endpoint.
                    new_api_key = "" if new_backend.using_openrouter else new_backend.api_key

                    # Update current settings
                    current_provider = new_provider
                    current_api_key = new_api_key
                    current_model = None  # Reset to use default model for new provider
                    
                    # Create new agent with new provider
                    agent = ContextAwareAgent(current_api_key, current_mode, provider=current_provider, model=current_model)
                    
                    # Get default model name from config
                    from config import Config
                    default_model = Config.get_default_model(current_provider)
                    
                    print(f"✅ Switched to provider: {current_provider}")
                    print(f"   Using model: {default_model}")
                else:
                    print(f"❌ Invalid provider. Available: {', '.join(available_providers)}")
            
            elif user_input.lower() == 'modes':
                print("\n🔧 Available context modes:")
                for mode in mode_map.keys():
                    print(f"  - {mode}")
            
            elif user_input.lower().startswith('mode '):
                new_mode = user_input[5:].strip()
                if new_mode in mode_map:
                    current_mode = mode_map[new_mode]
                    agent = ContextAwareAgent(current_api_key, current_mode, provider=current_provider, model=current_model)
                    print(f"✅ Switched to context mode: {current_mode.value}")
                    if current_mode != ContextMode.FULL:
                        print(f"⚠️ Warning: This mode intentionally disables certain features for testing")
                else:
                    print(f"❌ Invalid mode. Available: {', '.join(mode_map.keys())}")
            
            elif user_input.lower() == 'reset':
                agent.reset()
                print("✅ Agent trajectory and conversation history reset.")
            
            elif user_input.lower() == 'status':
                from config import Config
                model_name = current_model or Config.get_default_model(current_provider)
                print("\n📊 Current Configuration:")
                print(f"  Provider: {current_provider.upper()}")
                print(f"  Model: {model_name}")
                print(f"  Context Mode: {current_mode.value}")
                print(f"  Conversation History: {len(agent.conversation_history)} messages")
                print(f"  Tool Calls: {len(agent.trajectory.tool_calls)}")
                
                # API key status, derived from the registry so every selectable
                # provider reports something.
                spec = PROVIDERS.get(canonical_provider(current_provider))
                if spec is None:
                    pass
                elif not spec.requires_key:
                    print("  API Key: not required (local runtime)")
                else:
                    names = " / ".join(spec.key_vars)
                    key_status = "✅ Set" if spec.api_key() else "❌ Not set"
                    print(f"  API Key ({names}): {key_status}")
                    if not spec.api_key() and os.getenv("OPENROUTER_API_KEY"):
                        print("  Fallback: ✅ OPENROUTER_API_KEY set (routing via OpenRouter)")
            
            elif user_input:
                # Execute task
                print("\nProcessing...")
                result = agent.execute_task(user_input)
                
                print(f"\n{'='*40}")
                print(f"Terminal response completed: {_completed(result)}")
                print(f"Iterations: {result.get('iterations', 0)}")
                print(f"Tool Calls: {len(result['trajectory'].tool_calls)}")
                
                if result.get('final_answer'):
                    print(f"\nAnswer:")
                    print(result['final_answer'])
                
                if result.get('error'):
                    print(f"\nError: {result['error']}")
                    
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="上下文感知 AI Agent（第一章 实验 1.1：上下文消融实验）",
        epilog="""示例：
  # 交互模式（默认）
  python main.py

  # 运行完整消融实验（五种上下文模式对照）
  python main.py --mode ablation

  # 多案例消融对照，输出结果到指定文件
  python main.py --mode ablation --cases 3 --output my_ablation.json

  # 只对比“完整上下文”与“无历史消息”两种模式
  python main.py --mode ablation --ablation-modes full no_history

  # 单任务执行，指定上下文模式与提供商
  python main.py --mode single --task "把 1000 美元换算成欧元、英镑、日元并求平均值" \\
      --context-mode full --provider doubao
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--mode",
        choices=["single", "ablation", "interactive"],
        default="interactive",
        help="运行模式：single=单任务，ablation=消融实验，interactive=交互式（默认）"
    )
    parser.add_argument(
        "--task",
        type=str,
        help="要执行的任务/问题（用于 single 模式；不提供则从示例任务中选择）"
    )
    parser.add_argument(
        "--context-mode",
        choices=["full", "no_history", "no_reasoning", "no_tool_calls", "no_tool_results"],
        default="full",
        help="single 模式下的上下文模式：full=完整；no_history=无历史消息；"
             "no_reasoning=无思考过程；no_tool_calls=无工具定义；no_tool_results=无工具执行结果"
    )
    parser.add_argument(
        "--ablation-modes",
        nargs="+",
        choices=["full", "no_history", "no_reasoning", "no_tool_calls", "no_tool_results"],
        help="消融实验中要测试的上下文模式（默认测试全部五种）"
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=1,
        help="消融实验运行的案例数量（默认 1；>1 时在多个示例任务上做跨模式对照）"
    )
    parser.add_argument(
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        default="doubao",
        help="LLM 提供商（默认：doubao；openrouter 或缺失主 key 时经 OpenRouter 兜底；ollama 为本地免费）"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="使用的模型名称（可选，不指定则使用该提供商的默认模型）"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="LLM 提供商的 API Key（也可通过环境变量 SILICONFLOW_API_KEY/ARK_API_KEY/MOONSHOT_API_KEY/DEEPSEEK_API_KEY/ZHIPU_API_KEY 设置；缺失主 key 时可用 OPENROUTER_API_KEY 兜底）"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="结果输出文件路径（single 模式为 JSON 结果，ablation 模式为原始结果 JSON）"
    )

    args = parser.parse_args()
    
    # The registry knows each provider's key variables, the OpenRouter fallback
    # and which providers need no key at all, so resolve through it rather than
    # maintaining a per-provider chain here. An explicit --api-key still wins.
    try:
        backend = resolve_backend(args.provider, model=args.model, api_key=args.api_key)
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    api_key = args.api_key or ""
    if backend.using_openrouter and not args.api_key:
        logger.info(
            f"{args.provider} API key not set; falling back to OpenRouter "
            "(OPENROUTER_API_KEY). Set the provider key to use it directly."
        )
    elif not args.api_key:
        # Pass the resolved key through; ContextAwareAgent re-resolves and an
        # empty value would send it down the fallback path instead.
        api_key = backend.api_key
    
    # Log provider info
    logger.info(f"Using provider: {args.provider}, model: {args.model or 'default'}")
    
    # Execute based on mode
    if args.mode == "single":
        if not args.task:
            # Prompt user to select a sample task
            print("\n" + "="*60)
            print("SINGLE TASK MODE - No task provided")
            print("="*60)
            
            # Ensure PDFs exist
            ensure_sample_pdfs()
            
            # Get and display sample tasks
            sample_tasks = get_sample_tasks()
            print("\n📋 Available sample tasks:")
            for i, sample in enumerate(sample_tasks, 1):
                print(f"\n{i}. {sample['name']}")
                print(f"   {sample['description']}")
            
            print("\n" + "="*60)
            try:
                choice = input("\nSelect a task number (1-{}) or 'q' to quit: ".format(len(sample_tasks))).strip()
                if choice.lower() == 'q':
                    sys.exit(0)
                
                task_num = int(choice)
                if 1 <= task_num <= len(sample_tasks):
                    selected_task = sample_tasks[task_num - 1]
                    print(f"\n✅ Selected: {selected_task['name']}")
                    print("\nTask details:")
                    print("-"*40)
                    print(selected_task['task'])
                    print("-"*40)
                    
                    confirm = input("\nRun this task? (y/n): ").strip().lower()
                    if confirm == 'y':
                        run_single_task(api_key, selected_task['task'], args.context_mode,
                                      provider=args.provider, model=args.model, output=args.output)
                    else:
                        print("Task cancelled.")
                else:
                    print(f"Invalid selection. Please choose 1-{len(sample_tasks)}")
                    sys.exit(1)
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)
        else:
            run_single_task(api_key, args.task, args.context_mode,
                          provider=args.provider, model=args.model, output=args.output)

    elif args.mode == "ablation":
        run_ablation_study(api_key, provider=args.provider, model=args.model,
                          context_modes=args.ablation_modes, num_cases=args.cases,
                          output=args.output)
    
    else:  # interactive
        interactive_mode(api_key, provider=args.provider, model=args.model)


if __name__ == "__main__":
    main()
