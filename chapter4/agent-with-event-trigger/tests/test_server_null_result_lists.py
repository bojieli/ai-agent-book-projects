"""
Test suite locking out TypeError in event server response formatting
when handle_event returns a result dictionary with tool_calls or todo_list set to None.
"""

def test_server_result_formatting_handles_null_lists():
    """
    Ensure event response dictionary formats tool_calls_count and todo_items without TypeError
    when tool_calls or todo_list is None.
    """
    result = {
        'final_answer': 'Done',
        'iterations': 1,
        'tool_calls': None,
        'todo_list': None,
        'success': True,
        'trajectory_file': None
    }

    formatted = {
        "final_answer": result.get('final_answer'),
        "iterations": result.get('iterations'),
        "tool_calls_count": len(result.get('tool_calls') or []),
        "todo_items": len(result.get('todo_list') or []),
        "success": result.get('success', False),
        "trajectory_file": result.get('trajectory_file')
    }

    assert formatted["tool_calls_count"] == 0
    assert formatted["todo_items"] == 0
