"""
Test cases for Edit tool
Tests all features from tools.json
"""

import pytest
from pathlib import Path
from tools.edit_tool import EditTool


class TestEditTool:
    """Test Edit tool functionality"""
    
    def test_basic_edit(self, system_state, sample_files):
        """Test basic search and replace"""
        tool = EditTool(system_state)
        file_path = sample_files["python_file"]
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "Hello, {name}!",
            "new_string": "Hi, {name}!"
        })
        
        assert result.success
        assert result.data["replacements"] == 1
        assert "Hi, {name}!" in file_path.read_text()
    
    def test_replace_all_flag(self, system_state, temp_dir):
        """Test replace_all parameter"""
        tool = EditTool(system_state)
        file_path = temp_dir / "multi.txt"
        file_path.write_text("foo bar foo baz foo")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "foo",
            "new_string": "replaced",
            "replace_all": True
        })
        
        assert result.success
        assert result.data["replacements"] == 3
        assert file_path.read_text() == "replaced bar replaced baz replaced"

    def test_empty_old_string_replace_all_rejected(self, system_state, temp_dir):
        """Empty old_string with replace_all must not insert between every character."""
        tool = EditTool(system_state)
        file_path = temp_dir / "empty_old.txt"
        original = "abcd"
        file_path.write_text(original)

        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "",
            "new_string": "X",
            "replace_all": True,
        })

        assert "error" in result.data
        assert "empty" in result.data["error"].lower()
        assert file_path.read_text() == original
    
    def test_uniqueness_check(self, system_state, temp_dir):
        """Test that Edit fails if old_string is not unique (without replace_all)"""
        tool = EditTool(system_state)
        file_path = temp_dir / "multi.txt"
        file_path.write_text("foo bar foo baz foo")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "foo",
            "new_string": "replaced",
            "replace_all": False
        })
        
        assert "error" in result.data
        assert "appears 3 times" in result.data["error"]
    
    def test_string_not_found(self, system_state, sample_files):
        """Test error when old_string not found"""
        tool = EditTool(system_state)
        
        result = tool.execute({
            "file_path": str(sample_files["python_file"]),
            "old_string": "NONEXISTENT_STRING_12345",
            "new_string": "replacement"
        })
        
        assert "error" in result.data
        assert "not found" in result.data["error"].lower()
    
    def test_preserve_indentation(self, system_state, temp_dir):
        """Test that indentation is preserved"""
        tool = EditTool(system_state)
        file_path = temp_dir / "indent.py"
        file_path.write_text("""
def function():
    if True:
        print("hello")
""")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": '        print("hello")',
            "new_string": '        print("world")'
        })
        
        assert result.success
        content = file_path.read_text()
        assert '        print("world")' in content  # 8 spaces preserved
    
    def test_multiline_replacement(self, system_state, temp_dir):
        """Test replacing multiline strings"""
        tool = EditTool(system_state)
        file_path = temp_dir / "multi.txt"
        file_path.write_text("Line 1\nLine 2\nLine 3\nLine 4")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "Line 2\nLine 3",
            "new_string": "Replaced Lines"
        })
        
        assert result.success
        assert "Replaced Lines" in file_path.read_text()
    
    def test_file_not_found(self, system_state):
        """Test error when file doesn't exist"""
        tool = EditTool(system_state)
        
        result = tool.execute({
            "file_path": "/nonexistent/file.txt",
            "old_string": "old",
            "new_string": "new"
        })
        
        assert "error" in result.data
        assert "not found" in result.data["error"].lower()
    
    def test_lint_check_after_edit(self, system_state, temp_dir):
        """Test that lint check runs after Python file edit"""
        tool = EditTool(system_state)
        file_path = temp_dir / "test.py"
        file_path.write_text("def hello():\n    return 'world'\n")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "return 'world'",
            "new_string": "return 'universe'"
        })
        
        assert result.success
        assert "lint_check" in result.data
        assert not result.data["lint_check"]["has_errors"]
    
    def test_edit_creates_syntax_error(self, system_state, temp_dir):
        """Test lint check detects errors introduced by edit"""
        tool = EditTool(system_state)
        file_path = temp_dir / "test.py"
        file_path.write_text("def hello():\n    return 'world'\n")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "return 'world'",
            "new_string": "return 'world"  # Missing closing quote
        })
        
        assert result.success  # Edit succeeds
        assert "lint_check" in result.data
        assert result.data["lint_check"]["has_errors"]
    
    def test_length_tracking(self, system_state, temp_dir):
        """Test old_length and new_length tracking"""
        tool = EditTool(system_state)
        file_path = temp_dir / "test.txt"
        file_path.write_text("Short text")
        
        result = tool.execute({
            "file_path": str(file_path),
            "old_string": "Short",
            "new_string": "Very long expanded"
        })
        
        assert result.success
        assert result.data["old_length"] < result.data["new_length"]

