"""
Main script to demonstrate KV cache importance
Runs the ReAct agent with different implementations and compares performance
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any
from datetime import datetime
from agent import KVCacheAgent, KVCacheMode, compare_implementations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kv_cache_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_summary_task() -> str:
    """Create a task that requires reading multiple files"""
    return """Please analyze and summarize all the projects in the week1 and week2 directories.
For each project:
1. Find all Python files
2. Read the main files and understand the functionality
3. Identify the key features and purpose
4. Provide a comprehensive summary

Start with week1 projects, then move to week2. Be thorough in your analysis."""


def run_single_mode(api_key: str, mode: str, task: str = None, root_dir: str = "../.."):
    """
    Run agent in a single mode
    
    Args:
        api_key: API key for Kimi
        mode: KV cache mode to use
        task: Custom task (optional)
        root_dir: Root directory for file operations (default: "../.." = /projects from kv-cache dir)
    """
    # Parse mode
    mode_map = {
        "correct": KVCacheMode.CORRECT,
        "dynamic_system": KVCacheMode.DYNAMIC_SYSTEM,
        "shuffled_tools": KVCacheMode.SHUFFLED_TOOLS,
        "dynamic_profile": KVCacheMode.DYNAMIC_PROFILE,
        "sliding_window": KVCacheMode.SLIDING_WINDOW,
        "text_format": KVCacheMode.TEXT_FORMAT
    }
    
    if mode not in mode_map:
        logger.error(f"Invalid mode: {mode}")
        logger.info(f"Valid modes: {', '.join(mode_map.keys())}")
        return
    
    # Use default task if not provided
    if not task:
        task = create_summary_task()
    
    logger.info(f"Running in mode: {mode}")
    logger.info(f"Task: {task}")
    logger.info("="*80)
    
    # Create agent and execute task
    agent = KVCacheAgent(
        api_key=api_key,
        mode=mode_map[mode],
        root_dir=root_dir,
        verbose=True
    )
    
    result = agent.execute_task(task, max_iterations=30)
    
    # Print results
    print("\n" + "="*80)
    print(f"EXECUTION RESULTS - Mode: {mode}")
    print("="*80)
    
    metrics = result["metrics"]
    print(f"\n📊 Performance Metrics:")
    print(f"  • Time to First Token (TTFT): {metrics.ttft:.3f} seconds")
    
    # Show TTFT progression
    if metrics.ttft_per_iteration:
        print(f"  • TTFT per iteration:")
        for i, ttft in enumerate(metrics.ttft_per_iteration, 1):
            print(f"      Iteration {i}: {ttft:.3f}s")

        # Show improvement
        if len(metrics.ttft_per_iteration) > 1:
            first_ttft = metrics.ttft_per_iteration[0]
            last_ttft = metrics.ttft_per_iteration[-1]
            avg_after_first = sum(metrics.ttft_per_iteration[1:]) / len(metrics.ttft_per_iteration[1:])
            print(f"  • TTFT Analysis:")
            print(f"      First iteration: {first_ttft:.3f}s")
            print(f"      Last iteration: {last_ttft:.3f}s")
            print(f"      Average (after first): {avg_after_first:.3f}s")
            improvement = (first_ttft - last_ttft) / first_ttft * 100
            print(f"      Improvement: {improvement:.1f}%")
    
    print(f"  • Total Execution Time: {metrics.total_time:.3f} seconds")
    print(f"  • Iterations: {result['iterations']}")
    print(f"  • Tool Calls: {len(result['tool_calls'])}")
    
    print(f"\n🔄 Cache Statistics:")
    print(f"  • Cached Tokens: {metrics.cached_tokens:,}")
    print(f"  • Cache Hits: {metrics.cache_hits}")
    print(f"  • Cache Misses: {metrics.cache_misses}")
    if metrics.cache_hits + metrics.cache_misses > 0:
        hit_rate = metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100
        print(f"  • Cache Hit Rate: {hit_rate:.1f}%")
    
    print(f"\n💰 Token Usage:")
    print(f"  • Prompt Tokens: {metrics.prompt_tokens:,}")
    print(f"  • Completion Tokens: {metrics.completion_tokens:,}")
    print(f"  • Total Tokens: {metrics.prompt_tokens + metrics.completion_tokens:,}")
    if metrics.prompt_tokens > 0:
        cache_ratio = metrics.cached_tokens / metrics.prompt_tokens * 100
        print(f"  • Cache Ratio: {cache_ratio:.1f}% of prompt tokens cached")
    
    # Show tool calls summary
    if result["tool_calls"]:
        print(f"\n🔧 Tool Calls Summary:")
        tool_counts = {}
        for tc in result["tool_calls"]:
            tool_counts[tc.name] = tool_counts.get(tc.name, 0) + 1
        for tool_name, count in tool_counts.items():
            print(f"  • {tool_name}: {count} calls")
    
    # Save detailed results
    output_file = f"result_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        # Convert tool calls to serializable format
        result_copy = result.copy()
        result_copy["tool_calls"] = [
            {
                "name": tc.name,
                "arguments": tc.arguments,
                "timestamp": tc.timestamp
            }
            for tc in result["tool_calls"]
        ]
        json.dump(result_copy, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")


def select_mode_interactive():
    """
    Interactive mode selection menu
    
    Returns:
        Selected mode string or None for all modes
    """
    modes = [
        ("correct", "✅ Correct Implementation - Optimal KV cache usage"),
        ("dynamic_system", "❌ Dynamic System Prompt - Adds timestamps"),
        ("shuffled_tools", "❌ Shuffled Tools - Randomizes tool order"),
        ("dynamic_profile", "❌ Dynamic Profile - Updates user credits"),
        ("sliding_window", "❌ Sliding Window - Keeps only recent messages"),
        ("text_format", "❌ Text Format - Plain text instead of structured"),
        ("compare", "📊 Compare All - Run all modes and compare"),
    ]
    
    print("\n" + "="*60)
    print("KV CACHE DEMONSTRATION - MODE SELECTION")
    print("="*60)
    print("\nSelect a mode to run:\n")
    
    for i, (mode, description) in enumerate(modes, 1):
        print(f"  {i}. {description}")
    
    print("\n  0. Exit")
    print("-"*60)
    
    while True:
        try:
            choice = input("\nEnter your choice (0-7): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("Exiting...")
                sys.exit(0)
            elif 1 <= choice_num <= 6:
                selected = modes[choice_num - 1][0]
                print(f"\n✓ Selected: {modes[choice_num - 1][1]}")
                return selected
            elif choice_num == 7:
                print("\n✓ Selected: Compare all modes")
                return "compare"
            else:
                print("Invalid choice. Please enter a number between 0 and 7.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)

def run_comparison(api_key: str, task: str = None, root_dir: str = "../.."):
    """
    Run comparison across all modes
    
    Args:
        api_key: API key for Kimi
        task: Custom task (optional)
        root_dir: Root directory for file operations (default: "../.." = /projects from kv-cache dir)
    """
    # Use default task if not provided
    if not task:
        task = create_summary_task()
    
    logger.info("Starting KV Cache Comparison Study")
    logger.info(f"Task: {task[:200]}...")
    logger.info("="*80)
    
    # Run comparison
    results = compare_implementations(api_key, task, root_dir)
    
    # Print comparison table
    print("\n" + "="*80)
    print("KV CACHE COMPARISON RESULTS")
    print("="*80)
    
    # Create comparison table
    print(f"\n{'Mode':<20} {'First TTFT':<12} {'Avg TTFT':<12} {'Total (s)':<12} {'Cached':<12} {'Hit Rate':<12}")
    print("-"*92)
    
    for mode, data in results.items():
        metrics = data["metrics"]
        
        # Calculate average TTFT
        ttft_list = metrics.get("ttft_per_iteration", [])
        avg_ttft = sum(ttft_list) / len(ttft_list) if ttft_list else metrics["ttft"]
        
        # Calculate hit rate
        total_checks = metrics["cache_hits"] + metrics["cache_misses"]
        hit_rate = metrics["cache_hits"] / total_checks * 100 if total_checks > 0 else 0
        
        print(f"{mode:<20} {metrics['ttft']:<12.3f} {avg_ttft:<12.3f} {metrics['total_time']:<12.3f} "
              f"{metrics['cached_tokens']:<12,} {hit_rate:<12.1f}")
    
    # Analyze results
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # Find best and worst performers
    correct_metrics = results["correct"]["metrics"]
    
    print("\n🏆 Performance Impact (compared to correct implementation):")
    for mode, data in results.items():
        if mode == "correct":
            continue
        
        metrics = data["metrics"]
        ttft_diff = ((metrics["ttft"] - correct_metrics["ttft"]) / correct_metrics["ttft"]) * 100
        total_diff = ((metrics["total_time"] - correct_metrics["total_time"]) / correct_metrics["total_time"]) * 100
        cache_diff = correct_metrics["cached_tokens"] - metrics["cached_tokens"]
        
        print(f"\n{mode}:")
        print(f"  • TTFT: {'+' if ttft_diff > 0 else ''}{ttft_diff:.1f}% "
              f"({'slower' if ttft_diff > 0 else 'faster'})")
        print(f"  • Total Time: {'+' if total_diff > 0 else ''}{total_diff:.1f}% "
              f"({'slower' if total_diff > 0 else 'faster'})")
        print(f"  • Lost Cached Tokens: {cache_diff:,}")
    
    # Show TTFT progression comparison
    print("\n📈 TTFT Progression (first 5 iterations):")
    for mode, data in results.items():
        metrics = data["metrics"]
        ttft_list = metrics.get("ttft_per_iteration", [])[:5]
        if ttft_list:
            ttft_str = " → ".join([f"{t:.2f}s" for t in ttft_list])
            print(f"  {mode:<20}: {ttft_str}")
    
    # Key insights
    print("\n📝 Key Insights:")
    print("  1. The correct implementation maintains stable context for optimal KV cache usage")
    print("  2. TTFT improves dramatically after first iteration when cache is utilized")
    print("  3. Dynamic system prompts invalidate the entire cache on each request")
    print("  4. Shuffling tools breaks cache even though the functionality is identical")
    print("  5. Dynamic user profiles add unnecessary context changes")
    print("  6. Sliding windows may seem to reduce context but actually harm cache efficiency")
    print("  7. Text formatting breaks the structured message format that enables caching")
    
    # Save comparison results
    output_file = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Comparison results saved to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KV Cache Demonstration with ReAct Agent")
    parser.add_argument("--api-key", type=str, help="API key for Kimi (or use MOONSHOT_API_KEY env var)")
    parser.add_argument("--mode", type=str, help="Single mode to run (correct, dynamic_system, etc.)")
    parser.add_argument("--compare", action="store_true", help="Run comparison across all modes")
    parser.add_argument("--task", type=str, help="Custom task to execute")
    parser.add_argument("--root-dir", type=str, default="../..", help="Root directory for file operations (default: ../.. = /projects)")
    parser.add_argument("--interactive", action="store_true", default=True, 
                        help="Interactive mode selection (default: True)")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false",
                        help="Disable interactive mode")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        logger.error("Please provide API key via --api-key or MOONSHOT_API_KEY environment variable")
        sys.exit(1)
    
    # Run based on mode
    if args.compare:
        # Explicit --compare flag overrides interactive mode
        run_comparison(api_key, args.task, args.root_dir)
    elif args.mode:
        # Explicit --mode flag overrides interactive mode
        run_single_mode(api_key, args.mode, args.task, args.root_dir)
    elif args.interactive and not args.task:
        # Interactive mode selection (default)
        selected_mode = select_mode_interactive()
        if selected_mode == "compare":
            run_comparison(api_key, args.task, args.root_dir)
        else:
            run_single_mode(api_key, selected_mode, args.task, args.root_dir)
    else:
        # If task is provided without mode, ask which mode to use
        if args.task:
            print(f"\n📝 Custom task provided: {args.task}")
            selected_mode = select_mode_interactive()
            if selected_mode == "compare":
                run_comparison(api_key, args.task, args.root_dir)
            else:
                run_single_mode(api_key, selected_mode, args.task, args.root_dir)
        else:
            # Fallback to interactive mode
            selected_mode = select_mode_interactive()
            if selected_mode == "compare":
                run_comparison(api_key, args.task, args.root_dir)
            else:
                run_single_mode(api_key, selected_mode, args.task, args.root_dir)


if __name__ == "__main__":
    main()
