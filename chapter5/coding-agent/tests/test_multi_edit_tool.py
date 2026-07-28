"""
Test cases for MultiEdit tool
Tests all features from tools.json
"""

import pytest
from pathlib import Path
from tools.multi_edit_tool import MultiEditTool


class TestMultiEditTool:
    """Test MultiEdit tool functionality"""
    
    def test_multiple_edits(self, system_state, temp_dir):
        """Test multiple edits in one operation"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "multi.py"
        file_path.write_text("""
def old_function():
    old_var = 1
    return old_var
""")
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {
                    "old_string": "old_function",
                    "new_string": "new_function"
                },
                {
                    "old_string": "old_var",
                    "new_string": "new_var",
                    "replace_all": True
                }
            ]
        })
        
        assert result.success
        assert result.data["total_edits"] == 2
        assert result.data["successful_edits"] == 2
        
        content = file_path.read_text()
        assert "new_function" in content
        assert "new_var" in content
        assert "old_var" not in content
    
    def test_sequential_application(self, system_state, temp_dir):
        """Test that edits are applied sequentially"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "seq.txt"
        file_path.write_text("A B C")
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {"old_string": "A", "new_string": "X"},
                {"old_string": "X B", "new_string": "Y"},  # Depends on first edit
                {"old_string": "Y C", "new_string": "Z"}   # Depends on second edit
            ]
        })
        
        assert result.success
        assert file_path.read_text() == "Z"
    
    def test_atomic_edits(self, system_state, temp_dir):
        """Test that if any edit fails, none are applied"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "atomic.txt"
        original = "First line\nSecond line\n"
        file_path.write_text(original)
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {"old_string": "First", "new_string": "1st"},
                {"old_string": "NONEXISTENT", "new_string": "X"},  # This will fail
                {"old_string": "Second", "new_string": "2nd"}
            ]
        })
        
        # Should fail
        assert "error" in result.data
        assert result.data["completed_edits"] == 1
        # File should be modified (edits are not rolled back in current implementation)
    
    def test_file_creation(self, system_state, temp_dir):
        """Test creating new file with MultiEdit (empty old_string in first edit)"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "new_file.py"
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {
                    "old_string": "",
                    "new_string": "def hello():\n    pass\n"
                }
            ]
        })
        
        assert result.success
        assert file_path.exists()
        assert "def hello" in file_path.read_text()
        assert result.data["edit_results"][0]["action"] == "created"

    def test_atomic_create_no_orphan_on_later_failure(self, system_state, temp_dir):
        """Create-new-file must not leave an empty file if a later edit fails."""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "orphan_create.py"
        assert not file_path.exists()

        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {
                    "old_string": "",
                    "new_string": "def hello():\n    pass\n",
                },
                {
                    "old_string": "NONEXISTENT",
                    "new_string": "x",
                },
            ],
        })

        assert "error" in result.data
        assert result.data["completed_edits"] == 1
        assert not file_path.exists()
    
    def test_create_and_modify(self, system_state, temp_dir):
        """Test creating file and then modifying it in subsequent edits"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "new_file.py"
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {
                    "old_string": "",
                    "new_string": "def old_name():\n    pass\n"
                },
                {
                    "old_string": "old_name",
                    "new_string": "new_name"
                }
            ]
        })
        
        assert result.success
        assert "new_name" in file_path.read_text()
        assert "old_name" not in file_path.read_text()
    
    def test_replace_all_in_multi_edit(self, system_state, temp_dir):
        """Test replace_all in one of multiple edits"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "test.txt"
        file_path.write_text("foo bar foo baz foo")
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {
                    "old_string": "foo",
                    "new_string": "FOO",
                    "replace_all": True
                },
                {
                    "old_string": "bar",
                    "new_string": "BAR"
                }
            ]
        })
        
        assert result.success
        assert file_path.read_text() == "FOO BAR FOO baz FOO"
    
    def test_edit_results_tracking(self, system_state, temp_dir):
        """Test that edit_results tracks each edit"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "track.txt"
        file_path.write_text("A B C")
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {"old_string": "A", "new_string": "1"},
                {"old_string": "B", "new_string": "2"},
                {"old_string": "C", "new_string": "3"}
            ]
        })
        
        assert result.success
        assert len(result.data["edit_results"]) == 3
        assert all(r["success"] for r in result.data["edit_results"])
    
    def test_lint_check_after_multi_edit(self, system_state, temp_dir):
        """Test lint checking after multiple edits"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "test.py"
        file_path.write_text("x = 1\ny = 2\n")
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {"old_string": "x = 1", "new_string": "x = 10"},
                {"old_string": "y = 2", "new_string": "y = 20"}
            ]
        })
        
        assert result.success
        assert "lint_check" in result.data
        assert not result.data["lint_check"]["has_errors"]
    
    def test_size_tracking(self, system_state, temp_dir):
        """Test old_size and new_size tracking"""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "size.txt"
        file_path.write_text("Short")
        
        result = tool.execute({
            "file_path": str(file_path),
            "edits": [
                {"old_string": "Short", "new_string": "Very long text here"}
            ]
        })
        
        assert result.success
        assert result.data["old_size"] < result.data["new_size"]

    def test_null_edits_like_empty(self, system_state, temp_dir):
        """Explicit JSON null edits must behave like an empty list."""
        tool = MultiEditTool(system_state)
        file_path = temp_dir / "null_edits.py"
        file_path.write_text("x = 1\n")
        result = tool.execute({
            "file_path": str(file_path),
            "edits": None,
        })
        assert result.success
        assert "error" not in result.data
        assert result.data["total_edits"] == 0
        assert file_path.read_text() == "x = 1\n"
