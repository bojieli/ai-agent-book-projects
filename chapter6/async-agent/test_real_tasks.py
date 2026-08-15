"""Contract tests for real subprocess-backed Experiment 4-6 tasks."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import tasks


def test_unapproved_commands_are_rejected_before_execution():
    with pytest.raises(ValueError, match="unapproved"):
        tasks.resolve_job("python arbitrary.py")
    with pytest.raises(ValueError, match="only"):
        tasks.resolve_job("sh -c 'echo unsafe'")


def test_real_subprocess_completes_with_observed_metrics(monkeypatch):
    async def scenario():
        monkeypatch.setattr(tasks, "TICK_REAL", 0.002)
        completed = []

        async def on_complete(state):
            completed.append(state.task_id)

        manager = tasks.TaskManager(on_complete, lambda *_: None)
        state = manager.start("python analyze_fast.py")
        assert state._task is not None
        await state._task
        result = json.loads(state.result)
        assert completed == [state.task_id]
        assert state.status == "completed"
        assert state.pid and state.pid != os.getpid()
        assert state.returncode == 0
        assert state.progress == 100
        assert state.stdout_sha256 and len(state.stdout_sha256) == 64
        assert state.executable_receipt["mode"] == "real_subprocess"
        assert state.executable_receipt["shell"] is False
        assert state.executable_receipt["returncode"] == 0
        assert result["input_sha256"] == hashlib.sha256(
            tasks.DEFAULT_INPUT.read_bytes()
        ).hexdigest()
        assert result["bytes"] == tasks.DEFAULT_INPUT.stat().st_size
        assert result["lines"] > 100

    asyncio.run(scenario())

def test_cancel_terminates_real_child_process_and_freezes_progress(monkeypatch):
    async def scenario():
        monkeypatch.setattr(tasks, "TICK_REAL", 0.02)

        async def on_complete(_):
            raise AssertionError("cancelled process must not complete")

        manager = tasks.TaskManager(on_complete, lambda *_: None)
        state = manager.start("python analyze_slow.py")
        while state.pid is None:
            await asyncio.sleep(0.001)
        await asyncio.sleep(0.05)
        pid = state.pid
        assert manager.cancel(state.task_id)
        with pytest.raises(asyncio.CancelledError):
            await state._task
        frozen = state.progress
        await asyncio.sleep(0.05)
        assert state.status == "cancelled"
        assert state.progress == frozen < 100
        assert state.executable_receipt["cancelled"] is True
        assert state.returncode is not None
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)

    asyncio.run(scenario())
