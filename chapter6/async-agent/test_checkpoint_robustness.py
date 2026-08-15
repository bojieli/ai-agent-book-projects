"""
Test suite locking out TypeError and FileNotFoundError in AgentRuntime checkpointing
when tasks is None, trajectory is None, or destination directory doesn't exist.
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from runtime import AgentRuntime
from tasks import TaskManager


def test_save_checkpoint_creates_nested_directories():
    """
    Ensure save_checkpoint automatically creates parent directories when saving.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = AgentRuntime.__new__(AgentRuntime)
        runtime.snapshot = MagicMock(return_value={'trajectory': [], 'tasks': []})
        runtime.log = MagicMock()
        
        target_path = os.path.join(tmpdir, "nested", "sub", "checkpoint.json")
        result_path = runtime.save_checkpoint(target_path)
        
        assert result_path == target_path
        assert os.path.exists(target_path)


def test_load_checkpoint_handles_null_tasks_and_trajectory():
    """
    Ensure load_checkpoint gracefully handles JSON containing "tasks": null and
    "trajectory": null with a real TaskManager without raising TypeError.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "checkpoint.json")
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump({'trajectory': None, 'tasks': None}, f)

        runtime = AgentRuntime.__new__(AgentRuntime)
        runtime.tasks = TaskManager(on_complete=MagicMock(), log=MagicMock())
        runtime.log = MagicMock()

        data = runtime.load_checkpoint(target_path)
        assert data['tasks'] is None
        assert data['trajectory'] is None
        assert len(runtime.trajectory) == 0
        assert len(runtime.tasks._tasks) == 0
        runtime.log.assert_called_once()

def test_load_checkpoint_handles_null_task_fields_and_event_fields():
    """
    Ensure load_checkpoint gracefully handles JSON containing null fields in
    task records and trajectory events without setting None for non-optional attributes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "checkpoint.json")
        checkpoint_data = {
            'trajectory': [
                {
                    'type': 'user.input',
                    'message': {'role': 'user', 'content': 'hello'},
                    'label': None,
                    'ts': None,
                }
            ],
            'tasks': [
                {
                    'task_id': 'T1',
                    'command': 'python analyze_logs.py',
                    'rate': 50.0,
                    'progress': 100.0,
                    'status': 'completed',
                    'result': None,
                    'executable_receipt': None,
                }
            ]
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f)

        runtime = AgentRuntime.__new__(AgentRuntime)
        runtime.tasks = TaskManager(on_complete=MagicMock(), log=MagicMock())
        runtime.log = MagicMock()

        runtime.load_checkpoint(target_path)

        ev = runtime.trajectory[0]
        assert isinstance(ev.label, str)
        assert ev.label == ""
        assert isinstance(ev.ts, float)

        st = runtime.tasks.query('T1')
        assert isinstance(st.result, str)
        assert st.result == ""
        assert isinstance(st.executable_receipt, dict)
        assert st.executable_receipt == {}