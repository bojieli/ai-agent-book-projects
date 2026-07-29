"""
Test suite locking out TypeError and FileNotFoundError in AgentRuntime checkpointing
when tasks is None or destination directory doesn't exist.
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from runtime import AgentRuntime


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


def test_load_checkpoint_handles_null_tasks():
    """
    Ensure load_checkpoint logs task counts without TypeError when tasks key is None.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = os.path.join(tmpdir, "checkpoint.json")
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump({'trajectory': [], 'tasks': None}, f)

        runtime = AgentRuntime.__new__(AgentRuntime)
        runtime.tasks = MagicMock()
        runtime.log = MagicMock()

        data = runtime.load_checkpoint(target_path)
        assert data['tasks'] is None
        runtime.log.assert_called_once()
