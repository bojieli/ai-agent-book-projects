#!/usr/bin/env python3
"""
Quick demonstration of KV cache impact
Shows the difference between correct and incorrect implementations
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from _bootstrap import add_project_root

add_project_root()

from agent import KVCacheAgent, KVCacheMode

from agentbook.providers import PROVIDERS

def main():
    """Run a quick demo comparing correct vs incorrect implementation"""
    
    # Get API key. 优先 Moonshot/Kimi；缺失时回退 OPENROUTER_API_KEY
    # （KVCacheAgent 会自动切换到 OpenRouter 端点并映射模型名）。
    # 接受哪些环境变量由 agentbook 的 provider 注册表定义。
    api_key = PROVIDERS["kimi"].api_key() or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY (or KIMI_API_KEY / OPENROUTER_API_KEY)")
        print("   export MOONSHOT_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    print("🚀 KV Cache Quick Demo")
    print("="*60)
    
    # Simple task that requires multiple tool calls
    task = """Please do the following:
    1. Find all Python files in the chapter1 directory
    2. Read the main.py file from the context project
    3. Search for the word 'agent' in chapter1 files
    4. Provide a brief summary of what you found"""
    
    print(f"📝 Task: {task}")
    print("="*60)
    
    # Test 1: Correct implementation
    print("\n✅ Testing CORRECT implementation (with KV cache)...")
    print("-"*60)
    agent_correct = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=False  # Set to True for detailed logs
    )
    
    result_correct = agent_correct.execute_task(task, max_iterations=10)
    metrics_correct = result_correct["metrics"]
    
    print(f"✓ TTFT: {metrics_correct.ttft:.3f}s")
    print(f"✓ Total Time: {metrics_correct.total_time:.3f}s")
    print(f"✓ Cached Tokens: {metrics_correct.cached_tokens:,}")
    print(f"✓ Cache Hits: {metrics_correct.cache_hits}")
    print(f"✓ Total Tokens Used: {metrics_correct.prompt_tokens + metrics_correct.completion_tokens:,}")
    
    # Test 2: Incorrect implementation (dynamic system prompt)
    print("\n❌ Testing INCORRECT implementation (dynamic system prompt)...")
    print("-"*60)
    agent_incorrect = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.DYNAMIC_SYSTEM,
        root_dir="../..",
        verbose=False
    )
    
    result_incorrect = agent_incorrect.execute_task(task, max_iterations=10)
    metrics_incorrect = result_incorrect["metrics"]
    
    print(f"✗ TTFT: {metrics_incorrect.ttft:.3f}s")
    print(f"✗ Total Time: {metrics_incorrect.total_time:.3f}s")
    print(f"✗ Cached Tokens: {metrics_incorrect.cached_tokens:,}")
    print(f"✗ Cache Hits: {metrics_incorrect.cache_hits}")
    print(f"✗ Total Tokens Used: {metrics_incorrect.prompt_tokens + metrics_incorrect.completion_tokens:,}")
    
    # Comparison
    print("\n📊 Performance Impact:")
    print("="*60)
    
    ttft_diff = ((metrics_incorrect.ttft - metrics_correct.ttft) / metrics_correct.ttft) * 100
    time_diff = ((metrics_incorrect.total_time - metrics_correct.total_time) / metrics_correct.total_time) * 100
    cache_lost = metrics_correct.cached_tokens - metrics_incorrect.cached_tokens
    
    print(f"⚡ TTFT increased by: {ttft_diff:.1f}%")
    print(f"⏱️  Total time increased by: {time_diff:.1f}%")
    print(f"💾 Cache tokens lost: {cache_lost:,}")
    
    if ttft_diff > 50:
        print("\n⚠️  Dynamic system prompts severely impact performance!")
        print("   Even small context changes can invalidate the entire KV cache.")
    
    print("\n💡 Key Takeaway:")
    print("   Maintaining stable context is crucial for LLM performance.")
    print("   Small implementation details can have major performance impacts!")

if __name__ == "__main__":
    main()
