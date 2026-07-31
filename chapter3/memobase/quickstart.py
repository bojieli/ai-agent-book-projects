"""
Quick start script for testing Memobase Agent
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent import MemobaseAgent
from locomo_benchmark import LOCOMOBenchmark, BenchmarkTask


def quick_demo():
    """Run a quick demonstration of the agent's capabilities"""
    
    print("=" * 60)
    print("MEMOBASE AGENT - Quick Start Demo")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("KIMI_API_KEY", "")
    if not api_key or api_key == "your-kimi-api-key":
        print("\n⚠️  Warning: KIMI_API_KEY not set properly!")
        print("Please set your API key in .env file or as environment variable")
        print("\nContinuing with demo setup...")
        api_key = "demo-key"  # Use demo key for structure demonstration
    
    try:
        # Initialize agent
        print("\n🚀 Initializing Memobase Agent...")
        agent = MemobaseAgent(api_key=api_key)
        print("✅ Agent initialized successfully!")
        
        # Show initial memory state
        metrics = agent.get_performance_metrics()
        print(f"\n📊 Initial Memory State:")
        print(f"  • Total memories: {metrics['total_memories']}")
        print(f"  • Memory types: {list(metrics['memory_distribution'].keys())}")
        
        # Demo 1: Simple interaction with memory
        print("\n" + "-" * 40)
        print("Demo 1: Memory Storage and Retrieval")
        print("-" * 40)
        
        test_messages = [
            "Remember that I prefer Python for data science and JavaScript for web development.",
            "What programming language should I use for data analysis?",
            "What about for building a web application?"
        ]
        
        for msg in test_messages:
            print(f"\n👤 User: {msg}")
            if api_key != "demo-key":
                response = agent.process_message(msg)
                print(f"🤖 Agent: {response}")
            else:
                print("🤖 Agent: [Demo mode - API key required for actual response]")
            
            # Show memory growth
            metrics = agent.get_performance_metrics()
            print(f"   📊 Memories: {metrics['total_memories']} total")
        
        # Demo 2: Learning from experience
        print("\n" + "-" * 40)
        print("Demo 2: Learning from Experience")
        print("-" * 40)
        
        # Simulate learning
        agent._learn_from_outcome(
            task="debugging",
            approach="Check for infinite loops in recursive functions",
            outcome="Successfully identified stack overflow cause",
            success=True
        )
        print("✅ Learned from debugging experience")
        
        agent._learn_from_outcome(
            task="optimization",
            approach="Use memoization for recursive algorithms",
            outcome="Reduced computation time by 80%",
            success=True
        )
        print("✅ Learned optimization technique")
        
        # Show procedural memories
        procedural_memories = agent.memory_store.get_memories("procedural", limit=5)
        print(f"\n📚 Procedural Knowledge Acquired: {len(procedural_memories)} patterns")
        
        # Demo 3: Memory consolidation
        print("\n" + "-" * 40)
        print("Demo 3: Memory Consolidation")
        print("-" * 40)
        
        print("🧠 Triggering memory consolidation...")
        agent.consolidate_and_learn()
        print("✅ Consolidation complete")
        
        # Final memory statistics
        final_metrics = agent.get_performance_metrics()
        print(f"\n📊 Final Memory Statistics:")
        print(f"  • Total memories: {final_metrics['total_memories']}")
        for mem_type, count in final_metrics['memory_distribution'].items():
            print(f"    - {mem_type}: {count}")
        print(f"  • Memory clusters: {final_metrics['clusters_created']}")
        
        # Demo 4: Mini benchmark
        print("\n" + "-" * 40)
        print("Demo 4: Mini Benchmark Test")
        print("-" * 40)
        
        # Create a simple benchmark task
        task = BenchmarkTask(
            id="demo_001",
            category="multi_turn_reasoning",
            query="What are the key factors to consider when choosing a database for a web application?",
            expected_capabilities=["technical_knowledge", "comparative_analysis"]
        )
        
        print(f"📝 Task: {task.query}")
        
        if api_key != "demo-key":
            # Initialize mini benchmark
            benchmark = LOCOMOBenchmark()
            benchmark.tasks = [task]
            
            # Run benchmark
            print("🏃 Running benchmark...")
            results = benchmark.run_benchmark(agent, tasks=[task], verbose=False)
            
            # Show results
            print(f"\n📊 Benchmark Results:")
            print(f"  • Score: {results['overall']['average_score']:.2f}/1.00")
            print(f"  • Time: {results['overall']['average_time']:.2f}s")
            print(f"  • Success: {results['overall']['success_rate']:.0%}")
        else:
            print("📊 [Demo mode - API key required for benchmark execution]")
        
        print("\n" + "=" * 60)
        print("✅ Quick Start Demo Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Set your KIMI_API_KEY in .env file")
        print("2. Run 'python main.py --mode interactive' for full interaction")
        print("3. Run 'python main.py --mode benchmark' for complete evaluation")
        print("4. Check README.md for detailed documentation")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that KIMI_API_KEY is properly set")
        print("3. Verify network connectivity for API calls")


if __name__ == "__main__":
    quick_demo()
