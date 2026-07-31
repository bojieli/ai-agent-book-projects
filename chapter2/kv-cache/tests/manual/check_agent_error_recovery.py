#!/usr/bin/env python3
"""Manual live check for agent recovery after tool errors."""

import os
import sys

from _bootstrap import add_project_root

add_project_root()

from agent import KVCacheAgent, KVCacheMode


def check_agent_error_recovery():
    """Run the live agent against an intentionally failing tool path."""
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY environment variable")
        sys.exit(1)

    print("🧪 Testing agent error recovery")
    print("=" * 60)

    agent = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=True,
    )

    task = """Please do the following:
    1. Try to read a file that doesn't exist: 'non_existent_file.txt'
    2. Then find Python files in chapter1/context directory
    3. Tell me what you found"""

    print(f"Task: {task[:100]}...")
    result = agent.execute_task(task, max_iterations=10)

    print(f"\n✓ Completed in {result['iterations']} iterations")
    print(f"✓ Tool calls made: {len(result['tool_calls'])}")

    error_count = 0
    for tool_call in result["tool_calls"]:
        if tool_call.result and not tool_call.result.get("success", True):
            error_count += 1
            print(
                f"• Tool error in {tool_call.name}: "
                f"{tool_call.result.get('error', 'Unknown')[:50]}..."
            )

    print(f"✓ Errors encountered and handled: {error_count}")
    print(f"✓ Agent continued despite errors: {result['success']}")

    if result["final_answer"]:
        print("\nFinal answer provided despite errors:")
        print(f"{result['final_answer'][:200]}...")


if __name__ == "__main__":
    check_agent_error_recovery()
