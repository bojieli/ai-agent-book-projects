#!/usr/bin/env python3
"""
Test with a simpler task to diagnose the issue
"""

import os
import sys
import time

from _bootstrap import add_project_root

add_project_root()

from agent import ContextAwareAgent, ContextMode

def test_simple_task():
    """Test with a very simple task to check if the agent is working"""
    
    print("\n" + "="*60)
    print("🧪 SIMPLE TASK TEST")
    print("="*60)
    
    # Get API key
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("❌ SILICONFLOW_API_KEY not found")
        return
    
    print("✅ API key found")
    
    # Create agent
    agent = ContextAwareAgent(api_key, ContextMode.FULL, provider="siliconflow")
    print(f"✅ Agent created")
    print(f"   Model: {agent.model}")
    
    # Very simple task - no tools needed
    print("\n📝 Test 1: Simple question (no tools)")
    task1 = "What is 2 + 2? Just tell me the answer. FINAL ANSWER: provide the result."
    
    start = time.time()
    print("Executing...")
    
    try:
        result = agent.execute_task(task1, max_iterations=1)
        elapsed = time.time() - start
        
        print(f"✅ Completed in {elapsed:.2f} seconds")
        if result.get('final_answer'):
            print(f"   Answer: {result['final_answer'][:100]}")
        print(f"   Tool calls: {len(result['trajectory'].tool_calls)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    # Task with a single tool
    print("\n📝 Test 2: Simple calculation (with tool)")
    task2 = "Use the calculate tool to compute 15 * 3. FINAL ANSWER: provide the result."
    
    start = time.time()
    print("Executing...")
    
    try:
        result = agent.execute_task(task2, max_iterations=2)
        elapsed = time.time() - start
        
        print(f"✅ Completed in {elapsed:.2f} seconds")
        if result.get('final_answer'):
            print(f"   Answer: {result['final_answer'][:100]}")
        print(f"   Tool calls: {len(result['trajectory'].tool_calls)}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        print("The model might be taking too long to respond.")
        print("\nSuggestions:")
        print("1. Try using --provider doubao for faster responses")
        print("2. Check your internet connection")
        print("3. The model might be overloaded - try again later")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_simple_task()
