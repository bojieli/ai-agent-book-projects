"""max_occurrences=0 must stop the recurring timer (not run forever)."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import timer_tools as tt


async def _run():
    # Clear any leftover timers from other tests in this process.
    tt._active_timers.clear()
    for task in list(tt._timer_tasks.values()):
        task.cancel()
    tt._timer_tasks.clear()

    result = await tt.set_recurring_timer(
        interval_seconds=0.02,
        max_occurrences=0,
        timer_name="zero-max",
    )
    assert result["success"] is True
    timer_id = result["timer_id"]

    await asyncio.sleep(0.12)

    status = await tt.get_timer_status(timer_id)
    assert status["success"] is True
    timer = status["timer"]
    assert timer["status"] == "completed"
    assert timer["occurrences"] == 0

    # Positive max_occurrences still stops at the limit.
    result2 = await tt.set_recurring_timer(
        interval_seconds=0.02,
        max_occurrences=2,
        timer_name="two-max",
    )
    await asyncio.sleep(0.15)
    status2 = await tt.get_timer_status(result2["timer_id"])
    assert status2["timer"]["status"] == "completed"
    assert status2["timer"]["occurrences"] == 2


def test_max_occurrences_zero_completes_without_spinning():
    asyncio.run(_run())
