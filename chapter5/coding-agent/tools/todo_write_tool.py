"""
TodoWrite tool - Task list management
"""

from typing import Dict, Any
from .base import BaseTool


class TodoWriteTool(BaseTool):
    """Creates and manages structured task lists"""
    
    @property
    def name(self) -> str:
        return "TodoWrite"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update TODO list
        
        - Use this tool to create and manage a structured task list
        - Track progress, organize complex tasks
        - Helps user understand progress
        """
        # JSON null for required todos: same as empty list (LLM omit-as-null).
        todos = params["todos"]
        if todos is None:
            todos = []

        # Validate todo format
        for todo in todos:
            if not isinstance(todo, dict) or not all(k in todo for k in ["id", "content", "status"]):
                return {"error": "Each todo must be a dict and must have id, content, and status"}
            if todo["status"] not in ["pending", "in_progress", "completed"]:
                return {"error": f"Invalid status: {todo['status']}"}
        
        # Update state
        self.state.todos = todos
        
        return {
            "total_todos": len(todos),
            "pending": sum(1 for t in todos if t["status"] == "pending"),
            "in_progress": sum(1 for t in todos if t["status"] == "in_progress"),
            "completed": sum(1 for t in todos if t["status"] == "completed")
        }

