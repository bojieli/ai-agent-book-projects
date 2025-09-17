#!/usr/bin/env python3
"""
Test script to verify KV cache is properly invalidated in incorrect modes
"""

import os
import sys
import logging
from agent import KVCacheAgent, KVCacheMode

# Set up logging to see details
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cache_invalidation():
    """Test that incorrect modes properly invalidate KV cache each iteration"""
    
    # Get API key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY environment variable")
        sys.exit(1)
    
    print("🔬 Testing KV Cache Invalidation")
    print("="*60)
    
    # Simple task that requires multiple iterations
    task = "Find Python files in week1/context and tell me how many there are."
    
    print(f"Task: {task}")
    print("-"*40)
    
    # Test 1: CORRECT mode (should use cache)
    print("\n1️⃣ Testing CORRECT mode (should use cache):")
    agent_correct = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=True
    )
    
    result_correct = agent_correct.execute_task(task, max_iterations=5)
    metrics_correct = result_correct["metrics"]
    
    print(f"\n  Results for CORRECT mode:")
    print(f"  • Iterations: {result_correct['iterations']}")
    print(f"  • TTFT per iteration: {[f'{t:.2f}s' for t in metrics_correct.ttft_per_iteration]}")
    print(f"  • Cached tokens: {metrics_correct.cached_tokens}")
    print(f"  • Cache hits: {metrics_correct.cache_hits}")
    
    # Test 2: DYNAMIC_SYSTEM mode (should NOT use cache)
    print("\n2️⃣ Testing DYNAMIC_SYSTEM mode (should NOT use cache):")
    agent_dynamic = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.DYNAMIC_SYSTEM,
        root_dir="../..",
        verbose=True
    )
    
    result_dynamic = agent_dynamic.execute_task(task, max_iterations=5)
    metrics_dynamic = result_dynamic["metrics"]
    
    print(f"\n  Results for DYNAMIC_SYSTEM mode:")
    print(f"  • Iterations: {result_dynamic['iterations']}")
    print(f"  • TTFT per iteration: {[f'{t:.2f}s' for t in metrics_dynamic.ttft_per_iteration]}")
    print(f"  • Cached tokens: {metrics_dynamic.cached_tokens}")
    print(f"  • Cache hits: {metrics_dynamic.cache_hits}")
    
    # Analysis
    print("\n" + "="*60)
    print("📊 ANALYSIS:")
    print("-"*40)
    
    # Check TTFT improvement
    if len(metrics_correct.ttft_per_iteration) > 1:
        correct_improvement = (metrics_correct.ttft_per_iteration[0] - metrics_correct.ttft_per_iteration[-1]) / metrics_correct.ttft_per_iteration[0] * 100
        print(f"CORRECT mode TTFT improvement: {correct_improvement:.1f}%")
    
    if len(metrics_dynamic.ttft_per_iteration) > 1:
        dynamic_improvement = (metrics_dynamic.ttft_per_iteration[0] - metrics_dynamic.ttft_per_iteration[-1]) / metrics_dynamic.ttft_per_iteration[0] * 100
        print(f"DYNAMIC mode TTFT improvement: {dynamic_improvement:.1f}%")
    
    # Verify cache behavior
    print("\n✅ Verification:")
    if metrics_correct.cached_tokens > 0:
        print(f"  ✓ CORRECT mode used cache: {metrics_correct.cached_tokens} tokens")
    else:
        print(f"  ✗ CORRECT mode did NOT use cache (unexpected!)")
    
    if metrics_dynamic.cached_tokens == 0:
        print(f"  ✓ DYNAMIC mode did NOT use cache (expected)")
    else:
        print(f"  ✗ DYNAMIC mode used cache: {metrics_dynamic.cached_tokens} tokens (unexpected!)")
    
    # Check TTFT consistency
    print("\n🔍 TTFT Consistency Check:")
    if len(metrics_correct.ttft_per_iteration) > 2:
        # CORRECT mode should show improvement after first iteration
        first_ttft = metrics_correct.ttft_per_iteration[0]
        avg_rest = sum(metrics_correct.ttft_per_iteration[1:]) / len(metrics_correct.ttft_per_iteration[1:])
        if avg_rest < first_ttft * 0.7:  # At least 30% improvement
            print(f"  ✓ CORRECT mode shows cache benefit (first: {first_ttft:.2f}s, avg rest: {avg_rest:.2f}s)")
        else:
            print(f"  ⚠️ CORRECT mode improvement less than expected")
    
    if len(metrics_dynamic.ttft_per_iteration) > 2:
        # DYNAMIC mode should NOT show significant improvement
        all_ttfts = metrics_dynamic.ttft_per_iteration
        min_ttft = min(all_ttfts)
        max_ttft = max(all_ttfts)
        if (max_ttft - min_ttft) / max_ttft < 0.3:  # Less than 30% variation
            print(f"  ✓ DYNAMIC mode shows consistent TTFT (no cache benefit)")
        else:
            print(f"  ⚠️ DYNAMIC mode shows unexpected TTFT variation")
    
    print("\n💡 Key Finding:")
    print("The CORRECT mode should show significant TTFT improvement after the first")
    print("iteration due to KV cache, while incorrect modes should maintain")
    print("consistently high TTFT because the cache is invalidated on each iteration.")

if __name__ == "__main__":
    test_cache_invalidation()
