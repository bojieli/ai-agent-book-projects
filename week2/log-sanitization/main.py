#!/usr/bin/env python3
"""
Main script for Log Sanitization using Local LLM
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from agent import LogSanitizationAgent
from test_loader import TestCaseLoader
from config import OUTPUT_DIR


def main(test_id: Optional[str] = None, limit: Optional[int] = None):
    """
    Main function to run log sanitization
    
    Args:
        test_id: Specific test case ID to process (optional)
        limit: Maximum number of test cases to process (optional)
    """
    print("🚀 Starting Log Sanitization with Local LLM")
    print("=" * 60)
    
    # Initialize components
    try:
        print("📦 Loading test cases from user-memory-evaluation...")
        loader = TestCaseLoader()
        
        print("🤖 Initializing Ollama agent...")
        agent = LogSanitizationAgent()
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return 1
    
    # Get test cases to process
    if test_id:
        # Process specific test case
        print(f"\n📋 Processing specific test case: {test_id}")
        conversations = loader.get_test_case_conversations(test_id)
        
        if not conversations:
            print(f"❌ Test case {test_id} not found or has no conversations")
            return 1
        
        agent.process_test_case(test_id, conversations)
        
    else:
        # Process Layer 3 test cases (most complex, likely to have PII)
        print("\n📋 Getting Layer 3 test cases...")
        test_cases = loader.get_layer3_test_cases()
        
        if not test_cases:
            print("❌ No Layer 3 test cases found")
            return 1
        
        print(f"Found {len(test_cases)} Layer 3 test cases")
        
        # Apply limit if specified
        if limit:
            test_cases = test_cases[:limit]
            print(f"Processing first {limit} test cases")
        
        # Process each test case
        for i, tc in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Test Case: {tc['test_id']}")
            print(f"   Title: {tc['title']}")
            print(f"   Conversations: {tc['num_conversations']}")
            
            # Get conversation histories
            conversations = loader.get_test_case_conversations(tc['test_id'])
            
            if conversations:
                agent.process_test_case(tc['test_id'], conversations)
            else:
                print(f"   ⚠️  No conversations found for {tc['test_id']}")
    
    print("\n" + "=" * 60)
    print("✅ Log Sanitization Complete!")
    print(f"📁 Results saved to: {OUTPUT_DIR}")
    
    return 0


def demo_mode():
    """Run a quick demo with sample PII-containing text"""
    print("🎯 Running Demo Mode")
    print("=" * 60)
    
    # Create a sample conversation with Level 3 PII
    sample_conversation = {
        'conversation_id': 'demo_001',
        'timestamp': '2024-01-01 10:00:00',
        'messages': [
            {
                'role': 'user',
                'content': 'I need to update my information. My SSN is 123-45-6789.'
            },
            {
                'role': 'assistant',
                'content': 'I can help you update your information. Can you confirm your credit card?'
            },
            {
                'role': 'user',
                'content': 'Yes, it\'s 4532 1234 5678 9012. Also, my medical record number is MRN-789456.'
            },
            {
                'role': 'assistant',
                'content': 'Thank you. I\'ve noted your SSN ending in 6789 and card ending in 9012.'
            },
            {
                'role': 'user',
                'content': 'Great. My driver\'s license is DL-123456789 and passport is P987654321.'
            }
        ]
    }
    
    try:
        agent = LogSanitizationAgent()
        print("\n📝 Sample conversation created with Level 3 PII")
        print("🔍 Detecting and sanitizing PII...\n")
        
        result = agent.sanitize_conversation(sample_conversation, 'demo')
        
        print("\n" + "=" * 60)
        print("DEMO RESULTS")
        print("=" * 60)
        print(f"PII Items Found: {len(result['pii_found'])}")
        for pii in result['pii_found']:
            print(f"  - {pii}")
        
        print(f"\nReplacements Made: {result['replacements_made']}")
        print("\n--- SANITIZED TEXT ---")
        print(result['sanitized_text'])
        
        # Save demo results
        agent.save_sanitized_log('demo', [result])
        agent.metrics_collector.save_metrics()
        agent.metrics_collector.print_summary()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sanitize conversation logs using local LLM to detect and redact Level 3 PII"
    )
    
    parser.add_argument(
        '--test-id',
        type=str,
        help='Specific test case ID to process'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of test cases to process'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo mode with sample PII data'
    )
    
    args = parser.parse_args()
    
    if args.demo:
        exit_code = demo_mode()
    else:
        exit_code = main(test_id=args.test_id, limit=args.limit)
    
    sys.exit(exit_code)
