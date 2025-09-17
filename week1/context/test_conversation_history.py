#!/usr/bin/env python3
"""
Test script to verify conversation history persistence
"""

import os
from dotenv import load_dotenv
from agent import ContextAwareAgent, ContextMode
import json

# Load environment variables
load_dotenv()

def test_conversation_history():
    """Test that conversation history persists between tasks"""
    print("🧪 Testing Conversation History Persistence")
    print("=" * 50)
    
    # Get API key (use any available provider)
    api_key = os.getenv("ARK_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    provider = "doubao" if os.getenv("ARK_API_KEY") else ("kimi" if os.getenv("MOONSHOT_API_KEY") else "siliconflow")
    
    if not api_key:
        print("❌ No API key found. Please set one of:")
        print("  - ARK_API_KEY")
        print("  - MOONSHOT_API_KEY")
        print("  - SILICONFLOW_API_KEY")
        return False
    
    print(f"Using provider: {provider}")
    print("-" * 50)
    
    try:
        # Create agent
        agent = ContextAwareAgent(
            api_key=api_key,
            provider=provider,
            context_mode=ContextMode.FULL,
            verbose=False
        )
        
        # Test 1: First query
        print("\n📝 Test 1: First query")
        query1 = "Remember that my favorite number is 42. What is 10 + 5?"
        result1 = agent.execute_task(query1)
        print(f"Query: {query1}")
        print(f"Response: {result1.get('final_answer', 'No answer')}")
        
        # Check conversation history
        print(f"\n📚 Conversation history after first query:")
        print(f"  Total messages: {len(agent.conversation_history)}")
        
        # Print message roles
        for i, msg in enumerate(agent.conversation_history):
            role = msg.get('role', 'unknown')
            content_preview = str(msg.get('content', ''))[:50] + "..." if len(str(msg.get('content', ''))) > 50 else str(msg.get('content', ''))
            print(f"  Message {i}: Role={role}, Content={content_preview}")
        
        # Test 2: Second query that references first
        print("\n📝 Test 2: Second query (should remember context)")
        query2 = "What was my favorite number that I mentioned earlier?"
        result2 = agent.execute_task(query2)
        print(f"Query: {query2}")
        print(f"Response: {result2.get('final_answer', 'No answer')}")
        
        # Check if 42 is mentioned in the response
        if "42" in str(result2.get('final_answer', '')):
            print("✅ SUCCESS: Agent remembered the favorite number from conversation history!")
        else:
            print("⚠️  WARNING: Agent might not have remembered the number. Check response above.")
        
        # Check conversation history growth
        print(f"\n📚 Conversation history after second query:")
        print(f"  Total messages: {len(agent.conversation_history)}")
        
        # Test 3: Verify system prompt unchanged
        print("\n📝 Test 3: Verify system prompt remains unchanged")
        system_prompt = agent.conversation_history[0].get('content', '')
        if "favorite number" not in system_prompt and "42" not in system_prompt:
            print("✅ SUCCESS: System prompt remains unchanged!")
        else:
            print("❌ FAILURE: System prompt was modified!")
        
        # Test 4: Reset and verify history cleared
        print("\n📝 Test 4: Test reset functionality")
        agent.reset()
        print(f"  Messages after reset: {len(agent.conversation_history)}")
        
        if len(agent.conversation_history) == 1 and agent.conversation_history[0]['role'] == 'system':
            print("✅ SUCCESS: Reset properly cleared history and kept system prompt!")
        else:
            print("❌ FAILURE: Reset did not work correctly!")
        
        # Test 5: New conversation after reset
        print("\n📝 Test 5: New conversation after reset")
        query3 = "What was my favorite number?"
        result3 = agent.execute_task(query3)
        print(f"Query: {query3}")
        print(f"Response: {result3.get('final_answer', 'No answer')}")
        
        if "42" not in str(result3.get('final_answer', '')) and "don't" in str(result3.get('final_answer', '').lower()):
            print("✅ SUCCESS: Agent correctly doesn't remember after reset!")
        else:
            print("⚠️  Check if agent properly forgot the previous conversation")
        
        print("\n" + "=" * 50)
        print("Conversation history tests complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversation_history()
    exit(0 if success else 1)
