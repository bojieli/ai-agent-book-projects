#!/usr/bin/env python3
"""
Test script to demonstrate TTFT tracking across iterations
Shows how cache usage improves response times
"""

import os
import sys
from agent import KVCacheAgent, KVCacheMode

def test_ttft_tracking():
    """Test and display TTFT tracking across iterations"""
    
    # Get API key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY environment variable")
        sys.exit(1)
    
    print("📊 TTFT Tracking Demonstration")
    print("="*60)
    
    # Task that requires multiple iterations
    task = """Analyze the week1/context directory:
    1. Find all Python files
    2. Read the agent.py file (first 100 lines)
    3. Search for classes in the code
    4. Provide a summary of what you found"""
    
    print(f"Task: {task[:100]}...")
    print("="*60)
    
    # Test with correct implementation (should show cache benefits)
    print("\n✅ CORRECT Implementation (with KV cache):")
    print("-"*40)
    
    agent = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=False  # Set to True to see detailed logs
    )
    
    result = agent.execute_task(task, max_iterations=10)
    metrics = result["metrics"]
    
    # Display TTFT progression
    print(f"Iterations completed: {result['iterations']}")
    print(f"Tool calls made: {len(result['tool_calls'])}")
    print(f"\nTTFT per iteration:")
    
    for i, ttft in enumerate(metrics.ttft_per_iteration, 1):
        bar_length = int(ttft * 10)  # Visual bar representation
        bar = "█" * min(bar_length, 50)
        print(f"  Iter {i:2d}: {ttft:6.3f}s {bar}")
    
    # Calculate statistics
    if len(metrics.ttft_per_iteration) > 1:
        first = metrics.ttft_per_iteration[0]
        last = metrics.ttft_per_iteration[-1]
        avg_all = sum(metrics.ttft_per_iteration) / len(metrics.ttft_per_iteration)
        avg_after_first = sum(metrics.ttft_per_iteration[1:]) / len(metrics.ttft_per_iteration[1:])
        
        print(f"\n📈 Performance Analysis:")
        print(f"  • First iteration:    {first:.3f}s (cold start)")
        print(f"  • Last iteration:     {last:.3f}s")
        print(f"  • Average (all):      {avg_all:.3f}s")
        print(f"  • Average (cached):   {avg_after_first:.3f}s")
        print(f"  • Speed improvement:  {(first - last) / first * 100:.1f}%")
        print(f"  • Cached tokens:      {metrics.cached_tokens:,}")
    
    # Compare with dynamic system prompt (no cache benefits)
    print("\n" + "="*60)
    print("❌ DYNAMIC SYSTEM Implementation (breaks KV cache):")
    print("-"*40)
    
    agent2 = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.DYNAMIC_SYSTEM,
        root_dir="../..",
        verbose=False
    )
    
    result2 = agent2.execute_task(task, max_iterations=10)
    metrics2 = result2["metrics"]
    
    print(f"Iterations completed: {result2['iterations']}")
    print(f"Tool calls made: {len(result2['tool_calls'])}")
    print(f"\nTTFT per iteration:")
    
    for i, ttft in enumerate(metrics2.ttft_per_iteration, 1):
        bar_length = int(ttft * 10)
        bar = "█" * min(bar_length, 50)
        print(f"  Iter {i:2d}: {ttft:6.3f}s {bar}")
    
    if len(metrics2.ttft_per_iteration) > 1:
        first2 = metrics2.ttft_per_iteration[0]
        last2 = metrics2.ttft_per_iteration[-1]
        avg_all2 = sum(metrics2.ttft_per_iteration) / len(metrics2.ttft_per_iteration)
        
        print(f"\n📉 Performance Analysis:")
        print(f"  • First iteration:    {first2:.3f}s")
        print(f"  • Last iteration:     {last2:.3f}s")
        print(f"  • Average (all):      {avg_all2:.3f}s")
        print(f"  • Speed improvement:  {(first2 - last2) / first2 * 100:.1f}% (minimal)")
        print(f"  • Cached tokens:      {metrics2.cached_tokens:,} (should be 0)")
    
    # Comparison
    print("\n" + "="*60)
    print("🔬 COMPARISON:")
    print("-"*40)
    
    if metrics.ttft_per_iteration and metrics2.ttft_per_iteration:
        avg1 = sum(metrics.ttft_per_iteration) / len(metrics.ttft_per_iteration)
        avg2 = sum(metrics2.ttft_per_iteration) / len(metrics2.ttft_per_iteration)
        
        print(f"Average TTFT:")
        print(f"  • Correct (with cache):   {avg1:.3f}s")
        print(f"  • Dynamic (no cache):     {avg2:.3f}s")
        print(f"  • Difference:             {avg2 - avg1:.3f}s slower without cache")
        print(f"  • Performance penalty:    {(avg2 - avg1) / avg1 * 100:.1f}% slower")
        
        print(f"\nCache Usage:")
        print(f"  • Correct:   {metrics.cached_tokens:,} tokens cached")
        print(f"  • Dynamic:   {metrics2.cached_tokens:,} tokens cached")
    
    print("\n💡 Key Observation:")
    print("The correct implementation shows significant TTFT improvement after the")
    print("first iteration due to KV cache, while dynamic system prompt maintains")
    print("consistently high TTFT because the cache is invalidated on each request.")

if __name__ == "__main__":
    test_ttft_tracking()
