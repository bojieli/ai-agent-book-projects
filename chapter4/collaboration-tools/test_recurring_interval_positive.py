"""Recurring timers with interval_seconds <= 0 must not busy-loop."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import timer_tools as t


async def _probe(interval):
    t._active_timers.clear()
    t._timer_tasks.clear()
    result = await t.set_recurring_timer(interval, max_occurrences=None, timer_name="probe")
    await asyncio.sleep(0.05)
    for task in list(t._timer_tasks.values()):
        task.cancel()
    await asyncio.sleep(0)
    return result


def test_zero_interval_rejected():
    result = asyncio.run(_probe(0))
    assert result["success"] is False
    assert "positive" in result["error"]
    assert t._active_timers == {}


def test_negative_interval_rejected():
    result = asyncio.run(_probe(-5))
    assert result["success"] is False
    assert t._active_timers == {}


def test_positive_interval_still_accepted():
    async def run():
        t._active_timers.clear()
        t._timer_tasks.clear()
        result = await t.set_recurring_timer(60, max_occurrences=1, timer_name="ok")
        for task in list(t._timer_tasks.values()):
            task.cancel()
        await asyncio.sleep(0)
        return result

    result = asyncio.run(run())
    assert result["success"] is True
    assert result["interval_seconds"] == 60
