#!/usr/bin/env python3
"""
Demonstration of conversation-based memory processing
Shows how memory operations are triggered per conversation round
"""

import os
import sys
from dotenv import load_dotenv
from conversational_agent import ConversationalAgent, ConversationConfig
from background_memory_processor import BackgroundMemoryProcessor, MemoryProcessorConfig
from config import Config, MemoryMode
from memory_manager import create_memory_manager

# Load environment variables
load_dotenv()


def demonstrate_conversation_processing():
    """Demonstrate the conversation-based memory processing"""
    
    print("="*70)
    print("DEMONSTRATION: Conversation-Based Memory Processing")
    print("="*70)
    
    # Check API key
    if not Config.MOONSHOT_API_KEY:
        print("\n❌ Please set MOONSHOT_API_KEY environment variable")
        return
    
    # Setup
    user_id = "demo_conv_user"
    memory_mode = MemoryMode.NOTES
    
    print(f"\n📋 Configuration:")
    print(f"   • User ID: {user_id}")
    print(f"   • Memory Mode: {memory_mode.value}")
    print(f"   • Processing: After EACH conversation round")
    print(f"   • Output: List of memory operations\n")
    
    # Initialize components
    agent = ConversationalAgent(
        user_id=user_id,
        memory_mode=memory_mode,
        verbose=False
    )
    
    processor = BackgroundMemoryProcessor(
        user_id=user_id,
        memory_mode=memory_mode,
        config=MemoryProcessorConfig(
            conversation_interval=1,  # Process after each conversation
            min_conversation_turns=1,
            update_threshold=0.6,
            output_operations=True
        ),
        verbose=False
    )
    
    print("="*70)
    print("DEMONSTRATION BEGINS")
    print("="*70)
    
    # Conversation rounds
    conversations = [
        {
            "round": 1,
            "message": "Hello! I'm Jennifer, a data scientist specializing in NLP and computer vision.",
            "expected_ops": ["add"]
        },
        {
            "round": 2,
            "message": "I work at DataCorp and use Python with scikit-learn and transformers daily.",
            "expected_ops": ["add"]
        },
        {
            "round": 3,
            "message": "Actually, let me correct that - I work at AI Innovations, not DataCorp.",
            "expected_ops": ["update"]
        },
        {
            "round": 4,
            "message": "I'm also learning Rust for high-performance computing tasks.",
            "expected_ops": ["add"]
        },
        {
            "round": 5,
            "message": "What programming languages do I know?",
            "expected_ops": []  # Query, no updates expected
        }
    ]
    
    for conv in conversations:
        print(f"\n{'='*70}")
        print(f"CONVERSATION ROUND {conv['round']}")
        print(f"{'='*70}")
        
        # User message
        print(f"\n👤 User: {conv['message']}")
        
        # Get response
        response = agent.chat(conv['message'])
        print(f"\n🤖 Assistant: {response[:200]}..." if len(response) > 200 else f"\n🤖 Assistant: {response}")
        
        # Increment conversation counter
        processor.increment_conversation_count()
        
        # Process memory
        print(f"\n📝 Processing Memory (Round {conv['round']})...")
        print("-"*50)
        
        results = processor.process_recent_conversations()
        
        # Display operations
        operations = results.get('operations', [])
        
        if operations:
            print(f"Memory Operations: {len(operations)} operation(s)")
            print()
            for i, op in enumerate(operations, 1):
                icon = {
                    'add': '➕ ADD',
                    'update': '📝 UPDATE',
                    'delete': '🗑️ DELETE'
                }.get(op['action'], '❓ UNKNOWN')
                
                print(f"Operation {i}: {icon}")
                
                if op.get('content'):
                    content = op['content']
                    if len(content) > 100:
                        content = content[:97] + "..."
                    print(f"  Content: {content}")
                
                if op.get('memory_id'):
                    print(f"  Memory ID: {op['memory_id']}")
                
                if op.get('reason'):
                    print(f"  Reason: {op['reason'][:100]}...")
                
                print()
        else:
            print("Memory Operations: None (no updates needed)")
        
        # Show if operations match expectations
        actual_ops = [op['action'] for op in operations]
        expected = conv['expected_ops']
        
        if set(actual_ops) == set(expected) or (not actual_ops and not expected):
            print("✅ Operations as expected")
        else:
            print(f"⚠️ Expected {expected}, got {actual_ops}")
    
    # Final memory state
    print(f"\n{'='*70}")
    print("FINAL MEMORY STATE")
    print("="*70)
    
    memory_manager = create_memory_manager(user_id, memory_mode)
    memory_content = memory_manager.get_context_string()
    
    print("\nStored Memories:")
    print("-"*50)
    if memory_content:
        lines = memory_content.split('\n')
        for line in lines:
            if line.strip():
                print(f"  • {line.strip()}")
    else:
        print("  (No memories)")
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    
    print("\n✅ Demonstration Complete!")
    print("\nKey Points:")
    print("  1. Memory processing occurs after EACH conversation round")
    print("  2. Operations list shows exactly what changes (0, 1, or more operations)")
    print("  3. Each operation includes action type, content")
    print("  4. No memory updates for simple queries (demonstrating intelligent processing)")
    print("  5. Updates are incremental and context-aware")


