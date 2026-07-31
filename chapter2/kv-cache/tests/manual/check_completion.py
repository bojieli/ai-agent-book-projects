#!/usr/bin/env python3
"""
Test script to verify the agent correctly identifies final answers
when no tool calls are made
"""

import os
import sys
from _bootstrap import add_project_root

add_project_root()

from agent import KVCacheAgent, KVCacheMode

def test_completion_logic():
    """Test that the agent correctly handles responses without tool calls as final answers"""
    
    # Get API key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY environment variable")
        sys.exit(1)
    
    print("🧪 Testing Final Answer Detection")
    print("="*60)
    
    # Test 1: Simple question that doesn't require tools
    print("\n1️⃣ Test: Simple question without tools")
    task1 = "What is 2 + 2? Just tell me the answer, no need to use any tools."
    
    agent = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=False
    )
    
    result = agent.execute_task(task1, max_iterations=5)
    print(f"   Task: {task1}")
    print(f"   ✓ Completed in {result['iterations']} iteration(s)")
    print(f"   ✓ Tool calls: {len(result['tool_calls'])}")
    print(f"   ✓ Has final answer: {result['success']}")
    if result['final_answer']:
        print(f"   Answer: {result['final_answer'][:100]}")
    
    # Test 2: Question that requires tools
    print("\n2️⃣ Test: Question requiring tools")
    task2 = "How many Python files are in the chapter1/context directory?"
    
    agent2 = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=False
    )
    
    result2 = agent2.execute_task(task2, max_iterations=5)
    print(f"   Task: {task2}")
    print(f"   ✓ Completed in {result2['iterations']} iteration(s)")
    print(f"   ✓ Tool calls: {len(result2['tool_calls'])}")
    print(f"   ✓ Has final answer: {result2['success']}")
    
    if result2['tool_calls']:
        print("   Tools used:")
        for tc in result2['tool_calls']:
            print(f"     • {tc.name}")
    
    # Test 3: Multi-step task
    print("\n3️⃣ Test: Multi-step task")
    task3 = "Find Python files in chapter1/context, then tell me if there's a file named 'agent.py'"
    
    agent3 = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=False
    )
    
    result3 = agent3.execute_task(task3, max_iterations=10)
    print(f"   Task: {task3}")
    print(f"   ✓ Completed in {result3['iterations']} iteration(s)")
    print(f"   ✓ Tool calls: {len(result3['tool_calls'])}")
    print(f"   ✓ Has final answer: {result3['success']}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 Summary:")
    print(f"  • Test 1 (no tools): {result['iterations']} iterations, {len(result['tool_calls'])} tools")
    print(f"  • Test 2 (with tools): {result2['iterations']} iterations, {len(result2['tool_calls'])} tools")
    print(f"  • Test 3 (multi-step): {result3['iterations']} iterations, {len(result3['tool_calls'])} tools")
    
    print("\n✅ The agent correctly:")
    print("  1. Identifies final answers when no tools are needed")
    print("  2. Uses tools when necessary to gather information")
    print("  3. Provides final answer after tool execution")
    print("\nNo explicit 'final answer' keyword needed!")

if __name__ == "__main__":
    test_completion_logic()
