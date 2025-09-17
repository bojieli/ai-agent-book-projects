#!/usr/bin/env python3
"""
Test script to verify the updated agent works with standard OpenAI tool calling
"""

import os
import sys
import json
from agent import KVCacheAgent, KVCacheMode

def test_tool_calling():
    """Test that the agent correctly uses OpenAI tool calling format"""
    
    # Get API key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY environment variable")
        sys.exit(1)
    
    print("🧪 Testing Standard OpenAI Tool Calling Format")
    print("="*60)
    
    # Simple task that requires tool calls
    task = "Find all Python files in the week1/context directory and tell me how many there are."
    
    print(f"📝 Task: {task}")
    print("-"*60)
    
    # Create agent with correct implementation
    agent = KVCacheAgent(
        api_key=api_key,
        mode=KVCacheMode.CORRECT,
        root_dir="../..",
        verbose=True  # Enable verbose to see tool calls
    )
    
    # Execute task
    result = agent.execute_task(task, max_iterations=5)
    
    # Check results
    print("\n" + "="*60)
    print("📊 Results:")
    print(f"✓ Success: {result['success']}")
    print(f"✓ Iterations: {result['iterations']}")
    print(f"✓ Tool Calls Made: {len(result['tool_calls'])}")
    
    if result['tool_calls']:
        print("\n🔧 Tool Calls:")
        for tc in result['tool_calls']:
            print(f"  • {tc.name}({tc.arguments})")
            if tc.result and tc.result.get('success'):
                if tc.name == 'find':
                    print(f"    → Found {tc.result.get('count', 0)} files")
    
    if result['final_answer']:
        print(f"\n💬 Final Answer:")
        print(f"  {result['final_answer'][:200]}...")
    
    # Test metrics
    metrics = result['metrics']
    print(f"\n📈 Performance Metrics:")
    print(f"  • TTFT: {metrics.ttft:.3f}s")
    print(f"  • Total Time: {metrics.total_time:.3f}s")
    print(f"  • Cached Tokens: {metrics.cached_tokens}")
    
    print("\n✅ Tool calling test completed successfully!")

if __name__ == "__main__":
    test_tool_calling()
