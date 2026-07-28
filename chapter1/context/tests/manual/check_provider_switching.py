#!/usr/bin/env python3
"""
Test script to verify provider switching functionality
"""

import os

from _bootstrap import add_project_root

add_project_root()

from dotenv import load_dotenv
from agent import ContextAwareAgent, ContextMode
from config import Config

# Load environment variables
load_dotenv()

def test_provider_switching():
    """Test switching between different providers"""
    print("🧪 Testing Provider Switching")
    print("=" * 50)
    
    providers_to_test = []
    
    # Check which providers have API keys configured
    if os.getenv("SILICONFLOW_API_KEY"):
        providers_to_test.append(("siliconflow", os.getenv("SILICONFLOW_API_KEY")))
        print("✅ SiliconFlow API key found")
    else:
        print("⏭️  Skipping SiliconFlow (no API key)")
    
    if os.getenv("ARK_API_KEY"):
        providers_to_test.append(("doubao", os.getenv("ARK_API_KEY")))
        print("✅ Doubao API key found")
    else:
        print("⏭️  Skipping Doubao (no API key)")
    
    if os.getenv("MOONSHOT_API_KEY"):
        providers_to_test.append(("kimi", os.getenv("MOONSHOT_API_KEY")))
        print("✅ Kimi API key found")
    else:
        print("⏭️  Skipping Kimi (no API key)")

    if os.getenv("DEEPSEEK_API_KEY"):
        providers_to_test.append(("deepseek", os.getenv("DEEPSEEK_API_KEY")))
        print("✅ DeepSeek API key found")
    else:
        print("⏭️  Skipping DeepSeek (no API key)")
    
    if not providers_to_test:
        print("\n❌ No API keys configured. Please set at least one:")
        print("  - SILICONFLOW_API_KEY")
        print("  - ARK_API_KEY")
        print("  - MOONSHOT_API_KEY")
        print("  - DEEPSEEK_API_KEY")
        return
    
    print(f"\nTesting {len(providers_to_test)} provider(s)...")
    print("-" * 50)
    
    # Test each available provider
    for provider_name, api_key in providers_to_test:
        print(f"\n📌 Testing {provider_name.upper()}")
        
        try:
            # Create agent with provider
            agent = ContextAwareAgent(
                api_key=api_key,
                provider=provider_name,
                context_mode=ContextMode.FULL,
                verbose=False
            )
            
            # Get default model from config
            default_model = Config.get_default_model(provider_name)
            
            print(f"  Provider: {agent.provider}")
            print(f"  Model: {agent.model}")
            print(f"  Expected: {default_model}")
            print(f"  Base URL: {agent.client.base_url}")
            
            # Test with a simple query
            query = "What is 5 + 3?"
            print(f"  Testing query: {query}")
            
            response = agent.process(query)
            
            if "8" in response:
                print(f"  ✅ {provider_name} working correctly!")
            else:
                print(f"  ⚠️  {provider_name} response didn't contain expected answer")
                print(f"     Response: {response[:100]}...")
                
        except Exception as e:
            print(f"  ❌ Error with {provider_name}: {e}")
    
    print("\n" + "=" * 50)
    print("Provider switching test complete!")
    
    # Show summary
    print("\n📊 Summary:")
    print(f"  Providers tested: {len(providers_to_test)}")
    print("  Available providers: siliconflow, doubao, kimi, moonshot, deepseek")
    
    if len(providers_to_test) < 3:
        print("\n💡 Tip: Configure more API keys to test all providers")

if __name__ == "__main__":
    test_provider_switching()
