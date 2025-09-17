"""Main script to run user memory evaluation tests."""

import argparse
import json
from typing import Dict, Optional
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

from framework import UserMemoryEvaluationFramework, TestCaseExporter
from evaluator import LLMEvaluator, BatchEvaluator
from models import TestCase, EvaluationResult

console = Console()


class InteractiveEvaluator:
    """Interactive interface for testing agents with the evaluation framework."""
    
    def __init__(self, framework: UserMemoryEvaluationFramework):
        self.framework = framework
        self.results = {}
        
    def run_interactive_session(self):
        """Run an interactive evaluation session."""
        console.print("[bold cyan]User Memory Evaluation Framework[/bold cyan]")
        console.print("=" * 50)
        
        while True:
            console.print("\n[bold]Options:[/bold]")
            console.print("1. List all test cases")
            console.print("2. View test case details")
            console.print("3. Run single test case")
            console.print("4. Run batch evaluation")
            console.print("5. View evaluation results")
            console.print("6. Generate report")
            console.print("7. Export test cases")
            console.print("8. Exit")
            
            choice = Prompt.ask("Select an option", choices=["1","2","3","4","5","6","7","8"])
            
            if choice == "1":
                self.list_test_cases()
            elif choice == "2":
                self.view_test_case()
            elif choice == "3":
                self.run_single_test()
            elif choice == "4":
                self.run_batch_evaluation()
            elif choice == "5":
                self.view_results()
            elif choice == "6":
                self.generate_report()
            elif choice == "7":
                self.export_test_cases()
            elif choice == "8":
                if Confirm.ask("Are you sure you want to exit?"):
                    break
    
    def list_test_cases(self):
        """List all available test cases."""
        console.print("\n[bold]Available Test Cases:[/bold]")
        # Show all test cases with full titles organized by category
        self.framework.display_test_case_summary(show_full_titles=True, by_category=True)
        
    def view_test_case(self):
        """View details of a specific test case."""
        test_id = Prompt.ask("Enter test case ID")
        self.framework.display_test_case_detail(test_id)
        
    def run_single_test(self):
        """Run a single test case."""
        test_id = Prompt.ask("Enter test case ID to run")
        test_case = self.framework.get_test_case(test_id)
        
        if not test_case:
            console.print(f"[red]Test case {test_id} not found![/red]")
            return
        
        # Display conversation histories
        console.print(f"\n[bold]Test Case: {test_case.title}[/bold]")
        console.print(f"Category: {test_case.category}")
        console.print(f"\n[yellow]Conversation Histories:[/yellow]")
        
        for i, history in enumerate(test_case.conversation_histories, 1):
            console.print(f"\nConversation {i}: {history.conversation_id}")
            console.print(f"Business: {history.metadata.get('business', 'N/A')}")
            console.print(f"Rounds: {history.rounds}")
            
            if Confirm.ask(f"View conversation {i} details?", default=False):
                for msg in history.messages[:10]:  # Show first 10 messages
                    role_color = "cyan" if msg.role == "user" else "green"
                    console.print(f"[{role_color}]{msg.role}:[/{role_color}] {msg.content[:100]}...")
                console.print(f"... ({len(history.messages)} total messages)")
        
        # Display the user question
        console.print(f"\n[bold yellow]User Question:[/bold yellow]")
        console.print(test_case.user_question)
        
        # Get agent response
        console.print("\n[bold]Enter your agent's response:[/bold]")
        console.print("[dim](Paste your agent's response, then press Enter twice to submit)[/dim]")
        
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        
        agent_response = "\n".join(lines[:-1])  # Remove last empty line
        
        # Optional: Get extracted memory
        if Confirm.ask("Do you want to provide extracted memory separately?", default=False):
            console.print("[bold]Enter extracted memory:[/bold]")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            extracted_memory = "\n".join(lines[:-1])
        else:
            extracted_memory = None
        
        # Evaluate
        console.print("\n[cyan]Evaluating response...[/cyan]")
        result = self.framework.submit_and_evaluate(
            test_id, 
            agent_response, 
            extracted_memory
        )
        
        if result:
            self.results[test_id] = result
            self._display_result(result)
        
    def run_batch_evaluation(self):
        """Run batch evaluation on multiple test cases."""
        category = Prompt.ask(
            "Select category to evaluate",
            choices=["all", "layer1", "layer2", "layer3"],
            default="all"
        )
        
        if category == "all":
            category = None
        
        # Get test cases
        test_cases = self.framework.list_test_cases(category)
        console.print(f"\n[cyan]Found {len(test_cases)} test cases to evaluate[/cyan]")
        
        # Load agent responses from file
        file_path = Prompt.ask("Enter path to JSON file with agent responses")
        
        try:
            with open(file_path, 'r') as f:
                agent_responses = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading file: {e}[/red]")
            return
        
        # Run batch evaluation
        console.print("\n[cyan]Running batch evaluation...[/cyan]")
        results = self.framework.evaluate_batch(
            agent_responses,
            category=category
        )
        
        self.results.update(results)
        console.print(f"[green]Evaluated {len(results)} test cases[/green]")
        
    def view_results(self):
        """View evaluation results."""
        if not self.results:
            console.print("[yellow]No evaluation results available yet[/yellow]")
            return
        
        for test_id, result in self.results.items():
            console.print(f"\n[bold]{test_id}:[/bold]")
            self._display_result(result)
            
    def generate_report(self):
        """Generate and save evaluation report."""
        if not self.results:
            console.print("[yellow]No results to report[/yellow]")
            return
        
        output_file = Prompt.ask(
            "Enter output file path for report",
            default="evaluation_report.txt"
        )
        
        report = self.framework.generate_report(self.results, output_file)
        console.print(f"\n[green]Report saved to {output_file}[/green]")
        
        if Confirm.ask("Display report in console?"):
            console.print("\n" + report)
            
    def export_test_cases(self):
        """Export test cases to different formats."""
        format_choice = Prompt.ask(
            "Select export format",
            choices=["json", "markdown"]
        )
        
        output_file = Prompt.ask(
            f"Enter output file path",
            default=f"test_cases.{format_choice if format_choice == 'json' else 'md'}"
        )
        
        test_cases = self.framework.list_test_cases()
        
        if format_choice == "json":
            TestCaseExporter.export_to_json(test_cases, output_file)
        else:
            TestCaseExporter.export_to_markdown(test_cases, output_file)
            
        console.print(f"[green]Exported {len(test_cases)} test cases to {output_file}[/green]")
    
    def _display_result(self, result: EvaluationResult):
        """Display a single evaluation result."""
        # Use reward for determining pass/fail if passed is not explicitly set
        is_passed = result.passed if result.passed is not None else result.reward >= 0.6
        status_color = "green" if is_passed else "red"
        console.print(f"[{status_color}]Status: {'PASSED' if is_passed else 'FAILED'}[/{status_color}]")
        console.print(f"Reward: {result.reward:.3f}/1.000")
        console.print(f"Reasoning: {result.reasoning}")
        
        if result.required_info_found:
            console.print("Required Information Found:")
            for info, found in result.required_info_found.items():
                check = "✓" if found else "✗"
                color = "green" if found else "red"
                console.print(f"  [{color}]{check}[/{color}] {info}")
        
        if result.suggestions:
            console.print(f"[yellow]Suggestions: {result.suggestions}[/yellow]")


