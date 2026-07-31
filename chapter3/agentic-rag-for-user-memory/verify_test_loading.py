#!/usr/bin/env python3
"""Verify test case loading with correct field mapping"""

import os
import sys
from pathlib import Path

# Set dummy API key
os.environ["KIMI_API_KEY"] = os.getenv("KIMI_API_KEY", "test-kimi-key")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-openai-key")

from config import Config
from evaluator import UserMemoryEvaluator

# Initialize evaluator
config = Config.from_env()
evaluator = UserMemoryEvaluator(config)

# Load test cases
test_cases = evaluator.load_test_cases(category="layer1")

if test_cases:
    print(f"\nLoaded {len(test_cases)} test cases")
    
    # Check first test case
    test_id = test_cases[0]
    test_case = evaluator.test_cases[test_id]
    
    print(f"\nTest Case: {test_id}")
    print(f"  Title: {test_case.title}")
    print(f"  Category: {test_case.category}")
    print(f"  User Question: {test_case.user_question}")
    print(f"  Evaluation Criteria: {test_case.evaluation_criteria[:200]}..." if test_case.evaluation_criteria else "  Evaluation Criteria: None")
    print(f"  Expected Behavior: {test_case.expected_behavior[:100]}..." if test_case.expected_behavior else "  Expected Behavior: None")
    print(f"  Conversations: {len(test_case.conversation_histories)}")
    
    # Check conversation history structure
    if test_case.conversation_histories:
        conv = test_case.conversation_histories[0]
        print(f"\nFirst Conversation:")
        print(f"  ID: {conv.get('conversation_id', 'N/A')}")
        print(f"  Timestamp: {conv.get('timestamp', 'N/A')}")
        print(f"  Messages: {len(conv.get('messages', []))}")
        print(f"  Has metadata: {bool(conv.get('metadata', {}))}")
        
    print("\n✓ Test case structure is correct")
else:
    print("✗ No test cases loaded")
