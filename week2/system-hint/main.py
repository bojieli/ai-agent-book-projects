"""
Main entry point for System-Hint Enhanced Agent
Supports command-line tasks and interactive mode
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from agent import SystemHintAgent, SystemHintConfig, TodoStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_result(result: dict):
    """Print formatted result"""
    if result.get('success'):
        print("\n✅ Task completed successfully!")
        if result.get('final_answer'):
            print("\n📝 Final Answer:")
            print("-"*40)
            print(result['final_answer'])
    else:
        print("\n❌ Task failed!")
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    print(f"\n📊 Statistics:")
    print(f"  - Iterations: {result.get('iterations', 0)}")
    print(f"  - Tool calls: {len(result.get('tool_calls', []))}")
    
    if result.get('trajectory_file'):
        print(f"\n💾 Trajectory saved to: {result['trajectory_file']}")
    
    if result.get('todo_list'):
        print(f"\n📋 Final TODO List:")
        for item in result['todo_list']:
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'cancelled': '❌'
            }.get(item['status'], '❓')
            print(f"  [{item['id']}] {status_emoji} {item['content']} ({item['status']})")
    
    # Show tool call summary
    if result.get('tool_calls'):
        print(f"\n🔧 Tool Call Summary:")
        tool_summary = {}
        for call in result['tool_calls']:
            tool_name = call.tool_name
            if tool_name not in tool_summary:
                tool_summary[tool_name] = {
                    'count': 0,
                    'success': 0,
                    'failed': 0
                }
            tool_summary[tool_name]['count'] += 1
            if call.error:
                tool_summary[tool_name]['failed'] += 1
            else:
                tool_summary[tool_name]['success'] += 1
        
        for tool_name, stats in tool_summary.items():
            print(f"  - {tool_name}: {stats['count']} calls "
                  f"({stats['success']} success, {stats['failed']} failed)")


def get_sample_task() -> str:
    """Get the sample task for summarizing week1 and week2 projects"""
    return """Analyze and summarize the AI Agent projects in week1 and week2 directories. Create a comprehensive analysis file 'project_analysis_report.md' containing:

   - Overview of all the projects in week1 and week2 directories
   - What you have learned from the projects
    """


def execute_single_task(task: str, config: SystemHintConfig = None, verbose: bool = False):
    """Execute a single task with the agent"""
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Error: Please set KIMI_API_KEY environment variable")
        print("   export KIMI_API_KEY='your-api-key-here'")
        return None
    
    if config is None:
        config = SystemHintConfig(
            enable_timestamps=True,
            enable_tool_counter=True,
            enable_todo_list=True,
            enable_detailed_errors=True,
            enable_system_state=True
        )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=verbose
    )
    
    # For project analysis tasks, navigate to parent directory
    if "week1" in task.lower() and "week2" in task.lower():
        agent.current_directory = str(Path(__file__).parent.parent)
        print(f"📁 Working directory set to: {agent.current_directory}")
    
    print("\n🚀 Executing task...")
    result = agent.execute_task(task, max_iterations=30)
    return result


def interactive_mode():
    """Run the agent in interactive mode"""
    print_section("Interactive Mode - System-Hint Agent")
    
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Error: Please set KIMI_API_KEY environment variable")
        print("   export KIMI_API_KEY='your-api-key-here'")
        return
    
    # Initialize agent with full features
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True
    )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=False
    )
    
    print("\n✅ Agent initialized with full system hints")
    print("\nAvailable commands:")
    print("  'sample' - Run the sample project analysis task")
    print("  'reset'  - Reset agent state and conversation")
    print("  'config' - Show current configuration")
    print("  'quit'   - Exit interactive mode")
    print("\nOr enter any task for the agent to complete.")
    
    while True:
        try:
            print("\n" + "-"*60)
            user_input = input("Task > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'sample':
                task = get_sample_task()
                print("\n📋 Running sample task:")
                print(task)
                
                # Navigate to parent directory for project analysis
                original_dir = agent.current_directory
                agent.current_directory = str(Path(__file__).parent.parent)
                
                result = agent.execute_task(task, max_iterations=100)
                print_result(result)
                
                # Restore directory
                agent.current_directory = original_dir
                
            elif user_input.lower() == 'reset':
                agent.reset()
                print("✅ Agent state reset")
                
            elif user_input.lower() == 'config':
                print("\n📋 Current Configuration:")
                print(f"  - Timestamps: {'✅' if config.enable_timestamps else '❌'}")
                print(f"  - Tool Counter: {'✅' if config.enable_tool_counter else '❌'}")
                print(f"  - TODO List: {'✅' if config.enable_todo_list else '❌'}")
                print(f"  - Detailed Errors: {'✅' if config.enable_detailed_errors else '❌'}")
                print(f"  - System State: {'✅' if config.enable_system_state else '❌'}")
                print(f"  - Current Directory: {agent.current_directory}")
                
            else:
                # Execute user task
                result = agent.execute_task(user_input, max_iterations=25)
                print_result(result)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.error(f"Error in interactive mode: {e}", exc_info=True)


def demo_basic_features():
    """Demonstrate basic system hint features"""
    print_section("Demo: Basic System Hint Features")
    
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True
    )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=False
    )
    
    task = """Please complete the following tasks:
    1. Create a test directory called 'demo_output'
    2. Write a Python script that counts files in the current directory
    3. Execute the script and save the output
    4. Create a summary report of what was done
    
    Use the TODO list to track your progress."""
    
    result = agent.execute_task(task)
    print_result(result)


def demo_tool_loop_prevention():
    """Demonstrate tool call loop prevention"""
    print_section("Demo: Tool Call Loop Prevention")
    
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
    config = SystemHintConfig(
        enable_timestamps=False,
        enable_tool_counter=True,
        enable_todo_list=False,
        enable_detailed_errors=True,
        enable_system_state=False
    )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=False
    )
    
    task = """Try to read a file called 'nonexistent_file.txt' up to 3 times.
    After each failed attempt, note the failure and stop after 3 attempts."""
    
    result = agent.execute_task(task, max_iterations=10)
    print_result(result)
    
    if result.get('tool_calls'):
        read_file_calls = [c for c in result['tool_calls'] if c.tool_name == 'read_file']
        print(f"\n🛡️ Tool counter prevented loop: {len(read_file_calls)} read_file attempts")
        for call in read_file_calls:
            print(f"  - Call #{call.call_number}: {'Failed' if call.error else 'Success'}")


def demo_comparison():
    """Compare with and without system hints"""
    print_section("Demo: System Hints Comparison")
    
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
    task = """Create a simple Python script that prints 'Hello World' and save it as 'hello.py'."""
    
    # With system hints
    print("\n📋 WITH System Hints:")
    config_with = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True
    )
    
    agent_with = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config_with,
        verbose=False
    )
    
    result_with = agent_with.execute_task(task, max_iterations=10)
    print(f"  - Success: {result_with.get('success')}")
    print(f"  - Iterations: {result_with.get('iterations')}")
    print(f"  - Tool calls: {len(result_with.get('tool_calls', []))}")
    
    # Without system hints
    print("\n📋 WITHOUT System Hints:")
    config_without = SystemHintConfig(
        enable_timestamps=False,
        enable_tool_counter=False,
        enable_todo_list=False,
        enable_detailed_errors=False,
        enable_system_state=False
    )
    
    agent_without = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config_without,
        verbose=False
    )
    
    result_without = agent_without.execute_task(task, max_iterations=10)
    print(f"  - Success: {result_without.get('success')}")
    print(f"  - Iterations: {result_without.get('iterations')}")
    print(f"  - Tool calls: {len(result_without.get('tool_calls', []))}")
    
    print("\n💡 System hints typically lead to more efficient task completion!")


def main():
    """Main function with command-line argument support"""
    parser = argparse.ArgumentParser(
        description="System-Hint Enhanced AI Agent - Advanced trajectory management with system hints"
    )
    
    parser.add_argument(
        "--mode",
        choices=["single", "interactive", "demo", "sample"],
        default="interactive",
        help="Execution mode (default: interactive)"
    )
    
    parser.add_argument(
        "--task",
        type=str,
        help="Task to execute (for single mode)"
    )
    
    parser.add_argument(
        "--demo",
        choices=["basic", "loop", "comparison"],
        help="Specific demo to run (for demo mode)"
    )
    
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Disable timestamp tracking"
    )
    
    parser.add_argument(
        "--no-counter",
        action="store_true",
        help="Disable tool call counter"
    )
    
    parser.add_argument(
        "--no-todo",
        action="store_true",
        help="Disable TODO list management"
    )
    
    parser.add_argument(
        "--no-errors",
        action="store_true",
        help="Disable detailed error messages"
    )
    
    parser.add_argument(
        "--no-state",
        action="store_true",
        help="Disable system state tracking"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Configure based on command-line flags
    config = SystemHintConfig(
        enable_timestamps=not args.no_timestamps,
        enable_tool_counter=not args.no_counter,
        enable_todo_list=not args.no_todo,
        enable_detailed_errors=not args.no_errors,
        enable_system_state=not args.no_state
    )
    
    print("\n" + "🤖"*40)
    print("  SYSTEM-HINT ENHANCED AGENT")
    print("🤖"*40)
    
    if args.mode == "single":
        if not args.task:
            print("❌ Error: --task required for single mode")
            print("Example: python main.py --mode single --task 'Create a hello world script'")
            sys.exit(1)
        
        result = execute_single_task(args.task, config, verbose=args.verbose)
        if result:
            print_result(result)
    
    elif args.mode == "sample":
        # Run the sample task
        task = get_sample_task()
        print("\n📋 Running sample task:")
        print("-"*60)
        print(task)
        print("-"*60)
        
        result = execute_single_task(task, config, verbose=args.verbose)
        if result:
            print_result(result)
    
    elif args.mode == "demo":
        if args.demo == "basic":
            demo_basic_features()
        elif args.demo == "loop":
            demo_tool_loop_prevention()
        elif args.demo == "comparison":
            demo_comparison()
        else:
            # Run all demos
            print("\nRunning all demonstrations...")
            demo_basic_features()
            input("\nPress Enter to continue...")
            demo_tool_loop_prevention()
            input("\nPress Enter to continue...")
            demo_comparison()
    
    else:  # interactive mode
        interactive_mode()
    
    print("\n👋 Thank you for using System-Hint Enhanced Agent!")


if __name__ == "__main__":
    main()
