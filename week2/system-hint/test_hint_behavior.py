#!/usr/bin/env python
"""
Test script to demonstrate that system hints are added as user messages
temporarily before sending to LLM, but not stored in conversation history.
"""

import os
import json
from agent import SystemHintAgent, SystemHintConfig

def test_hint_behavior():
    """Test and demonstrate the system hint behavior"""
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
    # Create agent with system hints enabled
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_system_state=True,
        enable_todo_list=True,
        save_trajectory=True,
        trajectory_file="test_hint_trajectory.json"
    )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=False
    )
    
    # Execute a simple task
    task = "Create a file called test.txt with content 'Testing hint behavior'"
    result = agent.execute_task(task, max_iterations=5)
    
    if result['success']:
        print("✅ Task completed successfully\n")
    
    # Analyze the conversation history
    print("=" * 60)
    print("CONVERSATION HISTORY ANALYSIS")
    print("=" * 60)
    
    # Load the saved trajectory
    with open("test_hint_trajectory.json", 'r') as f:
        trajectory = json.load(f)
    
    conversation = trajectory['conversation_history']
    
    print(f"\nTotal messages in conversation history: {len(conversation)}")
    print("\nMessage roles and previews:")
    
    for i, msg in enumerate(conversation, 1):
        role = msg['role']
        content = msg.get('content', '')
        
        # Check if content contains system hints
        has_system_state = 'SYSTEM STATE' in content
        has_todo_list = 'CURRENT TASKS' in content
        
        preview = content[:80].replace('\n', ' ')
        if len(content) > 80:
            preview += "..."
        
        print(f"\n{i}. [{role.upper()}]")
        print(f"   Preview: {preview}")
        
        if has_system_state or has_todo_list:
            print(f"   ⚠️ Contains system hints: System State={has_system_state}, TODO List={has_todo_list}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Check if any messages contain system hints
    hints_in_history = any(
        'SYSTEM STATE' in msg.get('content', '') or 
        'CURRENT TASKS' in msg.get('content', '')
        for msg in conversation
    )
    
    if hints_in_history:
        print("❌ System hints found in conversation history (unexpected!)")
    else:
        print("✅ No system hints stored in conversation history (expected behavior)")
        print("   System hints are added as temporary user messages before LLM calls")
        print("   but are NOT stored in the conversation history.")
    
    # Clean up test files
    if os.path.exists("test.txt"):
        os.remove("test.txt")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_hint_behavior()
