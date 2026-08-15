"""
Quick start script for the Learning Agent.

This script provides a simple example of how to use the learning agent
for common tasks.
"""

import asyncio
from dotenv import load_dotenv
from browser_use import ChatOpenAI, ChatGoogle
from learning_agent import LearningAgent
from llm_factory import make_llm

# Load environment variables
load_dotenv()


async def example_search():
    """Example: Search on Google."""
    print("\n🔍 Example 1: Google Search")
    print("-" * 40)
    
    agent = LearningAgent(
        task="Go to Google and search for 'browser automation with AI'",
        llm=make_llm(),
        knowledge_base_path="./my_knowledge",
        headless=False  # Show browser
    )
    
    result = await agent.run(max_steps=10)
    print(f"✅ Completed in {result['execution_time']:.2f}s")
    print(f"   LLM calls: {result.get('llm_calls', 0)}")
    print(f"   Workflow reused: {result.get('replay_used', False)}")


async def example_weather():
    """Example: Check weather."""
    print("\n☀️ Example 2: Weather Check")
    print("-" * 40)
    
    agent = LearningAgent(
        task="Check the weather forecast for Tokyo",
        llm=ChatGoogle(model="gemini-3.5-flash"),  # You can use different LLMs
        knowledge_base_path="./my_knowledge",
        headless=False
    )
    
    result = await agent.run(max_steps=15)
    print(f"✅ Completed in {result['execution_time']:.2f}s")
    
    # Run again with different city - should be faster!
    print("\n   Running again for New York...")
    agent2 = LearningAgent(
        task="Check the weather forecast for New York",
        llm=ChatGoogle(model="gemini-3.5-flash"),
        knowledge_base_path="./my_knowledge",
        headless=False
    )
    
    result2 = await agent2.run(max_steps=15)
    print(f"✅ Completed in {result2['execution_time']:.2f}s")
    
    if result2.get('replay_used'):
        speedup = result['execution_time'] / result2['execution_time']
        print(f"   🚀 {speedup:.1f}x faster with learned workflow!")


async def example_custom_task():
    """Example: Custom task from user input."""
    print("\n💡 Example 3: Custom Task")
    print("-" * 40)
    
    task = input("Enter your task: ")
    
    if not task:
        task = "Go to Wikipedia and search for 'artificial intelligence'"
    
    print(f"\nTask: {task}")
    
    agent = LearningAgent(
        task=task,
        llm=make_llm(),
        knowledge_base_path="./my_knowledge",
        headless=False
    )
    
    result = await agent.run(max_steps=20)
    
    print(f"\n✅ Task completed!")
    print(f"   Success: {result['success']}")
    print(f"   Time: {result['execution_time']:.2f}s")
    print(f"   Workflow reused: {result.get('replay_used', False)}")
    
    if not result.get('replay_used'):
        print("\n💡 Tip: Try the same task again - it will be much faster!")


def show_knowledge_stats():
    """Show knowledge base statistics."""
    from learning_agent import KnowledgeBase
    
    print("\n📊 Knowledge Base Statistics")
    print("-" * 40)
    
    kb = KnowledgeBase("./my_knowledge")
    stats = kb.get_statistics()
    
    if stats['total_workflows'] == 0:
        print("No workflows learned yet. Run some tasks first!")
    else:
        for key, value in stats.items():
            formatted_key = key.replace('_', ' ').title()
            print(f"   {formatted_key}: {value}")
        
        print("\n   Learned workflows:")
        for workflow in kb.workflows.values():
            print(f"      • {workflow.intent}")
            if workflow.success_count > 0:
                print(f"        (used {workflow.success_count} times)")


async def main():
    """Main menu."""
    print("=" * 60)
    print("LEARNING AGENT - QUICK START")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Google Search Example")
        print("2. Weather Check Example")
        print("3. Custom Task")
        print("4. Show Knowledge Base Stats")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == "1":
            await example_search()
        elif choice == "2":
            await example_weather()
        elif choice == "3":
            await example_custom_task()
        elif choice == "4":
            show_knowledge_stats()
        elif choice == "5":
            print("\nGoodbye! 👋")
            break
        else:
            print("Invalid option, please try again.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye! 👋")