def demonstrate_interval_processing():
    """Demonstrate processing with different conversation intervals"""
    
    print("\n" + "="*70)
    print("DEMONSTRATION: Variable Conversation Intervals")
    print("="*70)
    
    if not Config.MOONSHOT_API_KEY:
        print("\n❌ Please set MOONSHOT_API_KEY environment variable")
        return
    
    # Test with interval = 3 (process every 3 conversations)
    user_id = "demo_interval_user"
    
    print(f"\n📋 Configuration:")
    print(f"   • Conversation Interval: 3 (process every 3rd conversation)")
    print(f"   • This simulates batched processing\n")
    
    agent = ConversationalAgent(user_id=user_id, memory_mode=MemoryMode.NOTES)
    
    processor = BackgroundMemoryProcessor(
        user_id=user_id,
        memory_mode=MemoryMode.NOTES,
        config=MemoryProcessorConfig(
            conversation_interval=3,  # Process every 3 conversations
            min_conversation_turns=1
        ),
        verbose=False
    )
    
    messages = [
        "I'm Tom and I work in finance.",
        "I use Excel and Python for data analysis.",
        "I'm learning SQL for database work.",  # Should trigger processing here
        "I also manage a team of 5 analysts.",
        "We focus on risk assessment.",
        "Our main tool is Bloomberg Terminal."  # Should trigger processing here
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n[Round {i}] User: {msg}")
        response = agent.chat(msg)
        print(f"Assistant: {response[:100]}...")
        
        processor.increment_conversation_count()
        
        if processor.should_process():
            print(f"\n🔔 Processing triggered after conversation {i}!")
            results = processor.process_recent_conversations()
            ops = results.get('operations', [])
            print(f"   Operations: {len(ops)} memory update(s)")
            for op in ops:
                print(f"   - {op['action']}: {op.get('content', '')[:50]}...")
        else:
            remaining = 3 - (i % 3) if (i % 3) != 0 else 3
            print(f"   [Will process in {remaining} more conversation(s)]")
    
    print("\n✅ Interval demonstration complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Demonstrate conversation-based processing")
    parser.add_argument(
        "--mode",
        choices=["single", "interval", "both"],
        default="single",
        help="Demonstration mode"
    )
    
    args = parser.parse_args()
    
    Config.create_directories()
    
    if args.mode == "single":
        demonstrate_conversation_processing()
    elif args.mode == "interval":
        demonstrate_interval_processing()
    else:
        demonstrate_conversation_processing()
        print("\n" + "="*70 + "\n")
        demonstrate_interval_processing()
