#!/usr/bin/env python3
"""
Quick start script to test the context compression experiment
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if environment is properly configured"""
    provider = os.getenv("LLM_PROVIDER", "kimi").lower()
    provider_key = os.getenv("DASHSCOPE_API_KEY") if provider in {"dashscope", "qwen", "bailian"} else os.getenv("MOONSHOT_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    
    print("🔍 Checking environment configuration...")
    print("-" * 40)
    
    if provider_key:
        print(f"✅ API key for {provider} is set")
    else:
        print(f"❌ API key for {provider} is NOT set")
        print("   Please add it to your .env file")
        print("   Set DASHSCOPE_API_KEY for dashscope/qwen/bailian or MOONSHOT_API_KEY for kimi")
        return False
    
    if serper_key:
        print("✅ SERPER_API_KEY is set")
    else:
        print("⚠️  SERPER_API_KEY is NOT set")
        print("   Web search will use mock data")
        print("   Get free API key at: https://serper.dev/")
    
    print("-" * 40)
    return True


def quick_test():
    """Run a quick test with context-aware citations strategy"""
    from agent import ResearchAgent
    from compression_strategies import CompressionStrategy
    from config import Config
    
    print("\n🚀 Running quick test with Context-Aware Citations strategy...")
    print("Task: Research OpenAI co-founders' current affiliations\n")
    
    # Create agent
    agent = ResearchAgent(
        api_key=Config.resolve_llm()[0],
        compression_strategy=CompressionStrategy.CONTEXT_AWARE_CITATIONS,
        verbose=False,
        enable_streaming=True
    )
    
    # Execute research
    result = agent.execute_research(max_iterations=10)
    
    # Print results
    print("\n" + "="*60)
    if result.get('success'):
        print("✅ SUCCESS!")
        print("\nFinal Answer:")
        print(result.get('final_answer', 'No answer found'))
        
        # Statistics
        trajectory = result.get('trajectory')
        if trajectory:
            print(f"\n📊 Statistics:")
            print(f"  - Tool calls: {len(trajectory.tool_calls)}")
            print(f"  - Execution time: {result.get('execution_time', 0):.2f}s")
    else:
        print("❌ FAILED")
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    print("="*60)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("CONTEXT COMPRESSION EXPERIMENT - QUICK START")
    print("="*60 + "\n")
    
    # Check environment
    if not check_environment():
        print("\n❌ Please configure your environment first!")
        print("\n1. Copy env.example to .env:")
        print("   cp env.example .env")
        print("\n2. Edit .env and add your API keys")
        print("\n3. Run this script again")
        sys.exit(1)
    
    # Menu
    print("\n📋 What would you like to do?")
    print("1. Run quick test (Context-Aware Citations)")
    print("2. Run full experiment (all 6 strategies)")
    print("3. Interactive demo (choose strategy)")
    print("4. Exit")
    
    try:
        choice = input("\nSelect option (1-4): ")
        
        if choice == "1":
            quick_test()
        elif choice == "2":
            print("\n🔬 Starting full experiment...")
            import experiment
            experiment.main()
        elif choice == "3":
            print("\n🎮 Starting interactive demo...")
            import main as demo
            demo.main()
        elif choice == "4":
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
