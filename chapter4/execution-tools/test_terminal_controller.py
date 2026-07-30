"""
Tests for Terminal Controller.
Tests command execution with directory navigation and file operations.
"""
import asyncio
import json
import pytest

from config import Config
from terminal_controller import TerminalController


@pytest.fixture(scope="function")
def tc(tmp_path, monkeypatch):
    """Create terminal controller with temp workspace."""
    monkeypatch.setattr(Config, "WORKSPACE_DIR", tmp_path)
    return TerminalController()


class TestTerminalBasics:
    """Tests for basic terminal operations."""
    
    @pytest.mark.asyncio
    async def test_get_current_directory(self, tc):
        """Test getting current directory."""
        result = await tc.get_current_directory()
        
        assert result["success"] is True
        assert "current_directory" in result
        assert "workspace" in result
        
        print(f"✅ Current directory: {result['current_directory']}")
    
    @pytest.mark.asyncio
    async def test_execute_command_simple(self, tc):
        """Test executing a simple command."""
        result = await tc.execute_command("echo 'Hello World'")
        
        assert result["success"] is True
        assert "Hello World" in result["stdout"]
        assert result["returncode"] == 0
        
        print(f"✅ Command executed: {result['command']}")
    
    @pytest.mark.asyncio
    async def test_execute_command_ls(self, tc):
        """Test listing directory."""
        result = await tc.execute_command("ls")
        
        assert result["success"] is True
        print(f"✅ Directory listing completed")
    
    @pytest.mark.asyncio
    async def test_command_history(self, tc):
        """Test command history."""
        await tc.execute_command("echo 'test1'")
        await tc.execute_command("echo 'test2'")
        await tc.execute_command("echo 'test3'")
        
        result = await tc.get_command_history(count=2)
        
        assert result["success"] is True
        assert len(result["history"]) == 2
        assert result["total"] == 3
        
        print(f"✅ Command history: {result['count']} recent commands")


class TestDirectoryOperations:
    """Tests for directory navigation."""
    
    @pytest.mark.asyncio
    async def test_change_directory(self, tc):
        """Test changing directory."""
        # Create a subdirectory
        subdir = Config.WORKSPACE_DIR / "subdir"
        subdir.mkdir()
        
        result = await tc.change_directory("subdir")
        
        assert result["success"] is True
        assert "subdir" in result["current_directory"]
        
        print(f"✅ Changed to: {result['current_directory']}")
    
    @pytest.mark.asyncio
    async def test_list_directory(self, tc):
        """Test listing directory."""
        # Create some files
        (Config.WORKSPACE_DIR / "file1.txt").write_text("test")
        (Config.WORKSPACE_DIR / "file2.txt").write_text("test")
        
        result = await tc.list_directory(".")
        
        assert result["success"] is True
        assert result["count"] >= 2
        
        print(f"✅ Listed {result['count']} items")
    
    @pytest.mark.asyncio
    async def test_change_to_nonexistent(self, tc):
        """Test changing to nonexistent directory."""
        result = await tc.change_directory("nonexistent")
        
        assert result["success"] is False
        assert "does not exist" in result["error"]
        
        print("✅ Correctly rejected nonexistent directory")


class TestFileOperations:
    """Tests for file operations through terminal controller."""
    
    @pytest.mark.asyncio
    async def test_write_file(self, tc):
        """Test writing a file."""
        result = await tc.write_file("test.txt", "Hello Terminal")
        
        assert result["success"] is True
        assert result["bytes_written"] > 0
        
        # Verify file exists
        file_path = Config.WORKSPACE_DIR / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Hello Terminal"
        
        print(f"✅ Wrote {result['bytes_written']} bytes")
    
    @pytest.mark.asyncio
    async def test_read_file(self, tc):
        """Test reading a file."""
        # Create a file
        test_file = Config.WORKSPACE_DIR / "read_test.txt"
        test_file.write_text("Test content\nLine 2")
        
        result = await tc.read_file("read_test.txt")
        
        assert result["success"] is True
        assert result["content"] == "Test content\nLine 2"
        assert result["lines"] == 2
        
        print(f"✅ Read file: {result['lines']} lines")
    
    @pytest.mark.asyncio
    async def test_insert_file_content(self, tc):
        """Test inserting content into file."""
        # Create a file
        test_file = Config.WORKSPACE_DIR / "insert_test.txt"
        test_file.write_text("Line 1\nLine 3")
        
        result = await tc.insert_file_content("insert_test.txt", "Line 2", 2)
        
        assert result["success"] is True
        assert result["line_number"] == 2
        
        # Verify content
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines[1] == "Line 2"
        
        print("✅ Inserted content at line 2")
    
    @pytest.mark.asyncio
    async def test_delete_file_content(self, tc):
        """Test deleting lines from file."""
        # Create a file
        test_file = Config.WORKSPACE_DIR / "delete_test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4")
        
        result = await tc.delete_file_content("delete_test.txt", 2, 3)
        
        assert result["success"] is True
        assert result["deleted_lines"] == 2
        
        # Verify content
        content = test_file.read_text()
        assert "Line 2" not in content
        assert "Line 3" not in content
        assert "Line 1" in content
        assert "Line 4" in content
        
        print(f"✅ Deleted {result['deleted_lines']} lines")
    
    @pytest.mark.asyncio
    async def test_update_file_content(self, tc):
        """Test updating a line in file."""
        # Create a file
        test_file = Config.WORKSPACE_DIR / "update_test.txt"
        test_file.write_text("Line 1\nOld Line 2\nLine 3")
        
        result = await tc.update_file_content("update_test.txt", 2, "New Line 2")
        
        assert result["success"] is True
        assert result["old_content"] == "Old Line 2"
        assert result["new_content"] == "New Line 2"
        
        # Verify content
        content = test_file.read_text()
        assert "New Line 2" in content
        assert "Old Line 2" not in content
        
        print("✅ Updated line 2")


if __name__ == "__main__":
    print("=" * 70)
    print("Running Terminal Controller Tests")
    print("=" * 70)
    print()
    
    pytest.main([__file__, "-v", "-s"])
