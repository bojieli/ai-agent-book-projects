"""Offline regression tests for recurring timer persistence."""

import asyncio
import json
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import timer_tools


class RecurringTimerPersistenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "timers.json"

        fake_config = types.ModuleType("config")
        fake_config.config = types.SimpleNamespace(
            timer=types.SimpleNamespace(storage_path=str(self.storage_path))
        )
        self.config_patch = patch.dict(sys.modules, {"config": fake_config})
        self.config_patch.start()

        timer_tools._active_timers.clear()
        timer_tools._timer_tasks.clear()

    async def asyncTearDown(self):
        tasks = list(timer_tools._timer_tasks.values())
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        timer_tools._timer_tasks.clear()
        timer_tools._active_timers.clear()
        self.config_patch.stop()
        self.temp_dir.cleanup()

    def recurring_timer(self, *, occurrences=1, max_occurrences=3, interval_seconds=3600):
        return {
            "timer_id": "recurring",
            "name": "heartbeat",
            "type": "recurring",
            "interval_seconds": interval_seconds,
            "max_occurrences": max_occurrences,
            "occurrences": occurrences,
            "callback_message": None,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

    def one_shot_timer(self):
        now = datetime.now()
        return {
            "timer_id": "one-shot",
            "name": "later",
            "duration_seconds": 3600,
            "start_time": now.isoformat(),
            "expiry_time": (now + timedelta(hours=1)).isoformat(),
            "callback_message": None,
            "callback_data": {},
            "status": "active",
            "created_at": now.isoformat(),
        }

    def write_timers(self, timers):
        self.storage_path.write_text(json.dumps(timers), encoding="utf-8")

    def read_timers(self):
        return json.loads(self.storage_path.read_text(encoding="utf-8"))

    async def test_load_restores_recurring_and_following_one_shot_timers(self):
        self.write_timers({
            "recurring": self.recurring_timer(),
            "one-shot": self.one_shot_timer(),
        })

        await timer_tools._load_timers()

        self.assertEqual(
            set(timer_tools._active_timers),
            {"recurring", "one-shot"},
        )
        self.assertEqual(
            set(timer_tools._timer_tasks),
            {"recurring", "one-shot"},
        )

    async def test_status_for_active_recurring_timer_does_not_require_expiry(self):
        timer_tools._active_timers["recurring"] = self.recurring_timer()

        result = await timer_tools.get_timer_status("recurring")

        self.assertTrue(result["success"])
        self.assertEqual(result["timer"]["status"], "active")
        self.assertNotIn("remaining_seconds", result["timer"])

    async def test_restored_timer_resumes_count_and_persists_completion(self):
        self.write_timers({
            "recurring": self.recurring_timer(
                occurrences=1,
                max_occurrences=2,
                interval_seconds=0,
            )
        })

        with patch.object(
            timer_tools,
            "_trigger_timer_callback",
            new_callable=AsyncMock,
        ) as callback:
            await timer_tools._load_timers()
            await asyncio.wait_for(timer_tools._timer_tasks["recurring"], timeout=1)

        timer = timer_tools._active_timers["recurring"]
        persisted = self.read_timers()["recurring"]
        self.assertEqual(callback.await_count, 1)
        self.assertEqual(timer["occurrences"], 2)
        self.assertEqual(timer["status"], "completed")
        self.assertEqual(persisted["occurrences"], 2)
        self.assertEqual(persisted["status"], "completed")

    async def test_load_completes_legacy_active_timer_already_at_limit(self):
        self.write_timers({
            "recurring": self.recurring_timer(
                occurrences=2,
                max_occurrences=2,
                interval_seconds=0,
            )
        })

        with patch.object(
            timer_tools,
            "_trigger_timer_callback",
            new_callable=AsyncMock,
        ) as callback:
            await timer_tools._load_timers()

        self.assertNotIn("recurring", timer_tools._timer_tasks)
        self.assertEqual(callback.await_count, 0)
        self.assertEqual(
            timer_tools._active_timers["recurring"]["status"],
            "completed",
        )
        self.assertEqual(
            self.read_timers()["recurring"]["status"],
            "completed",
        )


if __name__ == "__main__":
    unittest.main()
