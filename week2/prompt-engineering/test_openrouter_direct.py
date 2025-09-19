#!/usr/bin/env python3
"""
Direct test of OpenRouter API connection with openai/gpt-5
This helps isolate API connection issues from tau-bench logic
"""

import os
import sys
from litellm import completion

def test_openrouter():
    """Test direct API call to OpenRouter"""
    
    print("="*60)
    print("🔍 Testing OpenRouter API directly")
    print("="*60)
    
    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set!")
        print("   Please set: export OPENROUTER_API_KEY='your_key'")
        return
    else:
        print(f"✅ OPENROUTER_API_KEY found (length: {len(api_key)})")
    
    # Test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello, I'm working!' in exactly 5 words."}
    ]
    
    print("\n📤 Sending test message to OpenRouter...")
    print(f"   Model: openai/gpt-5")
    print(f"   Provider: openrouter")
    print(f"   Messages: {len(messages)}")
    
    # Enable verbose logging
    os.environ["LITELLM_LOG"] = "DEBUG"
    
    try:
        # Make API call with reasoning_effort set to low via extra_body
        response = completion(
            model="openai/gpt-5",
            custom_llm_provider="openrouter",
            messages=messages,
            temperature=1.0,  # gpt-5 only supports 1.0
            # Add reasoning_effort to minimize thinking tokens via extra_body
            extra_body={"reasoning_effort": "minimal"}  # Options: "minimal", "low", "medium", "high"
        )
        
        print("\n✅ SUCCESS! Response received:")
        print("─"*50)
        print(f"Content: {response.choices[0].message.content}")
        print(f"Model: {response.model}")
        print(f"Provider: {response._hidden_params.get('custom_llm_provider', 'unknown')}")
        if hasattr(response, 'usage'):
            print(f"Tokens used: {response.usage}")
        print("─"*50)
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        
        # Check common issues
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n💡 This looks like an authentication issue.")
            print("   Check that your OPENROUTER_API_KEY is valid.")
        elif "404" in str(e):
            print("\n💡 This might mean the model 'openai/gpt-5' is not available.")
            print("   Check OpenRouter's model list for available models.")
        elif "429" in str(e):
            print("\n💡 Rate limit exceeded. Wait a bit and try again.")
        elif "timeout" in str(e).lower():
            print("\n💡 Connection timeout. Check your network connection.")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_openrouter()
