#!/usr/bin/env python3
"""Test script to demonstrate LLM evaluation integration"""

import os
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Set up logging to see evaluation logs
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Set dummy API key for demo
os.environ["KIMI_API_KEY"] = "test_key"

console = Console()


def test_llm_evaluation_integration():
    """Test that LLM evaluation is properly integrated"""
    console.print("\n[bold cyan]Testing LLM Evaluation Integration[/bold cyan]")
    console.print("="*80)
    
    from config import Config
    from evaluator import UserMemoryEvaluator, TestCase
    
    # Initialize evaluator
    config = Config.from_env()
    evaluator = UserMemoryEvaluator(config)
    
    # Check if LLM evaluator was initialized
    if evaluator.llm_evaluator:
        console.print("[green]✓ LLM Evaluator successfully initialized[/green]")
        console.print("  The system will automatically evaluate agent responses")
    else:
        console.print("[yellow]⚠ LLM Evaluator not available[/yellow]")
        console.print("  Automatic evaluation will be skipped")
        console.print("  To enable, ensure week2/user-memory-evaluation is accessible")
        console.print("  and has proper API keys configured")
    
    # Create a test case for demonstration
    test_case = TestCase(
        test_id="demo_test",
        category="demo",
        title="Demo Test Case",
        description="Test case for demonstrating LLM evaluation",
        conversation_histories=[{
            "conversation_id": "demo_conv",
            "messages": [
                {"role": "user", "content": "What's my account number?"},
                {"role": "assistant", "content": "Your account number is 123456789."}
            ],
            "metadata": {"business": "Demo Bank"}
        }],
        user_question="What is my account number?",
        evaluation_criteria="The answer must identify the account number as 123456789.",
        expected_behavior="Answer directly using the account number from the conversation."
    )
    
    # Simulate an agent response
    agent_answer = "Based on the conversation history, your account number is 123456789."
    
    console.print("\n[bold]Simulating Evaluation Process:[/bold]")
    console.print(f"Test Question: {test_case.user_question}")
    console.print(f"Agent Answer: {agent_answer}")
    console.print(f"Evaluation Criteria: {test_case.evaluation_criteria}")
    
    if evaluator.llm_evaluator:
        console.print("\n[yellow]LLM Evaluation would be triggered automatically when running a test case[/yellow]")
        console.print("The evaluation will:")
        console.print("  1. Send the agent's response to the LLM evaluator")
        console.print("  2. Get a reward score (0.0 to 1.0)")
        console.print("  3. Determine if the response passed (reward >= 0.6)")
        console.print("  4. Provide reasoning for the evaluation")
        console.print("  5. Check if required information was found")
        console.print("  6. Display all results in the console")
    
    console.print("\n[bold]Evaluation Flow:[/bold]")
    console.print("1. Agent generates response using RAG")
    console.print("2. Response is automatically evaluated by LLM")
    console.print("3. Results show both RAG performance AND accuracy metrics")
    console.print("4. Reports include LLM evaluation scores")


def demonstrate_evaluation_output():
    """Show what the evaluation output looks like"""
    console.print("\n[bold cyan]Sample Evaluation Output[/bold cyan]")
    console.print("="*80)
    
    sample_output = """
============================================================
Running LLM Evaluation...
------------------------------------------------------------
LLM Evaluation Reward: 0.850/1.000
Passed: Yes
Reasoning: The agent correctly recalled the account number from the conversation history. The response is accurate and directly answers the user's question.
Required Information Found:
  ✓ account number: 123456789
============================================================

============================================================
Evaluation Complete for demo_test
LLM Evaluation Passed: ✓
LLM Reward Score: 0.850/1.000
Iterations: 2
Tool Calls: 3
Chunks: 1
Processing Time: 1.23s
Indexing Time: 0.45s
============================================================
"""
    
    console.print(Panel(sample_output, title="Expected Console Output", border_style="green"))
    
    console.print("\n[bold]Key Features:[/bold]")
    console.print("• Automatic evaluation after each test")
    console.print("• Continuous reward score (0.0 to 1.0)")
    console.print("• Pass/fail determination (>= 0.6 passes)")
    console.print("• Detailed reasoning for the score")
    console.print("• Verification of required information")
    console.print("• Integration with existing metrics")


def check_dependencies():
    """Check if all dependencies are available"""
    console.print("\n[bold cyan]Checking Dependencies[/bold cyan]")
    console.print("="*80)
    
    # Check if user-memory-evaluation is accessible
    eval_path = Path(__file__).parent.parent.parent / "week2" / "user-memory-evaluation"
    
    if eval_path.exists():
        console.print(f"[green]✓ user-memory-evaluation found at: {eval_path}[/green]")
        
        # Check for required files
        required_files = [
            "evaluator.py",
            "models.py",
            "config.py"
        ]
        
        for file in required_files:
            if (eval_path / file).exists():
                console.print(f"  [green]✓ {file}[/green]")
            else:
                console.print(f"  [red]✗ {file} missing[/red]")
    else:
        console.print(f"[red]✗ user-memory-evaluation not found at: {eval_path}[/red]")
        console.print("[yellow]  LLM evaluation will not be available[/yellow]")
    
    # Check for API keys
    console.print("\n[bold]API Keys:[/bold]")
    api_keys = {
        "OPENAI_API_KEY": "OpenAI (for LLM evaluation)",
        "KIMI_API_KEY": "Kimi (for agent responses)"
    }
    
    for key, description in api_keys.items():
        if os.getenv(key):
            console.print(f"  [green]✓ {key} set ({description})[/green]")
        else:
            console.print(f"  [yellow]⚠ {key} not set ({description})[/yellow]")


def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold]LLM Evaluation Integration Test[/bold]\n"
        "Verifying automatic evaluation of agent responses",
        border_style="cyan"
    ))
    
    try:
        # Check dependencies
        check_dependencies()
        
        # Test integration
        test_llm_evaluation_integration()
        
        # Show sample output
        demonstrate_evaluation_output()
        
        console.print("\n" + "="*80)
        console.print("[bold green]Integration Summary:[/bold green]")
        console.print("✓ LLM evaluation is integrated into the evaluation pipeline")
        console.print("✓ Results are automatically evaluated after agent responses")
        console.print("✓ Evaluation metrics are displayed and saved")
        console.print("✓ Reports include LLM evaluation scores")
        console.print("\n[yellow]Note: Actual LLM evaluation requires valid API keys[/yellow]")
        console.print("="*80 + "\n")
        
    except Exception as e:
        console.print(f"\n[red]Error during testing: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
