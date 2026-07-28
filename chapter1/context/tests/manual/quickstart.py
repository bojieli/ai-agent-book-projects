#!/usr/bin/env python3
"""
Quick Start Script for Context-Aware Agent
Run this to test the agent with a simple example
"""

import os
import sys

from _bootstrap import add_project_root

add_project_root()

from agent import ContextAwareAgent, ContextMode
from config import Config

def main():
    """Quick start demonstration"""
    
    print("\n" + "="*60)
    print("CONTEXT-AWARE AGENT - QUICK START")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("\n❌ ERROR: SILICONFLOW_API_KEY not found!")
        print("\nPlease set your API key:")
        print("1. Copy env.example to .env")
        print("2. Add your API key to .env")
        print("3. Or export SILICONFLOW_API_KEY=your_key_here")
        sys.exit(1)
    
    print("\n✅ API key found!")
    
    # Simple demonstration task
    demo_task = """
    Please help me with the following financial calculation:
    
    1. I have $10,000 USD that I want to convert to EUR, GBP, and JPY
    2. Calculate the average amount across all three currencies (converted back to USD)
    3. If I invest this average amount with a 5% annual return, what will it be worth in 2 years?
    
    Show all your calculations step by step.
    """
    
    print("\n📋 Demo Task:")
    print("-"*40)
    print(demo_task)
    print("-"*40)
    
    # Run with full context (baseline)
    print("\n🚀 Running agent with FULL context...")
    agent_full = ContextAwareAgent(api_key, ContextMode.FULL)
    result_full = agent_full.execute_task(demo_task)
    
    print("\n✨ Results with FULL Context:")
    print(f"Success: {result_full.get('success', False)}")
    print(f"Tool calls made: {len(result_full['trajectory'].tool_calls)}")
    print(f"Iterations: {result_full.get('iterations', 0)}")
    
    if result_full.get('final_answer'):
        print(f"\nFinal Answer:")
        print("-"*40)
        print(result_full['final_answer'])
    
    # Demonstrate context ablation effect
    print("\n" + "="*60)
    print("DEMONSTRATING CONTEXT ABLATION")
    print("="*60)
    
    print("\n🔬 Running same task with NO TOOL RESULTS context...")
    print("(Agent won't see the results of its tool calls)")
    
    agent_ablated = ContextAwareAgent(api_key, ContextMode.NO_TOOL_RESULTS)
    result_ablated = agent_ablated.execute_task(demo_task)
    
    print("\n⚠️ Results with NO TOOL RESULTS:")
    print(f"Success: {result_ablated.get('success', False)}")
    print(f"Tool calls made: {len(result_ablated['trajectory'].tool_calls)}")
    print(f"Iterations: {result_ablated.get('iterations', 0)}")
    
    if result_ablated.get('final_answer'):
        print(f"\nFinal Answer (likely incorrect):")
        print("-"*40)
        print(result_ablated['final_answer'][:500] + "...")
    
    # Summary
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    
    print("\n📊 Key Observations:")
    print(f"1. Full Context: {'✅ Success' if result_full.get('success') else '❌ Failed'}")
    print(f"2. No Tool Results: {'✅ Success' if result_ablated.get('success') else '❌ Failed'}")
    print(f"3. Efficiency difference: {result_ablated.get('iterations', 0) - result_full.get('iterations', 0)} more iterations without tool results")
    
    print("\n💡 Insight:")
    print("Without seeing tool results, the agent operates blind and may:")
    print("- Make incorrect calculations")
    print("- Repeat operations unnecessarily")
    print("- Fail to validate its work")
    
    print("\n" + "="*60)
    print("Quick start complete! 🎉")
    print("\nNext steps:")
    print("1. Run full ablation study: python main.py --mode ablation")
    print("2. Try interactive mode: python main.py --mode interactive")
    print("3. Read the README.md for more details")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
