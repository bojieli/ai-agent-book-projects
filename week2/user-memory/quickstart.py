#!/usr/bin/env python3
"""
Quick start script for User Memory System with Separated Architecture
Demonstrates conversation-based memory processing
"""

import os
import sys
import time
from dotenv import load_dotenv
from conversational_agent import ConversationalAgent, ConversationConfig
from background_memory_processor import BackgroundMemoryProcessor, MemoryProcessorConfig
from config import Config, MemoryMode
from memory_manager import create_memory_manager
from memory_operation_formatter import display_memory_operations

# Load environment variables
load_dotenv()


def quickstart():
    """Run a quick demonstration of the memory system with separated architecture"""
    print("\n" + "="*60)
    print("🚀 USER MEMORY SYSTEM - QUICK START")
    print("   (Conversation-Based Memory Processing)")
    print("="*60)
    
    # Check configuration
    if not Config.MOONSHOT_API_KEY:
        print("\n❌ ERROR: MOONSHOT_API_KEY not found!")
        print("\nPlease set up your .env file with:")
        print("  MOONSHOT_API_KEY=your_api_key_here")
        print("\nYou can get an API key from: https://platform.moonshot.cn/")
        sys.exit(1)
    
    # Create directories
    Config.create_directories()
    
    # Setup demo user
    user_id = "quickstart_user"
    memory_mode = MemoryMode.NOTES
    
    print(f"\n📌 Setting up separated architecture:")
    print(f"   • User: {user_id}")
    print(f"   • Memory Mode: {memory_mode.value}")
    print(f"   • Processing: After each conversation round")
    
    # Initialize conversational agent
    print("\n🤖 Initializing conversational agent...")
    agent = ConversationalAgent(
        user_id=user_id,
        memory_mode=memory_mode,
        config=ConversationConfig(
            enable_memory_context=True,
            enable_conversation_history=True
        ),
        verbose=False
    )
    
    # Initialize background memory processor
    print("🧠 Initializing memory processor...")
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
    
    print("✅ System initialized\n")
    
    # Session 1: Introduction
    print("="*60)
    print("SESSION 1: INTRODUCTION & LEARNING")
    print("="*60)
    
    intro_messages = [
        "Hi! I'm Alex, a software developer who loves Python and machine learning.",
        "I'm currently working on a recommendation system project using PyTorch.",
        "I prefer dark themes in my IDE and always use type hints in my Python code."
    ]
    
    for i, msg in enumerate(intro_messages, 1):
        print(f"\n[Conversation Round {i}]")
        print(f"👤 User: {msg}")
        
        # Have conversation
        response = agent.chat(msg)
        print(f"🤖 Assistant: {response[:150]}..." if len(response) > 150 else f"🤖 Assistant: {response}")
        
        # Trigger memory processing after each conversation
        processor.increment_conversation_count()
        
        print(f"\n📝 Processing memory after conversation {i}...")
        results = processor.process_recent_conversations()
        
        # Display memory operations
        operations = results.get('operations', [])
        if operations:
            print("\nMemory Operations:")
            for j, op in enumerate(operations, 1):
                icon = {'add': '➕', 'update': '📝', 'delete': '🗑️'}.get(op['action'], '❓')
                print(f"  {j}. {icon} {op['action'].upper()}: {op.get('content', '')[:80]}...")
        else:
            print("  ℹ️ No memory updates needed")
        
        summary = results.get('summary', {})
        if any(summary.values()):
            print(f"  Summary: {summary.get('added', 0)} added, {summary.get('updated', 0)} updated")
    
    # Show current memory state
    print("\n" + "="*40)
    print("💾 MEMORY STATE AFTER SESSION 1")
    print("="*40)
    memory_manager = create_memory_manager(user_id, memory_mode)
    print(memory_manager.get_context_string())
    
    # Session 2: Testing memory recall and updates
    print("\n" + "="*60)
    print("SESSION 2: MEMORY RECALL & UPDATES")
    print("="*60)
    
    # Start new conversation session
    agent.reset_session()
    print("🔄 Started new conversation session\n")
    
    recall_messages = [
        "What do you remember about my work and preferences?",
        "Actually, I recently switched from PyTorch to JAX for better performance.",
        "Can you recommend tools for my recommendation system based on what you know about me?"
    ]
    
    for i, msg in enumerate(recall_messages, 1):
        print(f"\n[Conversation Round {i}]")
        print(f"👤 User: {msg}")
        
        # Have conversation
        response = agent.chat(msg)
        
        # Show full response for memory recall questions
        if "remember" in msg.lower() or "recommend" in msg.lower():
            print(f"🤖 Assistant: {response}")
        else:
            print(f"🤖 Assistant: {response[:150]}..." if len(response) > 150 else f"🤖 Assistant: {response}")
        
        # Trigger memory processing
        processor.increment_conversation_count()
        
        print(f"\n📝 Processing memory after conversation {i}...")
        results = processor.process_recent_conversations()
        
        # Display memory operations
        operations = results.get('operations', [])
        if operations:
            print("\nMemory Operations:")
            for j, op in enumerate(operations, 1):
                icon = {'add': '➕', 'update': '📝', 'delete': '🗑️'}.get(op['action'], '❓')
                content = op.get('content', op.get('memory_id', 'N/A'))
                print(f"  {j}. {icon} {op['action'].upper()}: {content[:80]}...")
                if op.get('reason'):
                    print(f"     Reason: {op['reason'][:80]}...")
        else:
            print("  ℹ️ No memory updates needed")
        
        summary = results.get('summary', {})
        if any(summary.values()):
            print(f"  Summary: {summary.get('added', 0)} added, {summary.get('updated', 0)} updated")
    
    # Final memory state
    print("\n" + "="*40)
    print("💾 FINAL MEMORY STATE")
    print("="*40)
    memory_manager = create_memory_manager(user_id, memory_mode)
    final_memory = memory_manager.get_context_string()
    print(final_memory if final_memory else "No memories stored")
    
    # Summary
    print("\n" + "="*60)
    print("✨ QUICK START COMPLETED!")
    print("="*60)
    print("\n🎯 Key Features Demonstrated:")
    print("  • Separated conversation and memory processing")
    print("  • Memory operations after each conversation round")
    print("  • Clear list of add/update/delete operations")
    print("  • Memory persistence across sessions")
    
    print("\n📚 Next Steps:")
    print("  1. Interactive mode: python main.py --mode interactive --user your_name")
    print("  2. Adjust processing: --conversation-interval 2 (process every 2 conversations)")
    print("  3. Manual processing: --background-processing False")
    print("  4. Try JSON cards: --memory-mode json_cards")
    print("  5. Run full demo: python main.py --mode demo")


if __name__ == "__main__":
    quickstart()