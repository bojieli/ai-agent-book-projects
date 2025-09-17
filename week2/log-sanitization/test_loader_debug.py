#!/usr/bin/env python3
"""Debug script to test loading conversations"""

from test_loader import TestCaseLoader

def main():
    loader = TestCaseLoader()
    
    # Get all test cases
    print("Getting all test cases...")
    all_cases = loader.get_all_test_cases()
    print(f"Found {len(all_cases)} test cases")
    
    # Get Layer 3 test cases
    layer3_cases = loader.get_layer3_test_cases()
    print(f"Found {len(layer3_cases)} Layer 3 test cases")
    
    if layer3_cases:
        # Try to load the first one
        first_case = layer3_cases[0]
        print(f"\nTrying to load: {first_case['test_id']}")
        
        conversations = loader.get_test_case_conversations(first_case['test_id'])
        
        if conversations:
            print(f"Successfully loaded {len(conversations)} conversations")
            # Print first conversation snippet
            if conversations[0]['messages']:
                print(f"First message: {conversations[0]['messages'][0]['content'][:100]}...")
        else:
            print("Failed to load conversations")

if __name__ == "__main__":
    main()
