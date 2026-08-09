#!/usr/bin/env python3
"""Quick start script for Agentic RAG User Memory Evaluation

This script provides a simple demo to get started with the system.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Check for required environment variables
console = Console()


def check_environment():
    """Check if required environment variables are set"""
    required_vars = []
    optional_vars = []
    
    # Check for OpenAI API key (required for embeddings)
    if not os.getenv("OPENAI_API_KEY"):
        required_vars.append("OPENAI_API_KEY (required for embeddings)")
    
    # Check for at least one LLM provider
    llm_providers = [
        "KIMI_API_KEY",
        "DASHSCOPE_API_KEY",
        "SILICONFLOW_API_KEY", 
        "DOUBAO_API_KEY",
        "OPENROUTER_API_KEY"
    ]
    
    if not any(os.getenv(key) for key in llm_providers):
        required_vars.append("At least one LLM provider API key (KIMI_API_KEY recommended)")
    
    if required_vars:
        console.print(Panel(
            "[bold red]Missing Required Environment Variables[/bold red]\n\n" +
            "\n".join(f"• {var}" for var in required_vars) +
            "\n\n[yellow]Please set up your .env file:[/yellow]\n" +
            "1. Copy env.example to .env\n" +
            "2. Add your API keys\n" +
            "3. Run this script again",
            border_style="red"
        ))
        return False
    
    return True


def run_quick_demo():
    """Run a quick demonstration"""
    from config import Config
    from evaluator import UserMemoryEvaluator
    
    console.print(Panel.fit(
        "[bold cyan]Agentic RAG for User Memory - Quick Start Demo[/bold cyan]\n"
        "This demo will:\n"
        "1. Load a simple test case\n"
        "2. Chunk the conversation history\n"
        "3. Build a RAG index\n"
        "4. Answer a question using the indexed memory",
        border_style="cyan"
    ))
    
    console.print("\n[yellow]Initializing system...[/yellow]")
    
    # Create configuration with demo settings
    config = Config.from_env()
    config.chunking.rounds_per_chunk = 10  # Smaller chunks for demo
    config.evaluation.max_iterations = 5   # Fewer iterations for speed
    config.agent.enable_reasoning = True   # Show reasoning process
    
    # Initialize evaluator
    evaluator = UserMemoryEvaluator(config)
    
    # Load test cases (just layer1 for demo)
    console.print("\n[yellow]Loading test cases...[/yellow]")
    test_cases = evaluator.load_test_cases("layer1")
    
    if not test_cases:
        console.print("[red]No test cases found. Please check the path to week2/user-memory-evaluation[/red]")
        return
    
    # Use the first test case
    test_case = test_cases[0]
    test_id = test_case.test_id
    
    console.print(f"\n[green]Selected test case:[/green] {test_case.title}")
    console.print(f"[green]Question:[/green] {test_case.user_question}\n")
    
    # Evaluate the test case
    console.print("[yellow]Processing conversation history...[/yellow]")
    console.print("• Chunking conversations into segments")
    console.print("• Building search indexes")
    console.print("• Preparing RAG agent\n")
    
    result = evaluator.evaluate_test_case(test_id)
    
    # Display results
    console.print("\n" + "="*60)
    console.print("[bold green]Demo Results[/bold green]")
    console.print("="*60)
    
    console.print(f"\n[bold]Agent's Answer:[/bold]")
    console.print(Panel(result.agent_answer, border_style="cyan"))
    
    console.print(f"\n[bold]Expected Answer:[/bold]")
    console.print(Panel(result.expected_answer, border_style="green"))
    
    console.print(f"\n[bold]Performance Metrics:[/bold]")
    console.print(f"• Success: {'✓ Yes' if result.success else '✗ No'}")
    console.print(f"• Iterations: {result.iterations}")
    console.print(f"• Tool Calls: {result.tool_calls}")
    console.print(f"• Chunks Created: {result.chunk_count}")
    console.print(f"• Processing Time: {result.processing_time:.2f} seconds")
    console.print(f"• Indexing Time: {result.indexing_time:.2f} seconds")
    
    console.print("\n[bold cyan]Demo Complete![/bold cyan]")
    console.print("\nTo explore more:")
    console.print("• Run [bold]python main.py[/bold] for interactive mode")
    console.print("• Run [bold]python main.py --mode batch --category layer1[/bold] for batch evaluation")
    console.print("• Check the README.md for detailed documentation")


def main():
    """Main entry point"""
    console.print("\n[bold]Agentic RAG for User Memory Evaluation - Quick Start[/bold]\n")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check if .env file exists
    if not Path(".env").exists() and Path("env.example").exists():
        console.print("[yellow]Creating .env file from env.example...[/yellow]")
        import shutil
        shutil.copy("env.example", ".env")
        console.print("[red]Please edit .env file with your API keys and run again.[/red]")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the demo
    try:
        run_quick_demo()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error during demo: {e}[/red]")
        console.print("[yellow]Please check your configuration and try again[/yellow]")
        import traceback
        if os.getenv("DEBUG"):
            traceback.print_exc()


if __name__ == "__main__":
    main()
