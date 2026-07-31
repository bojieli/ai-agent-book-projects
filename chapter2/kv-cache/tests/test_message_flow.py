#!/usr/bin/env python3
"""
Test script to verify message flow in correct vs incorrect modes
"""

def test_message_flow_logic():
    """Simulate how messages are handled in different modes"""
    
    print("🔍 Testing Message Flow Logic")
    print("="*60)
    
    # Simulate CORRECT mode
    print("\n✅ CORRECT Mode:")
    print("-"*40)
    
    messages_correct = None
    history_correct = []
    
    for iteration in range(1, 4):
        print(f"\nIteration {iteration}:")
        
        if iteration == 1:
            # First iteration: create messages
            messages_correct = ["system", "task"]
            print(f"  • Created messages: {messages_correct}")
        else:
            print(f"  • Using existing messages: {messages_correct}")
        
        # Simulate tool call
        print(f"  • API returns tool call")
        messages_correct.append(f"assistant_iter{iteration}")
        history_correct.append(f"assistant_iter{iteration}")
        
        # Simulate tool result
        print(f"  • Tool executed")
        messages_correct.append(f"tool_result_iter{iteration}")
        history_correct.append(f"tool_result_iter{iteration}")
        
        print(f"  • Messages now: {messages_correct}")
        print(f"  • History now: {history_correct}")
    
    # Simulate INCORRECT mode
    print("\n\n❌ INCORRECT Mode (e.g., DYNAMIC_SYSTEM):")
    print("-"*40)
    
    history_incorrect = []
    
    for iteration in range(1, 4):
        print(f"\nIteration {iteration}:")
        
        # Always recreate messages from history
        messages_incorrect = ["system_with_timestamp", "task"] + history_incorrect
        print(f"  • Recreated messages: {messages_incorrect}")
        
        # Simulate tool call
        print(f"  • API returns tool call")
        messages_incorrect.append(f"assistant_iter{iteration}")
        history_incorrect.append(f"assistant_iter{iteration}")
        
        # Simulate tool result
        print(f"  • Tool executed")
        messages_incorrect.append(f"tool_result_iter{iteration}")
        history_incorrect.append(f"tool_result_iter{iteration}")
        
        print(f"  • Messages now: {messages_incorrect}")
        print(f"  • History now: {history_incorrect}")
    
    print("\n\n📊 Key Observations:")
    print("="*60)
    print("\n1. CORRECT Mode:")
    print("   • Messages list persists across iterations")
    print("   • Each iteration adds to the same list")
    print("   • Context remains stable → KV cache works")
    
    print("\n2. INCORRECT Mode:")
    print("   • Messages list recreated each iteration")
    print("   • System prompt changes (timestamp)")
    print("   • Context changes → KV cache invalidated")
    
    print("\n3. Both Modes:")
    print("   • Within an iteration, tool results are appended")
    print("   • This ensures the API sees complete conversation")
    print("   • History is maintained for reconstruction")

if __name__ == "__main__":
    test_message_flow_logic()
