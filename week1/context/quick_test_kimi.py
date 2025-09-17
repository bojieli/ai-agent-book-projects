#!/usr/bin/env python3
"""
Quick test script to verify Kimi K2 model integration
"""

import os
from dotenv import load_dotenv
from agent import ContextAwareAgent, ContextMode

# Load environment variables
load_dotenv()

def main():
    # Get API key
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("❌ ERROR: MOONSHOT_API_KEY not set")
        print("Please add to your .env file:")
        print("  MOONSHOT_API_KEY=your_api_key_here")
        return
    
    print("🚀 Testing Kimi K2 Model (kimi-k2-0905-preview)")
    print("=" * 50)
    
    try:
        # Create agent with Kimi provider
        agent = ContextAwareAgent(
            api_key=api_key,
            provider="kimi",
            context_mode=ContextMode.FULL,
            verbose=False
        )
        
        print(f"✅ Agent created successfully")
        print(f"   Provider: {agent.provider}")
        print(f"   Model: {agent.model}")
        print(f"   Base URL: {agent.client.base_url}")
        
        # Test simple query
        print("\n📝 Testing basic query...")
        query = "What is 2 + 2?"
        response = agent.process(query)
        print(f"   Query: {query}")
        print(f"   Response: {response}")
        
        print("\n✅ Kimi K2 integration is working!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
