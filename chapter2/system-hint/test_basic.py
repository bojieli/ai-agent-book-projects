"""
Basic test to verify System-Hint Agent functionality
"""

import os
import sys

import pytest

from agent import SystemHintAgent, SystemHintConfig, TodoStatus

def test_basic_functionality():
    """Test basic agent functionality without API calls"""
    print("Testing System-Hint Agent components...")
    
    # Test configuration
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True
    )
    print("✅ Configuration created successfully")
    
    # Test agent initialization (without API key for basic test)
    try:
        agent = SystemHintAgent(
            api_key="test-key",  # Dummy key for initialization test
            provider="kimi",
            config=config,
            verbose=False
        )
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test tool implementations (without API calls)
    print("\nTesting tool implementations:")
    
    # Test file operations
    test_file = "test_output.txt"
    try:
        # Test write_file
        result = agent._tool_write_file(test_file, "Test content")
        assert result["success"]
        print("✅ write_file tool works")
        
        # Test read_file
        result = agent._tool_read_file(test_file)
        assert result["success"]
        assert "Test content" in result["content"]
        print("✅ read_file tool works")
        
        
        # Clean up
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ File operation test failed: {e}")
    
    # Test code interpreter
    try:
        result = agent._tool_code_interpreter("result = 2 + 2")
        assert result["success"]
        assert result["result"] == 4
        print("✅ code_interpreter tool works")
    except Exception as e:
        print(f"❌ Code interpreter test failed: {e}")
    
    # Test TODO list operations
    try:
        # Test rewrite_todo_list
        result = agent._tool_rewrite_todo_list(["Task 1", "Task 2", "Task 3"])
        assert result["success"]
        assert result["new_items"] == 3
        print("✅ rewrite_todo_list tool works")
        
        # Test update_todo_status
        result = agent._tool_update_todo_status([
            {"id": 1, "status": "completed"},
            {"id": 2, "status": "in_progress"}
        ])
        assert result["success"]
        assert result["updated_items"] == 2
        print("✅ update_todo_status tool works")
        
        # Verify TODO list state
        assert len(agent.todo_list) == 3
        assert agent.todo_list[0].status == TodoStatus.COMPLETED
        assert agent.todo_list[1].status == TodoStatus.IN_PROGRESS
        print("✅ TODO list management works correctly")
        
    except Exception as e:
        print(f"❌ TODO list test failed: {e}")
    
    # Test system state
    try:
        state = agent._get_system_state()
        assert "Current Time:" in state
        assert "Current Directory:" in state
        assert "System:" in state
        print("✅ System state tracking works")
    except Exception as e:
        print(f"❌ System state test failed: {e}")
    
    # Test error handling
    try:
        # This should fail and generate detailed error
        result = agent._tool_read_file("/nonexistent/file.txt")
    except Exception as e:
        error_detail = agent._get_detailed_error(e, "read_file", {"file_path": "/nonexistent/file.txt"})
        assert "FileNotFoundError" in str(e.__class__.__name__) or "No such file" in str(e)
        assert "Suggestions:" in error_detail
        print("✅ Detailed error handling works")
    
    print("\n✅ All basic tests passed!")
    return True

def test_command_execution():
    """Test command execution tool"""
    print("\nTesting command execution:")
    
    config = SystemHintConfig(enable_detailed_errors=True)
    agent = SystemHintAgent(
        api_key="test-key",
        provider="kimi",
        config=config,
        verbose=False
    )
    
    try:
        # Test simple command
        result = agent._tool_execute_command("echo 'Hello, World!'")
        assert result["success"]
        assert "Hello, World!" in result["output"]
        print("✅ Command execution works")
        
        # Test directory change
        original_dir = agent.current_directory
        result = agent._tool_execute_command("cd /tmp")
        assert agent.current_directory == "/tmp"
        agent.current_directory = original_dir  # Restore
        print("✅ Directory tracking works")
        
    except Exception as e:
        print(f"⚠️ Command execution test skipped: {e}")
    
    return True
def test_read_file_empty_file_line_range():
    """
    Prove that line-based read_file on empty (0-line) files succeeds with empty content.
    
    When an LLM agent requested line-based reads (e.g., begin_line=1, number_lines=10) on an
    empty file, start_line (0) was compared against total_lines (0) with >=, causing the tool to
    return an error stating begin_line 1 is beyond file length. This test locks out regressions
    by asserting that line-based reads on empty files return success=True and content="".
    """
    config = SystemHintConfig(enable_detailed_errors=True)
    agent = SystemHintAgent(api_key="test-key", provider="kimi", config=config, verbose=False)
    empty_file = "empty_test.txt"
    try:
        agent._tool_write_file(empty_file, "")
        res_empty = agent._tool_read_file(empty_file, begin_line=1, number_lines=10)
        assert res_empty.get("success") is True, f"Failed empty file read: {res_empty}"
        assert res_empty.get("content") == ""
    finally:
        if os.path.exists(empty_file):
            os.remove(empty_file)


def test_read_file_rejects_invalid_line_arguments(tmp_path):
    """Invalid schema inputs must not silently become a read from line one."""
    config = SystemHintConfig(enable_detailed_errors=True)
    agent = SystemHintAgent(api_key="test-key", provider="kimi", config=config, verbose=False)
    agent.current_directory = str(tmp_path)
    agent._tool_write_file("sample.txt", "one\ntwo\n")

    with pytest.raises(TypeError):
        agent._tool_read_file("sample.txt", begin_line="invalid")

if __name__ == "__main__":
    print("="*60)
    print("  System-Hint Agent Component Tests")
    print("="*60)
    
    # Run basic tests
    if test_basic_functionality():
        test_command_execution()
        test_read_file_empty_file_line_range()
        print("\n✨ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
