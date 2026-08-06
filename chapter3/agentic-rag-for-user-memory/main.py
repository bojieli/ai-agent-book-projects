#!/usr/bin/env python3
"""Main entry point for Agentic RAG User Memory Evaluation System

This script provides an interactive interface for:
1. Loading test cases from the user-memory-evaluation framework
2. Chunking and indexing conversation histories
3. Evaluating the RAG agent on selected test cases
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import Config, ChunkingStrategy, IndexMode
from evaluator import UserMemoryEvaluator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for better output
console = Console()


class InteractiveRAGEvaluator:
    """Interactive interface for the RAG evaluation system"""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the interactive evaluator"""
        self.config = config or Config.from_env()
        self.evaluator = UserMemoryEvaluator(self.config)
        self.test_cases_loaded = False
        
    def run(self):
        """Run the interactive evaluation session"""
        console.print(Panel.fit(
            "[bold cyan]Agentic RAG for User Memory Evaluation[/bold cyan]\n"
            "Educational Project for Learning RAG + User Memory Systems",
            border_style="cyan"
        ))
        
        while True:
            self.show_menu()
            choice = Prompt.ask(
                "Select an option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                default="1"
            )
            
            if choice == "1":
                self.load_test_cases()
            elif choice == "2":
                self.view_test_cases()
            elif choice == "3":
                self.configure_settings()
            elif choice == "4":
                self.evaluate_single_test()
            elif choice == "5":
                self.evaluate_category()
            elif choice == "6":
                self.evaluate_all()
            elif choice == "7":
                self.view_results()
            elif choice == "8":
                self.generate_report()
            elif choice == "9":
                self.demo_mode()
            elif choice == "0":
                if Confirm.ask("Are you sure you want to exit?"):
                    console.print("[yellow]Goodbye![/yellow]")
                    break
    
    def show_menu(self):
        """Display the main menu"""
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("1. Load Test Cases")
        console.print("2. View Loaded Test Cases")
        console.print("3. Configure Settings")
        console.print("4. Evaluate Single Test Case")
        console.print("5. Evaluate by Category")
        console.print("6. Evaluate All Test Cases")
        console.print("7. View Results")
        console.print("8. Generate Report")
        console.print("9. Demo Mode (Quick Test)")
        console.print("0. Exit")
    
    def load_test_cases(self):
        """Load test cases from the evaluation framework"""
        console.print("\n[cyan]Loading test cases...[/cyan]")
        
        category = Prompt.ask(
            "Select category to load",
            choices=["all", "layer1", "layer2", "layer3"],
            default="all"
        )
        
        category_filter = None if category == "all" else category
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading test cases...", total=None)
            test_cases = self.evaluator.load_test_cases(category_filter)
            progress.update(task, completed=True)
        
        self.test_cases_loaded = True
        console.print(f"[green]✓ Loaded {len(test_cases)} test cases[/green]")
        
        # Show summary
        categories = {}
        for test_id in test_cases:
            tc = self.evaluator.test_cases[test_id]
            cat = tc.category
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            console.print(f"  {cat}: {count} test cases")
    
    def view_test_cases(self):
        """View loaded test cases"""
        if not self.test_cases_loaded:
            console.print("[yellow]No test cases loaded. Please load test cases first.[/yellow]")
            return
        
        # Create table
        table = Table(title="Loaded Test Cases")
        table.add_column("#", style="dim", width=4)
        table.add_column("ID", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Title", style="green")
        table.add_column("Conversations", justify="right")
        
        # Sort test cases for consistent numbering
        sorted_test_cases = sorted(self.evaluator.test_cases.items())
        
        for idx, (test_id, test_case) in enumerate(sorted_test_cases, 1):
            table.add_row(
                str(idx),
                test_id,
                test_case.category,
                test_case.title[:50] + "..." if len(test_case.title) > 50 else test_case.title,
                str(len(test_case.conversation_histories))
            )
        
        console.print(table)
        
        # Option to view details
        if Confirm.ask("\nView test case details?"):
            # Build a list of test IDs for selection
            test_ids_list = list(self.evaluator.test_cases.keys())
            test_ids_list.sort()
            
            console.print("\n[dim]Enter test ID or its index number from the table above[/dim]")
            user_input = Prompt.ask("Select test case")
            
            # Check if user entered a number (1-based index from table display)
            test_id = None
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(test_ids_list):
                    test_id = test_ids_list[idx]
                else:
                    console.print(f"[red]Invalid index number: {user_input}[/red]")
                    return
            else:
                test_id = user_input
            
            if test_id in self.evaluator.test_cases:
                test_case = self.evaluator.test_cases[test_id]
                console.print(Panel(
                    f"[bold]Test Case: {test_case.title}[/bold]\n\n"
                    f"Category: {test_case.category}\n"
                    f"Description: {test_case.description}\n\n"
                    f"[yellow]User Question:[/yellow]\n{test_case.user_question}\n\n"
                    f"[green]Evaluation Criteria:[/green]\n{test_case.evaluation_criteria[:200]}...\n\n"
                    f"Conversations: {len(test_case.conversation_histories)}"
                    + (f"\nExpected Behavior: {test_case.expected_behavior[:100]}..." if test_case.expected_behavior else ""),
                    title=test_id,
                    border_style="cyan"
                ))
            else:
                console.print(f"[red]Test case {test_id} not found[/red]")
    
    def configure_settings(self):
        """Configure RAG and evaluation settings"""
        console.print("\n[bold]Configuration Settings[/bold]")
        
        # Show current settings
        console.print(f"\nCurrent Settings:")
        console.print(f"  LLM Provider: {self.config.llm.provider}")
        console.print(f"  LLM Model: {self.config.llm.model}")
        console.print(f"  Chunking Strategy: {self.config.chunking.strategy}")
        console.print(f"  Rounds per Chunk: {self.config.chunking.rounds_per_chunk}")
        console.print(f"  Index Mode: {self.config.index.mode}")
        console.print(f"  Max Iterations: {self.config.evaluation.max_iterations}")
        
        if Confirm.ask("\nModify settings?"):
            # Chunking settings
            if Confirm.ask("Modify chunking settings?"):
                rounds = Prompt.ask(
                    "Rounds per chunk",
                    default=str(self.config.chunking.rounds_per_chunk)
                )
                self.config.chunking.rounds_per_chunk = int(rounds)
                
                overlap = Prompt.ask(
                    "Overlap rounds",
                    default=str(self.config.chunking.overlap_rounds)
                )
                self.config.chunking.overlap_rounds = int(overlap)
            
            # Index settings
            if Confirm.ask("Modify index settings?"):
                mode = Prompt.ask(
                    "Index mode",
                    choices=["dense", "sparse", "hybrid"],
                    default=self.config.index.mode
                )
                self.config.index.mode = IndexMode(mode)
            
            # Agent settings
            if Confirm.ask("Modify agent settings?"):
                max_iter = Prompt.ask(
                    "Max iterations",
                    default=str(self.config.evaluation.max_iterations)
                )
                self.config.evaluation.max_iterations = int(max_iter)
                
                self.config.agent.enable_reasoning = Confirm.ask(
                    "Enable reasoning output?",
                    default=self.config.agent.enable_reasoning
                )
            
            # Save configuration
            if Confirm.ask("Save configuration to file?"):
                config_file = Prompt.ask("Config file path", default="config.json")
                self.config.save(config_file)
                console.print(f"[green]Configuration saved to {config_file}[/green]")
    
    def evaluate_single_test(self):
        """Evaluate a single test case"""
        if not self.test_cases_loaded:
            console.print("[yellow]No test cases loaded. Please load test cases first.[/yellow]")
            return
        
        # Show available test cases for selection
        console.print("\n[bold]Available Test Cases:[/bold]")
        
        # Group by category for better organization
        categories = {}
        for test_id, test_case in self.evaluator.test_cases.items():
            cat = test_case.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((test_id, test_case.title))
        
        # Display test cases by category
        test_ids_list = []
        for cat in sorted(categories.keys()):
            console.print(f"\n[cyan]{cat.upper()}:[/cyan]")
            for test_id, title in sorted(categories[cat]):
                test_ids_list.append(test_id)
                # Show index number for easier selection
                idx = len(test_ids_list)
                console.print(f"  [{idx}] {test_id}: {title[:60]}...")
        
        console.print("\n[dim]Enter test ID directly or number from the list above[/dim]")
        
        # Allow user to enter either test ID or number
        user_input = Prompt.ask("Select test case")
        
        # Check if user entered a number
        test_id = None
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(test_ids_list):
                test_id = test_ids_list[idx]
            else:
                console.print(f"[red]Invalid selection number: {user_input}[/red]")
                return
        else:
            # User entered a test ID directly
            test_id = user_input
            if test_id not in self.evaluator.test_cases:
                console.print(f"[red]Test case {test_id} not found[/red]")
                return
        
        test_case = self.evaluator.test_cases[test_id]
        console.print(f"\n[cyan]Evaluating: {test_case.title}[/cyan]")
        console.print(f"Question: {test_case.user_question}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            
            try:
                result = self.evaluator.evaluate_test_case(test_id)
                progress.update(task, completed=True)
                
                # Display result
                status = "✓ Success" if result.success else "✗ Failed"
                console.print(f"\n[{'green' if result.success else 'red'}]{status}[/{'green' if result.success else 'red'}]")
                
                console.print("\nAgent Answer:")
                console.print(Panel(result.agent_answer, border_style="cyan"))
                
                console.print("\nEvaluation Criteria:")
                console.print(Panel(result.evaluation_criteria, border_style="green"))
                
                # Display LLM evaluation if available
                if hasattr(result, 'llm_evaluation') and result.llm_evaluation and 'reward' in result.llm_evaluation:
                    console.print("\nLLM Evaluation:")
                    llm_eval = result.llm_evaluation
                    eval_color = "green" if llm_eval['passed'] else "red"
                    console.print(f"  [{'green' if llm_eval['passed'] else 'red'}]Passed: {'Yes' if llm_eval['passed'] else 'No'}[/{eval_color}]")
                    console.print(f"  Reward Score: {llm_eval['reward']:.3f}/1.000")
                    console.print(f"  Reasoning: {llm_eval.get('reasoning', 'N/A')}")
                    
                    if llm_eval.get('required_info_found'):
                        console.print("\n  Required Information:")
                        for info, found in llm_eval['required_info_found'].items():
                            check = "[green]✓[/green]" if found else "[red]✗[/red]"
                            console.print(f"    {check} {info}")
                
                console.print(f"\nStatistics:")
                console.print(f"  Iterations: {result.iterations}")
                console.print(f"  Tool Calls: {result.tool_calls}")
                console.print(f"  Chunks Indexed: {result.chunk_count}")
                console.print(f"  Processing Time: {result.processing_time:.2f}s")
                console.print(f"  Indexing Time: {result.indexing_time:.2f}s")
                
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"Error: {e}")
    
    def evaluate_category(self):
        """Evaluate all test cases in a category"""
        if not self.test_cases_loaded:
            console.print("[yellow]No test cases loaded. Please load test cases first.[/yellow]")
            return
        
        # Show available categories and count
        categories_count = {}
        for test_case in self.evaluator.test_cases.values():
            cat = test_case.category
            categories_count[cat] = categories_count.get(cat, 0) + 1
        
        console.print("\n[bold]Available Categories:[/bold]")
        for cat in sorted(categories_count.keys()):
            console.print(f"  {cat}: {categories_count[cat]} test cases")
        
        category = Prompt.ask(
            "\nSelect category",
            choices=list(sorted(categories_count.keys()))
        )
        
        # Get and display test cases in category
        test_ids = []
        console.print(f"\n[cyan]Test cases in {category}:[/cyan]")
        for tid, tc in sorted(self.evaluator.test_cases.items()):
            if tc.category == category:
                test_ids.append(tid)
                console.print(f"  • {tid}: {tc.title[:60]}...")
        
        console.print(f"\n[cyan]Total: {len(test_ids)} test cases[/cyan]")
        
        if not Confirm.ask("Proceed with evaluation?"):
            return
        
        # Evaluate
        with Progress(console=console) as progress:
            task = progress.add_task(f"Evaluating {category}...", total=len(test_ids))
            
            for test_id in test_ids:
                try:
                    self.evaluator.evaluate_test_case(test_id)
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Error evaluating {test_id}: {e}[/red]")
                    progress.advance(task)
        
        console.print(f"[green]✓ Evaluation complete for {category}[/green]")
        self.show_category_results(category)
    
    def evaluate_all(self):
        """Evaluate all loaded test cases"""
        if not self.test_cases_loaded:
            console.print("[yellow]No test cases loaded. Please load test cases first.[/yellow]")
            return
        
        total = len(self.evaluator.test_cases)
        console.print(f"\n[cyan]Will evaluate {total} test cases[/cyan]")
        
        if not Confirm.ask("Proceed with full evaluation?"):
            return
        
        # Evaluate all
        results = self.evaluator.evaluate_batch()
        
        console.print(f"[green]✓ Evaluated {len(results)} test cases[/green]")
        
        # Show summary
        successful = sum(1 for r in results.values() if r.success)
        console.print(f"Success rate: {successful}/{total} ({100*successful/total:.1f}%)")
    
    def view_results(self):
        """View evaluation results"""
        if not self.evaluator.results:
            console.print("[yellow]No evaluation results available[/yellow]")
            return
        
        # Create results table
        table = Table(title="Evaluation Results")
        table.add_column("Test ID", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Iterations", justify="right")
        table.add_column("Tool Calls", justify="right")
        table.add_column("Time (s)", justify="right")
        
        for test_id, result in sorted(self.evaluator.results.items()):
            test_case = self.evaluator.test_cases.get(test_id)
            category = test_case.category if test_case else "unknown"
            status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
            
            table.add_row(
                test_id,
                category,
                status,
                str(result.iterations),
                str(result.tool_calls),
                f"{result.processing_time:.2f}"
            )
        
        console.print(table)
        
        # Summary statistics
        total = len(self.evaluator.results)
        successful = sum(1 for r in self.evaluator.results.values() if r.success)
        
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total: {total}")
        console.print(f"  Successful: {successful} ({100*successful/total:.1f}%)")
        
        # Option to view details
        if Confirm.ask("\nView detailed result?"):
            test_id = Prompt.ask("Enter test case ID")
            if test_id in self.evaluator.results:
                result = self.evaluator.results[test_id]
                console.print(Panel(
                    f"[bold]Test: {test_id}[/bold]\n\n"
                    f"Status: {'Success' if result.success else 'Failed'}\n"
                    f"Iterations: {result.iterations}\n"
                    f"Tool Calls: {result.tool_calls}\n"
                    f"Chunks: {result.chunk_count}\n"
                    f"Processing Time: {result.processing_time:.2f}s\n"
                    f"Indexing Time: {result.indexing_time:.2f}s\n\n"
                    f"[yellow]Agent Answer:[/yellow]\n{result.agent_answer[:300]}...",
                    border_style="cyan"
                ))
    
    def show_category_results(self, category: str):
        """Show results for a specific category"""
        category_results = {
            tid: r for tid, r in self.evaluator.results.items()
            if tid in self.evaluator.test_cases and 
            self.evaluator.test_cases[tid].category == category
        }
        
        if not category_results:
            console.print(f"[yellow]No results for {category}[/yellow]")
            return
        
        successful = sum(1 for r in category_results.values() if r.success)
        total = len(category_results)
        
        console.print(f"\n[bold]{category} Results:[/bold]")
        console.print(f"  Success Rate: {successful}/{total} ({100*successful/total:.1f}%)")
        
        # Average metrics
        if total > 0:
            avg_iter = sum(r.iterations for r in category_results.values()) / total
            avg_tools = sum(r.tool_calls for r in category_results.values()) / total
            avg_time = sum(r.processing_time for r in category_results.values()) / total
            
            console.print(f"  Avg Iterations: {avg_iter:.1f}")
            console.print(f"  Avg Tool Calls: {avg_tools:.1f}")
            console.print(f"  Avg Time: {avg_time:.2f}s")
    
    def generate_report(self):
        """Generate and save evaluation report"""
        if not self.evaluator.results:
            console.print("[yellow]No results to report[/yellow]")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"results/report_{timestamp}.txt"
        
        report = self.evaluator.generate_report(report_file)
        
        console.print(f"[green]✓ Report saved to {report_file}[/green]")
        
        if Confirm.ask("Display report?"):
            console.print("\n" + report)
        
        # Save JSON results
        if Confirm.ask("Save detailed results to JSON?"):
            json_file = f"results/results_{timestamp}.json"
            self.evaluator.save_results(json_file)
            console.print(f"[green]✓ Results saved to {json_file}[/green]")
    
    def demo_mode(self):
        """Run a quick demo with a simple test case"""
        console.print("\n[cyan]Demo Mode - Quick Test[/cyan]")
        console.print("This will run a simple Layer 1 test case for demonstration.\n")
        
        # Load only layer1 test cases
        if not self.test_cases_loaded:
            console.print("Loading Layer 1 test cases...")
            test_cases = self.evaluator.load_test_cases("layer1")
            self.test_cases_loaded = True
        
        # Get first layer1 test case
        layer1_tests = [
            tid for tid, tc in self.evaluator.test_cases.items()
            if tc.category == "layer1"
        ]
        
        if not layer1_tests:
            console.print("[red]No Layer 1 test cases available[/red]")
            return
        
        test_id = layer1_tests[0]
        test_case = self.evaluator.test_cases[test_id]
        
        console.print(f"[bold]Demo Test Case:[/bold] {test_case.title}")
        console.print(f"[bold]Question:[/bold] {test_case.user_question}\n")
        
        if Confirm.ask("Run demo?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running demo...", total=None)
                
                try:
                    result = self.evaluator.evaluate_test_case(test_id)
                    progress.update(task, completed=True)
                    
                    # Display results
                    console.print("\n[bold green]Demo Complete![/bold green]\n")
                    console.print(f"[bold]Agent's Answer:[/bold]")
                    console.print(Panel(result.agent_answer, border_style="cyan"))
                    
                    console.print(f"\n[bold]Performance:[/bold]")
                    console.print(f"  Success: {'Yes' if result.success else 'No'}")
                    console.print(f"  Iterations: {result.iterations}")
                    console.print(f"  Tool Calls: {result.tool_calls}")
                    console.print(f"  Time: {result.processing_time:.2f}s")
                    
                except Exception as e:
                    progress.update(task, completed=True)
                    console.print(f"[red]Demo failed: {e}[/red]")


def _apply_cli_overrides(config: Config, args) -> Config:
    """把命令行参数覆盖到配置上（未指定的项保持默认，不改变原有行为）。"""
    if args.provider:
        config.llm.provider = args.provider
    if args.model:
        config.llm.model = args.model
    if args.index_mode:
        config.index.mode = IndexMode(args.index_mode)
    if args.backend:
        config.index.retrieval_backend = args.backend
    if args.store_path:
        config.index.index_path = args.store_path
    if args.test_cases_dir:
        config.evaluation.test_cases_dir = args.test_cases_dir
    if args.rounds_per_chunk:
        config.chunking.rounds_per_chunk = args.rounds_per_chunk
    if args.top_k:
        config.agent.max_search_results = args.top_k
    return config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="实验 3-9 · 智能体化 RAG 用户记忆评估系统",
        epilog=(
            "示例:\n"
            "  python main.py                              # 交互式菜单（默认）\n"
            "  python main.py --mode offline-demo          # 离线对比演示，无需 API / port 4242\n"
            "  python main.py --mode batch --category layer2 --backend local\n"
            "  python main.py --mode batch --test-id layer2_01_multiple_vehicles --provider openai\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", type=str,
        help="配置文件（JSON）路径"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "batch", "demo", "offline-demo"],
        default="interactive",
        help="运行模式：interactive 交互菜单（默认）/ batch 批量评估 / demo 快速演示 / offline-demo 离线检索对比"
    )
    parser.add_argument(
        "--category",
        choices=["layer1", "layer2", "layer3"],
        help="批量模式下要评估的难度层次"
    )
    parser.add_argument(
        "--test-id", type=str,
        help="指定要评估的单个用例 ID"
    )
    parser.add_argument(
        "--query", type=str,
        help="offline-demo 模式下覆盖用例自带的用户问题"
    )
    parser.add_argument(
        "--provider", type=str,
        help="LLM 提供商（如 openai / kimi / siliconflow / deepseek 等）"
    )
    parser.add_argument(
        "--model", type=str,
        help="LLM 模型名，覆盖提供商默认模型"
    )
    parser.add_argument(
        "--index-mode", choices=["dense", "sparse", "hybrid"],
        help="检索策略：dense 稠密 / sparse 稀疏(BM25) / hybrid 混合"
    )
    parser.add_argument(
        "--backend", choices=["auto", "local", "pipeline"],
        help="检索后端：auto 自动（默认，pipeline 不可用则本地）/ local 内置离线 BM25 / pipeline 外部 4242 服务"
    )
    parser.add_argument(
        "--top-k", type=int,
        help="每次记忆检索返回的记忆块数量"
    )
    parser.add_argument(
        "--rounds-per-chunk", type=int,
        help="对话历史分块时每块的轮数（默认 20）"
    )
    parser.add_argument(
        "--store-path", type=str,
        help="记忆索引的存储路径前缀（默认 indexes/memory_index）"
    )
    parser.add_argument(
        "--test-cases-dir", type=str,
        help="评估集 test_cases 目录（默认 ../user-memory-evaluation/test_cases）"
    )
    parser.add_argument(
        "--output", type=str,
        help="结果输出文件路径"
    )

    args = parser.parse_args()

    # offline-demo 模式：委托给完全离线的对比演示脚本
    if args.mode == "offline-demo":
        import offline_demo
        demo_args = offline_demo.build_parser().parse_args([])
        if args.test_id:
            demo_args.test_id = args.test_id
        if args.query:
            demo_args.query = args.query
        if args.top_k:
            demo_args.top_k = args.top_k
        if args.rounds_per_chunk:
            demo_args.rounds_per_chunk = args.rounds_per_chunk
        if args.test_cases_dir:
            demo_args.test_cases_dir = args.test_cases_dir
        if args.output:
            demo_args.output = args.output
        offline_demo.run_demo(demo_args)
        return

    # Load configuration
    config = None
    if args.config:
        config = Config.load(args.config)
    else:
        config = Config.from_env()

    # 应用命令行覆盖项
    config = _apply_cli_overrides(config, args)

    if args.mode == "interactive":
        # Interactive mode
        evaluator = InteractiveRAGEvaluator(config)
        evaluator.run()
    
    elif args.mode == "batch":
        # Batch mode
        evaluator = UserMemoryEvaluator(config)
        
        if args.test_id:
            # Evaluate single test
            evaluator.load_test_cases()
            result = evaluator.evaluate_test_case(args.test_id)
            console.print(f"Result: {'Success' if result.success else 'Failed'}")
        else:
            # Evaluate category or all
            evaluator.load_test_cases(args.category)
            results = evaluator.evaluate_batch(category=args.category)
            
            # Generate report
            report_file = args.output or f"results/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report = evaluator.generate_report(report_file)
            console.print(f"Report saved to {report_file}")
            
            # Summary
            total = len(results)
            successful = sum(1 for r in results.values() if r.success)
            console.print(f"Success rate: {successful}/{total} ({100*successful/total:.1f}%)")
    
    elif args.mode == "demo":
        # Demo mode
        evaluator = InteractiveRAGEvaluator(config)
        evaluator.demo_mode()


if __name__ == "__main__":
    main()
