"""
Test cases for TodoWrite tool
Tests all features from tools.json
"""

import pytest
from tools.todo_write_tool import TodoWriteTool


class TestTodoWriteTool:
    """Test TodoWrite tool functionality"""
    
    def test_create_todo_list(self, system_state):
        """Test creating a TODO list"""
        tool = TodoWriteTool(system_state)
        
        todos = [
            {"id": "1", "content": "First task", "status": "pending"},
            {"id": "2", "content": "Second task", "status": "in_progress"},
            {"id": "3", "content": "Third task", "status": "completed"}
        ]
        
        result = tool.execute({"todos": todos})
        
        assert result.success
        assert result.data["total_todos"] == 3
        assert result.data["pending"] == 1
        assert result.data["in_progress"] == 1
        assert result.data["completed"] == 1
        
        # Verify state was updated
        assert system_state.todos == todos
    
    def test_update_todo_list(self, system_state):
        """Test updating an existing TODO list"""
        tool = TodoWriteTool(system_state)
        
        # Create initial list
        initial_todos = [
            {"id": "1", "content": "Task 1", "status": "pending"}
        ]
        tool.execute({"todos": initial_todos})
        
        # Update list
        updated_todos = [
            {"id": "1", "content": "Task 1", "status": "completed"}
        ]
        result = tool.execute({"todos": updated_todos})
        
        assert result.success
        assert result.data["completed"] == 1
        assert result.data["pending"] == 0
    
    def test_todo_validation_missing_fields(self, system_state):
        """Test validation rejects TODOs missing required fields"""
        tool = TodoWriteTool(system_state)
        
        # Missing 'status' field
        result = tool.execute({
            "todos": [{"id": "1", "content": "Task"}]
        })
        
        assert "error" in result.data
        assert "must have" in result.data["error"]
    
    def test_todo_validation_invalid_status(self, system_state):
        """Test validation rejects invalid status values"""
        tool = TodoWriteTool(system_state)
        
        result = tool.execute({
            "todos": [
                {"id": "1", "content": "Task", "status": "invalid_status"}
            ]
        })
        
        assert "error" in result.data
        assert "Invalid status" in result.data["error"]
    
    def test_valid_status_values(self, system_state):
        """Test all valid status values"""
        tool = TodoWriteTool(system_state)
        
        todos = [
            {"id": "1", "content": "Task 1", "status": "pending"},
            {"id": "2", "content": "Task 2", "status": "in_progress"},
            {"id": "3", "content": "Task 3", "status": "completed"}
        ]
        
        result = tool.execute({"todos": todos})
        
        assert result.success
        assert result.data["pending"] == 1
        assert result.data["in_progress"] == 1
        assert result.data["completed"] == 1
    
    def test_empty_todo_list(self, system_state):
        """Test creating empty TODO list"""
        tool = TodoWriteTool(system_state)
        
        result = tool.execute({"todos": []})
        
        assert result.success
        assert result.data["total_todos"] == 0
        assert result.data["pending"] == 0
        assert result.data["in_progress"] == 0
        assert result.data["completed"] == 0
    
    def test_statistics_calculation(self, system_state):
        """Test that statistics are calculated correctly"""
        tool = TodoWriteTool(system_state)
        
        todos = [
            {"id": "1", "content": "A", "status": "pending"},
            {"id": "2", "content": "B", "status": "pending"},
            {"id": "3", "content": "C", "status": "in_progress"},
            {"id": "4", "content": "D", "status": "completed"},
            {"id": "5", "content": "E", "status": "completed"},
            {"id": "6", "content": "F", "status": "completed"}
        ]
        
        result = tool.execute({"todos": todos})
        
        assert result.success
        assert result.data["total_todos"] == 6
        assert result.data["pending"] == 2
        assert result.data["in_progress"] == 1
        assert result.data["completed"] == 3

    def test_null_todos_like_empty(self, system_state):
        """Explicit JSON null todos must behave like an empty list."""
        tool = TodoWriteTool(system_state)
        result = tool.execute({"todos": None})
        assert result.success
        assert "error" not in result.data
        assert result.data["total_todos"] == 0
    def test_todo_validation_non_dict_item(self, system_state):
        """Test validation handles non-dict items in todos list gracefully."""
        tool = TodoWriteTool(system_state)
        result = tool.execute({"todos": [123]})
        assert "error" in result.data
        assert "Each todo must be a dict" in result.data["error"]

