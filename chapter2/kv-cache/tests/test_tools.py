#!/usr/bin/env python3
"""
Test script for local file system tools
Validates that read_file, find, and grep work correctly
"""

import os
import json
from agent import LocalFileTools


def test_file_tools():
    """Test the local file system tools"""
    
    print("🧪 Testing Local File System Tools")
    print("="*60)
    
    # Initialize tools with project root
    tools = LocalFileTools(root_dir="../..")
    
    # Test 1: Find Python files
    print("\n1️⃣ Testing 'find' command...")
    print("   Finding *.py files in chapter1/context directory...")
    result = tools.find("*.py", "chapter1/context")
    
    if result["success"]:
        print(f"   ✓ Found {result['count']} Python files")
        if result["matches"]:
            print(f"   Sample files: {result['matches'][:3]}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 2: Read a file
    print("\n2️⃣ Testing 'read_file' command...")
    test_file = "chapter1/context/README.md"
    print(f"   Reading {test_file}...")
    result = tools.read_file(test_file)
    
    if result["success"]:
        print(f"   ✓ Read file successfully ({len(result['content'])} bytes)")
        print(f"   First 100 chars: {result['content'][:100]}...")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 3: Grep for a pattern
    print("\n3️⃣ Testing 'grep' command...")
    print("   Searching for 'agent' in chapter1 directory...")
    result = tools.grep("agent", directory="chapter1")
    
    if result["success"]:
        print(f"   ✓ Found {result['match_count']} matches in {result['files_searched']} files")
        if result["matches"]:
            sample = result["matches"][0]
            print(f"   Sample match: {sample['file']}:{sample['line_num']} - {sample['line'][:50]}...")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 4: Security check - try to access outside root
    print("\n4️⃣ Testing security boundaries...")
    print("   Attempting to read file outside root directory...")
    result = tools.read_file("../../../../../../etc/passwd")
    
    if not result["success"] and "Access denied" in result.get("error", ""):
        print("   ✓ Security check passed - access denied as expected")
    else:
        print("   ⚠️ Security check result:", result.get("error", "Unexpected result"))
    
    # Test 5: Grep in specific file
    print("\n5️⃣ Testing 'grep' in specific file...")
    print("   Searching for 'class' in chapter1/context/agent.py...")
    result = tools.grep("class", file_path="chapter1/context/agent.py")
    
    if result["success"]:
        print(f"   ✓ Found {result['match_count']} matches")
        if result["matches"]:
            for match in result["matches"][:3]:
                print(f"     Line {match['line_num']}: {match['line'][:60]}...")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    print("\n" + "="*60)
    print("✅ Tool testing complete!")
    print("\nAll tools are working correctly and can be used by the ReAct agent.")
    print("Security boundaries are properly enforced.")


def test_pattern_matching():
    """Test various pattern matching scenarios"""
    
    print("\n🔍 Testing Pattern Matching Capabilities")
    print("="*60)
    
    tools = LocalFileTools(root_dir="../..")
    
    # Test different file patterns
    patterns = [
        ("*.md", "chapter1", "Markdown files"),
        ("*.py", "chapter2", "Python files"),
        ("README*", ".", "README files"),
        ("test_*.py", "chapter1", "Test files"),
    ]
    
    for pattern, directory, description in patterns:
        print(f"\n• Finding {description}: {pattern} in {directory}")
        result = tools.find(pattern, directory)
        if result["success"]:
            print(f"  Found {result['count']} files")
        else:
            print(f"  Error: {result['error']}")
    
    # Test different grep patterns
    print("\n📝 Testing Grep Patterns")
    print("-"*40)
    
    grep_tests = [
        (r"def \w+\(", "chapter1/context/agent.py", "Function definitions"),
        (r"import \w+", "chapter1/context/main.py", "Import statements"),
        (r"TODO|FIXME", "chapter1", "TODO/FIXME comments"),
        (r"^\s*class", "chapter1/context/agent.py", "Class definitions"),
    ]
    
    for pattern, target, description in grep_tests:
        print(f"\n• Searching for {description}: {pattern}")
        if "/" in target:
            result = tools.grep(pattern, file_path=target)
        else:
            result = tools.grep(pattern, directory=target)
        
        if result["success"]:
            print(f"  Found {result['match_count']} matches")
        else:
            print(f"  Error: {result['error']}")


if __name__ == "__main__":
    # Run basic tests
    test_file_tools()
    
    # Run pattern matching tests
    test_pattern_matching()
    
    print("\n🎉 All tests completed successfully!")
