#!/usr/bin/env python3
"""
Test script for GorillaFileSystem MCP Functions

This script tests all mcp_ functions in the GorillaFileSystem class.
Run this to verify all file system operations work correctly.
"""

import sys
import os
import traceback

# Add the current directory to the path to import gorilla_file_system
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gorilla_file_system import GorillaFileSystem, ActionArguments


def test_mcp_functions():
    """Test all mcp_ functions in the GorillaFileSystem class."""
    print("🧪 Testing GorillaFileSystem MCP Functions")
    print("=" * 60)
    
    # Initialize the file system
    args = ActionArguments(
        name="GorillaFileSystem",
        transport="sse"
    )
    
    file_system = GorillaFileSystem(args)
    
    # Load default scenario
    default_scenario = {
        "root": {
            "workspace": {
                "type": "directory",
                "contents": {
                    "projects": {
                        "type": "directory",
                        "contents": {
                            "web_app": {
                                "type": "directory",
                                "contents": {
                                    "src": {
                                        "type": "directory",
                                        "contents": {
                                            "main.py": {
                                                "type": "file",
                                                "content": "#!/usr/bin/env python3\nfrom flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello World!'\n\nif __name__ == '__main__':\n    app.run(debug=True)"
                                            },
                                            "utils.py": {
                                                "type": "file",
                                                "content": "# Utility functions\nimport os\nimport json\n\ndef load_config(path):\n    with open(path, 'r') as f:\n        return json.load(f)\n\ndef get_file_size(path):\n    return os.path.getsize(path)"
                                            }
                                        }
                                    },
                                    "README.md": {
                                        "type": "file",
                                        "content": "# MyWebApp\n\nA simple Flask web application.\n\n## Features\n- Hello World endpoint\n- Configuration management\n\n## Setup\n1. Install dependencies: `pip install flask`\n2. Run the app: `python src/main.py`"
                                    }
                                }
                            }
                        }
                    },
                    "temp": {
                        "type": "directory",
                        "contents": {}
                    }
                }
            }
        }
    }
    
    file_system._load_scenario(default_scenario)
    
    # Test results tracking
    tests_passed = 0
    tests_failed = 0
    
    def run_test(test_name, test_func):
        """Run a test and track results."""
        nonlocal tests_passed, tests_failed
        try:
            print(f"\n🔍 Testing {test_name}...")
            result = test_func()
            print(f"✅ {test_name}: PASSED")
            print(f"   Result: {result}")
            tests_passed += 1
            return result
        except Exception as e:
            print(f"❌ {test_name}: FAILED")
            print(f"   Error: {e}")
            tests_failed += 1
            return None
    
    # Test 1: mcp_pwd
    def test_pwd():
        return file_system.mcp_pwd()
    
    run_test("mcp_pwd", test_pwd)
    
    # Test 2: mcp_ls
    def test_ls():
        return file_system.mcp_ls()
    
    run_test("mcp_ls", test_ls)
    
    # Test 3: mcp_ls with hidden files
    def test_ls_hidden():
        return file_system.mcp_ls(a=True)
    
    run_test("mcp_ls (with hidden files)", test_ls_hidden)
    
    # Test 4: mcp_cd
    def test_cd():
        return file_system.mcp_cd("projects")
    
    run_test("mcp_cd", test_cd)
    
    # Test 5: mcp_mkdir
    def test_mkdir():
        return file_system.mcp_mkdir("test_dir")
    
    run_test("mcp_mkdir", test_mkdir)
    
    # Test 6: mcp_touch
    def test_touch():
        return file_system.mcp_touch("test_file.txt")
    
    run_test("mcp_touch", test_touch)
    
    # Test 7: mcp_echo (to file)
    def test_echo_to_file():
        return file_system.mcp_echo("Hello, FastMCP!", "test_file.txt")
    
    run_test("mcp_echo (to file)", test_echo_to_file)
    
    # Test 8: mcp_echo (to terminal)
    def test_echo_to_terminal():
        return file_system.mcp_echo("Hello, Terminal!")
    
    run_test("mcp_echo (to terminal)", test_echo_to_terminal)
    
    # Test 9: mcp_cat
    def test_cat():
        return file_system.mcp_cat("test_file.txt")
    
    run_test("mcp_cat", test_cat)
    
    # Test 10: mcp_find
    def test_find():
        return file_system.mcp_find(name="test")
    
    run_test("mcp_find", test_find)
    
    # Test 11: mcp_wc (words)
    def test_wc_words():
        return file_system.mcp_wc("test_file.txt", "w")
    
    run_test("mcp_wc (words)", test_wc_words)
    
    # Test 12: mcp_wc (lines)
    def test_wc_lines():
        return file_system.mcp_wc("test_file.txt", "l")
    
    run_test("mcp_wc (lines)", test_wc_lines)
    
    # Test 13: mcp_wc (characters)
    def test_wc_chars():
        return file_system.mcp_wc("test_file.txt", "c")
    
    run_test("mcp_wc (characters)", test_wc_chars)
    
    # Test 14: mcp_sort
    def test_sort():
        # Create a file with unsorted content
        file_system.mcp_echo("zebra\napple\nbanana\ncat", "unsorted.txt")
        return file_system.mcp_sort("unsorted.txt")
    
    run_test("mcp_sort", test_sort)
    
    # Test 15: mcp_grep
    def test_grep():
        return file_system.mcp_grep("test_file.txt", "Hello")
    
    run_test("mcp_grep", test_grep)
    
    # Test 16: mcp_du
    def test_du():
        return file_system.mcp_du()
    
    run_test("mcp_du", test_du)
    
    # Test 17: mcp_du (human readable)
    def test_du_human():
        return file_system.mcp_du(human_readable=True)
    
    run_test("mcp_du (human readable)", test_du_human)
    
    # Test 18: mcp_tail
    def test_tail():
        # Create a file with multiple lines
        file_system.mcp_echo("line1\nline2\nline3\nline4\nline5", "multi_line.txt")
        return file_system.mcp_tail("multi_line.txt", 3)
    
    run_test("mcp_tail", test_tail)
    
    # Test 19: mcp_diff
    def test_diff():
        # Create two different files
        file_system.mcp_echo("apple\nbanana\ncherry", "file1.txt")
        file_system.mcp_echo("apple\norange\ncherry", "file2.txt")
        return file_system.mcp_diff("file1.txt", "file2.txt")
    
    run_test("mcp_diff", test_diff)
    
    # Test 20: mcp_mv
    def test_mv():
        return file_system.mcp_mv("test_file.txt", "renamed_file.txt")
    
    run_test("mcp_mv", test_mv)
    
    # Test 21: mcp_cp
    def test_cp():
        return file_system.mcp_cp("renamed_file.txt", "copied_file.txt")
    
    run_test("mcp_cp", test_cp)
    
    # Test 22: mcp_rm
    def test_rm():
        return file_system.mcp_rm("copied_file.txt")
    
    run_test("mcp_rm", test_rm)
    
    # Test 23: mcp_rmdir
    def test_rmdir():
        # Create an empty directory first
        file_system.mcp_mkdir("empty_dir")
        return file_system.mcp_rmdir("empty_dir")
    
    run_test("mcp_rmdir", test_rmdir)
    
    # Test 24: mcp_cd (back to parent)
    def test_cd_parent():
        return file_system.mcp_cd("..")
    
    run_test("mcp_cd (parent)", test_cd_parent)
    
    # Test 25: mcp_cd (absolute path)
    def test_cd_absolute():
        return file_system.mcp_cd("/workspace")
    
    run_test("mcp_cd (absolute)", test_cd_absolute)
    
    # Test 26: Error handling - mcp_cat non-existent file
    def test_cat_error():
        return file_system.mcp_cat("non_existent_file.txt")
    
    run_test("mcp_cat (error case)", test_cat_error)
    
    # Test 27: Error handling - mcp_mkdir existing directory
    def test_mkdir_error():
        return file_system.mcp_mkdir("test_dir")  # Should fail as it already exists
    
    run_test("mcp_mkdir (error case)", test_mkdir_error)
    
    # Test 28: Error handling - mcp_touch existing file
    def test_touch_error():
        return file_system.mcp_touch("renamed_file.txt")  # Should fail as it already exists
    
    run_test("mcp_touch (error case)", test_touch_error)
    
    # Test 29: Error handling - mcp_rmdir non-empty directory
    def test_rmdir_error():
        return file_system.mcp_rmdir("test_dir")  # Should fail as it's not empty
    
    run_test("mcp_rmdir (error case)", test_rmdir_error)
    
    # Test 30: Error handling - mcp_cd non-existent directory
    def test_cd_error():
        return file_system.mcp_cd("non_existent_dir")
    
    run_test("mcp_cd (error case)", test_cd_error)
    
    # Print final results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    print(f"📈 Total Tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! GorillaFileSystem is working correctly.")
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please check the errors above.")
    
    return tests_failed == 0


def main():
    """Main function to run the tests."""
    print("🔧 GorillaFileSystem MCP Functions Test Suite")
    print("Testing all mcp_ functions in the GorillaFileSystem class")
    
    try:
        success = test_mcp_functions()
        if success:
            print("\n🚀 All tests completed successfully!")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main() 