#!/usr/bin/env python3
"""
Demo script showing conversation history persistence
"""

import os
from dotenv import load_dotenv
from agent import ContextAwareAgent, ContextMode

# Load environment variables
load_dotenv()

def main():
    # Get API key (use any available provider)
    api_key = os.getenv("ARK_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    provider = "doubao" if os.getenv("ARK_API_KEY") else ("kimi" if os.getenv("MOONSHOT_API_KEY") else "siliconflow")
    
    if not api_key:
        print("❌ No API key found. Please set one of:")
        print("  - ARK_API_KEY")
        print("  - MOONSHOT_API_KEY")
        print("  - SILICONFLOW_API_KEY")
        return
    
    print("🎭 Conversation History Demo")
    print("=" * 50)
    print(f"Provider: {provider.upper()}")
    print("-" * 50)
    
    # Create agent
    agent = ContextAwareAgent(
        api_key=api_key,
        provider=provider,
        context_mode=ContextMode.FULL,
        verbose=False
    )
    
    # Conversation 1: Set context
    print("\n💬 Turn 1: Setting context...")
    result = agent.execute_task("My name is Alice and I have a budget of $5,000. What is 20% of my budget?")
    print(f"Agent: {result.get('final_answer', 'No answer')}")
    
    # Conversation 2: Reference previous context
    print("\n💬 Turn 2: Referencing previous context...")
    result = agent.execute_task("Convert that 20% amount to EUR please.")
    print(f"Agent: {result.get('final_answer', 'No answer')}")
    
    # Conversation 3: Recall information
    print("\n💬 Turn 3: Recalling information...")
    result = agent.execute_task("What was my name and total budget that I mentioned?")
    print(f"Agent: {result.get('final_answer', 'No answer')}")
    
    print("\n" + "-" * 50)
    print(f"📊 Final Statistics:")
    print(f"  Total messages in history: {len(agent.conversation_history)}")
    print(f"  Total tool calls made: {len(agent.trajectory.tool_calls)}")
    
    # Show that system prompt is unchanged
    system_prompt = agent.conversation_history[0]['content']
    if "Alice" not in system_prompt and "5000" not in system_prompt:
        print("  ✅ System prompt remained unchanged")
    else:
        print("  ❌ System prompt was modified")
    
    print("\n✨ Demo complete!")

if __name__ == "__main__":
    main()