def run_demo_evaluation():
    """Run a demonstration evaluation with sample agent responses."""
    console.print("[bold cyan]Running Demo Evaluation[/bold cyan]")
    console.print("=" * 50)
    
    framework = UserMemoryEvaluationFramework()
    
    # Sample agent responses for demo
    sample_responses = {
        "layer1_01_bank_account": "Your checking account number is 4429853327.",
        "layer1_02_insurance_claim": "Your claim number is CLM-2024-894327 and adjuster Patricia Wong will call within 24-48 hours.",
        "layer2_01_multiple_vehicles": "I see you have a Honda Accord with service scheduled for Friday, November 24th at 8 AM at Firestone. You also have a Tesla Model 3 that was discussed but no service was scheduled. Which vehicle did you want to schedule service for?",
        "layer3_01_travel_coordination": "For your Tokyo trip in January, there's an urgent issue: your passport expires on February 18, 2025, which is less than a month after your return. You should renew it immediately since expedited processing takes 2-3 weeks. Once renewed, update your passport number with Delta (confirmation DELTA-JMK892). Your Chase Sapphire Reserve is ready for international use with no foreign fees, and you have Priority Pass for lounge access."
    }
    
    # Run evaluations
    results = {}
    for test_id, response in sample_responses.items():
        test_case = framework.get_test_case(test_id)
        if test_case:
            console.print(f"\n[cyan]Evaluating: {test_case.title}[/cyan]")
            result = framework.submit_and_evaluate(test_id, response)
            if result:
                results[test_id] = result
                is_passed = result.passed if result.passed is not None else result.reward >= 0.6
                status = "✓ PASSED" if is_passed else "✗ FAILED"
                console.print(f"{status} (Reward: {result.reward:.3f})")
    
    # Generate summary report
    if results:
        console.print("\n" + "=" * 50)
        report = framework.generate_report(results)
        console.print(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="User Memory Evaluation Framework")
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo", "batch"],
        default="interactive",
        help="Evaluation mode"
    )
    parser.add_argument(
        "--responses",
        type=str,
        help="Path to JSON file with agent responses (for batch mode)"
    )
    parser.add_argument(
        "--category",
        choices=["layer1", "layer2", "layer3"],
        help="Filter test cases by category"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_report.txt",
        help="Output file for evaluation report"
    )
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = UserMemoryEvaluationFramework()
    
    if args.mode == "demo":
        run_demo_evaluation()
    elif args.mode == "interactive":
        evaluator = InteractiveEvaluator(framework)
        evaluator.run_interactive_session()
    elif args.mode == "batch":
        if not args.responses:
            console.print("[red]Batch mode requires --responses file path[/red]")
            return
        
        with open(args.responses, 'r') as f:
            agent_responses = json.load(f)
        
        results = framework.evaluate_batch(
            agent_responses,
            category=args.category
        )
        
        report = framework.generate_report(results, args.output)
        console.print(f"[green]Report saved to {args.output}[/green]")
        console.print(f"Evaluated {len(results)} test cases")
        
        # Summary statistics
        passed = sum(1 for r in results.values() if r.passed)
        console.print(f"Passed: {passed}/{len(results)} ({100*passed/len(results):.1f}%)")


if __name__ == "__main__":
    main()
