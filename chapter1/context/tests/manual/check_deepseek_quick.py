#!/usr/bin/env python3
"""
Quick smoke test for DeepSeek provider (deepseek-v4-flash).
"""

import os
import sys
import time

from _bootstrap import add_project_root

add_project_root()

from dotenv import load_dotenv

load_dotenv()

task = "What is 10 + 5? Provide FINAL ANSWER with just the number."

print("=" * 60)
print("QUICK TEST - DeepSeek Provider")
print("=" * 60)

deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_key:
    print("❌ DEEPSEEK_API_KEY not set")
    print("Set it in .env or: export DEEPSEEK_API_KEY=your_key")
    print("Get a key at: https://platform.deepseek.com/api_keys")
    sys.exit(1)

from agent import ContextAwareAgent, ContextMode

agent = ContextAwareAgent(deepseek_key, ContextMode.FULL, provider="deepseek")
print(f"✅ Using: {agent.provider} / {agent.model}")
print(f"   Base URL: {agent.client.base_url}")
print(f"\n📝 Task: {task}")
print("-" * 40)

start = time.time()
print("Processing...")

try:
    result = agent.execute_task(task, max_iterations=3)
    elapsed = time.time() - start

    print(f"\n✅ Completed in {elapsed:.2f} seconds")

    if result.get("success"):
        print("Success: True")
        if result.get("final_answer"):
            print(f"Answer: {result['final_answer']}")
    else:
        print("Success: False")
        if result.get("error"):
            print(f"Error: {result['error']}")

    print(f"Iterations: {result.get('iterations', 0)}")
    print(f"Tool calls: {len(result['trajectory'].tool_calls)}")

except KeyboardInterrupt:
    print("\n⚠️ Interrupted")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    sys.exit(1)

print("=" * 60)
