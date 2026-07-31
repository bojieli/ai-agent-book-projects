#!/usr/bin/env python3
"""
Test that Doubao is the default provider
"""

import os
import sys

from _bootstrap import add_project_root

add_project_root()

# Test without any arguments - should use Doubao
print("Testing default provider...")

# Check if ARK_API_KEY is available
ark_key = os.getenv("ARK_API_KEY")
sf_key = os.getenv("SILICONFLOW_API_KEY")

print(f"ARK_API_KEY available: {'Yes' if ark_key else 'No'}")
print(f"SILICONFLOW_API_KEY available: {'Yes' if sf_key else 'No'}")

if ark_key:
    from agent import ContextAwareAgent, ContextMode
    from config import Config
    
    # Check config default
    print(f"\nConfig default provider: {Config.LLM_PROVIDER}")
    
    # Create agent with default provider from config
    agent = ContextAwareAgent(ark_key, ContextMode.FULL, provider=Config.LLM_PROVIDER)
    
    print(f"\n✅ Default agent created successfully!")
    print(f"Provider: {agent.provider}")
    print(f"Model: {agent.model}")
    print(f"Base URL: {agent.client.base_url}")
    
    if agent.provider == "doubao":
        print("\n🎉 SUCCESS: Doubao is the default provider!")
    else:
        print(f"\n❌ ERROR: Expected doubao, got {agent.provider}")
        sys.exit(1)
else:
    print("\n⚠️ ARK_API_KEY not set. Cannot test default provider.")
    print("Please set: export ARK_API_KEY=your_key_here")
