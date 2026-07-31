#!/usr/bin/env python3
"""
Test script for the read_file tool with offset and size parameters
"""

from agent import LocalFileTools

def test_file_range_reading():
    """Test reading files with offset and size parameters"""
    
    print("🧪 Testing File Range Reading")
    print("="*60)
    
    # Initialize tools
    tools = LocalFileTools(root_dir="../..")
    
    # Test file
    test_file = "chapter1/context/agent.py"
    
    # Test 1: Read first 10 lines
    print("\n1️⃣ Reading first 10 lines:")
    result = tools.read_file(test_file, offset=0, size=10)
    if result["success"]:
        print(f"   ✓ Read {result['lines_read']} lines from total {result['total_lines']}")
        print(f"   Range: lines {result['offset']}-{result['end_line']}")
        print(f"   First line: {result['content'].split(chr(10))[0][:50]}...")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 2: Read lines 100-110
    print("\n2️⃣ Reading lines 100-110:")
    result = tools.read_file(test_file, offset=100, size=10)
    if result["success"]:
        print(f"   ✓ Read {result['lines_read']} lines")
        print(f"   Range: lines {result['offset']}-{result['end_line']}")
        lines = result['content'].split('\n')
        if lines:
            print(f"   Sample: {lines[0][:60]}...")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 3: Read from offset 250 with size 500 (as specified)
    print("\n3️⃣ Reading from offset 250, size 500:")
    result = tools.read_file(test_file, offset=250, size=500)
    if result["success"]:
        print(f"   ✓ Read {result['lines_read']} lines")
        print(f"   Range: lines {result['offset']}-{result['end_line']}")
        print(f"   Total file has {result['total_lines']} lines")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 4: Read without size (from offset to end)
    print("\n4️⃣ Reading from offset 700 to end:")
    result = tools.read_file(test_file, offset=700)
    if result["success"]:
        print(f"   ✓ Read {result['lines_read']} lines")
        print(f"   Range: lines {result['offset']}-{result['end_line']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 5: Offset beyond file length
    print("\n5️⃣ Testing offset beyond file length:")
    result = tools.read_file(test_file, offset=10000, size=10)
    if result["success"]:
        print(f"   ✓ Handled gracefully: {result.get('message', 'No error')}")
        print(f"   Lines read: {result['lines_read']}")
    else:
        print(f"   Result: {result}")
    
    # Test 6: Read entire file (no offset, no size)
    print("\n6️⃣ Reading entire file (default behavior):")
    result = tools.read_file("chapter1/context/README.md")
    if result["success"]:
        print(f"   ✓ Read entire file")
        print(f"   Total lines: {result['total_lines']}")
        print(f"   Lines read: {result['lines_read']}")
        print(f"   Truncated: {result.get('truncated', False)}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 7: Compare with limit parameter (the user's original request)
    print("\n7️⃣ API-style usage (offset=250, size=500):")
    result = tools.read_file("chapter2/local_llm_serving/main.py", offset=250, size=500)
    if result["success"]:
        print(f"   ✓ Successfully read lines {result['offset']}-{result['end_line']}")
        print(f"   Lines read: {result['lines_read']}")
        print(f"   File has {result['total_lines']} total lines")
        
        # Show a sample of the content
        lines = result['content'].split('\n')[:3]
        print("\n   First 3 lines of content:")
        for i, line in enumerate(lines):
            print(f"     Line {250+i}: {line[:60]}..." if len(line) > 60 else f"     Line {250+i}: {line}")
    
    print("\n" + "="*60)
    print("✅ File range reading tests complete!")
    print("\nThe read_file tool now supports:")
    print("  • offset: Starting line number (0-based)")
    print("  • size: Number of lines to read")
    print("  • Handles edge cases gracefully")
    print("  • Maintains security boundaries")

if __name__ == "__main__":
    test_file_range_reading()
